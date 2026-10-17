# 03 — 跨端内容（Content Envelope）

invoke（及未来推送）的统一结果格式。协议只定 JSON；各端按 `card_type` / `content[].type` 自行渲染。

## 1. Envelope

```json
{
  "schema_version": 1,
  "request_id": "req_123",
  "app_id": "music.search",
  "status": "ok",
  "content": [],
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

| 字段 | 说明 |
|------|------|
| `status` | `ok` \| `error` |
| `content` | 条目数组；类型见 §2 |
| `display` | 展示意图；hints 见 [05-surfaces.md](05-surfaces.md) |
| `spoken` | 可选；供 `voice_reply` / TTS |
| `error` | `status=error` 时：`{ "code", "message" }` |

`display.card_type` 决定主渲染器；`content[]` 提供数据。两者应一致（如 `music_list` 配 `type:music` 条目）。

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
    "expires_at": 1790000000
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
`playback.url` 常有过期时间；勿永久写入 NVS。无 `media.play_*` 时隐藏 play，仍可展示列表。

`music.search` 的 `keyword` **可选**。省略或空字符串表示列出当前账号曲库（条数受 `display.max_items` 限制），此时 `display.auto_play` 为 `false`，只展示不自动播放。有具体歌名/歌手才搜索，并可由端决定是否播第一条。

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

### 2.8 `error`

```json
{
  "type": "error",
  "id": "e1",
  "code": "upstream_timeout",
  "message": "上游超时"
}
```

Capability: `content.error`（端应总能展示错误，即使未申报也建议内置）。

## 3. actions[] 公共形状

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
| `invoke` | `invoke.app_id` + `params` |
| `local` | `local`：**端本地动作 ID**（见下表），不是随意字符串 |
| `handoff` | `handoff` |

条目级 `requires`：缺则隐藏该 action。`requires` 写能力名（如 `media.play_local`）；`local` 写动作 ID（如 `media.play`）。二者不要混用。

### `run=local` 时 `local` 白名单（v1）

| `local` | 含义 | 通常 requires |
|---------|------|----------------|
| `media.play` | 播放当前条目的 `playback`（或 params 指定 track） | `media.play_local` 或 `media.play_via_xiaozhi`（由端选已声明管线） |
| `media.pause` | 暂停 | 对应 `action.pause` 或已有播控 |
| `media.stop` | 停止并释放解码器 | 同上 |
| `media.next` / `media.prev` | 下一首 / 上一首 | `action.next` / `action.prev` |

端不认识的 `local`：忽略该 action，禁止当脚本执行。管线选择：若只声明了 `media.play_local` 则走本机；只声明 `media.play_via_xiaozhi` 则走云；都有则端自定优先级（建议本机优先）。

## 4. 降级矩阵（全局）

端不支持当前 `display.card_type` 时，按序尝试：

| 当前 | 下一档 |
|------|--------|
| `music_list` | `list` → `plain_result`/`text` → `spoken` → `error.unsupported` |
| `news_list` | `list` → `text` → `spoken` → `error.unsupported` |
| `image_gallery` | 首张 `image` → `list`（仅 alt/title）→ `text` |
| `weather` | `text` → `spoken` |
| `list` | `text` → `spoken` |
| 未知类型 | 应用 `fallback.card_type` → `text` → `spoken` → `error.unsupported` |

降级时：

- `music` → `list_item`：title=歌名，subtitle=歌手；丢掉 playback 若无媒体能力。
- 截断至 `limits.max_list_items` / `display.max_items` / `limits.max_content_bytes`。

## 5. MCP 承载

小智 MCP `tools/call` 结果当前多为 `content[].type=text`。

| 阶段 | 要求 |
|------|------|
| 过渡期 | 允许把 **整份 Envelope JSON** 放进 tool 结果的一段 text，供端解析 |
| 端义务 | 识别 Envelope 后：**投递本机 UI / 播控**；另给模型一段短 `spoken.text` 或摘要，禁止「只把 JSON 念给用户」当作完成渲染 |
| 演进 | 结构化 resource，或 NodeLio 在代理层拆成「UI Envelope + 模型可读摘要」 |

面板 / 各端 UI **不得**把模型闲聊自然语言当唯一数据源来画列表或播控。

## 6. Schema

[schemas/content-envelope.schema.json](schemas/content-envelope.schema.json)
