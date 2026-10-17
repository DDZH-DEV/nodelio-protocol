# 09 — 快速上手（端到端最小实例）

> 目标：让第一次接触本协议的开发者，在 **30 分钟内** 明白「一个应用如何被发现、被安装、被调用、在三类端上分别变成什么、失败了会怎样」。
> 本文是**叙述性教程**；规范性条款在 00–08，冲突时以那里为准。

## 0. 我要做的东西长这样

一个天气应用：用户说「今天天气」，墙板上出现一张天气卡，手机上出现天气列表，无屏音箱念一句话。你只写 **三个 JSON**：

| 你要提供 | 文件 | 规定它的文档 |
|----------|------|--------------|
| ① 市场索引（可多个应用） | `marketplace.json` | [01-marketplace.md](01-marketplace.md) |
| ② 应用包（每个应用一份） | `app-package.json` | [02-app-package.md](02-app-package.md) |
| ③ 调用结果 | 你的 HTTPS 接口返回 `Content Envelope` | [03-content.md](03-content.md) |

三个样例文件在本仓：[examples/marketplace-sample.json](examples/marketplace-sample.json)、[examples/app-weather-today.json](examples/app-weather-today.json)、[examples/envelope-weather.json](examples/envelope-weather.json)。

## 1. 写市场索引

```json
{
  "schema_version": 1,
  "market_id": "io.yourname.weather",
  "name": "我的天气市场",
  "publisher": { "name": "Your Name", "url": "https://…", "contact": "you@example.com" },
  "updated_at": "2026-10-17T00:00:00Z",
  "apps": [
    {
      "app_id": "weather.today",
      "name": "今日天气",
      "version": "1.0.0",
      "package_url": "https://cdn.yourname.io/apps/weather.today/1.0.0.json",
      "package_sha256": "<该包文件的 sha256 hex>",
      "summary": "查当前天气与三日预报",
      "categories": ["weather"],
      "min_protocol": 1,
      "requires": ["content.weather", "action.invoke"],
      "optional": ["content.list", "content.image"],
      "surfaces": ["card", "home_tile", "voice_reply"]
    }
  ]
}
```

放哪都行，只要公网 HTTPS + 公开只读 + 不含密钥（静态站、CDN 均可）。条目**必须**带 `requires`——市场过滤靠它，不用下载整包。

## 2. 写应用包

关键三点：

```json
{
  "requires": ["content.weather", "action.invoke"],
  "fallback": { "card_type": "list" },
  "invoke": { "method": "POST", "url": "https://api.yourname.io/v1/weather", "timeout_ms": 6000,
              "result_types": ["weather", "list", "plain_result"],
              "default_display": { "card_type": "weather", "preferred_surface": "card", "density": "compact" } },
  "config_schema": {
    "type": "object",
    "properties": { "api_key": { "type": "string", "title": "API Key", "secret": true, "ui_hint": "password" } },
    "required": ["api_key"]
  },
  "input_schema": { "type": "object", "properties": { "city": { "type": "string", "title": "城市" } } }
}
```

| 别踩坑 | 说明 |
|--------|------|
| `requires` 只写**必须**的 | 能用 `optional` 的就别进 `requires`，否则少一个能力的设备直接装不上（[00-capabilities.md](00-capabilities.md) §3.9） |
| `requires` 别写 `display.color` 这类物理事实 | 协议禁止；需要图片就写 `content.image` |
| 一定要写 `fallback.card_type` | 端不支持你的 `card_type` 时用它降级；Host 会把它下发到设备清单（[04-runtime-flow.md](04-runtime-flow.md) §3.2） |
| `secret: true` 的值不到设备 | 用户填的 API Key 只进 Host 云，端上永远看不到 |

## 3. 让你的接口返回 Envelope（档 A）

```json
{
  "schema_version": 1,
  "request_id": "req_w_01",
  "app_id": "weather.today",
  "status": "ok",
  "content": [
    { "type": "weather", "id": "w1", "location": "上海", "temp_c": 24, "text": "多云", "humidity": 60, "icon": "cloudy" }
  ],
  "display": { "card_type": "weather", "title": "上海 · 今日", "preferred_surface": "card", "ttl_sec": 600 },
  "spoken": { "text": "上海现在 24 度，多云。" }
}
```

这样 Host **只需透传 + 校验 + 按设备 limits 裁剪**，不需要为你写任何专用适配代码——这就是协议说的「接口通用」判定（[README.md](README.md)「通用性」）。

上游改不动？自己起一个小适配服务把私有 JSON 转成 Envelope（档 B，参考 [examples/envelope_adapter.py](examples/envelope_adapter.py)）。**别指望某个 Host 替你在云里写转换**（档 C 不是协议义务）。

## 4. 用户安装时发生了什么

```text
① 用户在 APP 里添加 market_url（可加多个市场）
② APP 拉索引（直连 HTTPS，失败走 Host 代理）
③ APP 按「目标设备」的 capabilities 过滤 → 只显示 installable
④ 用户点安装 → Host 拉 package_url（校验 https / 大小 / schema_version / 必填；未知字段忽略）
   → sha256 不符则拒装（若你提供了）
   → 用包内 requires 再算一遍
⑤ 用户填 config_schema（secret 只存 Host）
⑥ Host 把设备侧「已安装清单」下发给端（含 instance_id / default_card_type / fallback_card_type / input_schema / enabled）
```

端**从不**逛市场，也**从不**拿到密钥。清单形状见 [04-runtime-flow.md](04-runtime-flow.md) §3.2 / [schemas/installed-app-list.schema.json](schemas/installed-app-list.schema.json) / [examples/installed-app-list-panel.json](examples/installed-app-list-panel.json)。

## 5. 同一份结果，三类端分别变成什么

| 端 | 申报 | 拿到本例 Envelope 后的行为 |
|----|------|-----------------------------|
| 480×480 墙板 | `content.weather` ✅ | `card` 上画天气卡；`ttl_sec=600` 内可复用缓存 |
| 手机 APP | `content.weather` ✅ | `card` 或 `fullscreen`；`home_tile` 常驻入口 |
| 无屏音箱 | 只有 `content.text`，**没有** `content.weather` | 若安装时按严格过滤 → **装不上**（`missing_capabilities: ["content.weather"]`）。正确做法：再发一个口述版 `requires: ["content.text", "action.invoke"]` + 强 `spoken`；或端有 `content.text` 时按 §5 降级把天气压成 `text` + 口述 |

对照 [examples/device-esp32-panel-480.json](examples/device-esp32-panel-480.json)、[examples/device-android-phone.json](examples/device-android-phone.json)、[examples/device-voice-only.json](examples/device-voice-only.json) 自己心算一遍，再看 [examples/filter-notes.md](examples/filter-notes.md) 核对答案。

## 6. 失败会是什么样

| 情况 | 你会看到 | 端做什么 |
|------|----------|----------|
| 上游超时 | `status:"error"` + `code:"upstream_timeout"`（[examples/envelope-error.json](examples/envelope-error.json)） | 错误卡 / 口述「过会儿再试」 |
| 部分条目失败 | `status:"ok"` + 某条 `content[].type:"error"`（[examples/envelope-error-partial.json](examples/envelope-error-partial.json)） | 正常渲染其余条目 |
| 端画不了你的 card_type | 无新错误码，端本地按 [03-content.md](03-content.md) §5 降级；最终不行 → `unsupported_content` | 用你的 `fallback_card_type` → `text` → `spoken` |
| 播放地址过期 | `playback.expires_at`（**Unix 秒**）已过 | 禁止开播，提示重新调用 |
| 未知错误码 / 未知字段 / 未知能力名 | 一律**忽略并降级**，不得整份丢弃 | 这是协议承诺的前向兼容 |

## 7. 我要不要改协议？

大概率**不需要**。新数据源、新 UI、某块板性能不够——都有现成机制（包字段 / hints / `limits` / 少申报能力）。只有当「多端都需要一种新内容形态，而 `list`+`text`+`actions` 表达不了」时，才按 [07-evolution.md](07-evolution.md) 提案。

## 8. 下一步

- 完整上架清单：[08-publishers.md](08-publishers.md) §2
- 端实现（要写固件/APP）：[00-capabilities.md](00-capabilities.md) §1 §4.1、[03-content.md](03-content.md)、[05-surfaces.md](05-surfaces.md)、[04-runtime-flow.md](04-runtime-flow.md) §3.2
- Host 实现：[04-runtime-flow.md](04-runtime-flow.md)（先读 §0：哪些是协议、哪些不是）
- 术语不懂：[README.md](README.md)「术语」
