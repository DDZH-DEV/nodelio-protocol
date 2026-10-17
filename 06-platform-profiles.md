# 06 — 平台附录（与协议的边界）

> 本文**不是**第二套协议，也不绑定任一厂商仓库或本机路径。  
> 它说明：各 **profile 类设备**如何把产品事实**诚实映射**到 `DeviceCapabilities`，避免把「某块板的现状」误当成跨端契约。

第三方只需要本 `Protocol/` 目录即可理解与实现；具体芯片型号、仓库路径、私有固件树由**各产品自己的**硬件/固件文档维护，**不要**写进本文件的权威表述。

## 1. 关联性（结论先说）

| 问题 | 与 Protocol 关系 |
|------|------------------|
| Envelope / card_type / requires 匹配 | **强** — 协议正文 |
| 某型号能不能本机播音乐、解码是否卡顿 | **弱** — 产品/固件事实；只通过「是否申报 `media.*` + `limits.media`」影响协议 |
| 对话区上方如何摆卡片、聊天区高度 | **无** — 纯平台 UX（[05-surfaces.md](05-surfaces.md) §7） |
| 编解码器型号、唤醒引擎与 TLS 互斥、息屏电流 | **无** — 各产品硬件约束文档；协议不写芯片名与仓库路径 |

**规则：** 实现方研究清楚「能不能、够不够」之后，用运行时申报表达结果；市场与云端 **只认申报**，不认原理图或本文举例。

```text
硬件/系统事实  →  固件是否实现并可验收  →  运行时 capabilities / limits
                      ↑ 唯一进入协议世界的闸门
```

## 2. Profile 与「产品文档」的关系

| profile | 指什么类设备 | 产品事实写在哪 |
|---------|--------------|----------------|
| `esp32-panel-480` | ~480×480 彩触墙板 / 面板类（MCU 资源紧） | **该产品**自己的硬件约束与固件说明（本协议不收录路径） |
| `android-phone` | 手机 / 平板类 Android 端 | 该 APP 工程与系统播放器文档 |
| `linux-kiosk` | Linux 大屏 / 展会机 | 该产品仓库 |
| `voice-only` | 无屏音箱 / 语音盒 | 该产品仓库 |

协议只规定 profile **名**与匹配算法；某品牌是否叫「某某 86 盒」、固件在哪个 Git 仓库，均与协议无关。

---

## 3. `esp32-panel-480`（嵌入式彩触面板类）

### 3.1 和协议强相关的部分

- 有彩屏 + 触摸 + 语音输入 → 可申报 `display.color`、`input.touch`、`input.voice`、若干 `content.*`、`card` 等。
- 内存紧、列表宜短 → `limits.max_content_bytes=4096`、`max_list_items=8` 是协议侧硬上限，端必须执行。
- 外网默认经云代理 → `net.http_via_server`；慎用 `net.http_direct`。

### 3.2 本机播音乐：协议不保证，产品要自证

本类设备常见情况（**类特征，非某一板卡承诺**）：

| 事实层 | 类设备上常见情况 | 对申报的含义 |
|--------|------------------|--------------|
| 硬件 | 往往有 I2S/codec 扬声器通路 | **仅证明可能出声**，不等于已实现 `media.play_local` |
| 助理会话音频 | 云端/助理下行语音（如 Opus）能播 | **不是** `media.play_via_xiaozhi`（该能力要求可注入**曲目 URL**） |
| 目标能力 | 拉 `playback.url` → 本机解码 → 喇叭 | 验收通过后才申报 `media.play_local` + `action.play` |
| 性能风险 | DRAM/PSRAM 紧；唤醒/会话与 TLS/解码常需互斥；刷屏与音频抢带宽 | 建议 `limits.media.concurrent_with_voice_session: false`；码率/格式测不过则缩小 `formats` 或不申报 |
| 省电 | 播放中可出声，背光仍可按 idle 熄 | 产品策略；协议不管 |

**不合理：** 因 profile 名或「板上有喇叭」就在市场里默认「可播音乐」。  
**合理：** 未通播控前，线上上报（完整展开 + 诚实裁剪，形状规则见 [00-capabilities.md](00-capabilities.md) §4.1）：

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
    "image": { "allowed": true, "max_edge_px": 480, "formats": ["jpeg", "png"] }
  }
}
```

要点：`media.play_local` / `action.play` **根本不在** `capabilities` 里（不是靠 `disabled` 表达）；无播控时不报 `now_playing`。构建期源文件可以写 `profile` + `disabled`，但发往 Host 前必须展开完毕。

- 当前诚实样例（无本机播放）：[examples/device-esp32-panel-480.json](examples/device-esp32-panel-480.json)  
- 播控验收后样例：[examples/device-esp32-panel-480-with-media.json](examples/device-esp32-panel-480-with-media.json)

### 3.3 会话中 UI（协议外）

若产品有「语音对话抽屉/气泡」，结果卡叠在其上方或压矮对话区：属于该端 overlay 策略，Surface 仍用 `card` / `notification` / `now_playing`。**不**因此新增 surface，也**不**在协议中引用任何私有源码路径。

### 3.4 语音工具（MCP 等）

若经助理工具调用 `invoke`：端须双投递——UI/播控消费 Envelope，模型侧只给短摘要。见 [03-content.md](03-content.md) §6。

---

## 4. `android-phone`

| 点 | 说明 |
|----|------|
| `media.play_local` | 通常用系统播放器；申报前确认音频焦点与前后台策略 |
| `fullscreen` | 富播放器、图库合理；资源紧的面板类不要强制抄 |
| `action.open_url` / `handoff` | 手机可做；面板类默认不要把这些放进 `requires` |
| 多端同账号 | `scope=account` 时同一 `app_id` 可装；各端按**自己的** capabilities 启用 |

性能一般足够普通码率音频；失败用错误 Envelope 即可，不必改协议。

---

## 5. `voice-only`

| 点 | 说明 |
|----|------|
| 无屏 | 不报 `content.music_list` 则严格匹配下装不了列表型音乐应用 |
| 口述应用 | 应另做 `requires: ["content.text", "action.invoke"]` + 强 `spoken` |
| 媒体 | 仅当固件能真正播流/播曲才报 `media.*`；TTS 读标题 ≠ 播放 |

---

## 6. `linux-kiosk`

按实际显示器与播放栈裁剪；可接近 `android-phone`。无触摸时勿报 `input.touch`，列表须键/旋钮/语音可导航（见 [00-capabilities.md](00-capabilities.md) §3.3）。

---

## 7. 缺口与演进（协议已知不足）

下列**有意未定**或仅作弱约定，避免协议膨胀；需要时再升版本：

| 缺口 | 现状 | 建议 |
|------|------|------|
| 列表分页 / 下一页 | 无统一字段 | 再用 `action.invoke` + params；或将来 `content.page` |
| 播放进度上报云 | 无 | 端本地 UI 即可；云统计另开 API |
| 多音轨/歌词/音质档 | 无 | 未进白名单前勿塞自定义可执行字段；可放可忽略扩展 |
| `session_card` surface | 未增设 | 用平台布局策略；多端都要过滤差异时再加 |
| 云端按码率预检 | 无强制 | 有设备档案时可拒过高码率 URL，属云产品质量 |

修订能力词典或 limits 形状时：先 `optional` + 降级，再考虑升 `requires`；版本规则见 [README.md](README.md)。
