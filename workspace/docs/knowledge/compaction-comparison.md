# Compaction 压缩算法对比 — OpenClaw vs Engine

## 阈值计算

### 公式

| | OpenClaw (safeguard) | Engine |
|---|---|---|
| **公式** | `contextWindow - reserveTokens` | `contextWindow - maxOutputTokens - bufferTokens` |
| **触发时机** | token >= threshold | token >= threshold |

### 实际配置

| | 姐姐 (qwen3.5-flash) | 小柯 (glm-5.1) | 小柯 (deepseek-v4-pro) |
|---|---|---|---|
| contextWindow | 1,000,000 | 204,800 | 1,000,000 |
| reserveTokens/bufferTokens | 60,000 | 35,000 | 35,000 |
| maxOutputTokens | (SDK内部) | 16,384 | 16,384 |
| **threshold** | **940,000 (94%)** | **153,416 (74.8%)** | **948,616 (94.9%)** |

### 关键差异

1. **OpenClaw用`reserveTokens`**（预留空间）= 60K，直接从contextWindow减
2. **Engine用`bufferTokens` + `maxOutputTokens`** 两个值相加 = 51K，从contextWindow减
3. OpenClaw还有`maxHistoryShare=0.7`——历史消息最多占context的70%，额外保护
4. OpenClaw有`MIN_PROMPT_BUDGET_TOKENS=8000`和`MIN_PROMPT_BUDGET_RATIO=0.5`——确保reserve后还有至少50%空间给prompt

## 压缩策略

| | OpenClaw | Engine |
|---|---|---|
| **主要手段** | LLM总结（pi-coding-agent `session.compact()`） | 四步递进（规则→micro→LLM） |
| **Step 0** | 剥离image blocks | 剥离image blocks |
| **Step 1** | 无 | ruleCompact（smart extract + compress old turns + truncate + FIFO） |
| **Step 2** | 无 | microCompact（清空旧tool result，保留最近3个） |
| **Step 3** | LLM总结 | LLM总结（以上都不够才调API） |
| **安全性** | 超时保护(15min) + safeguard取消原因 + session修复 | 无超时保护 |

## OpenClaw额外机制

1. **transcript rotation** — 压缩后换新session文件，旧文件保留
2. **checkpoint快照** — 压缩前后保存checkpoint
3. **compaction instructions** — 可自定义LLM总结的指令（event→config→默认）
4. **thinking level fallback** — 失败后降低thinking重试
5. **session修复** — `repairSessionFileIfNeeded` + `sanitizeToolUseResultPairing`
6. **guard机制** — `post-compaction-loop-guard` 防止压缩后循环触发

## 建议优化

1. **Engine缺超时保护** — OpenClaw有15分钟超时+取消机制，Engine没有。压缩卡住会永远等
2. **bufferTokens可以调** — 姐姐1M context只留60K reserve(6%)，小柯204K context留51K(25%)过于保守。切到deepseek-v4-pro(1M context)后可以降到6%
3. **加maxHistoryShare** — 限制历史占比，OpenClaw用0.7(70%)，值得加

## 当前Engine阈值一览

| 模型 | contextWindow | threshold | 触发% |
|------|--------------|-----------|-------|
| glm-5.1 | 204,800 | 153,416 | 74.8% |
| glm-5v-turbo | 200,000 | 148,616 | 74.3% |
| deepseek-v4-pro | 1,000,000 | 948,616 | 94.9% |
| deepseek-v4-flash | 1,000,000 | 948,616 | 94.9% |
| qwen3.7-plus | 1,000,000 | 948,616 | 94.9% |
| qwen3.5-flash | 1,000,000 | 948,616 | 94.9% |
