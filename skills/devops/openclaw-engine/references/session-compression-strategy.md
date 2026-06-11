# Session 压缩策略设计

> 基于 `cli_deepseek/core.py` 的 `_trim_context_if_needed()` 方法提炼
> 整理人：小柯 | 日期：2026-05-27
> 源码位置: `D:\work\gemini\cli_deepseek\core.py` 第200-430行

## 核心理念

**渐进式压缩**：从最高质量压缩开始，逐步降级，不到万不得已不删数据。

对比：
- **Hermes**: `/compact` 一压缩就全压缩成摘要，原文丢失不可逆
- **OpenClaw**: 无压缩，JSONL全量加载
- **本方案**: 4级递进，每级只在上一级不够时触发，最大程度保留信息

## Step 1: Smart JSON Extraction（最高质量）

- **触发**: 任何 tool result > 8000 字符
- **效果**: 50K → ~3K（压缩率 94%）
- **做法**: JSON解析→提取ESSENTIAL_FIELDS→最多保留30条记录
- **Fallback**: 不是JSON或提取后仍>30%原大小 → 截断到5000字符
- **适用所有轮次**（包括最近的），因为压缩质量高信息损失小

配置: TOOL_SIZE_LIMIT=8000, TRUNCATE_TO=5000, MAX_LIST_ITEMS=30

## Step 2: 旧轮次合并压缩（Turn Compression）

- **触发**: Step 1 之后仍超限
- **轮次**: user → assistant(tool_calls) → tool(s) → assistant(final)
- **效果**: 10+条 → 2条
- **关键**: tool结果折叠进assistant消息（`[Technical Summary]`+`[Conclusion]`），不留孤立tool消息
- **保护最近 KEEP_RECENT_TURNS=3 轮不压缩**

没有最终回答时tool结果转assistant角色，去掉tool_call_id。

## Step 3: 截断兜底（Truncation）

- **触发**: Step 1&2 之后仍超限
- **做法**: 暴力截断大 tool result 到 5000 字符 + `[TRUNCATED]`
- 低质量但保证不崩

## Step 4: FIFO 原子删除

- **触发**: Step 1-3 之后仍超限，最后手段
- **原子性**: 删就删一整轮（到下一个user消息），不留碎片
- **保护**: system消息永远不删，至少保留 MIN_HISTORY=5 条

## Engine 实现建议

1. 独立模块 `src/session/compressor.ts`
2. 对外暴露: `compressHistory(messages, maxTokens): Message[]`
3. 替换 main.ts restoreSession() 的粗暴 `slice(0.7)`
4. ESSENTIAL_FIELDS 做成可配置（不同业务保留不同字段）
5. 每级压缩都 log 效果（多少条→多少条）

## 两个触发点（2026-05-27讨论确认）

### 触发点1: restoreSession() — 恢复时压缩
加载JSONL后如果超限，用4级策略压缩（替代现在的逐条shift）。
当前状态：已实现简单截断（100条/50K tokens/保底10条），待替换为4级策略。

### 触发点2: handleQuery() 前检查 — 运行时session hygiene
每次query前检查history是否超限，超限就压缩。
**当前engine完全没有这层**——聊久了context会一直膨胀直到LLM报错。
这是Phase 5 compact的核心，优先级高于Session Restore的压缩（因为restore有简单截断兜底，运行时没有）。

实现顺序：先做触发点2（运行时压缩，影响更大），再做触发点1替换粗暴截断。

## 关键设计亮点

1. **原子性**: 删除时按完整轮次删，不留碎片
2. **渐进式**: 从最高质量压缩开始逐步降级
3. **tool结果合并**: 多条tool result合并折叠进assistant消息
4. **保护system**: system消息永远不删
5. **保最近N轮**: 最近对话完整保留
