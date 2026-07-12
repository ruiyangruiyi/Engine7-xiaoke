# Claude Code vs Engine API 请求对比

**日期：** 2026-06-28
**目的：** 对比 Claude Code 和我们 Engine 的 API 请求结构，确认 cache 策略差异

---

## HTTP Headers

### Claude Code

```
Content-Type: application/json
x-api-key: <key>                          # 或 Authorization: Bearer <token>（OAuth）
anthropic-version: 2025-04-15
User-Agent: claude-cli/<version> (ant, cli)
anthropic-beta: <oauth-beta-header>       # OAuth 用户才有
```

### Engine

```
Content-Type: application/json
x-api-key: <key>
anthropic-version: 2025-04-15
```

**差异：** Engine 更精简，没有 User-Agent、没有 OAuth、没有 beta header。

---

## System Prompt 结构

### Claude Code（5 层）

```json
{
  "system": [
    {
      "type": "text",
      "text": "x-anthropic-billing-header: cc_version=...; cc_entrypoint=...; cch=00000;",
      "cacheScope": null          // ← 不缓存！fingerprint 每次变
    },
    {
      "type": "text",
      "text": "<CLI system prompt prefix>",
      "cacheScope": "org"        // 或 "global"
    },
    {
      "type": "text",
      "text": "<静态 system prompt（SOUL/AGENTS/MEMORY 等）>",
      "cacheScope": "global"     // 全局缓存
    },
    {
      "type": "text",
      "text": "<__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__>",
      // 边界标记，分割静态/动态
    },
    {
      "type": "text",
      "text": "<动态 system prompt（运行时上下文）>",
      "cacheScope": null          // 不缓存
    }
  ]
}
```

**CC 的 cache 策略：**
- `global`: 全局缓存（跨用户共享）
- `org`: 组织级缓存
- `null`: 不缓存
- 有 `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` 边界标记分割静态/动态

**⚠️ 问题：** attribution header 的 fingerprint 根据消息内容算，每次可能变化，放在 system prompt 最前面但不参与缓存 → 可能打断后面内容的缓存链。

### Engine（2 层）

```json
{
  "system": [
    {
      "type": "text",
      "text": "<stable content（SOUL/AGENTS/MEMORY/SESSION-STATE 等）>",
      "cache_control": { "type": "ephemeral" }   // ← 可缓存
    },
    {
      "type": "text",
      "text": "<dynamic content（运行时上下文）>"
      // 无 cache_control → 不缓存
    }
  ]
}
```

**Engine 的 cache 策略：**
- stable → `cache_control: { type: 'ephemeral' }`（Anthropic 标准 prompt cache）
- dynamic → 无 cache_control（每 turn 重建）
- 没有 billing header、没有 fingerprint、没有边界标记

---

## 关键差异总结

| 方面 | Claude Code | Engine |
|------|-------------|--------|
| billing header | ✅ 有（`x-anthropic-billing-header`） | ❌ 无 |
| fingerprint | ✅ 有（根据消息内容算） | ❌ 无 |
| 缓存分层 | 5 层（billing + prefix + static + boundary + dynamic） | 2 层（stable + dynamic） |
| 缓存机制 | `cacheScope: global/org/null` | `cache_control: { type: 'ephemeral' }` |
| 边界标记 | `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` | 无（用 stable/dynamic 参数分割） |
| attribution header | ✅ 默认开（`CLAUDE_CODE_ATTRIBUTION_HEADER`） | ❌ 无 |
| User-Agent | ✅ 有（`claude-cli/version`） | ❌ 无 |

---

## 为什么 Engine 不需要 attribution header

1. **计费归属不同：** attribution header 是给 Anthropic 计费系统识别"这个请求来自 Claude Code"用的。我们用智谱 API（`open.bigmodel.cn`），智谱不认这个 header
2. **fingerprint 浪费 cache：** CC 的 fingerprint 根据消息内容算，每次可能不同 → system prompt 第一个 block 每次变 → 打断后面缓存链 → cache miss → 浪费 token
3. **Engine 的 stable/dynamic 分层更干净：** 直接用 Anthropic 标准 `cache_control: { type: 'ephemeral' }`，不搞额外层级

## 已执行的修复

**Claude Code 已关闭 attribution header：**
```json
// ~/.claude/settings.json → env
"CLAUDE_CODE_ATTRIBUTION_HEADER": "0"
```

**Engine 无需修改** — 本来就没有这个逻辑。

---

## 源码位置

| 文件 | 说明 |
|------|------|
| `start-claude-code/src/constants/system.ts:73` | CC `getAttributionHeader()` — 生成 billing header |
| `start-claude-code/src/utils/api.ts:332-429` | CC system prompt 分层 + cacheScope |
| `engine/src/models/anthropic-provider.ts:149-195` | Engine stable/dynamic 分层 + cache_control |
| `engine/src/models/provider.ts:49` | Engine `systemStable` 类型定义 |
