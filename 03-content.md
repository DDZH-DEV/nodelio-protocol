# 03 — 跨端内容（Content Envelope）

invoke（及未来推送）的统一结果格式。协议只定 JSON；各端按 `card_type` / `content[].type` 自行渲染。

## 1. Envelope

```json
{
  "schema_version": 1,
  "request_id": "req_123",
  "app_id": "music.search",
  "status": "ok",
  "content": [
    { "type": "music", "id": "song_001", "title": "晴天", "artist": "周杰伦" }
  ],
  "display": {
    "card_type": "music_list",
    "title": "搜索结果",
    "preferred_surface": "card",
    "density": "compact",
    "prefer_image": true,
    "max_items": 8,
    "ttl_sec": 300
  },
  "spoken": {
    "text": "找到 3 首相关歌曲"
  }
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `schema_version` | 是 | 当前 `1` |
| `app_id` | 是 | 产生本结果的应用（实例路由真相在端清单/Host 记录里） |
| `status` | 是 | `ok` \| `error` |
| `request_id` | 否 | 由**发起方**生成、原样回带（[04-runtime-flow.md](04-runtime-flow.md) §4） |
| `content` | `status=ok` 时必填 | 条目数组；类型见 §2。`ok` 且确实无数据时可为空数组（端按空态渲染，**不要**伪装成 error） |
| `display` | `status=ok` 时必填 | 展示意图；hints 见 [05-surfaces.md](05-surfaces.md) §3 |
| `display.card_type` | 是 | 主渲染器选择；端不支持则走 §5 降级 |
| `spoken` | 否 | 供 `voice_reply` / TTS；**有屏端也建议带**（无屏与降级最后一档全靠它） |
| `error` | `status=error` 时必填 | `{ code, message, retryable? }`；见 §3 |
| `truncated` | 否 | Host 按 `limits` 硬截断时置 `true` |

`display.card_type` 决定主渲染器；`content[]` 提供数据。两者应一致（如 `music_list` 配 `type:music` 条目）；capability / card_type / content[].type 三列对照见 §3.4。

**完整文档树（本文件内 §）**：§1 信封 → §2 条目类型 → §3 错误 → §4 actions → §5 降级矩阵 → §6 MCP 承载 → §7 Schema。

## 2. content[].type 白名单（v1）

所有条目建议含：`type`, `id`（稳定字符串）。

### 2.1 `text`

```json
{ "type": "text", "id": "t1", "text": "你好", "markdown": false }
```

Capability: `content.text`。对应 card：`plain_result`。

### 2.2 `list_item`（用于 `card_type: list`）

```json
{
  "type": "list_item",
  "id": "i1",
  "title": "标题",
  "subtitle": "副标题",
  "image_url": "https://…",
  "actions": []
}
```

Capability: `content.list`。

### 2.3 `image`

```json
{
  "type": "image",
  "id": "img1",
  "url": "https://…/a.jpg",
  "width": 480,
  "height": 480,
  "alt": "封面",
  "mime": "image/jpeg"
}
```

Capability: `content.image`。Gallery：`card_type: image_gallery`，多条 `image`；翻页为端本地行为。

### 2.4 `music`

```json
{
  "type": "music",
  "id": "song_001",
  "title": "晴天",
  "artist": "周杰伦",
  "album": "叶惠美",
  "cover_url": "https://…/cover.jpg",
  "duration_ms": 269000,
  "playback": {
    "url": "https://…/a.mp3",
    "mime": "audio/mpeg",
    "expires_at": 1792300000
  },
  "actions": [
    {
      "id": "play",
      "title": "播放",
      "run": "local",
      "local": "media.play",
      "params": { "track_id": "song_001" }
    }
  ]
}
```

Capability: `content.music` / 列表卡 `content.music_list`。  
无 `media.play_*` 时隐藏 play，仍可展示列表。

#### `playback.expires_at`（硬性语义）

| 项 | 要求 |
|----|------|
| 类型 | **Unix 时间戳，单位秒**（JSON number，如 `1790000000`）。**不是** RFC3339 字符串 |
| 发布者 | 有时效的播放 URL **宜**带 `expires_at`；过期后端不得继续请求该 URL |
| 端 | `expires_at > 0` 且当前时间已超过 → **禁止开播**；可提示用户重新 invoke 取新列表 |
| Host | 透传时若 `music` 条目有 `playback.url` 但缺 `expires_at`，**可**补合理默认（建议 ≤ 30 分钟）；已过期则须去掉或失效 `playback.url`，不得假装仍可播 |
| 存储 | 勿把带时效的 URL 永久写入 NVS / 本地库当唯一真相 |

Host 为表达「已失效」可增加**可选**提示字段（非权威白名单）：`playback.expired: true`、条目级 `playable: false`。端不认识则忽略；**不得**依赖这些字段代替 `expires_at` 判断。

`music.search` 的 `keyword` **可选**（产品语义示例）：省略或空字符串表示浏览/列曲库（条数受 `display.max_items` 限制），此时 `display.auto_play` 宜为 `false`。有具体关键词才搜索；是否自动播第一条由端与 `display.auto_play` 决定。

### 2.5 `news`

```json
{
  "type": "news",
  "id": "n1",
  "title": "标题",
  "summary": "摘要",
  "source": "新华社",
  "published_at": "2026-10-15T08:30:00Z",
  "image_url": "https://…",
  "article_url": "https://…",
  "actions": [
    {
      "id": "open",
      "title": "阅读",
      "run": "handoff",
      "handoff": { "kind": "open_url", "url": "https://…" }
    }
  ]
}
```

Capability: `content.news` / `content.news_list`。

### 2.6 `weather`

```json
{
  "type": "weather",
  "id": "w1",
  "location": "上海",
  "temp_c": 24,
  "text": "多云",
  "humidity": 60,
  "icon": "cloudy"
}
```

Capability: `content.weather`。`icon` 为约定名，由端映射本地图标，禁止下发任意脚本。

### 2.7 `action`（独立动作块）

```json
{
  "type": "action",
  "id": "a1",
  "title": "刷新",
  "run": "invoke",
  "invoke": { "app_id": "news.latest", "params": {} }
}
```

Capability: `content.action`。

> **`invoke.app_id` 的解析规则见 §3.2**：目标是**该端已安装的实例**，不是全局裸 `app_id`。

### 2.8 `error`

```json
{ "type": "error", "id": "e1", "code": "upstream_timeout", "message": "上游超时" }
```

Capability: `content.error`（端应总能展示错误，即使未申报也建议内置）。

## 3. 错误的唯一表达方式（硬性）

### 3.1 一份 Envelope 只有一套错误语义

| 情形 | 正确写法 |
|------|----------|
| **整次调用失败**（上游挂了、超时、未装、限流） | `status: "error"` + 根级 **`error: { code, message }`**（权威，见下） |
| 部分条目失败 / 逐条状态 | `content[]` 里放 `{ "type": "error", "code", "message" }`，**同时** `status: "ok"`（表示这仍是可用结果） |
| 端渲染时本地失败（不支持的 card_type、无媒体管线） | 端**自行**构造本地错误卡：`code: "unsupported_content"`（协议规定的端侧码），**不**要求回传上游 |
| `status:"error"` 时 `content` / `display` | 可以合法地为空数组与最小 `display`（`card_type: "error"`）；schema 已把二者放宽到该分支（见 §3.3），**不得**因错误响应无法过校验而丢信封 |

禁止：同时用「HTTP 5xx + 纯文本 body」表达应用级失败（端拿不到可渲染结构）。若 Host 需要 HTTP 状态码，**必须**仍返回合法 Envelope（`status:"error"`）；HTTP 状态用于传输层，Envelope 用于应用层。

### 3.2 跨实例 invoke（`content[].type:"action"` 与 `run:"invoke"`）

`invoke.app_id` **不能**被 Host 唯一解析（多市场同名，[01-marketplace.md](01-marketplace.md) §6.1）。因此：

| 项 | 规则 |
|----|------|
| 首选字段 | `invoke.instance_id`：端已装清单里的 `instance_id`（[04-runtime-flow.md](04-runtime-flow.md) §3.2）。Host 直接按实例路由 |
| 兼容写法 | 只有 `app_id` 时，Host **必须**在**同一设备/账号的已装实例**中查找：命中 1 个 → 路由；命中 ≥2 个 → 返回 `code:"ambiguous_target"`（或按 Host 文档声明的确定性规则选定并在 warning 中标出），**禁止**随机挑选 |
| 目标未安装 / `enabled:false` | 返回 `code:"not_installed"`；端**应**隐藏该 action（可用条目级 `requires` 预过滤） |
| 目标端能力不足 | 走目标自己的降级，不阻断当前卡 |
| 递归 | **必须**限定跳数（建议 `invoke` 链深度 ≤ 2）；超深返回 `code:"internal"` 并记日志 |
| 安全 | 嵌套 invoke **不得**绕过发起端的 `limits`（按发起端裁剪）；同样受 Host 限流约束 |

### 3.3 错误码（v1 标准表）

权威枚举：[schemas/vocabulary.schema.json](schemas/vocabulary.schema.json) `$defs.error_code_v1`。

| `code` | 含义 | 谁产生 | 端建议动作 |
|--------|------|--------|------------|
| `unsupported_content` | 端无法渲染任何可降级的形态 | 端 | 本地错误卡 / `voice_reply` 口述 |
| `upstream_timeout` | 上游超 `timeout_ms` | Host | 提示重试 |
| `upstream_error` | 上游非 2xx / 非 Envelope / 校验失败 | Host | 显示 `message`，可重试 |
| `not_installed` | 目标实例未安装或被禁用 | Host / 端 | 隐藏 action，引导去 APP 安装 |
| `config_missing` | 必填配置未填写 | Host | 提示补配置 |
| `rate_limited` | 触发 Host 限流 | Host | 退避后重试；勿立即自动重试 |
| `media_expired` | `playback.expires_at` 已过 | 端 | 重新 invoke 取新列表 |
| `payload_too_large` | 超 `limits.max_content_bytes` 且无法有意义裁剪 | Host | 提示简化查询 |
| `ambiguous_target` | 裸 `app_id` 命中多实例（§3.2） | Host | 提示改用 `instance_id`（发布者应修包） |
| `internal` | 兜底 | 任一侧 | 通用错误 UI |

| 规则 | 要求 |
|------|------|
| 码风格 | 统一 `snake_case`（v1 中 `error.unsupported` 与 `unsupported_content` 混用过，现**以本表为准**；旧写法按 B 级兼容读作 `unsupported_content`，Host 宜归一化后再下发） |
| 未知码 | 端**必须**按通用错误展示（用 `message` / `spoken`），**禁止**因未知码丢弃整份 Envelope |
| `message` | 面向人的短句；**禁止**含密钥、上游鉴权头、内部堆栈、他人设备 ID |
| 样例 | [examples/envelope-error.json](examples/envelope-error.json) |

### 3.4 capability ↔ card_type ↔ content[].type（v1 总表）

三处命名**各自独立**，靠下表映射；新增任一项须按 [07-evolution.md](07-evolution.md) C 级同时补齐三列与 [schemas/vocabulary.schema.json](schemas/vocabulary.schema.json)。

| capability（端申报） | `display.card_type` | `content[].type` | 说明 |
|----------------------|---------------------|------------------|------|
| `content.text` | `plain_result` | `text` | 纯文本 |
| `content.list` | `list` | `list_item` | 通用列表 |
| `content.image` | `image` | `image` | 单图 |
| `content.image_gallery` | `image_gallery` | `image`（多条） | 翻页为端本地行为 |
| `content.music` | `music_list`（可 `max_items:1`） | `music` | v1 **没有** `music` card_type；单首也用列表卡 |
| `content.music_list` | `music_list` | `music` | 歌曲列表 |
| `content.news` | `news_list`（可 `max_items:1`） | `news` | 同上，单条无专用 card |
| `content.news_list` | `news_list` | `news` | 新闻列表 |
| `content.weather` | `weather` | `weather` | 三者同名，别混用途 |
| `content.action` | 无专属：嵌在 `list` / `plain_result` 或独立块变按钮 | `action` | 独立动作块 |
| `content.error` | `error` | `error` | 错误展示，见 §3 |

> 结论：v1 的 `card_type` 是**卡片形态**，`content[].type` 是**条目类型**，`content.*` 是**端能力**——三者不是一一同名映射。声明能力时用 `content.*`，选择渲染器时用 `card_type`，填数据时用 `content[].type`。

## 4. actions[] 公共形状

```json
{
  "id": "play",
  "title": "播放",
  "run": "invoke",
  "invoke": { "app_id": "music.play", "params": { "track_id": "song_001" } },
  "local": "media.pause",
  "handoff": { "kind": "open_url", "url": "https://…" },
  "requires": ["media.play_local"]
}
```

| `run` | 使用字段 |
|-------|----------|
| `invoke` | `invoke`：`{ instance_id \| app_id, params }`；裸 `app_id` 的解析规则见 §3.2 |
| `local` | `local`：**端本地动作 ID**（见下表白名单），不是随意字符串 |
| `handoff` | `handoff: { kind, url?, … }`：`kind` ∈ v1 `{ "open_url" }`（词典 `handoff_kind_v1`），`url` 须 https（例外同 [04-runtime-flow.md](04-runtime-flow.md) §8.1） |

未知 `run` / 未知 `handoff.kind` / 不认识的 `local`：**忽略该 action**（隐藏按钮），禁止当脚本执行、禁止整卡失败。

### 4.1 `run=local` 时 `local` 白名单（v1）

| `local` | 含义 | 通常 requires |
|---------|------|----------------|
| `media.play` | 播放当前条目的 `playback`（或 params 指定 track） | `media.play_local` 或 `media.play_via_xiaozhi`（由端选已声明管线） |
| `media.pause` | 暂停 | 对应 `action.pause` 或已有播控 |
| `media.stop` | 停止并释放解码器 | 同上 |
| `media.next` / `media.prev` | 下一首 / 上一首 | `action.next` / `action.prev` |

端不认识的 `local`：忽略该 action，禁止当脚本执行。管线选择：若只声明了 `media.play_local` 则走本机；只声明 `media.play_via_xiaozhi` 则走云；都有则端自定优先级（建议本机优先）。

## 5. 降级矩阵（全局）

端不支持当前 `display.card_type` 时，按序尝试：

| 当前 | 下一档 |
|------|--------|
| `music_list` | `list` → `plain_result`/`text` → `spoken` → `error`（`unsupported_content`） |
| `news_list` | `list` → `text` → `spoken` → `error`（`unsupported_content`） |
| `image_gallery` | 首张 `image` → `list`（仅 alt/title）→ `text` |
| `weather` | `list` / `plain_result` / `text` → `spoken` |
| `list` | `text` → `spoken` |
| `image` / `error` / `plain_result` | `text` → `spoken` |
| 未知类型 | 应用 `fallback_card_type`（取自已装清单，[04-runtime-flow.md](04-runtime-flow.md) §3.2）→ `text` → `spoken` → `error`（`unsupported_content`） |

**可装 ≠ 每种 card 都有专用 UI。** 白名单里的 `weather`、`image_gallery` 等，若目标端尚未实现专用渲染，须走本矩阵降级，**禁止**在市场条目上假装「该端已完整支持」。新形态优先用已实现的 `list` / `plain_result`；真不够再按 [07-evolution.md](07-evolution.md) 提案。

降级时：

- `music` → `list_item`：title=歌名，subtitle=歌手；丢掉 playback 若无媒体能力或 URL 已过期。
- 截断至 `limits.max_list_items` / `display.max_items` / `limits.max_content_bytes`；Host 硬截断时标 `truncated: true`；端本地截断宜标 `truncated_locally: true`（可选）。
- 降级**不得**伪造：`content[].type` 与 `display.card_type` 必须一并改写为实际渲染的那一档。

## 6. MCP 承载

小智 MCP `tools/call` 结果当前多为 `content[].type=text`。

| 阶段 | 要求 |
|------|------|
| 过渡期 | 允许把 **整份 Envelope JSON** 放进 tool 结果的一段 text，供端解析 |
| 端义务 | 识别 Envelope 后：**投递本机 UI / 播控**；另给模型一段短 `spoken.text` 或摘要，禁止「只把 JSON 念给用户」当作完成渲染 |
| 演进 | 结构化 resource，或 NodeLio 在代理层拆成「UI Envelope + 模型可读摘要」 |

面板 / 各端 UI **不得**把模型闲聊自然语言当唯一数据源来画列表或播控。

**识别 Envelope 的判定条件**（过渡期必备，避免误吞普通文本）：该 text 段 trim 后以 `{` 开头，且 JSON 解析结果同时满足 `schema_version === 1` 且存在 `content` 数组且存在 `display.card_type`。任一不满足 → 视为普通文本，交模型口语，**不做** UI 投递。样例：[examples/mcp-tool-envelope-in-text.md](examples/mcp-tool-envelope-in-text.md)。

## 7. Schema

- 结构：[schemas/content-envelope.schema.json](schemas/content-envelope.schema.json)
- 词典（`content[].type` / `card_type` / `local` / `handoff.kind` / 错误码）：[schemas/vocabulary.schema.json](schemas/vocabulary.schema.json)
- 校验立场：枚举仅提示用途，运行时按 §5 降级，未知值不拒收（[07-evolution.md](07-evolution.md) §5.1）
