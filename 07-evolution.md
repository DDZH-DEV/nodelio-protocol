# 07 — 协议演进规范（给完善协议的人）

> 第三方或内部开发者若要**改本协议**（新能力、新 `card_type`、新 surface、改匹配规则等），须先读本文。  
> 实现某一端产品、或只发应用包 / 市场 JSON，**不必**改协议；按现有白名单与申报即可。

本规范本身也是契约的一部分：合入前的评审清单，不是可选建议。

## 0. 官方仓库与 PR（硬性）

| 项 | 要求 |
|----|------|
| 权威发布 | 以 GitHub 上的 **`nodelio-protocol`** 仓库为准（仅协议 + schema + examples） |
| 提交流程 | **Fork → 开 Pull Request → 维护者审核合并**；贡献者默认无 `main` 直推权限 |
| 审核权 | 仅维护者（仓库管理员）决定是否合并；可要求按本文补齐后再合 |
| PR 必带 | 首行 `Evolution: A\|B\|C\|D\|E`；§7 清单；无本机路径 / 无私有仓假设 |
| 同步 | 厂商 monorepo 内若有副本，合入官方仓库后由维护者再同步；**勿**只改私有副本当作「已进协议」 |

详见根目录 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 1. 你该不该改协议？

| 你的想法 | 正确落点 |
|----------|----------|
| 新音乐源 / 新天气 API | **应用包 + 云适配**；不改协议 |
| 某块板 UI 更好看、会话区上方弹卡 | **该端固件/APP**；不改协议（见 [05-surfaces.md](05-surfaces.md) §7） |
| 某 SoC 内存不够、解码卡 | **运行时少申报 / 收紧 `limits`** + 产品硬件文档；不改协议词典「迁就」单板 |
| 多端都需要同一种新内容形态（如「菜谱步骤」） | **可提案**进协议：`content.*` + `card_type` + 降级 + schema + 样例 |
| 多端都需要新槽位（如「锁屏小部件」） | **可提案**新 `surface`（须证明过滤上真有差异） |
| 私有实验字段 | 用 §6 扩展规则；**先不要**进权威白名单 |

**默认：能用现有 `list` / `text` / `action.invoke` / hints 表达的，不扩协议。**

## 2. 不可违背的边界

1. **定结构，不定外观** — 禁止下发控件树、像素坐标、可执行 UI/脚本、`data:` 可执行载荷。
2. **协议通用** — 正文与样例**禁止**依赖某厂商本机路径、私有仓库名、单一芯片丝印；产品细节放各厂商文档。
3. **控家隔离** — 技能通道不替代 `layout` / 设备开关指令；禁止技能 Envelope 下发任意 GPIO。
4. **密钥不下发** — 第三方 API Key 只留云端；协议字段不得鼓励明文进设备。
5. **未知可忽略** — 新字段须能被旧端安全忽略；破坏性变更走 §5 版本规则。
6. **诚实申报** — 不得用协议文案暗示「有某 profile 名就必然具备某媒体能力」。

## 3. 变更分级

| 级别 | 例子 | 要求 |
|------|------|------|
| **A. 文档澄清** | 改正义、补边界、补样例说明 | 不改 schema 枚举；`schema_version` 不变 |
| **B. 可忽略扩展** | 新可选字段、新 `optional` 能力名 | 旧端忽略；补词典 + schema（若有）+ 样例；给出降级/隐藏行为 |
| **C. 白名单扩张** | 新 `content.type` / `card_type` / `surface` / `local` 动作 | 同 B，且**必须**写入 [03](03-content.md) 降级矩阵或 [05](05-surfaces.md) 选择说明 |
| **D. 行为变更** | 改匹配算法、改 `requires` 语义、收紧旧字段含义 | 须升 `protocol_version` 或 `schema_version`（见 §5）；写迁移说明 |
| **E. 破坏性删除/改名** | 删能力名、改枚举取值 | **禁止**在同一 major 内；新 major + 弃用期 |

提案人在 PR/变更说明首行标注级别：`Evolution: B` 等。

## 4. 命名约定

| 种类 | 规则 | 例 |
|------|------|-----|
| capability | `领域.具体`，小写，`.` 分段 | `content.recipe_list`、`media.play_local` |
| `content[].type` | 单数名词或短名 | `music`、`list_item`、`weather` |
| `display.card_type` | 与内容对应，列表用 `_list` | `music_list`、`plain_result` |
| surface | 短槽位名，无厂商前缀 | `card`、`now_playing` |
| `local` 动作 ID | `media.*` / `ui.*` 等，与 capability 区分 | `media.play`（动作）vs `media.play_local`（能力） |
| profile | `平台-形态` 或已有枚举扩展 | `esp32-panel-480`；新 profile 先论证不能用 `extra`/`disabled` |
| `market_id` | 反向域名风格，**≥3 段**，小写 + 数字 + 连字符 | `com.example.skills`；语法见 [01-marketplace.md](01-marketplace.md) §1.1 |
| `app_id` | 小写点分段，建议 ≥2 段 | `weather.today`、`music.search` |
| 错误 `code` | `snake_case`，**唯一风格** | `upstream_timeout`；码表见 [03-content.md](03-content.md) §3.3 |
| `handoff.kind` | `snake_case` 动词短语 | `open_url` |
| 分类（`categories`） | 优先用 v1 词表；自定义须可原样显示 | `music` / `tool` / `info` |

**禁止：** 同义多名（`play_song` + `media.play_local`）、厂商前缀进核心词典（`acme.weather`）、把 URL 路径或类名当 type、一个概念两种大小写风格（`error.unsupported` 与 `unsupported_content` 并存即为反例，已统一为后者）。

### 4.1 关于 `media.play_via_xiaozhi`（既有违规的处置）

该名字含厂商词，与 §4「禁止厂商前缀进核心词典」冲突，且第三方读不懂。**决议**：

| 步骤 | 动作 | 级别 |
|------|------|------|
| 1（已做） | 在 [00-capabilities.md](00-capabilities.md) §3.5.1 补权威语义（注入助理/云侧音频下行管线，非本机解码） | A |
| 2 | 提案 `media.play_via_assistant` 作为正名，词典同时保留旧名 | B |
| 3 | 新发布的端与包**用新名**；Host 须把旧名按同义解析（alias 表进 `vocabulary.schema.json`） | B |
| 4 | 一个 major 弃用期后从新端申报中移除旧名 | E |

禁止：跳过 §2 语义说明直接改名（会破坏既有端），或在词典里留两个不同实现含义的名字。


## 5. 版本规则

- `schema_version`：Envelope / 市场 / 包 / capabilities **文档根**的形状重大变更时递增；当前 **1**。
- `protocol_version`（端申报）与应用 `min_protocol`：端实现的协议主版本；应用可要求下限。
- **B/C 级**：一般不升 major；旧端靠「忽略未知 + 降级矩阵」存活。
- **D/E 级**：升 `protocol_version`（及必要时 `schema_version`）；变更说明须含：
  - 旧端行为（忽略 / 报错 / 降级）
  - 迁移窗口（建议至少一个次版本弃用期再删）
- 新能力进入应用 `requires`（变为安装硬条件）：须已在多端可选落地一段时间，或明确只服务新 major。

### 5.1 schema 校验立场（硬性，决定 PR 里怎么写 schema）

协议承诺「未知字段忽略、未知枚举值降级」，因此 schema 必须与承诺一致，否则 B/C 级演进一落地就校验失败：

| 位置 | 必须怎么写 | 不得怎么写 |
|------|------------|------------|
| 任何文档根与对象 | `additionalProperties: true` | ❌ `false`（会拒 `x_` 扩展与旧 Host 新增字段，违反 [04-runtime-flow.md](04-runtime-flow.md) §8.2） |
| 名字集合类字段：`capabilities`、`requires`、`optional`、`local`、`content[].type`、`card_type`、`surface`、`actions[].run`、`handoff.kind`、错误 `code` | **形状** `pattern` + `anyOf`（v1 词典 ∪ 形状合法的自由串），运行时降级 | ❌ 纯 `enum` 硬拒 |
| 真正的封闭集合（`status`、`density`、`fetch`、`limits.image.formats`、`invoke.method`、`ui_hint`、`profile`） | 可以 `enum`（新增取值属 D 级，因为旧端遇未知值无法安全行为） | — |
| v1 权威词典 | 只维护在 [schemas/vocabulary.schema.json](schemas/vocabulary.schema.json) `$defs`，其余 schema 一律 `$ref` | ❌ 在各 schema 里复制一份枚举（会漂移） |
| URL 字段 | `pattern: ^https://` 保持默认严格 | ❌ 为「内网联调」放宽 schema（例外是 Host 校验层的产品行为，见 [04-runtime-flow.md](04-runtime-flow.md) §8.1） |

判定口诀：**「端能安全忽略」→ 形状约束；「端不知道该怎么办」→ enum。**

## 6. 厂商 / 实验扩展（未进白名单）

在正式合入前，允许：

```json
{
  "x_vendor": { "acme_experiment": true },
  "display": { "card_type": "list", "x_acme_layout": "dense" }
}
```

| 规则 | 说明 |
|------|------|
| 前缀 | 建议 `x_` 或文档声明的 vendor 对象；**权威 schema 可 `additionalProperties` 忽略** |
| 不得 | 用扩展绕过安全（脚本、密钥、控件树） |
| 晋升 | 至少两个独立实现或明确跨端需求 → 按 §3 C 走正式白名单 |
| 端 | 不认识的扩展 **必须忽略**，不得崩溃 |

## 7. 合入清单（B/C/D 必勾）

提案须同时更新（缺一不收）：

- [ ] 对应正文：`00`～`06` 中相关章节
- [ ] **`schemas/vocabulary.schema.json`**（新能力名 / `content.type` / `card_type` / `surface` / `local` / 错误码 / 分类的**唯一权威表**）——若名字集合有变化却只改了 Markdown，视为未完成
- [ ] 其余 `schemas/*.json`（字段 / `$ref`），并遵守 §5.1 的校验立场（新增对象字段 → `additionalProperties: true`）
- [ ] 若改**设备侧清单**或安装/配置载荷：改 `schemas/installed-app-list.schema.json` + `04` §3.2 + 样例
- [ ] 若改 `config_schema` / `input_schema` 允许范围：改 `schemas/json-schema-subset.schema.json` + `02` §2.1
- [ ] `examples/` 至少一份正例；影响过滤则更新 `filter-notes.md`；涉错误则更新 `envelope-error.json`
- [ ] **降级路径**：未知或旧端如何落到 `list` / `text` / `spoken` / `error`
- [ ] **谁申报、谁 requires**：能力进词典；应用示例用 `optional` 还是 `requires` 有理由；`requires` 须过 [00-capabilities.md](00-capabilities.md) §3.9 分类
- [ ] **无本机路径 / 无私有仓假设**（正文与样例都不得引用协议仓之外的文件）
- [ ] 变更说明含级别（§3）与版本影响（§5）
- [ ] 若改匹配或安全：改 [04-runtime-flow.md](04-runtime-flow.md)（含 §8.1 SSRF 边界）
- [ ] 更新 `CHANGELOG.md`（把状态性表述留在 changelog，不写进权威正文）
- [ ] 交叉引用编号是否因本次改动漂移：全库 grep `§` 与 `NN-*.md` 链接

仅 A 级可只改 Markdown（但仍须检查链接与 §5.1 立场没被文档矛盾）。

## 8. 评审关注点（维护者）

1. 是否其实是单一产品需求（应拒进协议）？
2. 旧端是否仍能忽略或降级？
3. 是否与现有 type 重复、能否用 `list`+`actions` 表达？
4. 是否引入可执行或布局下发？
5. 安全与 limits 是否仍可执行？新 URL 类字段是否过 §8.1（SSRF / 重定向逐跳）？
6. 是否**外部开发者读得懂**：字段有无「谁产生、何时失效、失败怎么办」；新增概念是否需要进 `09-quickstart.md` 或术语表？
7. schema 与文档是否一致（§5.1 立场、vocabulary 是否同步）？

维护者可要求：先落地「一端实验扩展」，再晋升白名单。

## 9. 建议提案模板

```markdown
## Evolution: B|C|D|E
## 摘要
（一句话）

## 动机
跨端场景是什么？为何现有 list/text/invoke 不够？

## 提案
- 新名字：
- schema 变更：
- 降级：
- 对 requires / optional 的影响：

## 兼容
旧端行为：忽略 / 降级 / 需升 protocol_version

## 样例
链接到 examples/ 或内附 JSON
```

## 10. 与「只做端 / 只做应用」的关系

| 角色 | 读什么 | 改什么 |
|------|--------|--------|
| 应用/市场作者 | **[09-quickstart.md](09-quickstart.md)** → **[08-publishers.md](08-publishers.md)**、01～03、examples | 自己的 JSON / Envelope 上游；不改 Protocol |
| 端固件作者 | **09-quickstart.md**、00、03、05、06 + schemas（尤其 `installed-app-list`） | 本端实现与申报；实验用 §6 |
| Host 云作者 | 04（含 §0 规范性边界、§3.2、§8.1）、08 §3–4、schemas | 透传 Envelope、安装键 `(market_url_origin, market_id, app_id)`；不把档 C 写成协议义务 |
| 协议贡献者 | **本文 + 全文** | 按清单改本目录 |

实现参考（某一厂商的 SERVER/固件）**不是**协议正文；第三方无该仓库也不影响遵守本契约。反过来说：本协议**不规定** Host 的 HTTP 路径与鉴权头（[04-runtime-flow.md](04-runtime-flow.md) §0），需要对接某一具体 Host 时必须再读该 Host 的产品文档。
