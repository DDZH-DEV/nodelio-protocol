# 02 — 应用包（App Package）

单个应用的权威描述：元数据、能力需求、配置项、invoke、默认展示与 MCP 暴露。安装后由 Host 云持有；设备只拿脱敏清单（形状见 [04-runtime-flow.md](04-runtime-flow.md) §3.2）。

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
    "result_types": ["music_list", "list", "plain_result"],
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
| `app_id` / `version` | `app_id` 在**所属市场内**唯一（语法见 [01-marketplace.md](01-marketplace.md) §1.1）；跨市场防撞见安装键 `(market_id, app_id)` 与其 URL 绑定（[01-marketplace.md](01-marketplace.md) §6、§6.1）；`version` 为 **semver**，已发布版本不得改内容 |
| `publisher` | 可选：`{ name, url, contact }`，与索引级同义；包内更精确时以包内为准 |
| `requires` / `optional` | 能力名形状与准入分类见 [00-capabilities.md](00-capabilities.md) §3.8–§3.9；词典见 [schemas/vocabulary.schema.json](schemas/vocabulary.schema.json) |
| `surfaces` | 见 [05-surfaces.md](05-surfaces.md)；未知 surface 由端忽略 |
| `fallback.card_type` | 端不支持默认 card 时的首选降级。**安装时 Host 必须把它写进设备侧清单**（`fallback_card_type`，[04-runtime-flow.md](04-runtime-flow.md) §3.2），否则端拿不到、降级第 1 步无法执行 |
| `config_schema` | JSON Schema **子集**（§2.1）；`secret: true` 的属性仅存 Host，任何面向端的响应不回传值 |
| `input_schema` | 单次 invoke 参数的子集 schema；供端搜索框、MCP 工具参数与设备侧清单下发（[04-runtime-flow.md](04-runtime-flow.md) §3.2） |
| `invoke.url` | 可选。Host 代 invoke 的上游地址：**公网必须 https**；相对路径仅与 Host 同源；私网 http 属 Host 联调模式（[04-runtime-flow.md](04-runtime-flow.md) §8.1）。亦可安装后由控制台绑定，**不下发设备** |
| `invoke.method` | `POST`（推荐，参数放 body）\| `GET`（参数由 Host 按 `input_schema` 编码为 query）。Host **必须**按此调用，不自作主张 |
| `invoke.timeout_ms` | 500–30000；缺省建议 6000 |
| `invoke.result_types` | 本应用可能返回的 `display.card_type`；Host **可**据此校验信封是否越界（越界 → 拒或降级，属产品质量，须可预期） |
| `invoke.default_display` | 默认 presentation hints；安装时映射进设备侧清单的 `default_card_type` / `preferred_surface` / `density` / `max_items` |
| `expose_mcp` | 是否进入统一技能 list（如 `self.skill.list`）语义 |
| `mcp` | 给模型的短名与描述（调用仍走统一 `skill.invoke` + **实例 id**，禁止每应用一个工具名）。`mcp.name` 只是展示/提示用途，**不得**要求 Host 用它注册独立 MCP 工具 |
| `ui.entry_title` / `entry_icon` | 入口短名（建议 ≤12 字）与图标**名**提示；Host **可**用作启动台短名。**不是**布局、不是像素坐标、不是文件路径。端不认识的图标名**必须**回落到自有默认图标 |

### 2.1 `config_schema` / `input_schema` 允许的 JSON Schema 子集（硬性）

机器可读：[schemas/json-schema-subset.schema.json](schemas/json-schema-subset.schema.json)。子集限定为以下关键字，目的是让资源紧张端也能生成表单：

| 允许 | 说明 |
|------|------|
| `type`（顶层必为 `object`，属性用基础类型）、`properties`、`required`、`items` | 结构 |
| `title`、`description`、`default`、`enum`、`const` | 取值与展示 |
| `minLength`/`maxLength`/`pattern`、`minimum`/`maximum`/`exclusive*`、`minItems`/`maxItems`/`uniqueItems` | 约束 |
| `format` ∈ `email` `uri` `date` `date-time` `ipv4` `ipv6` | 可选，端可不实现校验 |
| **`secret`**（NodeLio 扩展，**非** JSON Schema 标准） | `true` → 值仅存 Host、加密保存，**禁止**出现在任何面向端的响应、日志、或 invoke 响应回显 |
| **`ui_hint`**（NodeLio 扩展） | `text` `textarea` `select` `number` `toggle` `password`；端不认识时按 `type` + `secret` 自择控件（`secret=true` 必须密码型） |

| 禁止 / 未定义 | 原因与行为 |
|---------------|-------------|
| `allOf` / `anyOf` / `oneOf` / `not` / `if-then-else` / `$ref` / 条件依赖 | 端无法可靠渲染跨字段依赖；Host **必须**拒装含这些关键字的配置表单（属 D 级才可扩展） |
| 嵌套超过 **2 层**的 `object`（`input_schema` 同理） | 面板渲染成本；超层记 warning 并按扁平提示渲染 |
| 未知关键字 | Host **忽略**并可 warning，**禁止**因此拒装（与「未知字段忽略」一致） |
| 深层 `additionalProperties` 语义 | 不使用；`config_schema` 只认列出的属性 |

### 2.2 「迁移提示」不属于协议

早期版本此处有一张「与现有 `PanelSkill` 字段对应」表（`skillId` / `uiHint` / `authToken` …）。那是**某一厂商 Host 实现的内部字段名**，第三方 clone 本协议仓库时无从对照，按 [07-evolution.md](07-evolution.md) §2 第 2 条不得留在协议正文里，故已移除。

> 若某 Host 需要把自己已有的技能表映射到 App Package（做兼容导入），请写在该 Host **自己的**产品文档；映射建议：ID → `app_id`、UI 提示 → `invoke.default_display.card_type`、单次参数 → `input_schema`、开关 → `expose_mcp`、令牌 → 仅存 Host 的配置项。

## 3. Action 路由（包级默认）

包可声明常用动作模板；Content 内 `actions[]` 可覆盖（条目级形状见 [03-content.md](03-content.md) §4）。

| `run` | 含义 |
|-------|------|
| `invoke` | 交给 Host 代调：**按安装实例路由**（`instance_id`，或裸 `app_id` 的歧义规则见 [03-content.md](03-content.md) §3.2）。具体 HTTP 路径属 Host 产品（[04-runtime-flow.md](04-runtime-flow.md) §0） |
| `local` | 端本地动作，取值见 [03-content.md](03-content.md) §4.1 白名单（`media.play` / `media.pause` / …） |
| `handoff` | 交给 companion；`kind` v1 仅 `open_url`（[03-content.md](03-content.md) §4） |

端无对应 capability → **隐藏该按钮**，不整卡失败。

## 4. 安装作用域

安装记录（Host 云持有；非包文件字段，但协议约定其语义）：

| scope | 含义 |
|-------|------|
| `account` | 账号级；各设备按**自身**能力启用/禁用；主键含 `(market_url_origin, market_id, app_id)` |
| `device` | 仅指定 `device_id` 可见 |

## 5. Schema

- 结构：[schemas/app-package.schema.json](schemas/app-package.schema.json)
- 配置/参数子集：[schemas/json-schema-subset.schema.json](schemas/json-schema-subset.schema.json)（§2.1）
- 词典：[schemas/vocabulary.schema.json](schemas/vocabulary.schema.json)
- 设备侧清单（安装后由 Host 下发什么）：[schemas/installed-app-list.schema.json](schemas/installed-app-list.schema.json)（[04-runtime-flow.md](04-runtime-flow.md) §3.2）

