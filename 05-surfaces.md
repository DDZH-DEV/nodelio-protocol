# 05 — 交互面（Surfaces）与呈现提示

**Content** 描述数据；**Surface** 描述出现在设备的哪一类交互槽位；**presentation hints** 是可选拥挤提示。三者分离，才能让墙板、手机、无屏音箱、旋钮机共用同一 Envelope。

```text
Content → Surface → hints → 平台渲染器（由各端作者自行发挥）
```

Surface 只是**槽位名字**（结果出现在「卡片区 / 首页磁贴 / 口述」等），**不是**交互设计说明书。具体怎么点、怎么滑、怎么播，由该硬件/OS 的实现者决定。

禁止：远程下发具体控件树、像素坐标、可执行 UI 脚本。

## 1. Surface 字典（v1）

| surface | 含义 | 典型端 |
|---------|------|--------|
| `card` | 技能结果 / 会话区卡片 | 墙板、手机 |
| `home_tile` | 首页常驻入口磁贴 | 墙板（与 layout 并存） |
| `fullscreen` | 沉浸（播放器、大图） | 手机、大屏 |
| `voice_reply` | 以口述 / TTS 为主（可无像素 UI） | 无屏、小智口语 |
| `notification` | 短时提示（toast / 系统通知） | 手机；墙板 toast |
| `now_playing` | 迷你播控条 | 有扬声器且支持播控的端 |

端在 `DeviceCapabilities.surfaces` 中声明；应用在包 / 市场条目中声明。

### 匹配

```text
usable_surfaces = app.surfaces ∩ device.surfaces
若任一方未声明 surfaces，则视为「不限制」，由端用自有默认面展示。
能展示 ⟺ 存在至少一种 usable surface，或可降级到 voice_reply/text。
```

## 2. 选择算法

给定 Envelope 的 `display.preferred_surface`：

1. 若 ∈ `device.surfaces` → 用它。
2. 否则由**端作者自定**回退顺序（下列仅为理解示例，非强制）：
   - 有屏触控常见：`card` → `fullscreen` → …
   - 无屏常见：`voice_reply` → …
3. `card_type` 与 surface 的常见组合（示例，非强制 UI）：

| card_type | 常见 surface |
|-----------|----------------|
| `music_list` | `card`；播放中叠加 `now_playing` / `fullscreen` |
| `news_list` | `card`；点开文章 `handoff` 或手机 `fullscreen` |
| `image_gallery` | `fullscreen` 优先，否则 `card` |
| `plain_result` | `card` 或 `voice_reply` |
| `weather` | `card` / `home_tile` |

## 3. Presentation hints

位于 `display`（见 [03-content.md](03-content.md)）：

| 字段 | 值 | 说明 |
|------|-----|------|
| `preferred_surface` | surface 名 | 偏好面 |
| `density` | `compact` \| `normal` \| `rich` | 拥挤度；小屏/E-ink 可强制 compact |
| `prefer_image` | bool | false 时端应丢图 |
| `max_items` | int | 与 `limits.max_list_items` 取更严 |
| `ttl_sec` | int | 缓存建议 |
| `title` | string | 面标题 |
| `auto_play` | bool | **可选**。结果到达后是否自动播放首选条目；**缺省 = false**，端不得自行默认自动播。仅当端声明任一 `media.play_*` 才有意义（[03-content.md](03-content.md) §2.4 `keyword` 语义与此一致） |

端可忽略 hints，但不得执行未识别的扩展为代码。未知 hint 名：忽略（形状词典见 [schemas/vocabulary.schema.json](schemas/vocabulary.schema.json)）。

### 端强制策略示例

| 端 | 策略 |
|----|------|
| esp32-panel-480 | 默认 `density=compact`；`max_items≤8`；大图缩略或丢弃 |
| display.mono | `prefer_image=false` |
| display.none | 仅 `spoken` / `voice_reply` |
| input 无 touch | 列表用键/旋钮焦点模型，不依赖手势 |

## 4. 同一 Content，不同 Surface（示例）

音乐搜索 Envelope 不变：

| 端 | Surface | 行为 |
|----|---------|------|
| 墙板 | `card` + `now_playing` | 列表点选 → 已声明的 `media.play_local`（未声明则只展示） |
| 手机 | `fullscreen` | 富播放器 + `media.play_local` |
| 音箱 | `voice_reply` | 播报 `spoken.text` + 直接播第一首（若有 media） |

## 5. home_tile 与控家 layout

- `home_tile` 是技能入口，**不替代** layout 里的灯控磁贴。
- 墙板可将技能入口放在系统「技能」页或少量首页槽位；schema 增量须向后兼容。
- 磁贴点击 → 本地打开 `card` 或直接 `invoke` 默认查询（由应用 `ui` / 配置决定）。
- **钉选元数据**（`pinned` / `home_order` / 默认 invoke 参数）**不属于** Envelope 字段，也不属于本协议：由 Host 云按设备隔离下发，形状由各 Host 自己的产品文档规定。协议只保证：这些元数据不得改变 §1 的 surface 语义与 §3 的 hints 含义。

## 6. Schema 片段

Surface 名的**形状**约束见 [schemas/surfaces.schema.json](schemas/surfaces.schema.json)（供 `$ref`；小写短名，未知值忽略）；v1 **权威集合**见 [schemas/vocabulary.schema.json](schemas/vocabulary.schema.json) `$defs.surface_v1`。二者分工与理由见 [00-capabilities.md](00-capabilities.md) §3.8、[07-evolution.md](07-evolution.md) §5.1。

## 7. 平台呈现策略（不属于协议强制）

Surface 只命名槽位。下列属于**各端产品文档**，不进 schema、不做跨端一致性验收：

| 话题 | 协议 | 平台 |
|------|------|------|
| 会话中结果出现在对话框上方、压矮聊天区 | 仍用 `card`（或端自选回退） | 墙板 overlay 布局策略 |
| 列表行高、封面是否显示 | `density` / `prefer_image` hints | LVGL / Compose 实现 |
| 播放条贴顶还是贴底 | `now_playing` 槽位 | 端 UI |
| 卡片在会话结束是否自动关 | `ttl_sec` 为缓存建议 | 端生命周期（建议：新 Envelope 覆盖；会话结束可保留 `now_playing`） |

**不新增** `session_card` 一类 surface，除非多端都需要「与会话绑定」的可过滤差异；墙板用「`card` + 会话态布局」即可。多端差异说明见 [06-platform-profiles.md](06-platform-profiles.md)。
