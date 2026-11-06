# 10 — 主动消息提醒与推送（Push & Notice）

第三方应用在后台任务完成、外部状态变化、阈值告警或待用户确认时，经 Host 云向墙板与多端主动投递轻量提醒（Notice）的统一契约。

## 0. 规范性边界（先读）

与 [04-runtime-flow.md](04-runtime-flow.md) §0 一致，本章节严格区分**协议契约**与 **Host 产品实现**：

| 内容 | 规范性 |
|------|--------|
| 应用包 `push` 声明结构（§2 + [schemas/app-package.schema.json](schemas/app-package.schema.json)） | **协议** |
| Notice 载荷形状、三态 `mode`、`severity`、`notice_id` 幂等、`coalesce_key` 折叠去重、`ttl_sec` 与 `invoke` 衔接语义（§4 + [schemas/notice.schema.json](schemas/notice.schema.json)） | **协议** |
| 端重启/断线重连后的未读对账与「不重复打扰」规则（§3.2） | **协议** |
| `push_token` 的实例级授权边界、配额/最高级别钳制（clamp）语义（§2.2、§5） | **协议** |
| **应用上游 ↔ Host** 的 HTTP 入站路径名（如示例中的 `POST /api/push/v1/notices`） | **非协议**（Host 产品文档定义） |
| **Host ↔ 端**的下行推送传输通道（MQTT topic、WebSocket 帧、HTTP 对账路径） | **非协议**（Host 与端自定） |
| 端顶栏未读角标、横幅 Toast、消息中心抽屉的具体像素布局与动效 | **非协议**（各端自定外观） |

---

## 1. 核心原则：推提醒（Notice），拉内容（Envelope）

1. **轻量提醒与重内容分离**：主动推送通道只传递 ≤ 1 KB 的结构化提醒元数据（`Notice`），**禁止**在推送载荷中直接塞入完整业务列表、长正文或 UI 控件树。
2. **点开或自动展开回流标准 Invoke**：当用户点击通知（或高优通知自动展开）时，端携带 `notice.invoke` 中的 `app_id` / `instance_id` 与 `params`，走标准 [04-runtime-flow.md](04-runtime-flow.md) §4 `invoke` 流程向 Host 拉取 [03-content.md](03-content.md) Content Envelope 并选 Surface 渲染。
3. **端零新增卡片类型**：任何支持本协议标准 `card_type`（`list` / `plain_result` / `news_list` / `weather` 等）的应用，接入主动推送时**无需固件新增专用 UI 页面**。

---

## 2. 应用包 `push` 声明

应用需要主动推送能力时，在 [02-app-package.md](02-app-package.md) 应用包根对象声明可选字段 `push`：

```json
{
  "schema_version": 1,
  "app_id": "dsh.task",
  "version": "1.1.0",
  "name": "任务管家",
  "min_protocol": 1,
  "requires": ["content.list", "action.invoke"],
  "invoke": {
    "method": "POST",
    "url": "https://api.example.com/v1/tasks/status"
  },
  "push": {
    "modes": ["info", "action", "alert"],
    "max_severity": "warning",
    "min_interval_sec": 30
  }
}
```

### 2.1 字段定义

| 字段 | 类型 | 要求 |
|------|------|------|
| `push.modes` | `string[]` | 可选。应用会使用的通知模式子集，取值 `info` \| `action` \| `alert`；缺省 `["info"]` |
| `push.max_severity` | `string` | 可选。应用可发送的最高严重级别：`normal` \| `warning` \| `critical`；缺省 `normal` |
| `push.min_interval_sec` | `integer` | 可选。同一安装实例允许的最小推送间隔秒数（`1`–`86400`），缺省 `30` |

### 2.2 Host 强制钳制（Clamp）与配额

- **级别钳制（MUST）**：若上游推送请求的 `severity` 高于包声明的 `push.max_severity`（顺序：`normal < warning < critical`），Host **必须**将其降级（clamp）为 `max_severity` 或直接拒绝，防止普通信息类应用滥用 `critical` 红色告警与半夜亮屏响铃。
- **模式钳制（MUST）**：若请求 `mode` 不在 `push.modes` 声明集合内，Host **必须**将其降级为 `info` 或拒绝。
- **频率限制（SHOULD）**：Host **宜**按 `(owner, instance_id)` 执行不低于 `min_interval_sec` 的限流；超限时返回 `rate_limited`（但含相同 `coalesce_key` 的状态收尾/消警更新可由 Host 策略豁免）。

---

## 3. 去重、折叠与断电重启保持（硬性）

墙板等常驻设备面临 MQTT 重连重放、断网积压、断电重启等场景。Host 与端**必须**共同保证「未读不丢、绝不重复打扰」：

### 3.1 四层去重机制

| 层级 | 字段 / 机制 | 规范要求 |
|------|-------------|----------|
| 1. 唯一幂等键 | `notice_id` | 每条通知具备全局或单面板唯一 `notice_id`（建议 16–40 字符）。端收到本地未读库中已存在的 `notice_id` 时，**必须**静默忽略，**禁止**再次弹 Toast、响铃或自动 `invoke` |
| 2. 同源折叠键 | `coalesce_key` | 同一业务会话或同一监测指标（如 `"dsh:session:s_42"`、`"sensor:co2:living_room"`）的后续推送携带相同 `coalesce_key`。Host 与端收到同 `coalesce_key` 的新通知时，**必须**原位替换旧未读条目（未读总数不累加） |
| 3. 生存期淘汰 | `ttl_sec` | 通知有效秒数（默认 `300`，范围 `10`–`86400`）。超时未处理的 `pending` 通知自动转为 `expired`，不再向重连或重启的端下发 |
| 4. 已读墓碑环 | `notice_clear` / Tombstone | 用户在端上点开或划掉通知后，端立即将该 `notice_id` 记入本地短期墓碑环并异步通知 Host 标为 `resolved`；若异步请求完成前发生重连对账，端**必须**用墓碑环过滤掉刚消警的 `notice_id`，防止界面「死而复生」 |

### 3.2 重启与断线重连对账语义

1. **端本地持久化**：端收到新通知或状态变更时，**应**将当前未读列表持久化至本地非易失存储（如 Flash / NVS），确保断电重启首帧即可恢复未读角标。
2. **云端真值静默对齐**：端开机启动（Bootstrap）与长连接重连成功时，向 Host 拉取当前有效 `pending` 未读列表并与本地缓存对齐。
3. **静默对齐禁令（MUST）**：开机与重连拉取到的历史未读通知，**只更新顶栏未读角标与消息中心列表**，**严禁**逐条重新弹横幅 Toast、严禁重复播放提示音、严禁自动触发 `invoke` 抢占用户当前屏幕。

---

## 4. Notice 载荷结构

机器可读 Schema：[schemas/notice.schema.json](schemas/notice.schema.json)。

```json
{
  "schema_version": 1,
  "notice_id": "9f8c7b6a5d4e3f2a1b0c9d8e7f6a5b4c",
  "app_id": "dsh.task",
  "instance_id": "com.example.market::dsh.task",
  "mode": "action",
  "severity": "warning",
  "title": "部署脚本需要你确认是否继续",
  "coalesce_key": "dsh.task:session:build_20261103",
  "ttl_sec": 600,
  "wake": true,
  "invoke": {
    "app_id": "com.example.market::dsh.task",
    "params": {
      "session": "build_20261103"
    }
  }
}
```

### 4.1 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `notice_id` | `string` | 端下行必填 | 幂等唯一 ID（`[A-Za-z0-9_:-]{1,64}`）。应用入站缺省时由 Host 生成 |
| `app_id` | `string` | 是 | 来源应用 ID（由 Host 根据鉴权凭据注入或校验） |
| `instance_id` | `string` | 宜 | 安装实例键（`market_id::app_id`），多市场同名安全路由 |
| `mode` | `string` | 是 | `info`（轻通知）\| `action`（待确认交互）\| `alert`（告警） |
| `severity` | `string` | 否 | `normal`（默认）\| `warning` \| `critical` |
| `title` | `string` | 是 | 简短提醒文案（1–120 字），供横幅 Toast 与消息中心列表直接展示 |
| `coalesce_key` | `string` | 否 | 同源折叠键（≤ 64 字符）；相同键的新通知替换旧未读 |
| `ttl_sec` | `integer` | 否 | 有效期秒数，默认 `300`，范围 `10`–`86400` |
| `wake` | `boolean` | 否 | 息屏时是否点亮屏幕；缺省由 `mode` + `severity` 推导（`action` 或 `alert`+`warning/critical` 默认 `true`） |
| `invoke` | `object` | 否 | `{ "app_id": "...", "params": { ... } }`。用户点击「查看」或高优自动展开时调用的目标与参数 |
| `disposition` | `string` | 否 | 入站专用：`pending`（缺省，创建/更新未读）\| `resolved`（上游消警）。见 §5.1 |

### 4.2 三态行为矩阵

| `mode` | 典型场景 | 息屏行为 | 到达时即时反馈 | 何时执行 `invoke` 拉取 Envelope |
|--------|----------|----------|----------------|--------------------------------|
| `info` | 每日摘要、任务完成、快递到达 | `wake=false` 时入延迟队列，亮屏再吐 Toast；未读角标即时 +1 | 顶部 Toast + 未读角标 | **不自动拉取**；仅当用户点开消息中心并点「查看」时拉取 |
| `action` | 审批确认、二选一交互 | 点亮屏幕 | 顶部 Toast + 未读角标（橙色）+ 自动/一键展开 | 亮屏后自动调起 `invoke` 渲染带 `actions[]` 的卡片，或由用户在消息中心点「查看」 |
| `alert` | 传感器超标、安防/离线告警 | `warning`/`critical` 点亮屏幕 | `critical` 播放告警提示音 + 红色未读角标 + 顶部 Toast | `critical`（或显式带 `invoke`）自动调起 `invoke` 展示告警卡片 |

---

## 5. 入站鉴权与安全边界（应用上游 → Host）

1. **实例级 `push_token`（MUST）**：
   - 当用户安装声明了 `push` 的应用包时，Host 为该安装实例签发独立的 `push_token`（Host 数据库仅存 SHA-256 哈希，明文仅在签发或轮换时返回一次）。
   - 应用上游推送时通过鉴权头（如 `Authorization: Bearer <push_token>`）向 Host 证明身份。
2. **禁止跨应用/跨账号伪造（MUST）**：
   - Host 凭 `push_token` 反查对应的 `(owner, market_id, app_id, scope, bound_device_id)`，**强制覆盖**下发载荷中的 `app_id` 与 `instance_id`。
   - 若该安装实例为 `scope="device"`，Host **必须**只投递给 `bound_device_id`；若上游请求指定了其他 `device_id`，Host **必须**拒绝（`403 Forbidden`）。
   - 若该安装实例为 `scope="account"`，上游可指定该 `owner` 名下的某一目标设备，或缺省由 Host 广播给该 `owner` 名下所有支持通知的面板。
3. **卸载/禁用即刻吊销（MUST）**：
   - 用户卸载应用或将 `is_enabled` 置为 `false` 时，关联的 `push_token` 立即失效，后续入站推送一律返回 `401 Unauthorized`。
4. **消警同步（`notice_clear`）**：
   - 任一端消警后，Host 将通知状态更新为 `resolved`，并向同账号其余在线面板下发 `notice_clear { "notice_id": "..." }`，实现多面板一处已读、处处消警。

### 5.1 上游消警（`disposition=resolved`，Evolution B）

应用上游在业务侧已处理完同一事务（例如客服已回复、工单已关闭）时可主动消警，避免墙板未读角标悬挂到 `ttl_sec`：

| 项 | 要求 |
|----|------|
| 字段 | 入站体可选 `disposition`：`pending`（缺省）\| `resolved` |
| 匹配键 | `disposition=resolved` 时**必须**提供 `coalesce_key` 或 `notice_id`（或二者皆有） |
| Host 行为（MUST） | 在 `push_token` 绑定的 owner / 目标面板范围内，将匹配的 `pending` 通知标为 `resolved`，并向对应在线面板下发已有的 `notice_clear { "notice_id": "..." }` |
| 匹配范围 | 有 `notice_id` 时按 id 精确消警；否则按 `coalesce_key` 消掉该面板上同键的全部 `pending` |
| 响应 | 成功返回 `ok` 与 `cleared_count`；无匹配未读时仍返回 `ok` 且 `cleared_count=0`（幂等） |
| 旧端 | 不认识入站字段的 Host 实现可忽略本字段；已实现端仅消费既有 `notice_clear`，无需改固件 |

