# CC 源码 maxTokens 逻辑分析

> 2026-07-17 凌晨挖的，翀哥要求。

## 核心结论

1. **CC 不是硬编码单一值** — 按模型分桶查表（opus-4-6=64K, sonnet=32K, claude-3=4K）
2. **CC 不做动态减法** — max_output_tokens 不根据 inputTokens 计算，是模型独立属性
3. **CC 靠 recovery 机制处理溢出** — 触顶后 escalate + 多轮续写，不是预防性调小

## CC 的 maxTokens 优先级链（高→低）

| 优先级 | 来源 | 示例 |
|---|---|---|
| 1 | API retry context 临时覆盖 | |
| 2 | options.maxOutputTokensOverride（escalate 到 64K） | |
| 3 | 环境变量 CLAUDE_CODE_MAX_OUTPUT_TOKENS | |
| 4 | GrowthBook 实验开关（8K cap） | |
| 5 | **模型默认值**（查表） | opus-4-6=64K, sonnet=32K |
| 6 | 兜底常量 32K | |

## 关键函数

### getModelMaxOutputTokens(model) — context.ts:149-210
按模型 canonical name 分桶：
- opus-4-6: default=64K, upperLimit=128K
- sonnet-4-6: default=32K, upperLimit=128K
- claude-3-opus: default=4K, upperLimit=4K
- 默认兜底: default=32K, upperLimit=64K

### getMaxOutputTokensForModel(model) — claude.ts:3399
```ts
const maxOutputTokens = getModelMaxOutputTokens(model)
const defaultTokens = isMaxTokensCapEnabled()
  ? Math.min(maxOutputTokens.default, CAPPED_DEFAULT_MAX_TOKENS)  // 8K
  : maxOutputTokens.default
```

### contextWindow 的唯一"减法" — autoCompact.ts:33
```ts
function getEffectiveContextWindowSize(model) {
  return contextWindow - reservedTokensForSummary  // 用于 autoCompact 阈值
}
```
这不是算 max_output_tokens，是算"输入可用窗口"。

## Engine 的缺陷

engine `createModelDeps` 里 `maxTokens: 4096` 硬编码，不管 config 里写什么。

**正确做法**：从 modelDef.maxTokens 读取（config 里已经有这个字段）。

```ts
// 现在（错误）
maxTokens: 4096,

// 应该改成（对齐 CC 思路）
maxTokens: modelDef.maxTokens || 4096,
```

## 关键常量

```ts
MAX_OUTPUT_TOKENS_DEFAULT = 32_000        // context.ts:15
MAX_OUTPUT_TOKENS_UPPER_LIMIT = 64_000    // context.ts:16
CAPPED_DEFAULT_MAX_TOKENS = 8_000         // slot 优化
ESCALATED_MAX_TOKENS = 64_000             // 触顶升级值
COMPACT_MAX_OUTPUT_TOKENS = 20_000        // compact 摘要
```
