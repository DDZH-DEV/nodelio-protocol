# 02 — 应用包（App Package）

单个应用的权威描述：元数据、能力需求、配置项、invoke、默认展示与 MCP 暴露。安装后由 NodeLio SERVER 持有；设备只拿脱敏清单。

## 1. 形状

```json
{
  "schema_version": 1,
  "app_id": "music.search",
  "version": "1.0.0",
  "name": "音乐搜索",
  "description": "搜索歌曲并返回可播放列表",
  "icon_url": "https://cdn.example.com/icons/music.png",
  "categories": ["music"],
  "min_protocol": 1,
  "requires": ["content.music_list", "action.invoke"],
  "optional": ["media.play_local", "media.play_via_xiaozhi", "content.image"],
  "surfaces": ["card", "now_playing", "voice_reply", "fullscreen"],
  "fallback": { "card_type": "list" },
  "config_schema": {
    "type": "object",
    "properties": {
      "api_key": {
        "type": "string",
        "title": "API Key",
        "secret": true
      },
      "region": {
        "type": "string",
        "title": "地区",
        "enum": ["cn", "global"],
        "default": "cn"
      }
    },
    "required": ["api_key"]
  },
  "invoke": {
    "method": "POST",
    "url": "https://api.example.com/v1/music/search",
    "timeout_ms": 6000,
    "result_types": ["music_list", "list", "text"],
    "default_display": {
      "card_type": "music_list",
      "preferred_surface": "card",
      "density": "compact",
      "max_items": 8
    }
  },
  "expose_mcp": true,
  "mcp": {
    "name": "music.search",
    "description": "Search music tracks by keyword"
  },
  "ui": {
    "entry_title": "音乐",
    "entry_icon": "music_note"
  }
}
```

实际第三方 URL 与 Auth 头由 Host 云在安装/配置时绑定（可来自包扩展字段或控制台），**不下发到设备**。包内可不含明文 `invoke.url`；若含，仅 Host 可读。

**上游响应**：宜直接为 [03-content.md](03-content.md) Content Envelope（发布者档 A）。若私有 API 无法改，发布者应自建适配服务输出 Envelope（档 B），而非依赖某一 Host 为你写云内专用转换（档 C 非协议义务）。见 [08-publishers.md](08-publishers.md) §3。

## 2. 字段说明

| 字段 | 说明 |
|------|------|
| `app_id` / `version` | `app_id` 在**所属市场内**唯一；跨市场防撞见安装键 `(market_id, app_id)`（[01-marketplace.md](01-marketplace.md) §6）；升级策略由 Host 定 |
| `requires` / `optional` | 见 [00-capabilities.md](00-capabilities.md) |
| `surfaces` | 见 [05-surfaces.md](05-surfaces.md) |
| `fallback.card_type` | 端不支持默认 card 时的首选降级 |
| `config_schema` | JSON Schema 子集；`secret: true` 的属性仅存 SERVER，list 接口不返回值 |
| `invoke.url` | 可选。Host 代 invoke 的上游地址（公网 https；相对路径仅 Host 同源）。亦可安装后由控制台绑定，**不下发设备** |
| `invoke.result_types` | 本应用可能返回的 `display.card_type` |
| `invoke.default_display` | 默认 presentation hints |
| `expose_mcp` | 是否进入统一技能 list（如 `self.skill.list`）语义 |
| `mcp` | 给模型的短名与描述（调用仍走统一 `skill.invoke` + 实例 id，禁止每应用一个工具名） |
| `ui.entry_title` / `entry_icon` | 入口短名与图标名提示；Host **可**用作启动台短名。**不是**布局或像素坐标 |

### 与现有 `PanelSkill` 对应（迁移提示）

| PanelSkill | App Package |
|------------|-------------|
| `skillId` | `app_id` |
| `uiHint` | `invoke.default_display.card_type` |
| `inputSchema` | `config_schema` + invoke 参数 schema（可另增 `input_schema`） |
| `exposeMcp` | `expose_mcp` |
| `authToken` | 仅 SERVER，不进包的设备可见面 |

可选扩展 `input_schema`：描述单次 invoke 的参数（如 `keyword`），供 MCP / 面板搜索框使用。

## 3. Action 路由（包级默认）

包可声明常用动作模板；Content 内 `actions[]` 可覆盖。

| `run` | 含义 |
|-------|------|
| `invoke` | `POST …/panel/skills/{app_id}/invoke`（或等价） |
| `local` | 端本地能力，如 `media.pause` |
| `handoff` | 交给 companion（如手机 `open_url`） |

端无对应 capability → **隐藏该按钮**，不整卡失败。

## 4. 安装作用域

安装记录（SERVER，非包文件字段，但协议约定）：

| scope | 含义 |
|-------|------|
| `account` | 账号级；各设备按自身能力启用/禁用 |
| `device` | 仅指定 `device_id` |

## 5. Schema

[schemas/app-package.schema.json](schemas/app-package.schema.json)
