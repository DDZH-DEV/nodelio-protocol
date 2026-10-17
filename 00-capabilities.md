# 00 — 端能力（DeviceCapabilities）

端必须能回答：「我能渲染什么、输入什么、怎么播媒体、资源上限是多少？」应用与市场用同一套能力名做过滤。

## 1. 匹配算法

```text
missing = app.requires − device.capabilities
installable = (missing 为空)
           ∧ (protocol_version ≥ app.min_protocol)
           ∧ surfaces_ok

surfaces_ok =
  若任一方未声明 surfaces → true
  否则 app.surfaces ∩ device.surfaces ≠ ∅
```

- `optional` 缺失：不阻止安装；隐藏依赖该能力的 action，或按降级矩阵削弱展示。
- UI 须能给出 `missing_capabilities`（及可选的 `missing_surfaces`）。
- SERVER 代理市场时可预过滤，**端仍须本地再算一次**。

## 2. DeviceCapabilities 对象

```json
{
  "schema_version": 1,
  "protocol_version": 1,
  "platform": "esp32-panel",
  "profile": "esp32-panel-480",
  "capabilities": ["content.text", "content.list", "action.invoke"],
  "surfaces": ["card", "notification", "voice_reply"],
  "limits": {
    "max_content_bytes": 4096,
    "max_list_items": 8,
    "image": { "max_edge_px": 480, "formats": ["jpeg", "png"], "allowed": true },
    "media": {
      "formats": ["audio/mpeg"],
      "max_bitrate_kbps": 128,
      "concurrent_with_voice_session": false,
      "fetch": "http_via_server"
    }
  }
}
```

| 字段 | 说明 |
|------|------|
| `protocol_version` | 本端实现的 Protocol 主版本 |
| `platform` | 自由短名：`esp32-panel` / `android` / `linux` / `voice` |
| `profile` | 可选；见 §4，展开后再允许 `extra_capabilities` / `disabled` |
| `capabilities` | **本构建已实现**的能力集合（权威表 §3；见 §3.6 诚实规则） |
| `surfaces` | 支持的交互面，见 [05-surfaces.md](05-surfaces.md) |
| `limits` | 硬上限；嵌入式必须执行；媒体见 §3.7 |

### limits 建议默认

| 端 | max_content_bytes | max_list_items | image |
|----|-------------------|----------------|-------|
| esp32-panel-480 | 4096 | 8 | edge≤480，jpeg/png |
| android-phone | 262144 | 50 | 宽裕 |
| voice-only | 2048 | 5 | `allowed: false` |

## 3. 能力字典（v1）

### 3.1 Content（与 card_type 对应）

| capability | 含义 |
|------------|------|
| `content.text` | 纯文本 / `plain_result` |
| `content.list` | 通用列表 |
| `content.image` | 单图 |
| `content.image_gallery` | 多图翻页 |
| `content.music` | 单曲条目 |
| `content.music_list` | 歌曲列表卡 |
| `content.news` | 单条新闻 |
| `content.news_list` | 新闻列表 |
| `content.weather` | 天气卡 |
| `content.action` | 独立动作块 |
| `content.error` | 错误展示 |

声明 `content.music_list` 通常隐含能展示其条目级 `content.music` 字段；若只能列表不能播，不要申报 `media.*`。

### 3.2 Action / 网络

| capability | 含义 |
|------------|------|
| `action.invoke` | 可对 SERVER 发起 skill invoke |
| `action.play` | 可触发「播放」类 action（具体管线见 media.*） |
| `action.pause` / `action.next` / `action.prev` | 播控 |
| `action.open_url` | 可打开 http(s)（多为手机） |
| `action.handoff` | 可把动作交给 companion 设备 |
| `net.http_via_server` | 仅经 NodeLio SERVER 访问外网（墙板默认） |
| `net.http_direct` | 允许端直连外网（慎用） |

### 3.3 输入

| capability | 含义 |
|------------|------|
| `input.touch` | 触摸 |
| `input.voice` | 语音口令 / 对话 |
| `input.key` | 物理键 / D-pad |
| `input.rotary` | 旋钮 |

无 `input.touch` 时，列表须可用 `input.key` / `rotary` / `voice` 导航；应用不得 `requires: ["input.touch"]` 除非确实无法降级。

### 3.4 显示

| capability | 含义 |
|------------|------|
| `display.color` | 彩色像素屏 |
| `display.mono` | 单色 / 墨水屏 |
| `display.none` | 无屏 |

### 3.5 媒体输出

| capability | 含义 | 非含义 |
|------------|------|--------|
| `media.play_local` | **本机**拉取（或经云代理）`playback.url`，解码后从本机扬声器/耳机输出 | 「板上有喇叭」≠ 已实现；「助理能说话」≠ play_local |
| `media.play_via_xiaozhi` | 交给云端/助理侧**可注入任意曲目 URL** 的播控管线（能力名历史保留） | 仅有会话语音下行（助理在说话）**不算**本能力 |
| `media.play_handoff` | 投到 companion（手机/音箱）播放 | — |

`action.play` / `pause` / `next` / `prev`：表示端能展示并触发播控动作；**具体走哪条管线**由条目 `actions[].run` + `media.*` 决定。有 `action.play` 无任一 `media.play_*` 时：可展示列表，须隐藏/降级播放钮。

音乐类应用推荐（播放勿进 `requires`，除非应用离开播放无意义）：

```json
"requires": ["content.music_list", "action.invoke"],
"optional": ["media.play_local", "media.play_via_xiaozhi", "action.play", "content.image"]
```

### 3.6 申报诚实（硬性）

1. **运行时 `capabilities` = 本固件/本 APP 构建已实现且可验收的集合**，不是原理图、不是路线图。
2. Profile 预设是**类目标模板**；未实现的项必须用 `disabled` 去掉，或展开后不要写入运行时 JSON。
3. 不得用「有喇叭 / 能跑语音助理会话」推断 `media.play_local` 或 `media.play_via_xiaozhi`。
4. 性能不够（OOM、无法与语音会话并存、仅支持 PCM 不支持 MP3）→ **不要申报**对应能力，或收紧 `limits.media` 后仍测不过则撤声明。
5. 平台算力、互斥、功耗等细节见 [06-platform-profiles.md](06-platform-profiles.md)；**协议只消费申报结果**。

### 3.7 `limits.media`（可选，有 media.* 时建议）

```json
"limits": {
  "max_content_bytes": 4096,
  "max_list_items": 8,
  "image": { "allowed": true, "max_edge_px": 480, "formats": ["jpeg", "png"] },
  "media": {
    "formats": ["audio/mpeg", "audio/mp4"],
    "max_bitrate_kbps": 128,
    "max_duration_sec": 600,
    "concurrent_with_voice_session": false,
    "fetch": "http_via_server"
  }
}
```

| 字段 | 说明 |
|------|------|
| `formats` | 本机可解码的 `playback.mime` 白名单 |
| `max_bitrate_kbps` / `max_duration_sec` | 软上限；超限可拒播或只播前 N 秒（端自定，须可预期） |
| `concurrent_with_voice_session` | `false` = 播前须结束/挂起语音助理会话（嵌入式常见） |
| `fetch` | `http_via_server` \| `http_direct`；须与 `net.*` 能力一致 |

无 `limits.media` 时：端仍须遵守已声明的 `media.*`；SERVER 无法替端保证码率可行，只宜按设备档案做粗裁剪。

## 4. Profile 预设

端可只写 `profile`，实现方展开为默认 `capabilities` + `surfaces` + `limits`，再用：

- `extra_capabilities`: string[] 追加
- `disabled`: string[] 从展开结果中去掉

展开结果在**发往市场过滤 / 安装校验之前**必须再做一次「本构建诚实裁剪」。

### `esp32-panel-480`

**内容 / 输入（类默认，通常可声明）：**  
`content.text`, `content.list`, `content.music_list`, `content.news_list`, `content.weather`, `content.error`, `action.invoke`, `net.http_via_server`, `input.touch`, `input.voice`, `display.color`

**播控（类目标，默认不自动等于已实现）：**  
- 模板可含 `action.play`、`media.play_local`（本机拉流解码）  
- **不要**把 `media.play_via_xiaozhi` 当作本 profile 默认——会话语音 ≠ 曲库注入  
- 固件未通播控验收前：运行时必须 `disabled: ["media.play_local", "action.play"]` 或展开时省略  

**surfaces：** `card`, `home_tile`, `notification`, `voice_reply`, `now_playing`（`now_playing` 仅在确有播控 UI 时声明）

**limits：** 见 §2 表；有 `media.play_local` 时须带 `limits.media`（建议 `concurrent_with_voice_session: false`，`fetch: http_via_server`）

硬件能不能播、内存够不够 → [06-platform-profiles.md](06-platform-profiles.md) §esp32-panel，**不由本词典保证**。

### `android-phone`

- 上述 content.* 全开 + `content.image` + `content.image_gallery`
- `media.play_local`, `action.play`, `action.pause`, `action.open_url`, `action.handoff`, `net.http_via_server`
- surfaces: `card`, `fullscreen`, `notification`, `now_playing`, `voice_reply`
- `limits.media` 可较宽；`concurrent_with_voice_session` 可由实现决定

### `linux-kiosk`

- 近 android；按实际裁剪 touch / 分辨率 / media formats

### `voice-only`

- `content.text`, `content.error`, `action.invoke`, `input.voice`, `display.none`, `net.http_via_server`
- `media.play_via_xiaozhi` 或 `media.play_local`：**仅当**该音箱固件真能播曲，不要因「能 TTS」而声明
- surfaces: `voice_reply`（及可选 `notification`）

新硬件：选最近 profile → `extra` / `disabled`，**禁止私造同义能力名**。新名字须先进入本词典再发应用。

## 5. 降级与运行时

见 [03-content.md](03-content.md) §降级矩阵。原则：

1. 先用应用 `fallback.card_type`（若端支持）。
2. 再按全局矩阵降档。
3. 仍不行 → `error` + `code: unsupported_content`，或 `voice_reply` 口述摘要（若有 `surface.voice_reply` 与文本）。

## 6. Schema

机器可读：[schemas/device-capabilities.schema.json](schemas/device-capabilities.schema.json)
