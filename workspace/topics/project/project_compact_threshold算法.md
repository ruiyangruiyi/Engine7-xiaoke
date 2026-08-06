---
name: compact threshold算法
description: Engine auto-compact触发阈值的完整计算方法（含overhead校准）
type: project
---

# Compact Threshold 算法

## 公式

```
threshold = (contextWindow - maxOutputTokens) - bufferTokens - systemOverheadTokens
```

## 各参数来源

| 参数 | 来源 | 示例值（xiaoke/claude-sonnet-4） |
|------|------|--------|
| contextWindow | 模型配置 `xiaoke.json` models[].contextWindow | 200,000 |
| maxOutputTokens | compact配置 `compaction.maxOutputTokens` | 16,384 |
| bufferTokens | compact配置 `compaction.bufferTokens` | **23,000** |
| systemOverheadTokens | 运行时计算（system prompt + tools + memory files） | ~31,000 |

## systemOverheadTokens 计算

启动时第一轮 query() 调用前计算一次，复用 `/api/context` 同一套函数：

```
overhead = systemPromptTokens + toolDefinitionTokens + memoryFileTokens
```

- **systemPromptTokens**: `roughTokenCountEstimation(systemStable)` — char/4 估算
- **toolDefinitionTokens**: `estimateToolDefinitionTokens(toolDefs)` — 按 name+description+parameters 分别算，1.1x pad
- **memoryFileTokens**: `scanMemoryFiles(workspace)` — 扫描 SOUL.md + AGENTS.md + memory指令，取 stable 部分

不走HTTP，不走API，直接函数调用。

## 实际计算示例（xiaoke profile, claude-sonnet-4）

```
contextWindow     = 200,000
maxOutputTokens   =  16,384
effectiveWindow   = 183,616

bufferTokens      =  23,000

systemPromptTokens ≈ 11,000   (58K chars / 4)
toolDefinitionTokens ≈ 14,300  (name+desc+schema, 1.1x pad)
memoryFileTokens   ≈  6,000   (SOUL.md + AGENTS.md + memory指令)

overhead = 11,000 + 14,300 + 6,000 = 31,300

### 6/13实测值（main session, xiaoke profile）

```
system  = 10,334
tools   = 14,285
memory  =  3,160
------------------------
overhead = 27,779
```

**vs 翀哥给的估算表（6/13早上）：**
- system: 估算11K / 实测10.3K ✅ 接近
- tools: 估算14.3K / 实测14.3K ✅ 准确
- memory: 估算6K / 实测3.2K ❌ 偏低（dynamic部分如recall注入的topic文件未计入——但dynamic memory随消息变化，算在messages的attachmentTokens中，不在overhead里是正确的）

翀哥说"有就行，这个也都是估算"——误差几千token有23K buffer兜着，够用。

threshold = 183,616 - 23,000 - 31,300 = 129,316
```

当 `estimateMessageTokens(currentMessages) >= threshold` 时触发压缩。

## bufferTokens 的由来（为什么是 23K 不是 43K）

原来配置是 **43,616**，是对齐 OpenClaw 倒推出来的。OpenClaw 的默认 buffer（13K）暗含了 system prompt 开销（~20K），所以配置成 43,616 来"包住"overhead。

但 Engine 的 system prompt / tools / memory 跟 OpenClaw 不同。overhead 被拆出独立计算后，bufferTokens 回归到其本意——**纯安全余量**，用于应对 token 估算法误差和输出波动。

6/13 翀哥分析后说：**"那这样就加回20K应该 否则太低了 把43K改成23K先"**

- 43K = 13K(CC默认buffer) + 30K(暗含overhead)
- 23K = 13K(CC默认buffer) + 10K(额外安全余量) ← overhead 已独立计算，不再需要暗含

**Why:** overhead 独立计算后，原来 buffer 里暗含的 30K 要拆出来。23K 是在拆出后的纯安全余量（13K CC默认 + 10K 翀哥追加）。

**How to apply:** 改模型/contextWindow/加tools/改system prompt后，overhead会自动重新计算（systemOverheadTokens=null时触发）。如果觉得触发太早或太晚，调 `bufferTokens` 即可。

## 日志策略

compact 日志统一走 engine log（`console.log`），不单独写文件。Engine 的日志系统已 monkey-patch `console.log`，所有输出自动按天分文件写到 `/Users/chongzhang/xiaoke//logs/engine-YYYY-MM-DD.log`。compact 日志用 `[compact]` 前缀（如 `[ruleCompact]`、`[autoCompact]`、`[microcompact]`），grep 即可筛选。

**Why:** 调问题时需要看完整上下文——compact 触发在 query loop 里，前后是 query 引擎的日志，分开看要来回切文件，浪费时间。且 `appendFileSync` 同步写文件在高频场景下有性能开销。

**How to apply:** grep engine log 用 `[ruleCompact]`, `[autoCompact]`, `[microcompact]`, `[compress]`。compact 日志含耗时 ms、路径标记（如 `(no LLM)`）、overhead 值。日志文件约 3.6MB/天，不会无限制增长。

## 历史演变

- **v1（对齐 OpenClaw）**: `threshold = effectiveWindow - buffer(43K)` — overhead 暗含在 43K buffer 里。43K = 13K(CC默认buffer) + 30K(暗含overhead)。但 OpenClaw 的 system prompt 跟 Engine 不同，暗含值不准。
- **v2（API usage 校准）**: `threshold = effectiveWindow - buffer(43K)` + 第一次 API 返回后用 `prompt_tokens - messageEstimate` 校准 overhead。问题是 API 启动慢，第一轮不可用。
- **v3（当前，函数调用）**: `threshold = effectiveWindow - buffer(23K) - overhead` — 调用 context-analyzer（`analyzeContextUsage`/`estimateToolDefinitionTokens`/`scanMemoryFiles`）直接计算 overhead，不走 HTTP 不走 API。buffer 从 43K 降回 23K（拆出 overhead 后回归纯安全余量）。

## 归档说明

这份文档最早写在 `topics/` 下（记忆提取系统自动读取），但翀哥说算法/方案/架构决策应该写到 `docs/` 下。后续新增的算法/方案文档直接写 `docs/`，不再放 `topics/`。

## 相关文件

- 算法入口: `src/compact/autoCompact.ts` → `getAutoCompactThreshold()`
- overhead计算: `src/core/query.ts` → query() 开头
- token估算: `src/compact/tokenEstimate.ts`
- tools估算: `src/utils/context-analyzer.ts` → `estimateToolDefinitionTokens()`
- memory扫描: `src/utils/context-analyzer.ts` → `scanMemoryFiles()`
- 配置: `configs/xiaoke.json` → `compaction` 节
