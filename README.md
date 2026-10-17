# NodeLio Protocol — 应用市场 / 技能包 / 跨端内容

> **权威契约**（v1）。本仓库可单独克隆；**不依赖**任一厂商本机路径或私有固件树。各厂商的硬件约束、固件、云实现留在各自工程，仅通过运行时 `DeviceCapabilities` 与本协议对齐。

## 仓库与贡献

| 项 | 说明 |
|----|------|
| 官方仓库 | 本 GitHub 仓库（`nodelio-protocol`）为协议文档与 schema 的**对外权威副本** |
| 如何参与 | Fork → PR；维护者审核后合并。规范见 [07-evolution.md](07-evolution.md)、[CONTRIBUTING.md](CONTRIBUTING.md) |
| 不要 PR 的内容 | 单一产品 UI、芯片丝印、本机绝对路径、私有仓库字段名、API Key；`examples/` 下**允许**少量「离线参考脚本」（不进入任一端或 Host 的运行路径，须自带用途与边界注释） |
| License | [MIT](LICENSE) |
| 变更历史 | [CHANGELOG.md](CHANGELOG.md)（状态性表述写这里，不写进权威正文） |

## 先读哪三份（按角色）

| 你是谁 | 顺序 |
|--------|------|
| 要发应用 / 发市场 | **[09-quickstart.md](09-quickstart.md)** → [08-publishers.md](08-publishers.md) → 01 / 02 / 03 + `examples/` |
| 要写某一端的固件或 APP | [09-quickstart.md](09-quickstart.md) → 00（能力与申报）→ 03（信封与降级）→ 05（槽位）→ 04 §3.2（已装清单）→ 06（本类设备现实） |
| 要写 Host 云 | 04（全部，尤其 §0 边界、§3、§8.1）→ 08 §3–4 → schemas |
| 要改协议本身 | [07-evolution.md](07-evolution.md) + 全文 |

## 规范性关键词（本仓库所有文档遵守）

沿用 RFC 2119 / 8174 语义，中英对照如下：

| 写法 | 含义 | 中文等价 |
|------|------|----------|
| **MUST / 必须 / 禁止 / 不得** | 绝对要求；违反即不合规 | 硬性 |
| **SHOULD / 宜 / 应** | 强烈建议；偏离须有理由并能说明 | 默认做法 |
| **MAY / 可** | 真可选；实现自定，不影响互操作 | 可选 |
| **建议 / 宜**（表格与说明里） | 非约束性提示，属产品选择 | 提示 |
| 文档中标注「**示例**」「典型端」「常见组合」 | **不是**要求，仅为理解辅助 | 非规范 |

判定合规性时：只看 **MUST** 项是否满足；SHOULD 未满足不构成「不合规」，但端/Host 须能解释。

## 目标

任意发布者可托管「应用市场」JSON；用户可添加**多个**市场地址，按**目标设备能力**过滤、安装并配置；invoke 经 Host 云代理后，设备只消费统一 **Content Envelope**；ESP / Linux / Android 等端各自渲染，**不接收布局树或可执行脚本**。

**发给外部开发者的入口**：[09-quickstart.md](09-quickstart.md)（端到端最小实例）→ [08-publishers.md](08-publishers.md)（多市场、防撞键、invoke 档位、上架清单）。

## 通用性（多发布者硬性）

不同人各自托管市场时，**契约同一套**。判定：

> 只换 `market_url` 与包内 invoke 地址，不改设备固件、不改 Companion 浏览逻辑、Host 云**不**为该应用新增专用转换分支，仍能安装并上屏 → 接口通用。

| 层 | 契约 | 谁提供 |
|----|------|--------|
| 市场索引 | [01-marketplace.md](01-marketplace.md) | 任意发布者 HTTPS |
| 应用包 | [02-app-package.md](02-app-package.md) | 应用作者 |
| 调用结果 | [03-content.md](03-content.md) Envelope | 应用作者上游（推荐直接返回；或发布者自建适配服务） |
| 能力过滤 | [00-capabilities.md](00-capabilities.md) | 端申报 + 安装前校验 |
| 安装 / 密钥 / 代 invoke | [04-runtime-flow.md](04-runtime-flow.md) | Host 云（产品实现，语义须对齐本协议） |
| 呈现 | [05-surfaces.md](05-surfaces.md) | 各端自定外观 |

**安装实例键**：`(market_id, app_id)`，并由**来源 URL 锚定** `market_id` — 禁止仅用裸 `app_id` 作全局唯一键（两家市场可同名应用并存；接管同名 `market_id` 的攻击面见 [01-marketplace.md](01-marketplace.md) §6.1）。细节见 [08-publishers.md](08-publishers.md) §4、[01-marketplace.md](01-marketplace.md) §6–§6.1。

**Invoke**：上游已是 Envelope 时，Host **透传 + 校验/裁剪**即可；不得以「未进本厂适配白名单」拒绝合规档 A/B 应用。见 [04-runtime-flow.md](04-runtime-flow.md) §4、[08-publishers.md](08-publishers.md) §3。

## 边界：只定结构，不定交互外观

| 协议定 | 协议不定（留给各平台 / 各硬件作者） |
|--------|--------------------------------------|
| JSON 字段、白名单 type / card_type / surface 名 | 按钮长什么样、动画、手势、字体、配色 |
| `requires` 匹配与降级链（数据如何变瘦） | 降级后具体 UI 怎么摆 |
| Action 的 `run`（invoke / local / handoff）语义 | 播控条样式、列表滚动物理、焦点框 |
| limits / 安全（字节、HTTPS、禁脚本） | 是否用 LVGL / Compose / Qt / 纯 TTS |
| 能力**名**与匹配算法 | 某块板「算力够不够、解码稳不稳」等产品事实 |

**原则**：同一 Envelope，墙板、手机、音箱可以完全不同的交互；只要能正确消费结构并遵守能力申报即可。文档中的「建议优先级 / 典型端」仅作理解帮助，**不是**必须照做的 UX 规范。

## 协议 vs 平台产品（必读）

Protocol 是**所有未来端**共用的词汇与匹配规则，**不是**某一块板的规格书。

| 层级 | 回答的问题 | 权威位置 |
|------|------------|----------|
| **Protocol** | 字段叫什么、怎么匹配、Envelope 长什么样、未知类型怎么降级 | 本目录 |
| **DeviceCapabilities（运行时）** | **这台设备当前固件**能渲染/播/拉什么 | 端上报的 JSON；须诚实 |
| **Profile 预设** | 某一类端的**目标**能力模板（可被 `disabled` / `extra` 裁剪） | [00-capabilities.md](00-capabilities.md) §4 |
| **平台产品附录** | profile **类**设备如何映射申报；不写具体仓库/芯片路径 | [06-platform-profiles.md](06-platform-profiles.md) |

**不合理预期（协议故意不做）：**

- 看到 profile 名 `esp32-panel-480` 就假定「一定能本机播 MP3」→ **否**。只有运行时 `capabilities` 含 `media.play_local` 且通过该端验收，才算能播。
- 用协议规定「对话气泡上方弹列表、抽屉压到多少像素」→ **否**。那是平台呈现策略（见 [05-surfaces.md](05-surfaces.md) §7）。
- 把扬声器芯片型号、AFE 与 TLS 互斥写进 schema → **否**。写进平台附录 / 硬件约束文档。

**合理关联：** 产品结论应**反映到**运行时申报（有则声明 + 填 `limits.media`；无则不声明或 `disabled`），市场过滤只认申报，不认「图纸上有喇叭」。

## 分层

```text
Marketplace Index     市场可装应用列表（公开只读，任意发布者托管）
        ↓ install（经 Host 云）
App Package           单个应用元数据 / 配置项 / invoke / requires
        ↓ 安装产物：设备侧「已安装清单」（04 §3.2，结构由协议规定）
Content Envelope      结构化结果（music / news / list / …）
        ↓
Surface + hints       出现在哪、怎么挤（非控件树）
        ↓
端渲染器              LVGL / Android / Linux / TTS …
```

与控家通道隔离：开关/情景/PWM 仍走各产品自己的控制通道。技能是平行通道。

## 术语（先对齐这 8 个词）

| 术语 | 含义 | 谁实现 |
|------|------|--------|
| **Host 云**（旧文档偶写作「SERVER」） | 用户所信任的中心服务：代拉包、存密钥、代 invoke、下发已装清单。协议规定它**必须做什么**，不规定它的 HTTP 路径（[04-runtime-flow.md](04-runtime-flow.md) §0） | 平台/自建者 |
| **Companion APP** | 用户管理市场、安装、配置的手机端应用；也是无屏设备的「配网/配置代理」 | 各端 |
| **端 / 目标设备** | 真正渲染 Envelope 的设备（墙板、手机、音箱）。过滤按**目标设备**申报，不按手机 | 各硬件作者 |
| **市场（market）** | 一份公开只读的 `marketplace.json` 及其发布者 | 任意发布者 |
| **应用包（app package）** | 单个应用的自描述 JSON | 应用作者 |
| **安装实例 / `instance_id`** | `(market_url_origin, market_id, app_id)` 的一次安装；Host 生成 id 供端与 MCP 引用（[01-marketplace.md](01-marketplace.md) §6.1） | Host 云 |
| **Envelope** | invoke 的统一结果信封（[03-content.md](03-content.md)） | 应用上游（推荐直出）或发布者适配服务 |
| **档 A / B / C** | A = 上游直接返回 Envelope；B = 发布者自建适配服务输出 Envelope；C = 某一 Host 在云内为你写专用转换（**非协议义务**）。详见 [08-publishers.md](08-publishers.md) §3 | 发布者（A/B） |

> 「小智」是 `media.play_via_xiaozhi` 这一**历史能力名**里的厂商词，指一类语音助理固件生态；其协议语义见 [00-capabilities.md](00-capabilities.md) §3.5.1，正名提案见 [07-evolution.md](07-evolution.md) §4.1。协议正文其余部分不使用厂商名。

## 文档索引

| 文件 | 内容 |
|------|------|
| [09-quickstart.md](09-quickstart.md) | **上手**：端到端最小实例（发布→过滤→安装→清单→渲染→失败），含三端渲染对照 |
| [00-capabilities.md](00-capabilities.md) | 能力字典、DeviceCapabilities、生效计算（§4.1）、匹配、limits、降级 |
| [01-marketplace.md](01-marketplace.md) | 市场索引、ID/semver 语法、完整性、market_id 绑定、过滤与安装 |
| [02-app-package.md](02-app-package.md) | 应用包、JSON Schema 子集、actions、MCP |
| [03-content.md](03-content.md) | Content Envelope 白名单、**错误唯一表达与码表（§3）**、降级矩阵 |
| [04-runtime-flow.md](04-runtime-flow.md) | 规范性边界（§0）、时序、**设备侧清单形状（§3.2）**、安全与 **SSRF 边界（§8.1）** |
| [05-surfaces.md](05-surfaces.md) | 交互面与 presentation hints（含 `auto_play`） |
| [06-platform-profiles.md](06-platform-profiles.md) | 平台附录：申报诚实、媒体现实、与协议的弱相关边界 |
| [07-evolution.md](07-evolution.md) | **完善协议前必读**：变更分级、命名、版本、**schema 校验立场（§5.1）**、合入清单 |
| [08-publishers.md](08-publishers.md) | **市场/应用发布者**：上架、多市场、Envelope 上游、防撞键 |
| [CHANGELOG.md](CHANGELOG.md) | 变更历史与本轮澄清范围 |
| [schemas/](schemas/) | JSON Schema + **vocabulary（权威词典）** |
| [examples/](examples/) | 样例（含错误信封、已装清单、MCP 承载） |

## 语言与版本

- 本文档目前为**中文**。英文镜像属 [CHANGELOG.md](CHANGELOG.md) 跟踪的待办；翻译时须按「规范性关键词」表逐句对齐 MUST/SHOULD/MAY，不得自由意译。
- 校验样例可用 `ajv` 等工具离线跑（须本地解析 `schemas/` 内的 `$ref`，`$id` 指向 GitHub raw URL）。CI 脚本不在本协议仓内维护（见上文「不要 PR 的内容」与 [07-evolution.md](07-evolution.md) §2）。

## 拉取路径（推荐）

| 动作 | 推荐 |
|------|------|
| APP 浏览市场索引 | `fetch.mode=auto`：优先直连 HTTPS；失败则 Host 云代理 |
| 墙板逛市场 | **不推荐**；由 APP 安装后 Host 云下发已安装清单 |
| 安装 / 密钥 / 配置 | **必须**经 Host 云 |
| invoke | **必须**经 Host 云代理；上游宜已是 Envelope（透传+校验）；否则由发布者自适配或（非协议义务）Host 特例转换 |
| 渲染 | 端只消费 Envelope + 本机 Surface |


## 端能力筛选（硬性）

- 端声明 `DeviceCapabilities`（可基于 profile；**线上上报只写展开后的最终集合**，见 [00-capabilities.md](00-capabilities.md) §4.1）。
- 应用声明 `requires` / `optional`；市场条目须带 `requires`（不下整包即可过滤）。`requires` 里允许哪些名字见 [00-capabilities.md](00-capabilities.md) §3.9。
- **可安装** ⟺ `requires ⊆ device.capabilities`，且 `app.surfaces ∩ device.surfaces ≠ ∅`（若双方声明了 surfaces）。
- APP 逛市场时按**目标设备**（所选墙板等）过滤，不是只按手机能力。
- 运行时未知 `card_type` / 缺能力 → 走固定降级矩阵，禁止伪装可装。

## 版本

- 文档与 JSON 根字段：`schema_version`（整数，当前 **1**）。
- 市场条目 / 应用包：`min_protocol` — 端的 `protocol_version` 须 ≥ 该值；与包内冲突**取较严**（[01-marketplace.md](01-marketplace.md) §1.3）。
- 未知字段：**忽略**（Host/端不得因额外字段拒装或拒渲染）。未知 `content.type` / `card_type` / 能力名 / surface：按 [00-capabilities.md](00-capabilities.md) §3.8 与 [03-content.md](03-content.md) §5 降级，**禁止**枚举硬拒（schema 立场见 [07-evolution.md](07-evolution.md) §5.1）。
- 公网传输须 HTTPS；同源相对路径与私网联调例外属 Host 显式开关，见 [04-runtime-flow.md](04-runtime-flow.md) §8.1。
- 播放 URL 过期：`playback.expires_at` = **Unix 秒**，见 [03-content.md](03-content.md) §2.4。
- 失败：`status:"error"` + `error.code`（唯一表达与码表见 [03-content.md](03-content.md) §3）。
- 新能力 / 新 type：先作 `optional` + 降级；major 才升为普遍 `requires`。
- **改协议本身**：见 [07-evolution.md](07-evolution.md)（分级、命名、版本、合入清单）。历史与本轮澄清范围见 [CHANGELOG.md](CHANGELOG.md)。
- **纯档 A 最小样例**：[examples/app-demo-envelope.json](examples/app-demo-envelope.json) + [examples/envelope-demo-plain.json](examples/envelope-demo-plain.json)。

## 禁止

- 下发任何 UI 对象树 / 控件树 / 像素坐标（无论 LVGL、Compose 还是自绘）、任意 UI 脚本、未校验的可执行字段
- 把第三方 API Key 明文下发到设备日志或固件
- 为每个第三方 API 在固件中 fork 专用页面（应增 capability / surface / card_type）
- 要求每个社区应用必须进入某一 Host 的「云内专用适配白名单」才能安装（档 A/B 即应可装，见 [08-publishers.md](08-publishers.md) §3）
- 把单一产品路径 / 私有仓库字段名写进协议正文（见 [07-evolution.md](07-evolution.md) §2）
- 用「设备有某硬件」推断能力：过滤与渲染只认运行时申报（[00-capabilities.md](00-capabilities.md) §3.6、[06-platform-profiles.md](06-platform-profiles.md)）
- 在协议正文规定 Host 的 HTTP 路径 / 鉴权头名（语义与 JSON 形状属协议；路径属 Host 产品文档）

