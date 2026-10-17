# 04 — 运行时流程

端到端时序、多端绑定与安全边界。HTTP 路径名以现有面板 API 为参照，实现阶段可别名兼容。

## 1. 总览

```text
发布者托管 marketplace.json + app-package.json
        ↓
用户在 APP 添加 market_url
        ↓
拉索引（直连或 SERVER 代理）→ 按目标设备 capabilities 过滤
        ↓
安装：SERVER 拉 package → 校验 → 存配置/密钥
        ↓
设备 GET 已安装清单 → 用户/语音 invoke
        ↓
SERVER 调上游 → 规范化 Content Envelope → 端选 Surface 渲染
```

## 2. 能力声明

- 固件/APP 启动时持有静态或半静态 `DeviceCapabilities`（随固件版本变）。
- **诚实申报**：只包含本构建已实现可验收的能力；profile 模板中未实现项须 `disabled` 或省略。硬件有扬声器 ≠ 已有 `media.play_*`。见 [00-capabilities.md](00-capabilities.md) §3.6、[06-platform-profiles.md](06-platform-profiles.md)。
- APP 管理墙板时：使用该墙板**上报**的 capabilities 作为「目标设备」，不要只用产品名臆造。
- 固件升级可增加 capabilities；已安装应用若 `requires` 仍满足则继续启用，否则标记 `disabled`。

## 3. 浏览与安装

### 3.1 APP

1. 保存用户 `market_url` 列表。
2. `auto` 拉取索引；校验 `schema_version`。
3. 对每个 app 计算 `installable` / `missing_capabilities`。
4. 用户安装 → 调用 SERVER（示例语义）：
   - `POST /api/…/skills/install` `{ market_id, app_id, package_url, scope, device_id? }`
5. SERVER 拉取 package（HTTPS、大小上限、JSON Schema）。
6. 二次 `requires` / `surfaces` / `min_protocol`。
7. 返回 `config_schema` 表单；用户提交；`secret` 加密存 SERVER。

### 3.2 墙板

- 不拉市场索引。
- `GET /api/devices/{panelId}/panel/skills`：已安装且对本机能力可启用的脱敏清单。
- 能力不足：`enabled: false` + `missing_capabilities`，勿当可 invoke。

## 4. Invoke

```text
端 / MCP
  → POST …/skills/{instance_or_app}/invoke
  → Body: invoke params（无密钥）
  → Host 附 Auth 调上游（按安装记录解析，含 market_id）
  → 若上游已是 Envelope：校验 + 按 limits 裁剪后透传
  → 若上游非 Envelope：仅当该 Host 显式提供特例转换（非协议义务）；否则应失败并提示发布者改用档 A/B
  → 返回端
```

- **默认路径**：上游 = Envelope（[08-publishers.md](08-publishers.md) 档 A/B）。Host **不得**因「无本厂 adapter」拒绝合法 Envelope 上游。
- 超时建议 ≤ 6s；失败返回 `status:error`。
- 响应体积不得超过目标设备 `limits.max_content_bytes`（Host 宜按设备档案裁剪摘要 + 分页）。
- 语音：统一 `skill.invoke`（名称以端实现为准）→ 同上；UI/播控解析 Envelope，不解析模型闲聊文本。
- 路由键：安装实例须能回溯 `(market_id, app_id)`，避免多市场同名冲突。

## 5. 渲染与交互

1. 选 Surface：`display.preferred_surface` ∈ 本机 `surfaces`，否则按 [05-surfaces.md](05-surfaces.md) 优先级。
2. 选 card_type：支持则渲染，否则降级矩阵。
3. Action：按 `run` + capability 显示；点击：
   - **禁止**在 UI 主线程 / LVGL 回调内同步 HTTP。
   - ESP：本地乐观更新 → `nl_cmd_async`（或等价）后台 invoke。
4. 播放：`media.play_local` / `media.play_via_xiaozhi` / `handoff`；URL 过期须重新 invoke。

## 6. 推送（可选）

云端主动更新（新闻、天气）可用 MQTT / `panel/notify` 下发 **同一 Envelope**，勿依赖 MCP `notifications/*`（小智侧可能忽略）。`ttl_sec` 控制缓存。

## 7. 多端与 scope

| scope | 行为 |
|-------|------|
| `account` | 一处安装（键含 `market_id`+`app_id`）；手机与墙板各自按能力启用；同键不同 Surface |
| `device` | 仅该 `device_id` 清单可见 |

卸载：Host 删实例；设备 list 不再返回。同账号下卸载市场 A 的应用不影响市场 B 的同名 `app_id`。

## 8. 安全

| 规则 | 要求 |
|------|------|
| 传输 | 市场 / package / 媒体 URL 使用 HTTPS |
| 密钥 | 不下发设备；不进日志明文 |
| 体积 | 遵守 `limits.max_content_bytes`；SERVER 可硬截断并标 `truncated:true` |
| 图片 | 遵守 `limits.image`；无 `content.image` 则剥图 |
| 字段 | 禁止可执行脚本、LVGL 树、`data:` 可执行载荷 |
| 市场 | SERVER 可维护 URL 黑名单 / 证书钉扎策略 |
| 播放 URL | 尊重 `expires_at`；勿长期持久化 |

## 9. 与控家并行

| 通道 | 用途 |
|------|------|
| layout + `panel/command` | 灯、继电器、PWM、情景 |
| 本协议 skills | 第三方内容与工具 |

勿用技能 Envelope 替代设备开关指令；勿在技能里下发任意 GPIO。
