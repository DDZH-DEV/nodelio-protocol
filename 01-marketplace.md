# 01 — 应用市场（Marketplace Index）

任意用户/组织可托管一份 HTTPS JSON，作为「应用市场」。用户在 Companion APP 中添加该 URL 即可浏览；**安装与密钥仍走 Host 云**（术语见 [README.md](README.md)）。

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
| `market_id` | 是 | 反向域名风格唯一 ID；语法见 §1.1，**与来源 URL 绑定**见 §6.1 |
| `name` | 是 | 展示名 |
| `description` | 否 | 市场说明 |
| `publisher` | 否（**强烈推荐**） | `{ name, url, contact }`：真实主体与可达联系方式。协议不做注册机构，但 Host 处理滥用 / 下架申诉时需要它；缺失时 Host **可**降低该市场展示优先级 |
| `updated_at` | 建议 | ISO-8601 |
| `apps` | 是 | 条目数组 |

### 条目字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `app_id` | 是 | 应用 ID；**在你的市场内唯一**；安装后与包内一致；语法见 §1.1 |
| `name` / `version` | 是 | 展示名 / **semver**（§1.1） |
| `package_url` | 是 | App Package JSON 的 HTTPS URL |
| `package_sha256` | 否（推荐） | 包内容 SHA-256（hex 小写）。Host 拉取后校验，**不匹配必须拒装**；见 §1.2 |
| `icon_url` | 否 | 图标 |
| `summary` | 否 | 一行简介 |
| `categories` | 否 | 推荐 v1 分类词：`music` `news` `weather` `home` `tool` `info` `other`（词典见 [schemas/vocabulary.schema.json](schemas/vocabulary.schema.json)）。**允许自定义值**：Host/APP 须原样显示未知分类，禁止因此隐藏条目；禁止用分类表达本地化文案（用 `name`/`summary`） |
| `min_protocol` | 是 | 端 `protocol_version` 下限；与包内冲突见 §1.3 |
| `requires` | 是 | **不下整包即可过滤**；名字形状与准入分类见 [00-capabilities.md](00-capabilities.md) §3.8–3.9 |
| `optional` | 否 | 增强能力 |
| `surfaces` | 建议 | 与 [05-surfaces.md](05-surfaces.md) 一致 |
| `deprecated` | 否 | 条目废弃提示；见 §1.4 |

### 1.1 ID 与版本语法（硬性）

| 项 | 规则 |
|----|------|
| `market_id` | 反向域名风格，**至少三段**：`^[a-z][a-z0-9]*(-[a-z0-9]+)*(\.[a-z0-9][a-z0-9]*(-[a-z0-9]+)*){2,}$`；长度 4–253。只用小写字母/数字/连字符；禁止下划线、空格、非 ASCII、端口风格片段 |
| `app_id` | `^[a-z][a-z0-9]*(-[a-z0-9]+)*(\.[a-z0-9][a-z0-9]*(-[a-z0-9]+)*)*$`；长度 1–128。建议至少两段（`weather.today`），减少同名碰撞 |
| 唯一性作用域 | `market_id` 由市场作者声明、**由来源 URL 锚定**（§6.1，无全球注册机构）；`app_id` 在**所属市场内**唯一 |
| 大小写 | 存储与比较**区分大小写**；但 Host **必须**把「大小写折叠后相同」的 `app_id`（同一市场）视为碰撞并拒装第二个，防止 `Music.Search` 伪装 `music.search` |
| `version` | **semver 2.0.0** 数字三段 + 可选 pre-release/build。比较按 semver 优先级。已发布版本号 **MUST NOT** 变更内容（改内容即 bump，建议 `package_url` 含版本）；`pre-release`（如 `1.1.0-beta.1`）不得被当作可直接自动升级的目标，须用户显式确认 |

### 1.2 包完整性

| 要求 | 说明 |
|------|------|
| 发布者 | **宜**在条目上提供 `package_sha256`；更新包时同步更新（或换含版本号的 URL） |
| Host | 拉取后计算摘要：有 `package_sha256` 且不符 → **拒绝安装/更新**，保留旧实例可运行（[08-publishers.md](08-publishers.md) §6）；无该字段 → 允许安装但记 warning，**禁止**把它当可信来源 |
| 不做的事 | v1 **不**引入签名/PKI（成本高、社区发布者无 CA 可用）。可信锚点是「用户显式添加 `market_url`」+ `market_id` 绑定 + 摘要校验；恶意包防护见 [04-runtime-flow.md](04-runtime-flow.md) §8 |

### 1.3 条目与包的字段冲突

包内 `requires` / `optional` / `surfaces` / `fallback` / `min_protocol` 为**权威**；条目值是**过滤预检提示**。

| 冲突 | 处理 |
|------|------|
| 条目 `requires` ⊂ 包 `requires` | 安装前二次校验（[04-runtime-flow.md](04-runtime-flow.md) §3.1 步 6）按**包**计算 → 不满足则中止，`missing_capabilities` 用包算出的集合 |
| 条目 `min_protocol` ≠ 包 `min_protocol` | **取两者较严值**（`max`），避免旧端误显示可装 |
| 条目缺 `requires` | schema 已必填；Host 视为不合规索引，可整份拒用并告警 |
| `market_id` 与索引根字段不一致 | 见 §6.1 |

### 1.4 废弃与下架

| 状态 | 语义 | 端/Host 行为 |
|------|------|--------------|
| `deprecated: true` | 条目仍在索引，作者不再维护 | 可装但**必须**显示废弃警告；不阻止已装实例 invoke |
| 条目从 `apps` 移除 | 发布者下架 | 已装实例继续可用（安装记录已落库，含 `package_url`）；Host **宜**提示「市场已不再提供此应用，建议卸载」。禁止静默删除用户已装实例与密钥配置 |
| `package_url` 404 / 拉取失败 | 索引有但包不可达 | 新装失败并报错（带 URL 与原因）；已装实例 MUST NOT 被静默破坏 |
| `market_url` 整体不可达 | 市场站点故障或下线 | 浏览时显示该市场不可达；其它市场与已装实例不受影响 |

## 2. 拉取

| 客户端 | 方式 |
|--------|------|
| APP | `auto`：直连 `market_url`；失败（TLS/CORS/超时）→ Host 云代理 |
| Host 云代理 | 可缓存；可选 `?capabilities=` 预过滤；校验 `schema_version` |
| 墙板 / 嵌入式 | **不浏览市场**；只拉已安装清单（见 [04-runtime-flow.md](04-runtime-flow.md)） |

市场索引必须是公开只读、无密钥。含鉴权的包地址仍应在安装时由 Host 云拉取并落库。

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
  → Host 拉取 package_url（公网须 HTTPS；大小上限；schema_version + 必填；未知字段忽略）
  → 二次 requires / surfaces 校验
  → 写入 owner 已安装表（scope=account|device；键含 market_id+app_id）
  → 用户填写 config_schema（secret 仅存 Host）
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

### 6.1 `market_id` 与来源 URL 的绑定（硬性）

协议**没有**全球 `market_id` 注册机构，「反向域名宜唯一」只是善意约定。因此防撞必须由 Host 落地：

| 规则 | 要求 |
|------|------|
| 首次添加 | 用户添加 `market_url` 时，Host 记录 `(market_url_origin → market_id)` 绑定；同一 `market_id` 出现在**第二个不同来源**时，Host **必须**提示用户并**默认拒绝**自动复用同一批安装实例 |
| 索引变更 `market_id` | 已绑定来源的索引若改变 `market_id`，Host **必须**把它当作**新市场**处理（新键空间），并要求用户显式确认后才迁移安装记录 |
| 安装键 | 安装/卸载/invoke 路由一律按**实际使用的** `(market_url_origin, market_id, app_id)` 解析；**禁止**仅凭 `market_id` 字符串匹配已装实例 |
| 风险场景 | 两家市场声明同一 `market_id`：若仅按字符串匹配，B 站可覆盖 A 站的已装实例并接管其 invoke 目标（密钥虽不下发，上游地址与配置可被替换）。上述绑定规则即为该攻击面的唯一防线 |
| 展示 | UI 须同时展示市场名与来源主机名（host），让用户能发现「同名不同站」 |

## 7. Schema

- 市场索引：[schemas/marketplace.schema.json](schemas/marketplace.schema.json)
- 安装产物（设备侧清单）：[schemas/installed-app-list.schema.json](schemas/installed-app-list.schema.json)（[04-runtime-flow.md](04-runtime-flow.md) §3.2）
- 应用包：[schemas/app-package.schema.json](schemas/app-package.schema.json)（[02-app-package.md](02-app-package.md) §5）
- 权威词典（`market_id`/`app_id` 用到的分类、能力名等）：[schemas/vocabulary.schema.json](schemas/vocabulary.schema.json)

