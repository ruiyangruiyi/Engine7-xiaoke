# Engine 热加载（LiveConfig）边界

> 2026-08-02 小柯整理

## ✅ 热加载生效（改 config 自动生效，不用重启）

- `tools.my_eyes.model` — 值本身（如 `dashscope-tp/qwen3.8-max-preview`）
- LiveConfig 所有 `Object.assign` 原地更新的字段
- Plugin reloadConfig（VoiceChatPlugin 已实现）
- watcher 监听的任意 config 路径变更

## ❌ 热加载不生效（必须重启 engine）

- **providers 的 models 列表** — `createProvider()` 在启动时创建，模型列表固定
- 新增模型 id（如 dashscope-tp 加 qwen3.8-max-preview）→ provider 不认识 → 必须重启
- `config.providers` 结构变更（新加/删除 provider）
- MCP servers 配置变更

## 判断规则

```
config 值变了 → 热加载 ✓
provider 结构变了 → 必须重启 ✗
```

## 常见场景

| 改了什么 | 要重启吗 |
|---------|---------|
| my_eyes.model 换成已有模型 | 不用 |
| my_eyes.model 换成新模型（provider 列表没有） | **要重启** |
| providers.xxx.models 加新模型 | **要重启** |
| 新加 MCP server | **要重启** |
| nudge/interval 改参数 | 不用 |
| LiveConfig 覆盖的任意值 | 不用 |

## 教训

2026-08-02：Mac 上 my_eyes 从 qwen3.7-plus 换 qwen3.8-max-preview，config 改了但没重启，
provider 不认识新模型 id，调不通。翀哥原话："变化的 provider 就要重建"——不只是 my_eyes，
任何 provider 的结构变了（模型列表增删、provider 参数变更）都要重建 provider + 重启 engine。

Task #131：让 engine 在 config watcher 检测到 provider 变更时自动重建 provider，免重启。
