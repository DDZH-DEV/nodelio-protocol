# Changelog

协议本身的**状态性表述**（「本轮做了什么」「是否升号」）只写这里，不写进 00–09 权威正文。
变更分级定义见 [07-evolution.md](07-evolution.md) §3。

`schema_version` / `protocol_version` 当前均为 **1**。

---

## 未发布（DeepSeek agent 审查修订轮）— Evolution **B**（可忽略扩展）+ **A**（澄清）

> 分支：`deepseek-agent/protocol-review-fixes`。来源：一次面向外部开发者的完整可读性/可实现性审查。
> 原则：不升 major；新增内容要么是**澄清**，要么是**旧端可安全忽略**的可选字段/形状。

### P0 — 补齐阻塞外部实现的契约

- **00 §4.1 生效能力计算顺序 + 线上形状**：钉死 `profile → extra → disabled → 诚实裁剪 → 一致性 → 线上只写 capabilities`；同一 JSON 中 `capabilities` 与 `disabled` 并存时以 `capabilities` 为准。06 §3.2 与 `examples/device-esp32-panel-480.json` 同步改为线上形状。
- **04 §3.2 设备侧「已安装清单」形状**：新增 `schemas/installed-app-list.schema.json` + `examples/installed-app-list-panel.json`；明确 `instance_id` / `enabled` / `disabled_reason` / `missing_capabilities` / **`fallback_card_type` 必须下发**（否则 00 §5、03 §5 的降级第 1 步无从执行）/ `config_present`。
- **01 §6.1 `market_id` 与来源 URL 绑定**：补上无注册机构下的防撞与「同名市场接管已装实例」防线；安装键扩展为 `(market_url_origin, market_id, app_id)`。
- **schema 与「未知字段忽略」一致**：`marketplace` / `device-capabilities` 改 `additionalProperties: true`；`capabilities`/`requires`/`content[].type`/`card_type`/`surface`/错误码改为**形状约束 + 词典 anyOf**（新增 07 §5.1「schema 校验立场」）。
- **03 §3 错误的唯一表达方式 + 码表**：根级 `error{code,message,retryable}` 权威、条目级 `error` 表局部失败、端本地失败用 `unsupported_content`；统一 `snake_case`（旧 `error.unsupported` 读作 `unsupported_content`）；新增 `examples/envelope-error.json`、`envelope-error-partial.json`；schema 用 `if/then` 让 `status:"error"` 信封合法。
- **新增 `schemas/vocabulary.schema.json`**：能力名 / `content.type` / `card_type` / `surface` / `local` / `handoff.kind` / `profile` / 错误码 / 分类的**唯一权威词典**；其余 schema 一律 `$ref`。

### P1 — 安全与可读性

- **04 §8.1 SSRF 边界**：默认拒绝回环 / 链路本地 / RFC1918 / 云元数据；按解析后 IP 与**逐跳重定向**判定；内网 http 与同源相对路径收进**显式默认关闭的联调开关**；`secret` 值禁止发往私网 http。
- **完整性与主体**：`package_sha256`、索引/包级 `publisher{name,url,contact}`、`deprecated`（01 §1.2、§1.4）。
- **00 §3.5.1** 首次给出 `media.play_via_xiaozhi` 的权威语义（注入助理/云侧音频下行，非本机解码），并记录正名 `media.play_via_assistant` 的演进路径（07 §4.1）。

### P2 — 自相矛盾与一致性清理

- **移除协议正文里的厂商内部引用**：02 的 `PanelSkill` 迁移表改为「不属于协议」说明；05 §5 不再引用 `ESP32-IDF/docs/panel-skills.md`（单独 clone 协议仓时是死链）。
- **README「不要 PR 的内容」**与 `examples/envelope_adapter.py` 的冲突：改为允许 `examples/` 下**离线参考脚本**（不进运行路径），adapter 头部同步说明。
- **00 §3.9**：`display.*` 不得进 `requires`；`marketplace-sample.json` 的 `gallery.photo` 随之从 `requires: [display.color]` 改为 `optional`。
- **补齐既有但未定义的字段**：`display.auto_play`（05 §3 + schema）、`handoff.kind` 枚举（03 §4）、`local` 白名单引用化、`request_id` 由发起方生成（04 §4）。
- **01 §1.1 ID/semver 语法**、**§1.3 条目与包冲突取较严**、**02 §2.1 JSON Schema 子集**（新增 `schemas/json-schema-subset.schema.json`，`secret`/`ui_hint` 标为 NodeLio 扩展）。
- **样例修错**：`envelope-music-list.json` 的 `expires_at` 原值（≈2026-09-21）早于样例 `updated_at`，会让正确实现 03 §2.4 的端把播放钮全隐藏 → 改为未来时间；06 §3.2 运行时样例原本缺必填字段，已补全。
- `schemas/*.json` 的 `$id` 由不可解析的 `nodelio.local` 改为 GitHub raw URL；`surfaces.schema.json` 从 enum 改为形状约束（理由见 07 §5.1）。

### P3 — 文档可用性

- **README**：规范性关键词表（MUST/SHOULD/MAY 中英对照）、「先读哪三份」按角色路由、术语表（Host 云 / Companion / 端 / 市场 / 包 / 安装实例 / Envelope / 档 A-B-C）、语言与校验说明；把「本轮为 Evolution A」等状态语移入本文件。
- **新增 [09-quickstart.md](09-quickstart.md)**：端到端最小实例 + 三端渲染对照 + 失败一览；配 `examples/app-weather-today.json`、`envelope-weather.json`、`mcp-tool-envelope-in-text.md`。
- **08 §9 样例索引**、**§6 废弃/下架矩阵**扩写；`filter-notes.md` 重算为 5 条目并新增「enabled 为何 false」表。
- 交叉引用编号统一校对（03 因插入 §3 错误章，降级矩阵/MCP/schema 后移为 §5/§6/§7）。

### 明确**没有**做的事（避免误读）

- 未升 `schema_version` / `protocol_version`；未新增能力名、`card_type`、`surface`。
- 未规定任何 Host 的 HTTP 路径 / 鉴权头（反而在 04 §0 明确它**不属于**协议）。
- 未把 `media.play_via_xiaozhi` 直接改名（会破坏既有端），只给出语义与分步演进。
- 未引入包签名 / PKI（成本与社区可用性权衡，见 01 §1.2）。
- `limits.image.formats`（短名）与 `limits.media.formats`（MIME）仍不一致：统一属 **D 级**，本轮只写明映射规则。

### 待办（下一轮提案）

1. `media.play_via_assistant` 正名 + alias 表（B）。
2. 列表分页 / `content.page`（C，多端确有需求时）。
3. i18n：`name` / `summary` / `spoken.text` 的多语言形状（B）。
4. 图片格式与 MIME 统一（D）。
5. 英文镜像（README + 08 + 09 + schema 注释优先）。
6. 仓库外 CI：`ajv` 校验 `examples/*.json` 对 `schemas/*`（含 `$ref` 本地解析）。

---

## v1（初始） — 协议骨架 + 一轮 Evolution **A** 澄清

- 00–08 初版：能力字典与匹配、市场索引、应用包、Content Envelope、运行时流程、Surfaces、平台附录、演进规范、发布者指南。
- Evolution A 澄清（提交 `3cb760f`）：`playback.expires_at` = Unix 秒、公网 HTTPS 与私网例外、档 A 最小样例、未知字段忽略、`expires_at` 过期剥播放与 `truncated` 标记。
- 提交 `bf3dd2b`：新增 `examples/envelope_adapter.py`（档 B 参考实现）。
- 提交 `fe5e1af`：本地协议版本初始化。
