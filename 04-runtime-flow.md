# 04 — 运行时流程

端到端时序、多端绑定与安全边界。

## 0. 本文里哪些是协议、哪些不是（先读）

| 内容 | 规范性 |
|------|--------|
| 流程顺序、每一步的**输入语义与产出语义**（谁提供什么、必须校验什么） | **协议** |
| 设备侧「已安装清单」的**文档形状**（§3.2 + [schemas/installed-app-list.schema.json](schemas/installed-app-list.schema.json)）、Envelope 语义、能力匹配 | **协议** |
| HTTP **路径名、方法、鉴权头、响应外壳、错误码 → HTTP 状态码映射** | **非协议**（Host 产品实现） |
| 本文出现的 `/api/…/skills/install`、`/panel/skills/{id}/invoke` 等 | 仅为**可读的示例语义**，第三方不得假定任一 Host 使用这些路径 |

**给端实现者的结论**：端只需要问「我如何从我自己的 Host 取已安装清单 / 如何 invoke」——答案是**载荷结构由本协议规定，传输接口由你的 Host 文档规定**。两个 Host 可以有不同的 URL 而仍然都合规。若你要写可跨 Host 复用的端代码，把 API 适配层留在端外或按你 Host 的文档实现。

## 1. 总览

```text
发布者托管 marketplace.json + app-package.json
        ↓
用户在 APP 添加 market_url
        ↓
拉索引（直连或 Host 云代理）→ 按目标设备 capabilities 过滤
        ↓
安装：Host 云拉 package → 校验 → 存配置/密钥
        ↓
设备 GET 已安装清单 → 用户/语音 invoke
        ↓
Host 云调上游 → 校验/裁剪 Content Envelope → 端选 Surface 渲染
```

## 2. 能力声明

- 固件/APP 启动时持有静态或半静态 `DeviceCapabilities`（随固件版本变）。
- **诚实申报**：只包含本构建已实现可验收的能力；profile 模板中未实现项须 `disabled` 或省略。硬件有扬声器 ≠ 已有 `media.play_*`。见 [00-capabilities.md](00-capabilities.md) §3.6、[06-platform-profiles.md](06-platform-profiles.md)。
- APP 管理墙板时：使用该墙板**上报**的 capabilities 作为「目标设备」，不要只用产品名臆造。
- 固件升级可增加 capabilities；已安装应用若 `requires` 仍满足则继续启用，否则标记 `disabled`。

## 3. 浏览与安装

### 3.1 APP

1. 保存用户 `market_url` 列表（多条并存）。
2. `auto` 拉取索引；校验 `schema_version`；按 §8.1 传输规则；绑定 `market_id ↔ market_url_origin`（[01-marketplace.md](01-marketplace.md) §6.1）。
3. 对每个 app 计算 `installable` / `missing_capabilities`（按**目标设备**申报，非手机本机）。
4. 用户安装 → 请求 Host 云（语义：`{ market_id, app_id, package_url, scope, device_id? }`；**HTTP 路径与鉴权属 Host 产品**，见 §0）：
5. Host 云拉取 package（§8.1 传输；大小上限；校验 `schema_version` 与必填；**未知字段忽略**，勿因额外字段拒装；有 `package_sha256` 则校验，不符即拒）。
6. 用**包内** `requires` / `surfaces` / `min_protocol` 二次校验（与条目冲突取较严，[01-marketplace.md](01-marketplace.md) §1.3）。
7. 返回 `config_schema` 表单；用户提交；`secret` 仅存 Host 云（宜加密），任何面向端的响应不回传值。
8. 写入安装实例，键 `(market_url_origin, market_id, app_id)`；生成 `instance_id`；更新该设备清单。

### 3.2 墙板 / 嵌入式：已安装清单（协议规定的载荷形状）

端**不浏览市场**，只取 Host 下发的已安装清单。该清单的**结构属协议**（否则端无法一致地决定显示、invoke 与降级）：

```json
{
  "schema_version": 1,
  "device_id": "panel-01",
  "apps": [
    {
      "instance_id": "inst_7f3a",
      "market_id": "com.example.nodelio-market",
      "market_name": "示例应用市场",
      "app_id": "music.search",
      "version": "1.0.0",
      "name": "音乐搜索",
      "enabled": true,
      "requires": ["content.music_list", "action.invoke"],
      "optional": ["media.play_local", "content.image"],
      "surfaces": ["card", "now_playing", "voice_reply"],
      "default_card_type": "music_list",
      "fallback_card_type": "list",
      "preferred_surface": "card",
      "density": "compact",
      "max_items": 8,
      "input_schema": { "type": "object", "properties": { "keyword": { "type": "string" } } },
      "config_present": true,
      "deprecated": false,
      "ui": { "entry_title": "音乐", "entry_icon": "music_note" }
    },
    {
      "instance_id": "inst_9b12",
      "market_id": "io.other-market",
      "app_id": "gallery.photo",
      "version": "2.1.0",
      "name": "高清图库",
      "enabled": false,
      "disabled_reason": "missing_capabilities",
      "missing_capabilities": ["content.image_gallery"],
      "requires": ["content.image_gallery", "action.invoke"]
    }
  ]
}
```

| 字段 | 要求 |
|------|------|
| `instance_id` | Host 生成，唯一解析 `(market_url_origin, market_id, app_id)`（[01-marketplace.md](01-marketplace.md) §6.1）。端 invoke 与 MCP 引用用它，**不要**用裸 `app_id` 当路由键 |
| `enabled` | `true` 仅当 `requires ⊆ 本机 capabilities` ∧ surfaces 有交集 ∧ `protocol_version ≥ min_protocol` ∧ 必填配置已填 ∧ 未撤销。`false` 时端**禁止**提供 invoke 入口 |
| `disabled_reason` + `missing_capabilities` | `enabled=false` 时应给出，供 UI 说明「为何不可用」而非静默消失 |
| `requires` / `surfaces` / `min_protocol` | 包内权威值，供端**本地复核**——Host 预过滤不可替代本地计算（[00-capabilities.md](00-capabilities.md) §1） |
| `default_card_type` / **`fallback_card_type`** / `preferred_surface` / `density` / `max_items` | 渲染与降级所需。**`fallback_card_type` 必须下发**：[00-capabilities.md](00-capabilities.md) §5 与 [03-content.md](03-content.md) §5 降级矩阵的第 1 步依赖它，而它只存在于包里；不下发则该步形同虚设 |
| `input_schema` | 单次 invoke 参数（搜索框、MCP 工具参数） |
| `config_present` / `config_missing_keys` | 只给「是否齐备 / 缺哪些属性名」，**禁止**回传任何 secret 或明文配置值 |
| `ui.entry_icon` | 端图标名提示；未识别的名字**必须**回落到端自有默认图标（禁止崩溃、禁止当路径拼接） |

机器可读：[schemas/installed-app-list.schema.json](schemas/installed-app-list.schema.json)；样例：[examples/installed-app-list-panel.json](examples/installed-app-list-panel.json)。


## 4. Invoke

```text
端 / MCP
   body: { "params": { …input_schema 定义的参数… }, "request_id": "…" }
   路由用 instance_id（多市场同名安全）
  → Host 按安装记录解析上游与 Auth（含 market_url_origin / market_id）
  → 若上游已是 Envelope：校验 + 按该端 limits 裁剪后透传
  → 若上游非 Envelope：仅当该 Host 显式提供特例转换（非协议义务）；否则返回 status:error + code:upstream_error
  → 返回端
```

- **默认路径**：上游 = Envelope（[08-publishers.md](08-publishers.md) 档 A/B）。Host **不得**因「无本厂 adapter」拒绝合法 Envelope 上游。
- **HTTP method**：路径与具体 URL 由 Host 实现决定（协议不规定路径）。带参数 body / 有副作用的 invoke 用 `POST`；仅无副作用的纯查询（`app-package.invoke.method=GET`）可用 `GET` 并随查询串传参。两端/Host 须就方法语义一致。
- **请求/响应语义**：请求体只含 `input_schema` 参数，**禁止**携带密钥；响应体是一个完整 Content Envelope（含失败情形——用 HTTP 状态 + `status:"error"` 双轨时，Envelope **必须**仍然合法，见 [03-content.md](03-content.md) §3.1）。
- `request_id`：由**发起方**（端 / Host / 语音链路）生成并原样回带，用于串联日志；Host 不得自行替换后又不告知。格式不限，建议 `[A-Za-z0-9_-]{1,64}`。
- 超时：`invoke.timeout_ms`（默认建议 ≤ 6000ms）；超时 → `status:"error"` + `code:"upstream_timeout"`。
- 响应体积不得超过目标设备 `limits.max_content_bytes`（Host 按设备档案裁剪并标 `truncated: true`）。
- 媒体条目：尊重 `playback.expires_at`（[03-content.md](03-content.md) §2.4）；过期须重新 invoke。
- Host **可**对同一设备 invoke 限流，防刷上游；被限流时返回 `code:"rate_limited"`（策略参数属产品，不进协议枚举）。
- 语音：统一 `skill.invoke`（名称以端实现为准）→ 同上；UI/播控解析 Envelope，不解析模型闲聊文本。
- **嵌套 invoke 的解析（`content[].type:"action"` 与 `actions[].run="invoke"`）**：见 [03-content.md](03-content.md) §3.2 —— 目标是**已安装实例**，不是裸 `app_id`。
- 路由键：安装实例须能回溯 `(market_url_origin, market_id, app_id)`，避免多市场同名冲突（[01-marketplace.md](01-marketplace.md) §6.1）。

## 5. 渲染与交互

1. 选 Surface：`display.preferred_surface` ∈ 本机 `surfaces`，否则按 [05-surfaces.md](05-surfaces.md) 优先级。
2. 选 card_type：支持则渲染，否则降级矩阵。
3. Action：按 `run` + capability 显示；点击：
   - **禁止**在任何 UI 主线程 / 渲染回调内同步 HTTP（协议通用规则，不绑定具体 UI 框架）。
   - 端自选异步通道：本地乐观更新 → 后台 invoke；实现细节属端产品文档，**不写进协议**。
4. 播放：`media.play_local` / `media.play_via_xiaozhi` / `handoff`；URL 过期须重新 invoke。

## 6. 推送（可选）

云端主动更新（新闻、天气）可用各产品既有推送通道下发 **同一 Envelope**（MQTT / 长连接 / 轮询等，路径名属 Host 实现）。`ttl_sec` 控制缓存。勿依赖 MCP `notifications/*` 作为唯一通路（部分助理固件可能忽略）。

## 7. 多端与 scope

| scope | 行为 |
|-------|------|
| `account` | 一处安装（键含 `market_id`+`app_id`）；手机与墙板各自按能力启用；同键不同 Surface |
| `device` | 仅该 `device_id` 清单可见 |

卸载：Host 删实例；设备 list 不再返回。同账号下卸载市场 A 的应用不影响市场 B 的同名 `app_id`。

## 8. 安全

### 8.1 传输与 SSRF 边界（硬性）

Host 会用**自己**的网络栈去拉取任意第三方提供的 URL（市场索引、`package_url`、invoke 上游、媒体 URL）。发布者控制这些 URL，因此「允许内网 http」等价于**允许发布者探测 Host 所在内网**。规则如下：

| 规则 | 要求 |
|------|------|
| 公网传输 | 市场索引、`package_url`、invoke 上游、媒体 URL：**HTTPS**（绝对地址）。公网 `http://` 一律拒装/拒 invoke |
| 默认策略 | Host **必须**默认拒绝解析到以下目标的出站请求：回环（`127.0.0.0/8`、`::1`）、链路本地（`169.254.0.0/16`、`fe80::/10`）、RFC1918 / ULA（`10/8`、`172.16/12`、`192.168/16`、`fc00::/7`）、云元数据（`169.254.169.254`、`fd00:ec2::254`）、`0.0.0.0`。须按**解析后的 IP** 判定，不能只看主机名字符串 |
| 重定向 | 跟随重定向时**逐跳**重做上述判定（`http→https` 降级、跳内网都必须拒） |
| DNS 重绑 | 宜在建立连接后按**实际对端 IP** 再校验一次（TOCTOU）；无法做到时至少记录并在文档中声明该残余风险 |
| 例外开关 | 「允许同源相对路径」与「允许内网/回环 http」属**自建部署便利**，Host **必须**把它做成**显式、默认关闭**的配置项（联调模式），且：① 只影响该 Host 实例；② 开启时须在 UI/日志明示；③ 相对路径仍限**与 Host 同源**（如 `/static/…`）；④ 密钥类配置（`secret`）**禁止**发往私网 http 上游 |
| 同源相对路径 | 允许（`/static/nodelio-market/…` 这类），因为不引入 SSRF；仍须过 schema 与大小校验 |
| 协议层做法 | schema 里 `package_url` / `icon_url` 的 `pattern` 保持 `^https://` **默认严格**；私网联调由 Host 校验层放开（属产品行为），**不得**通过弱化 schema 来表达例外 |
| 市场来源 | Host **可**维护主机允许/黑名单、单包大小上限、抓取超时；on-prem 部署默认名单为空即宽松，但上述内网规则**仍适用** |

### 8.2 其余安全规则

| 规则 | 要求 |
|------|------|
| 密钥 | 不下发设备；不进日志明文；Host 宜加密存储（如带版本前缀的本地对称加密）；轮换后须用户重填属产品行为；`config_schema` 中 `secret:true` 的属性**禁止**出现在任何面向端的响应里 |
| 完整性 | 条目带 `package_sha256` 时 Host 必须校验，不符即拒装（[01-marketplace.md](01-marketplace.md) §1.2）；不带时记 warning，禁止据此建立信任 |
| 身份绑定 | `(market_url_origin → market_id)` 绑定见 [01-marketplace.md](01-marketplace.md) §6.1，防同名市场接管已装实例 |
| 体积 | 遵守 `limits.max_content_bytes`；Host 可硬截断并标 `truncated:true` |
| 图片 | 遵守 `limits.image`；无 `content.image` 则剥图；图片 URL 同受 §8.1 传输与内网规则约束 |
| 字段 | 禁止可执行脚本、UI 对象树 / 控件树、`data:` 可执行载荷；包/Envelope **未知字段忽略**（`additionalProperties` 一律 `true`，见 [07-evolution.md](07-evolution.md) §5.1） |
| 播放 URL | 尊重 `expires_at`（Unix 秒）；勿长期持久化；代理媒体时须鉴权并按 §8.1 校验目标，限制响应大小与 MIME，禁止把设备可控 URL 无校验转发 |
| 滥用 | Host **可**记录 invoke 审计（含 `deviceId`）并对同一设备限流；返回 `rate_limited` |
| 拒装诊断 | Host 因 schema/必填/形状不合法能力名拒装时，**必须**返回可定位信息（字段路径 + 非法值），不得只回「校验失败」 |

## 9. 与控家并行

| 通道 | 用途 |
|------|------|
| layout + `panel/command` | 灯、继电器、PWM、情景 |
| 本协议 skills | 第三方内容与工具 |

勿用技能 Envelope 替代设备开关指令；勿在技能里下发任意 GPIO。
