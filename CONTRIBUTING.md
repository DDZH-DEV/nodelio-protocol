# Contributing

本仓库是 **NodeLio Protocol** 的权威发布副本（仅协议文档与 schema，不含任一端固件或云实现）。

## 先分清你的角色

| 你是 | 该做什么 |
|------|----------|
| 应用 / 市场发布者 | **不必**改本仓库。读 [09-quickstart.md](09-quickstart.md) → [08-publishers.md](08-publishers.md)，发你自己的 JSON |
| 某端（固件/APP）实现者 | **不必**改本仓库。读 00 / 03 / 04 §3.2 / 05；私有实验按 [07-evolution.md](07-evolution.md) §6 用 `x_` 扩展 |
| Host 云实现者 | **不必**改本仓库。读 04（含 §0）+ 08 §3–4 |
| 要**改协议本身** | 按下面流程 |

## 改协议的流程

1. 先读 [07-evolution.md](07-evolution.md)：变更分级（§3）、命名（§4）、版本（§5）、**schema 校验立场（§5.1）**、合入清单（§7）。
2. Fork → 分支 → Pull Request → **由维护者审核合并**（请勿要求直接 push 到 `main`）。
3. PR 说明**首行**标注 `Evolution: A|B|C|D|E`，并勾选 07 §7 清单。
4. 名字集合类变更必须同步 [schemas/vocabulary.schema.json](schemas/vocabulary.schema.json)（唯一权威词典），否则视为未完成。
5. 变更历史写入 [CHANGELOG.md](CHANGELOG.md)；**不要**把「本轮做了什么 / 是否升号」写进 00–09 权威正文。

## PR 里不要放

- 单一产品 UI、芯片丝印、本机绝对路径、私有仓库字段名、API Key
- 依赖本仓库之外文件的引用（单独 clone 后必须是死链的东西 → 改成本仓内文档）
- `examples/` 下允许**离线参考脚本**（如档 B 的 `envelope_adapter.py`）：不得进入任一端或 Host 的运行路径，须在文件头写清用途与边界

## 自检建议（提交前）

- `examples/*.json` 对 `schemas/*` 跑一次校验（`ajv` 等；`$ref` 需本地解析 `schemas/` 目录）
- 全库搜 `§` 引用与相对链接，确认编号未因你的插入而漂移
- 新增字段是否被旧端安全忽略（07 §5.1）；新增枚举值是否会让旧端「不知道该怎么办」（那属 D 级）

应用作者 / 端实现者通常**不必**改本仓库；按现有白名单发 JSON、做端渲染即可。
