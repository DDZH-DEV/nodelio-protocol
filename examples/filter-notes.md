# 市场过滤示例说明

目标设备取自同目录 `device-*.json`，市场取自 `marketplace-sample.json`。

## 墙板两份样例（勿混）

| 文件 | 含义 |
|------|------|
| `device-esp32-panel-480.json` | **当前诚实申报**：能渲染音乐列表，**尚未**申报本机播放（`disabled` 掉 media） |
| `device-esp32-panel-480-with-media.json` | **播控验收通过后**才应上报的形态（含 `media.play_local` + `limits.media`） |

硬件有喇叭 ≠ 自动用 with-media。见 [06-platform-profiles.md](../06-platform-profiles.md)。

## 对 `esp32-panel-480`（content-only 样例）

| app_id | installable | 原因 |
|--------|-------------|------|
| `music.search` | 是 | `requires` 仅 content + invoke；播放在 `optional` |
| `news.latest` | 是 | 有 `content.news_list` |
| `gallery.photo` | **否** | 缺 `content.image_gallery` |

安装后：可 invoke 出列表卡；无 `media.play_local` 时隐藏播放 action，仍可展示歌名。  
with-media 样例下：点播走本机拉流；`concurrent_with_voice_session=false` 由端执行（播前挂起会话）。

## 对 `android-phone`

三个应用均可装（含 `gallery.photo`）。音乐可用 `fullscreen` + `media.play_local`。

## 对 `voice-only`

| app_id | installable | 说明 |
|--------|-------------|------|
| `music.search` | **否**（严格） | 缺 `content.music_list` |
| `news.latest` | **否**（严格） | 缺 `content.news_list` |
| `gallery.photo` | 否 | 缺图库能力 |

若实现选择「宽松语音」：仍可不装，或由 SERVER 在 invoke 时只返回 `spoken` + 降级 `text`（须应用声明 `fallback`——v1 推荐严格匹配，语音盒单独做口述型应用 `requires: ["content.text"]`）。

## 同一 Envelope，不同 Surface

`envelope-music-list.json`：

- 墙板：`preferred_surface=card` → 列表卡；有 `media.play_local` 才点播，否则只展示
- 手机：可改用 `fullscreen`
- 若将来语音盒可装口述版：只用 `spoken.text`
