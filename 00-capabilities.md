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
- Host 云代理市场时可预过滤，**端仍须本地再算一次**。

## 2. DeviceCapabilities 对象

**线上上报形状**（完整展开、诚实裁剪后的集合；生效顺序见 §4.1，不带 `disabled`）：

```json
{
  "schema_version": 1,
  "protocol_version": 1,
  "platform": "esp32-panel",
  "capabilities": [
    "content.text",
    "content.list",
    "content.music_list",
    "content.news_list",
    "content.weather",
    "content.error",
    "action.invoke",
    "net.http_via_server",
    "input.touch",
    "input.voice",
    "display.color"
  ],
  "surfaces": ["card", "home_tile", "notification", "voice_reply"],
  "limits": {
    "max_content_bytes": 4096,
    "max_list_items": 8,
    "image": { "max_edge_px": 480, "formats": ["jpeg", "png"], "allowed": true }
  }
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `protocol_version` | 是 | 本端实现的 Protocol 主版本 |
| `platform` | 是 | 短名，小写连字符（schema 有 `pattern`）：`esp32-panel` / `android` / `linux` / `voice` |
| `capabilities` | 是 | **本构建已实现**的能力集合，线上唯一权威（词典 §3 + 机器可读 `vocabulary.schema.json`；诚实规则 §3.6；生效计算 §4.1） |
| `profile` | 否 | **构建期**输入；线上可留作类别标签，但 Host 不得据此推断能力 |
| `extra_capabilities` / `disabled` | 否 | **构建期**输入；线上 JSON SHOULD 省略（出现时以 `capabilities` 为准） |
| `surfaces` | 否 | 支持的交互面，见 [05-surfaces.md](05-surfaces.md) |
| `limits` | 否 | 硬上限；嵌入式必须执行；媒体见 §3.7 |

`limits` 缺失时：端仍**必须**执行 §3.7 与 [04-runtime-flow.md](04-runtime-flow.md) §8.2 的字节/图片/媒体底线；Host 云按保守上限（`max_content_bytes ≤ 8192`、`max_list_items ≤ 8`、剥图）代裁剪。完整端样例：[examples/device-esp32-panel-480.json](examples/device-esp32-panel-480.json)（已同步为线上形状）。

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
| `action.invoke` | 可向 Host 云发起 skill invoke |
| `action.play` | 可触发「播放」类 action（具体管线见 media.*） |
| `action.pause` / `action.next` / `action.prev` | 播控 |
| `action.open_url` | 可打开 http(s)（多为手机） |
| `action.handoff` | 可把动作交给 companion 设备 |
| `net.http_via_server` | 仅经 Host 云访问外网（墙板默认）；名字里的 server 指 Host 云 |
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

### 3.5.1 `media.play_via_xiaozhi` 到底指什么（易混，必读）

历史名，保留是为兼容已发布端。语义是**「把曲目 URL 注入助理/云侧的音频下行管线」**：

| 项 | 说明 |
|----|------|
| 数据通路 | 端 **MUST NOT** 自己拉流解码。端把 `playback.url` 交给助理会话/云端播控接口，由**对侧**拉流并混入语音下行 |
| 前置条件 | 该会话管线开放「播放指定 URL」的接口（小智类固件多为 `set url` / 播放器指令；不同厂商接口名不同） |
| 与 `media.play_local` 差别 | 本机拉流 + 本机 codec + 本机喇叭 vs. 交给外部管线出声道 |
| 与「助理正在说话」差别 | 仅 TTS 会话下行、没有注入接口 = **没有**本能力（见 §3.6） |
| 端应做 | 声明本能力时，`local: media.play` 可走该通路；`limits.media` 可缺省（对侧承担解码），若已知对侧支持的格式/码率可填入以便云端预检 |
| 建议演进名 | `media.play_via_assistant`（07 §3 B 级提案；发布后本名保留 alias 至少一个 major） |

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

无 `limits.media` 时：端仍须遵守已声明的 `media.*`；Host 云无法替端保证码率可行，只宜按设备档案做粗裁剪。

### 3.8 词典的机器可读形式与校验策略（硬性）

权威集合见 [schemas/vocabulary.schema.json](schemas/vocabulary.schema.json)（`$defs`）：`capability_name_v1`、`content_type_v1`、`card_type_v1`、`surface_v1`、`local_action_v1`、`handoff_kind_v1`、`profile_v1`、`error_code_v1`。文档表格与本文件冲突时，**以该文件为准**（合入协议改动时两边同改，见 [07-evolution.md](07-evolution.md) §7）。

| 场景 | 端 / Host 行为 |
|------|----------------|
| 能力名形状合法（`^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$`）但**不在 v1 词典** | 视为**未实现**：过滤时按「设备缺失该能力」处理（应用侧则进 `missing_capabilities`）；渲染时按 §5 降级；**禁止**因未知名字拒收整份 JSON |
| 能力名**形状不合法**（大写、空格、斜杠、中文） | **协议错误**：Host 安装校验拒装并返回可诊断错误（字段名 + 非法值）；端收到时忽略该条 + 记 warning |
| `content[].type` / `card_type` / `surface` 未知 | 走 [03-content.md](03-content.md) §5 降级矩阵 / 忽略该 surface；**禁止**整体丢弃 |

> **schema 立场（避免与「未知字段忽略」自相矛盾）**：`capabilities` / `requires` / `optional` 在 schema 中用**形状 pattern** 约束而非 v1 枚举硬拒——否则 B 级演进（新能力名）在旧 Host 上永远校验不过。`surface` / `card_type` 的 `enum` 主要服务编辑器提示与 CI；运行时 MUST 按上表降级。`limits.image.formats` 用短名（`jpeg`），`limits.media.formats` 与 Envelope 用完整 MIME（`image/jpeg`、`audio/mpeg`）：比对时按 subtype 映射（`jpeg` ↔ `image/jpeg`）。统一两侧写法属 **D 级**，v1 冻结现状。

### 3.9 `requires` 里允许出现哪些名字

| 类别 | 进 `requires`？ | 说明 |
|------|-----------------|------|
| `content.*`、`action.*`（渲染与交互形态） | ✅ 可以 | 应用真正的安装条件 |
| `media.play_*` | ⚠️ 仅当应用离开播放无意义 | 一般放 `optional`（§3.5） |
| `net.*`、`input.*` | ⚠️ 谨慎 | 仅当缺了该输入/通路整个应用不可用（如必须手势翻页） |
| `display.color` / `display.mono` / `display.none` | ❌ **禁止** | 物理显示事实，不是渲染契约。用 `content.image*` 表达需要图片渲染，用 `limits.image.allowed` 表达端能画到什么；墨水屏/无屏靠 `density` 与降级矩阵处理。若确实「非彩屏不可用」，那是产品选择，须按 [07-evolution.md](07-evolution.md) 提案新增语义名，而不是复用物理名 |

## 4. Profile 预设与生效能力计算

### 4.1 生效顺序与「线上形状」（硬性）

`profile` / `extra_capabilities` / `disabled` 是**构建期输入**；市场过滤与安装校验只消费**展开后的最终集合**。计算顺序固定如下（端实现与 Host 均按此，勿自创顺序）：

```text
1. base = profile 展开（§4.2 类目标模板；未写 profile → base = 空集）
2. base = base ∪ extra_capabilities          # 追加；名字须过 §3.8 形状校验
3. eff  = base − disabled                    # 去掉未实现项
4. eff  = honest_trim(eff)                   # §3.6：未过本构建验收的名字不得出现在 eff
5. eff  = enforce_consistency(eff, limits, surfaces)
     # 例：limits.media.fetch 与 net.* 一致；报 now_playing 须有任一 media.play_* 或 action.play
6. 线上上报 MUST 只写 { capabilities: eff, surfaces, limits }
```

| 规则 | 要求 |
|------|------|
| 线上唯一权威 | 同一份 JSON 同时出现 `capabilities` 与 `extra_capabilities`/`disabled` 时，Host **MUST** 直接以 `capabilities` 为准并记 warning——**不重算**，避免两种顺序得出不同结果 |
| 线上 SHOULD | 不带 `profile` / `extra_capabilities` / `disabled`；这些留在构建期文件/代码常量里 |
| 线上 `profile` 的作用 | 仅作人类可读类别标签与 Host 默认 `limits` 兜底；**禁止**据此推断任何能力（§3.6、§3.5.1） |
| 与模板冲突 | `capabilities` 与 profile 模板不一致时**不报错、不改写**，以 `capabilities` 为准——「诚实申报优先于模板」的直接推论 |

> 为什么钉死：若允许「线上带 profile、由 Host 展开再 disabled」，则同一固件在不同 Host 上可装集合不同，过滤结果不可复现。步骤 6 把生效集合的**唯一真相固定在端自己上报的 `capabilities`** 上。

### 4.2 各 profile 类目标模板

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
- 固件未通播控验收前：**线上上报的 `capabilities` 里不得出现** `media.play_local` / `action.play`（§4.1 步骤 3–6）；构建期可用 `disabled: [...]`，但发往 Host 前必须已展开并去掉

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

1. 先用应用 `fallback.card_type`（若端支持）。**该值必须出现在设备侧已安装清单里**（`fallback_card_type` 字段，见 [04-runtime-flow.md](04-runtime-flow.md) §3.2），否则端无从取得。
2. 再按全局矩阵降档。
3. 仍不行 → `error` + `code: unsupported_content`，或 `voice_reply` 口述摘要（若有 `surface.voice_reply` 与文本）。

## 6. Schema

- 结构：[schemas/device-capabilities.schema.json](schemas/device-capabilities.schema.json)
- 词典（能力名 / card_type / surface / 错误码等）：[schemas/vocabulary.schema.json](schemas/vocabulary.schema.json) —— §3.8
