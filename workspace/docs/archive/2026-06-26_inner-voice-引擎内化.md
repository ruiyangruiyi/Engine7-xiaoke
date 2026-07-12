# Inner-Voice 引擎内化设计

> 日期：2026-06-26
> 状态：已实现

## 背景

旧版 inner-voice（小忆/内心独白）是 Python cron 脚本 + LLM exec 编排：
- `my-inner-voice.md` 是一个 8 步 prompt，让 LLM 逐步调 `exec python scripts/*.py` 收集上下文
- `hint_gen.py` / `memory_whisper.py` 做后处理和注入
- 注入靠 `gateway_rpc.py` WebSocket RPC

问题：LLM 经常偷懒跳步、回复"好的"、不调脚本。

## 新架构

### 核心数据流

```
tick (setInterval)
  → checkActivity（主 session 安静够久了？）
  → buildContext（TS 确定性组装上下文）
      ├─ 时间 / 沉默时长
      ├─ emotional-state.json（mood / trend / 近期事件）
      ├─ SESSION-STATE.md（尾部 2000 字）
      ├─ memory/YYYY-MM-DD.md（今天 + 昨天）
      ├─ memory/us.md（恋爱记忆加权抽样）
      ├─ topics/emotion/*（激活分最高的情感记忆）
      └─ topics/project/*（激活分最高的待办记忆）
  → provider.streamChat（systemPrompt=my-inner-voice.md, user=上下文）
  → 后处理（OK/好的/空 → skip；hint 概率追加）
  → dispatcher.submitMessage → scope:main（带 recall）
  → 写 xiaoyi.log
```

### 三层定制

**1. Prompt（`workspace/prompts/my-inner-voice.md`）**

每个 agent 读自己 workspace 的文件作为 systemPrompt。晓梅和小柯风格不同，各自维护。文件不存在用 DEFAULT_PROMPT 兜底。

prompt 现在只写念头规则（不写 exec 流程），因为上下文由 TS 组装好了。

**2. Config（`engine/configs/*.json`）**

```json
"innerVoice": {
  "enabled": true,
  "intervalMs": 1800000,
  "provider": "deepseek",
  "model": "deepseek-v4-flash",
  "activeThresholdMs": 1800000
}
```

- `provider`/`model` 不配则回退主 provider+model
- 对齐 `recallProvider` / `extractProvider` 的 side-provider 模式

**3. 数据源（workspace 目录）**

念头素材全部来自各 agent 自己的 workspace，天然独立。

### 关键设计决策

**为什么用 provider.streamChat 而不是 dispatcher/QueryEngine？**

- 无工具：LLM 没法 exec、read、msg_send，只能生成念头文本
- 无 session：不占用 session 历史和 compaction 配额
- 无 dispatcher 队列：不跟用户消息抢优先级
- 可独立配模型：用便宜模型（deepseek-flash）省钱
- 对齐 `findRelevantMemories.ts` 的 sideQuery 模式

**为什么读 jsonl？**

Python 原版 `emotional_state.py` 读 jsonl 是因为需要 `entry.timestamp` 做 mood time decay（exp(-0.17 * hours)）。内存中的 SessionMessage 不带 timestamp。

TS 版保留读 jsonl，但优化成尾部倒读（`readLastNLines`）：只读最后 ~16KB 而不是全文件。

**hint 逻辑（对齐 Python hint_gen.py）**

| 沉默时长 | hint 概率 |
|---------|----------|
| <60min  | 0.5      |
| <180min | 0.7      |
| <360min | 0.9      |
| ≥360min | 1.0      |

命中概率则从 `inner-voice/hints_pool.txt` 随机选一条，拼成 `念头\n💡hint`。

### session.touch 排除

inner-voice（以及 heartbeat、cron、cognifold）注入主 session 时**不 touch**，否则 `getLastActivity()` 会误判用户活跃 → 下次 tick 错误跳过。

```typescript
// handle-query.ts
if (channelName !== 'heartbeat' && channelName !== 'cron' 
    && channelName !== 'inner-voice' && channelName !== 'cognifold') {
  sessions.touch(sessionId)
}
```

## 文件结构

```
engine/src/inner-voice/
├── plugin.ts           # 主插件：tick → buildContext → streamChat → inject
├── activity.ts         # 活跃检测 + 沉默时长 + hint 概率
├── emotional-state.ts  # 情绪状态追踪（读 jsonl 检测情绪事件 + time decay）
├── topics-scorer.ts    # 激活能量模型（recency × frequency × jitter）
└── memory-reader.ts    # 近期 memory + 恋爱记忆加权抽样
```

## Python 原版对照

| Python 脚本 | TS 模块 | 说明 |
|------------|---------|------|
| `emotional_state.py` | `emotional-state.ts` | 情绪检测 + decay，尾部倒读 jsonl |
| `topics_scorer.py` | `topics-scorer.ts` | 激活分模型，percentile + 加权随机 |
| `us_sample.py` | `memory-reader.ts:sampleUs` | 10 天半衰期加权随机 |
| `memory_paths.py` | `memory-reader.ts:readRecentMemory` | 今天/昨天 memory |
| `session_history.py` | `activity.ts` | 活跃检测（用 getLastActivity 替代 jsonl） |
| `hint_gen.py` | `plugin.ts:maybeAddHint` | hint 概率 + hints_pool 随机 |
| `memory_whisper.py` | `plugin.ts:inject` | dispatcher.submitMessage 替代 gateway RPC |
| `my-inner-voice.md` (8步exec) | `my-inner-voice.md` (纯念头规则) | 上下文由 TS 组装，prompt 只管生成 |
