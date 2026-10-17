# MCP 过渡期承载示例（03-content.md §6）

场景：语音助理通过统一 MCP 工具调用 `skill.invoke`，Host 云把结果塞进 tool 返回的 `text` 段。

## 1. Host → 助理（tool 结果，过渡期形状）

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"schema_version\":1,\"request_id\":\"req_music_001\",\"app_id\":\"music.search\",\"status\":\"ok\",\"content\":[{\"type\":\"music\",\"id\":\"song_001\",\"title\":\"晴天\",\"artist\":\"周杰伦\",\"playback\":{\"url\":\"https://cdn.example.com/audio/qingtian.mp3\",\"mime\":\"audio/mpeg\",\"expires_at\":1792300000}}],\"display\":{\"card_type\":\"music_list\",\"title\":\"搜索结果\",\"preferred_surface\":\"card\",\"max_items\":8},\"spoken\":{\"text\":\"找到 1 首：晴天\"}}"
    }
  ]
}
```

> 完整可读版信封见 [envelope-music-list.json](envelope-music-list.json)（此处为单条目精简版，内容一致）。

## 2. 端的识别判定（必须严格，避免误吞普通文本）

```text
取 content[0].text
  → trim 后以 '{' 开头？           否 → 当普通文本交模型口语
  → JSON 解析成功？                否 → 当普通文本
  → schema_version === 1 ？        否 → 当普通文本
  → 存在 content 数组 ？           否 → 当普通文本
  → 存在 display.card_type ？      否 → 当普通文本
以上全过 → 认定是本协议 Envelope
```

## 3. 认定后的**双投递**（端义务）

| 目标 | 投什么 | 反例 |
|------|--------|------|
| 本机 UI / 播控 | 完整 Envelope：按 `display.card_type` 选渲染器，不支持则走 §5 降级矩阵 | ❌ 只把 JSON 字符串显示给用户 |
| 模型 / 口语 | **一段短文本**：优先 `spoken.text`（本例「找到 1 首：晴天」） | ❌ 把整份 JSON 念给用户当「已渲染」 |

```text
// 伪码
if isEnvelope(text):
    renderLocally(envelope)                       # 卡片 / now_playing / 播放
    replyToModel(envelope.spoken?.text
                 || firstTitle(envelope.content)
                 || "已显示结果")                  # 短摘要，交口语管线
else:
    passThroughToModel(text)
```

## 4. 常见错误做法

| 做法 | 为什么错 |
|------|----------|
| 端解析模型的自然语言闲聊来画列表 | 无结构保证、无 id、无过期语义，播控与降级全部失效（03 §6） |
| Host 直接把上游原始 API JSON 塞进 tool text | 不是 Envelope，端只能当普通文本；等于放弃整个协议（应走档 A/B） |
| 端识别到 Envelope 却只回「好的」 | 用户看不到列表、也听不到摘要，等价于失败 |
| 把 `playback.url` 长期存进 NVS 当唯一真相 | 忽略 `expires_at`（Unix 秒），下次开播必失败（03 §2.4） |

## 5. 演进方向（非当前义务）

结构化 resource，或 Host 代理层拆成「UI Envelope 走设备通道 + 模型可读摘要走 tool text」两条，端不再需要猜 JSON。
