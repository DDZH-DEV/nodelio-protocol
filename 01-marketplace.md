# 01 — 应用市场（Marketplace Index）

任意用户/组织可托管一份 HTTPS JSON，作为「应用市场」。NodeLio 用户在 APP 中添加该 URL 即可浏览；**安装与密钥仍走 NodeLio SERVER**。

## 1. 索引文档形状

```json
{
  "schema_version": 1,
  "market_id": "com.example.nodelio-market",
  "name": "示例应用市场",
  "description": "社区技能与资讯",
  "updated_at": "2026-10-15T00:00:00Z",
  "apps": [
    {
      "app_id": "music.search",
      "name": "音乐搜索",
      "version": "1.0.0",
      "package_url": "https://cdn.example.com/apps/music.search/1.0.0.json",
      "icon_url": "https://cdn.example.com/icons/music.png",
      "summary": "搜索并播放歌曲",
      "categories": ["music"],
      "min_protocol": 1,
      "requires": ["content.music_list", "action.invoke"],
      "optional": ["media.play_local", "content.image"],
      "surfaces": ["card", "now_playing", "voice_reply"]
    }
  ]
}
```

### 根字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `schema_version` | 是 | 当前 1 |
| `market_id` | 是 | 反向域名风格唯一 ID |
| `name` | 是 | 展示名 |
| `description` | 否 | 市场说明 |
| `updated_at` | 建议 | ISO-8601 |
| `apps` | 是 | 条目数组 |

### 条目字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `app_id` | 是 | 应用 ID；安装后与包内一致 |
| `name` / `version` | 是 | 展示与版本 |
| `package_url` | 是 | App Package JSON 的 HTTPS URL |
| `icon_url` | 否 | 图标 |
| `summary` | 否 | 一行简介 |
| `categories` | 否 | 如 `music` `news` `weather` `tool` |
| `min_protocol` | 是 | 端 `protocol_version` 下限 |
| `requires` | 是 | **不下整包即可过滤** |
| `optional` | 否 | 增强能力 |
| `surfaces` | 建议 | 与 [05-surfaces.md](05-surfaces.md) 一致 |

包内 `requires` 为权威；若与条目冲突，**以包为准**，安装前二次校验失败则中止。

## 2. 拉取

| 客户端 | 方式 |
|--------|------|
| APP | `auto`：直连 `market_url`；失败（TLS/CORS/超时）→ `POST/GET` SERVER 代理 |
| SERVER 代理 | 可缓存；可选 `?capabilities=` 预过滤；校验 `schema_version` |
| 墙板 / 嵌入式 | **不浏览市场**；只拉已安装清单（见 [04-runtime-flow.md](04-runtime-flow.md)） |

市场索引必须是公开只读、无密钥。含鉴权的包地址仍应在安装时由 SERVER 拉取并落库。

## 3. 过滤与展示

对**目标设备** `DeviceCapabilities`（APP 当前选中的墙板，或本机）：

1. 计算 `installable`（见 [00-capabilities.md](00-capabilities.md)）。
2. 默认列表只显示 `installable=true`。
3. 可选「显示不兼容」：灰显 + `missing_capabilities`。
4. 禁止把不可装项显示为「可安装」。

同一账号下切换目标设备时，列表应重新过滤。

## 4. 安装（概要）

```text
用户选中可装 app
  → SERVER 拉取 package_url（校验 HTTPS / 大小 / schema）
  → 二次 requires / surfaces 校验
  → 写入 owner 已安装表（scope=account|device）
  → 用户填写 config_schema（secret 仅存 SERVER）
  → 设备下次 list 可见
```

细节与安全见 [04-runtime-flow.md](04-runtime-flow.md)。

## 5. 发布者义务

- 提供稳定 `package_url`（建议 URL 含版本号）。
- 条目 `requires` 与包一致。
- 不在索引中放 token。
- 变更 `updated_at`；破坏性变更升 `app` version / `min_protocol`。
- 完整上架步骤见 [08-publishers.md](08-publishers.md)。

## 6. 多市场并存

- 用户 / Companion 可保存**多个** `market_url`；浏览时可合并列表，每条须保留来源 `market_id`（及展示用市场名）。
- 同一账号下，来自不同市场的相同 `app_id` **允许同时安装**。
- Host 安装记录主键：**(market_id, app_id)**（另可存 `version`、`package_url`、scope、`device_id`）。
- UI 宜展示「来自：{市场 name}」，避免用户无法区分同名应用。

## 7. Schema

[schemas/marketplace.schema.json](schemas/marketplace.schema.json)
