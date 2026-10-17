# 08 — 发布者指南（多市场 / 通用接口）

> 给**应用市场作者**与**应用作者**。只读本文 + schema + examples 即可发市场；**不必**改协议仓库、不必改任一端固件、**不必**向某一 Host 云提交专用适配代码（见 §3 档 A/B）。  
> `Evolution: A`（文档澄清；不升 `schema_version`）。

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
| 1 | `marketplace.json` | 符合 [01-marketplace.md](01-marketplace.md)；公开 HTTPS；无 token。可放任意静态站或 CDN |
| 2 | 每个应用一份 `app-package.json` | 符合 [02-app-package.md](02-app-package.md)；`package_url` 稳定（建议含版本号）。脱离索引所在站点时用**绝对 https**；与 Host 同源时才可用该 Host 约定的相对路径 |
| 3 | invoke 上游 | **响应体为 Content Envelope**（[03-content.md](03-content.md)）；HTTPS；超时内返回 |
| 4 | `requires` / `surfaces` | 与包一致；条目上须带 `requires` 供过滤 |
| 5 | （可选）`config_schema` | 用户 API Key 等；`secret: true` 仅存 Host 云 |

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
| `market_id` | 反向域名风格，**全球宜唯一**（如 `com.example.skills`）；你拥有该市场 |
| `app_id` | 在**你的市场内**唯一（如 `weather.today`） |
| **安装实例键** | Host **必须**用 `(market_id, app_id)`（可选再加 `version` 策略）；禁止仅用裸 `app_id` 作为全局唯一安装键 |
| 端 / MCP 引用 | 可用 Host 生成的实例 id；若暴露 `app_id`，须能区分来源市场（展示名带市场或命名空间） |

两家市场都发布 `app_id: "music.search"` → 用户可同时安装两份；互不覆盖。

## 5. 能力与可装

- 只声明你真正需要的 `requires`；能放 `optional` 的不要写进 `requires`。
- 过滤算法见 [00-capabilities.md](00-capabilities.md)：`requires ⊆ device.capabilities`。
- 端未实现的 `card_type` → 走 [03-content.md](03-content.md) 降级；不要依赖未进白名单的类型「假装可装」。

## 6. 升级

- 破坏性变更：升 `version`，必要时升 `min_protocol`。
- 新 `package_url`（建议 URL 含版本）→ Host 再拉包、再校验；失败时应保留旧版可运行（产品行为，协议要求「不得因失败安装而静默损坏已装实例」的语义由 Host 保证）。

## 7. 安全义务

- 索引与包：公开只读；**禁止**放 API Key。
- 密钥：仅通过 Companion 安装向导写入 Host；设备 list **不得**回传 secret 值。
- 媒体 URL：宜带过期；遵守设备 `limits`。

## 8. 不要做的事

- 要求用户刷定制固件才能用你的应用  
- 要求 Host 为你的 API fork 专用页面或专用 MCP 工具名（统一 `invoke` + `app_id` / 实例 id）  
- 在 Envelope 里下发 GPIO / 控家指令（控家走平行通道，见 [04-runtime-flow.md](04-runtime-flow.md) §9）  
- 把某一厂商的仓库路径、芯片丝印写进你的包当硬依赖  

## 9. 样例

| 文件 | 用途 |
|------|------|
| [examples/marketplace-sample.json](examples/marketplace-sample.json) | 市场索引 |
| [examples/app-music-search.json](examples/app-music-search.json) | 应用包 |
| [examples/envelope-*.json](examples/) | 上游应返回的 Envelope 形状 |

## 10. 改协议？

只有当你需要**新的**跨端内容形态（新 `card_type` / capability / surface）且现有 `list`/`text`/降级不够用时，才走 [07-evolution.md](07-evolution.md) 提 PR。发市场、发应用、自建档 B 适配 → **不必**改本仓库。
