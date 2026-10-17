# 市场过滤示例说明

目标设备取自同目录 `device-*.json`，市场取自 `marketplace-sample.json`（5 个条目）。

> 设备 JSON 均为**线上形状**（完整展开后的 `capabilities`，不带 `disabled`）；生效计算见 [../00-capabilities.md](../00-capabilities.md) §4.1。

## 墙板两份样例（勿混）

| 文件 | 含义 |
|------|------|
| `device-esp32-panel-480.json` | **当前诚实申报**：能渲染音乐/新闻列表，**尚未**申报本机播放（集合里根本没有 `media.play_local` / `action.play`） |
| `device-esp32-panel-480-with-media.json` | **播控验收通过后**才应上报的形态（含 `media.play_local` + `limits.media`） |

硬件有喇叭 ≠ 自动用 with-media。见 [../06-platform-profiles.md](../06-platform-profiles.md)。

## 对 `esp32-panel-480`（content-only 样例）

| app_id | installable | 原因 |
|--------|-------------|------|
| `music.search` | 是 | `requires` 仅 content + invoke；播放在 `optional` |
| `news.latest` | 是 | 有 `content.news_list` |
| `demo.envelope` | 是 | 纯档 A；`content.text` + `action.invoke` |
| `weather.today` | 是 | 有 `content.weather`（若该端尚未实现天气专用渲染，运行时按 [../03-content.md](../03-content.md) §5 降级到 `list`/`text`，**可装 ≠ 有专用 UI**） |
| `gallery.photo` | **否** | 缺 `content.image_gallery`（`missing_capabilities`） |

安装后：可 invoke 出列表卡；无 `media.play_local` 时隐藏播放 action，仍可展示歌名。
with-media 样例下：点播走本机拉流；`concurrent_with_voice_session=false` 由端执行（播前挂起会话）。

## 对 `android-phone`

五个应用均可装（含 `gallery.photo`）。音乐可用 `fullscreen` + `media.play_local`。

## 对 `voice-only`

| app_id | installable | 说明 |
|--------|-------------|------|
| `demo.envelope` | **是** | `requires: content.text + action.invoke` 全满足，且 `surfaces` 含 `voice_reply` |
| `music.search` | **否**（严格） | 缺 `content.music_list` |
| `news.latest` | **否**（严格） | 缺 `content.news_list` |
| `weather.today` | **否**（严格） | 缺 `content.weather` → 语音盒需要天气，应让发布者**另发口述版**（`requires: ["content.text","action.invoke"]` + 强 `spoken`），而不是让端假装能装 |
| `gallery.photo` | 否 | 缺图库能力 |

若实现选择「宽松语音」：仍可不装，或由 Host 在 invoke 时只返回 `spoken` + 降级 `text`（须应用声明 `fallback`，且该字段已随设备清单下发 `fallback_card_type`——v1 推荐严格匹配）。

## 同一 Envelope，不同 Surface

`envelope-music-list.json`：

- 墙板：`preferred_surface=card` → 列表卡；有 `media.play_local` 才点播，否则只展示
- 手机：可改用 `fullscreen`
- 语音盒（口述版应用）：只用 `spoken.text`

## 已装清单里的 enabled 怎么算

对照 `installed-app-list-panel.json`（目标设备 = `device-esp32-panel-480.json`）：

| instance | enabled | 原因 |
|----------|---------|------|
| `inst_7f3a` music.search | `true` | requires 全覆盖 |
| `inst_2c81` demo.envelope | `true` | 纯文本档 A |
| `inst_5d40` news.latest | `false` | `disabled_reason: config_required`——能力够，但 `api_key` 没填 |
| `inst_9b12` gallery.photo | `false` | `disabled_reason: missing_capabilities`，`missing_capabilities: ["content.image_gallery"]` |

要点：**能力够 ≠ 可 invoke**（配置缺失同样禁用），且禁用项必须带原因，端 UI 才能解释而不是让条目凭空消失。
