# NodeLio Protocol — 应用市场 / 技能包 / 跨端内容

> **权威契约**（v1）。本仓库可单独克隆；**不依赖**任一厂商本机路径或私有固件树。各厂商的硬件约束、固件、云实现留在各自工程，仅通过运行时 `DeviceCapabilities` 与本协议对齐。

## 仓库与贡献

| 项 | 说明 |
|----|------|
| 官方仓库 | 本 GitHub 仓库（`nodelio-protocol`）为协议文档与 schema 的**对外权威副本** |
| 如何参与 | Fork → PR；维护者审核后合并。规范见 [07-evolution.md](07-evolution.md)、[CONTRIBUTING.md](CONTRIBUTING.md) |
| 不要 PR 的内容 | 单一产品 UI、芯片丝印、本机绝对路径、可执行脚本、API Key |
| License | [MIT](LICENSE) |

## 目标

任意发布者可托管「应用市场」JSON；用户可添加**多个**市场地址，按**目标设备能力**过滤、安装并配置；invoke 经 Host 云代理后，设备只消费统一 **Content Envelope**；ESP / Linux / Android 等端各自渲染，**不接收布局树或可执行脚本**。

**发给外部开发者的入口**：[08-publishers.md](08-publishers.md)（多市场、防撞键、invoke 档位、上架清单）。

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

**安装实例键**：`(market_id, app_id)` — 禁止仅用裸 `app_id` 作全局唯一键（两家市场可同名应用并存）。细节见 [08-publishers.md](08-publishers.md) §4、[01-marketplace.md](01-marketplace.md) §7。

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
Marketplace Index     市场可装应用列表（公开只读）
        ↓ install
App Package           单个应用元数据 / 配置项 / invoke / requires
        ↓ invoke（经 SERVER）
Content Envelope      结构化结果（music / news / list / …）
        ↓
Surface + hints       出现在哪、怎么挤（非控件树）
        ↓
端渲染器              LVGL / Android / Linux / TTS …
```

与控家通道隔离：开关/情景/PWM 仍走 `layout` + `panel/command`。技能是平行通道。

## 文档索引

| 文件 | 内容 |
|------|------|
| [00-capabilities.md](00-capabilities.md) | 能力字典、DeviceCapabilities、匹配、limits、降级 |
| [01-marketplace.md](01-marketplace.md) | 市场索引、直连/代理拉取、过滤与安装 |
| [02-app-package.md](02-app-package.md) | 应用包、config_schema、actions、MCP |
| [03-content.md](03-content.md) | Content Envelope 白名单类型 |
| [04-runtime-flow.md](04-runtime-flow.md) | 端到端时序、安全、多端绑定 |
| [05-surfaces.md](05-surfaces.md) | 交互面与 presentation hints |
| [06-platform-profiles.md](06-platform-profiles.md) | 平台附录：申报诚实、媒体现实、与协议的弱相关边界 |
| [07-evolution.md](07-evolution.md) | **完善协议前必读**：变更分级、命名、版本、合入清单 |
| [08-publishers.md](08-publishers.md) | **市场/应用发布者**：上架、多市场、Envelope 上游、防撞键 |
| [schemas/](schemas/) | JSON Schema |
| [examples/](examples/) | 样例 |

## 拉取路径（推荐）

| 动作 | 推荐 |
|------|------|
| APP 浏览市场索引 | `fetch.mode=auto`：优先直连 HTTPS；失败则 SERVER 代理 |
| 墙板逛市场 | **不推荐**；由 APP 安装后 SERVER 下发已安装清单 |
| 安装 / 密钥 / 配置 | **必须**经 SERVER |
| invoke | **必须**经 Host 云代理；上游宜已是 Envelope（透传+校验）；否则由发布者自适配或（非协议义务）Host 特例转换 |
| 渲染 | 端只消费 Envelope + 本机 Surface |

## 端能力筛选（硬性）

- 端声明 `DeviceCapabilities`（可基于 profile）。
- 应用声明 `requires` / `optional`；市场条目须带 `requires`（不下整包即可过滤）。
- **可安装** ⟺ `requires ⊆ device.capabilities`，且 `app.surfaces ∩ device.surfaces ≠ ∅`（若双方声明了 surfaces）。
- APP 逛市场时按**目标设备**（所选墙板等）过滤，不是只按手机能力。
- 运行时未知 `card_type` / 缺能力 → 走固定降级矩阵，禁止伪装可装。

## 版本

- 文档与 JSON 根字段：`schema_version`（整数，当前 **1**）。
- 市场条目 / 应用包：`min_protocol` — 端的 `protocol_version` 须 ≥ 该值。
- 未知字段：**忽略**。未知 `content.type` / `card_type`：走 [03-content.md](03-content.md) 降级矩阵。
- 新能力 / 新 type：先作 `optional` + 降级；major 才升为普遍 `requires`。
- **改协议本身**：见 [07-evolution.md](07-evolution.md)（分级、命名、合入清单）。

## 禁止

- 下发 LVGL 对象树、任意 UI 脚本、未校验的可执行字段
- 把第三方 API Key 明文下发到设备日志或固件
- 为每个第三方 API 在固件中 fork 专用页面（应增 capability / surface / card_type）
- 要求每个社区应用必须进入某一 Host 的「云内专用适配白名单」才能安装（档 A/B 除外规，见 [08-publishers.md](08-publishers.md) §3）
- 把单一产品路径/仓库写进协议正文（见 [07-evolution.md](07-evolution.md) §2）
