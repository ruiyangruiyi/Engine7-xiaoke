# Compaction 防失忆机制 — 完整流程

> 落盘时间: 2026-07-31 | 翀哥要求总结，以防后面忘记

## 什么时候触发

当对话 token 数接近上下文窗口上限时，engine 自动触发 compaction（压缩）。

**重要：换 1M 上下文模型后（Qwen 3.7 Max 等），compaction 几乎不会触发。** 以前 200K 上下文时经常触发。

阈值算法（`autoCompact.ts`）：
```
threshold = (contextWindow - 20000) - buffer - overhead
buffer = 23000（默认）
overhead = system prompt + tools + memory files
```

## 三层防失忆保护

### 第 1 层：PreCompact Flush 消息（强制）

**位置**: `src/compact/autoCompact.ts:46-47`

compaction 触发前，engine 往对话里注入一条**强制指令消息**：

```
⚠️ Pre-compaction memory flush: 上下文即将被压缩。

你必须立即执行以下操作：
1. 用 write 工具覆盖更新 memory/working-buffer.md，写入当前最新状态
   （正在做什么、做到哪了、下一步具体动作）
2. 将重要信息追加到 memory/daily/YYYY-MM-DD.md

working-buffer.md 是最高优先级——它会被 PostCompact hook 自动注入到压缩后的上下文。
不写 = 压缩后失忆。
```

- 最多等 agent 2 轮（`PRE_COMPACT_FLUSH_MAX_TURNS = 2`），超了就强制压缩
- **这是强制提醒**，不是可选的

### 第 2 层：PreCompact Hook（兜底存档）

**位置**: `src/engine-startup.ts:299-358`

不管 agent 有没有写 buffer，hook 都会在压缩前自动执行：
- 读 session JSONL 最近 20 条 user/assistant 消息
- 追加写入 `memory/daily/YYYY-MM-DD.md`

**路径修复记录**（2026-07-31）：
- 原代码：`path.join(workspace, 'sessions')` ← 不存在
- 修复后：`path.join(config.stateDir, 'agents', 'main', 'sessions')` ← 正确路径
- commit: `79b33d13`
- 发现者: CC (Claude Code)，修复: 小柯

### 第 3 层：PostCompact Hook（恢复任务）

**位置**: `src/engine-startup.ts:362-395`

压缩完成后，读 `memory/working-buffer.md` 注入到新上下文：

```
[PostCompact 任务恢复] 压缩前你正在执行以下任务，请继续：
{buffer内容}
```

- 如果 buffer 超过 10 分钟没更新，打 warn 日志
- 如果 buffer 为空或不存在，什么都不注入 → 任务可能断档

## 完整时序

```
对话 token → 接近阈值
  │
  ├─ 1. 注入 flush 消息（强制提醒 agent 写 buffer）
  │     └─ 最多等 2 轮
  │
  ├─ 2. PreCompact hook 执行（兜底存最近 20 条到日记）
  │
  ├─ 3. 执行压缩（rule-based + LLM 摘要）
  │
  └─ 4. PostCompact hook 执行（读 buffer 注入到新上下文）
        └─ agent 恢复任务
```

## 关键文件

| 文件 | 作用 |
|------|------|
| `src/compact/autoCompact.ts` | 压缩触发逻辑 + flush 消息 + 阈值计算 |
| `src/compact/types.ts` | CompactConfig 类型定义 |
| `src/engine-startup.ts:299` | PreCompact hook（兜底存档） |
| `src/engine-startup.ts:362` | PostCompact hook（buffer 注入） |
| `src/hooks/executor.ts` | Hook 执行器 |
| `src/hooks/types.ts` | Hook 类型定义 |

## 手动保障（AGENTS.md 规则）

除了 engine 自动机制，AGENTS.md 里还要求：
- 聊了超过 6 轮 → 主动写 working-buffer
- 涉及决策数值 → 主动写 working-buffer
- Pre-Compaction 消息收到 → **必须执行**，不是建议

## 为什么 2026 年 6 月中旬后没触发过

1. 换了 1M 上下文模型 → 对话很难攒到压缩阈值
2. session 不会自动清空（JSONL 一直在）
3. 不是 bug，是上下文窗口变大了

## 配置参考（xiaoke.json）

```json
"compaction": {
  "enabled": true,
  "bufferTokens": 23000,
  "maxOutputTokens": 16384,
  "minReductionRatio": 0.3,
  "ruleBased": { "enabled": true, "essentialFields": [] },
  "memoryFlush": { "enabled": true, "forceFlushTranscriptBytes": "2.0mb" }
}
```
