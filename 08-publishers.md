# 08 — 发布者指南（多市场 / 通用接口）

> 给**应用市场作者**与**应用作者**。只读 [09-quickstart.md](09-quickstart.md) + 本文 + schema + examples 即可发市场；**不必**改协议仓库、不必改任一端固件、**不必**向某一 Host 云提交专用适配代码（见 §3 档 A/B）。
> 变更历史与本轮澄清范围见 [CHANGELOG.md](CHANGELOG.md)。

## 1. 你在生态里的位置

```text
你托管：marketplace.json + app-package.json +（推荐）返回 Envelope 的 HTTPS
用户：在 Companion APP 添加你的 market_url
Host 云：install、存密钥、代设备 invoke
设备：只拉已装清单 + 渲染 Envelope（不逛你的市场）
```

多人可同时托管各自市场；用户可添加多个 `market_url`。契约同一套，见 [README.md](README.md)「通用性」。

## 2. 最小上架清单

| 步骤 | 产出 | 要求 |
|------|------|------|
| 0 | 读 [09-quickstart.md](09-quickstart.md) | 端到端一遍再动手，少踩 `requires` / 降级坑 |
| 1 | `marketplace.json` | 符合 [01-marketplace.md](01-marketplace.md)；公网用 HTTPS；无 token。可放任意静态站或 CDN。`market_id` / `app_id` 语法见其 §1.1；**宜**填 `publisher` |
| 2 | 每个应用一份 `app-package.json` | 符合 [02-app-package.md](02-app-package.md)；`package_url` 稳定且**含版本号**；`version` 用 semver；**公网必须绝对 https**；仅 Host 同源或内网联调才可用相对路径 / 私网 http，且那是 Host 的显式联调开关（[04-runtime-flow.md](04-runtime-flow.md) §8.1）。**宜**提供 `package_sha256` |
| 3 | invoke 上游 | **响应体为 Content Envelope**（[03-content.md](03-content.md)）；公网 HTTPS；超时内返回；失败也返回合法 Envelope（`status:"error"` + `error.code`，其 §3） |
| 4 | `requires` / `surfaces` | 与包一致；条目上须带 `requires` 供过滤；`requires` 只写真正必需的（分类规则 [00-capabilities.md](00-capabilities.md) §3.9） |
| 5 | `fallback.card_type` | **必写**（不写则端只能落到全局矩阵的 `text`）；Host 会把它随设备清单下发 |
| 6 | （可选）`config_schema` | 用户 API Key 等；`secret: true` 仅存 Host 云；只能用 §2.1 允许的 JSON Schema 子集（跨字段依赖关键字会导致拒装） |

**不要**：下发 UI 树、可执行脚本、设备侧密钥；不要假设某块板的像素布局。

## 3. Invoke 三档（通用性关键）

Host 云把上游结果交给设备前，设备侧只认 Envelope。你怎么提供 Envelope：

| 档 | 你做什么 | Host 云应做什么 | 是否「接口通用」 |
|----|----------|-----------------|------------------|
| **A. Envelope 原生** | 你的 API 直接返回合法 Envelope | **透传** + 校验 / 按设备 `limits` 裁剪 + 注入用户配置的 Auth | **是（推荐默认）** |
| **B. 发布者自适配** | 你另起适配服务：调私有上游 → 输出 Envelope；包里只指向该适配 URL | 同 A | **是** |
| **C. Host 内置适配** | 上游无法改，且某 Host 厂商愿意在云内写专用转换 | 该 Host 的产品行为，**非本协议义务** | 否（特例；不可假定每个 Host 都有） |

**协议要求**：只要上游（或你的档 B 服务）返回的是 Envelope，**任意合规 Host 都必须能安装并 invoke**，不得以「未录入本厂适配白名单」拒绝档 A/B。

## 4. 身份：多市场防撞

| 键 | 规则 |
|----|------|
| `market_id` | 反向域名风格，**≥3 段**，语法见 [01-marketplace.md](01-marketplace.md) §1.1；全球**无注册机构**，靠 Host 的来源 URL 绑定防撞（§6.1） |
| `app_id` | 在**你的市场内**唯一（如 `weather.today`）；大小写折叠后相同视为同一 id（Host 会拒第二个） |
| **安装实例键** | Host **必须**用 `(market_url_origin, market_id, app_id)`；禁止仅用裸 `app_id` 作为全局唯一安装键 |
| 端 / MCP 引用 | 用 Host 生成的 `instance_id`；若暴露 `app_id`，须能区分来源市场（展示名带市场） |

两家市场都发布 `app_id: "music.search"` → 用户可同时安装两份；互不覆盖。

**你自己也要配合防撞**：不要用别人的 `market_id`（例如模仿 `com.example.nodelio-market`）；换域名/换托管站点时**保留原 `market_id`**，改 `market_id` 等于发布一个新市场，用户已装实例不会自动迁移。

## 5. 能力与可装

- 只声明你真正需要的 `requires`；能放 `optional` 的不要写进 `requires`。
- 过滤算法见 [00-capabilities.md](00-capabilities.md)：`requires ⊆ device.capabilities`。
- `requires` 里**不要**放 `display.color` / `input.touch` 这类物理或输入事实（分类规则 [00-capabilities.md](00-capabilities.md) §3.9）。
- 端未实现的 `card_type` → 走 [03-content.md](03-content.md) §5 降级；不要依赖未进白名单的类型「假装可装」。
- **目标端类别要自查**：给无屏音箱发列表型应用必然装不上（严格过滤），正确做法是**另发一个口述版应用包**（`requires: ["content.text","action.invoke"]` + 强 `spoken`），见 [examples/filter-notes.md](examples/filter-notes.md)。

## 6. 升级、废弃与下架

| 变更类型 | 你要做的 | 用户侧结果 |
|----------|----------|------------|
| 修 bug / 加字段 | bump `version`（semver），换含版本号的 `package_url`，更新 `package_sha256` | Host 再拉包、再校验；失败**必须**保留旧版可运行 |
| 破坏性变更（改 Envelope 形状、改 `requires`） | 升 `version` major，必要时升 `min_protocol` | 不满足 `min_protocol` 的端显示「需升级」而非装坏 |
| 不再维护 | 条目 `deprecated: true` | 新装显示警告，已装仍可 invoke（[01-marketplace.md](01-marketplace.md) §1.4） |
| 下架 | 从 `apps` 移除 | 已装实例仍可 invoke；Host 宜提示「市场已不再提供」。你**不能**指望用户已配的密钥被保留 forever——请在 `publisher.contact` 留可达地址 |
| 包不可达（404） | 修 `package_url` | 新装失败并报原因；已装不被静默破坏 |

## 7. 安全义务

- 索引与包：公开只读；**禁止**放 API Key。
- 密钥：仅通过 Companion 安装向导写入 Host；设备 list **不得**回传 secret 值。
- 上游失败**不要**只回 HTTP 5xx + 文本：返回合法 Envelope（`status:"error"` + `error.code`，[03-content.md](03-content.md) §3），否则端只能给你通用错误，用户体验和信息量都归零。
- `error.message` 里**禁止**出现密钥、鉴权头、内部堆栈、他人设备 ID。
- 媒体 URL：有时效则带 `playback.expires_at`（**Unix 秒**，见 [03-content.md](03-content.md) §2.4）；遵守设备 `limits`。
- 你的任何 URL（索引、包、invoke、媒体、`icon_url`、`article_url`、`handoff.url`）在公网**必须 https**；不要把目标指向内网/元数据地址——合规 Host 会按 [04-runtime-flow.md](04-runtime-flow.md) §8.1 直接拒绝（SSRF 防护）。
- 只声明目标端**已实现**的 `requires` / `card_type`；未实现类型须能降级，勿把 `image_gallery` 等未支持能力写成「墙板必可装」。
- **宜**为每个包提供 `package_sha256`：用户能确认你发布的包没被 CDN 篡改，Host 能拒不符的更新。

## 8. 不要做的事

- 要求用户刷定制固件才能用你的应用
- 要求 Host 为你的 API fork 专用页面或专用 MCP 工具名（统一 `invoke` + `instance_id`）
- 在 Envelope 里下发 GPIO / 控家指令（控家走平行通道，见 [04-runtime-flow.md](04-runtime-flow.md) §9）
- 把某一厂商的仓库路径、芯片丝印写进你的包当硬依赖
- 用公网 `http://` 的 `package_url` / 市场索引冒充可装（合规 Host 应拒绝）
- 在 `config_schema` 里用 `allOf` / `if` / `$ref` 等超出子集的关键字（[02-app-package.md](02-app-package.md) §2.1 → 会被拒装）
- 在包里塞 `actions[].local` 的自创字符串当脚本（白名单见 [03-content.md](03-content.md) §4.1）
- 假定 `profile` 名意味着某项能力（只有端上报的 `capabilities` 算数）

## 9. 样例

| 文件 | 用途 |
|------|------|
| [examples/marketplace-sample.json](examples/marketplace-sample.json) | 市场索引 |
| [examples/app-music-search.json](examples/app-music-search.json) | 应用包（音乐） |
| [examples/app-weather-today.json](examples/app-weather-today.json) | 应用包（天气，`fallback` + `ui_hint` 用法） |
| [examples/app-demo-envelope.json](examples/app-demo-envelope.json) | **纯档 A** 应用包（上游即 Envelope） |
| [examples/envelope-demo-plain.json](examples/envelope-demo-plain.json) | 档 A 上游响应（`plain_result`） |
| [examples/envelope-weather.json](examples/envelope-weather.json) | 上游响应（`weather`） |
| [examples/envelope-error.json](examples/envelope-error.json) | **整体失败**的信封（`status:"error"` + `error.code`） |
| [examples/envelope-error-partial.json](examples/envelope-error-partial.json) | **部分失败**（`status:"ok"` + 条目级 `error`） |
| [examples/installed-app-list-panel.json](examples/installed-app-list-panel.json) | 设备侧已安装清单（端实现者最该看的一份） |
| [examples/mcp-tool-envelope-in-text.md](examples/mcp-tool-envelope-in-text.md) | 语音 MCP 过渡期承载与识别判定 |
| [examples/envelope-*.json](examples/) | 其它 Envelope 形状 |
| [examples/filter-notes.md](examples/filter-notes.md) | 各设备对各应用的可装答案（自测用） |
| [examples/envelope_adapter.py](examples/envelope_adapter.py) | 档 B 参考实现：任意 JSON → Envelope（**不进** Host 主路径；离线跑的参考代码） |

## 10. 改协议？

只有当你需要**新的**跨端内容形态（新 `card_type` / capability / surface）且现有 `list`/`text`/降级不够用时，才走 [07-evolution.md](07-evolution.md) 提 PR。发市场、发应用、自建档 B 适配 → **不必**改本仓库。

