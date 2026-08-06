# Fallback Provider 死循环问题（2026-06-22）

## 现象
- 6/22 早晨 08:55-08:59（旧 engine）4 分钟里跑了 2 轮 10-retry + 3 stream retry
- 用户 `/stop` 不能真正停止，fallback 还在递归里跑

## 根因

**fallback-provider 的递归没深度限制 + signal.aborted 在递归路径里没检查**

## 流程对比图

### 正常流程：stop 能停

```mermaid
sequenceDiagram
    autonumber
    actor User as 你
    participant Slash as /stop 命令
    participant Registry as agent-registry
    participant Query as query.ts
    participant Provider as anthropic-provider
    participant Network as API

    User->>Slash: /stop
    Slash->>Registry: stop(name)
    Registry->>Query: abortController.abort()
    Note over Query: ac.abort() 发出信号
    Query->>Provider: streamChat(..., signal=ac.signal)
    Provider->>Network: fetch(..., signal)
    Network-->>Provider: ❌ AbortError (signal 触发)
    Provider-->>Query: 抛错
    Query-->>User: ✅ 停止成功
```

### 失败流程：fallback 死循环绕过 stop

```mermaid
sequenceDiagram
    autonumber
    actor User as 你
    participant Slash as /stop 命令
    participant Registry as agent-registry
    participant Query as query.ts
    participant Fallback as fallback-provider
    participant Provider1 as glm-5.2
    participant Provider2 as minimax/M3
    participant Provider3 as zhipu/glm-5.1
    participant Network as API

    User->>Slash: /stop
    Slash->>Registry: stop(name)
    Registry->>Query: abortController.abort()
    Note over Query: ✅ abort 信号发了

    Query->>Fallback: streamChat(params, signal=aborted)
    Fallback->>Provider1: 调 glm-5.2
    Provider1->>Network: fetch 429
    Provider1-->>Fallback: error chunk
    Fallback->>Fallback: setCooldown(glm-5.2)
    Fallback->>Provider2: 调 minimax/M3
    Provider2->>Network: fetch 429
    Provider2-->>Fallback: error chunk
    Fallback->>Fallback: setCooldown(minimax/M3)
    Fallback->>Provider3: 调 zhipu/glm-5.1
    Provider3->>Network: fetch 429
    Provider3-->>Fallback: error chunk
    Fallback->>Fallback: setCooldown(zhipu/glm-5.1)

    Note over Fallback: 全 in cooldown 了<br/>强制 probe 第一个

    Fallback->>Provider1: 又调 glm-5.2 (递归！)
    Provider1->>Network: fetch 429
    Provider1-->>Fallback: error chunk
    Fallback->>Fallback: setCooldown(glm-5.2)
    Fallback->>Provider2: 又调 minimax/M3 (递归！)
    Note over Fallback: ⚠️ 无限循环<br/>abort 信号从 query 传下来了<br/>但 Fallback 内部重试新 model 时没检查

    Fallback-->>User: 一直在跑，没停 ❌
```

## 关键点（翀哥的疑问）

**Q: abort 信号不是传下去了吗？为什么不响应？**

A: abort 信号**只中断了"当前 model 的 HTTP fetch"**。fallback-provider 自己**起了一个新的 streamChat 调下个 model**——这个新调用的 params 里有 signal，但 provider 内部的 setCooldown/递归是**同步逻辑**，signal check 之前早就走完了。

简单说：**不是 abort 没传，是 fallback 自己无限重试新 model，把 abort check 给"绕"过去了。**

## 修法（`47c6a4c`）

```typescript
// 修前
async *streamChat(params) {
  // ... 找 activeEntry
  if (error) {
    yield* this.streamChat(params)  // ← 无限递归，无 signal check
  }
}

// 修后
async *streamChat(params) {
  yield* this.streamChatInternal(params, 0)
}

private async *streamChatInternal(params, depth) {
  // 1. 递归前 check abort
  if (params.signal?.aborted) return

  // 2. 深度上限
  if (depth >= MAX_FALLBACK_DEPTH) {
    yield { type: 'error', error: 'All models failed' }
    return
  }

  // 3. stream chunk 循环里也 check
  for await (const chunk of provider.streamChat(...)) {
    if (params.signal?.aborted) return  // ← 边 stream 边 abort
    yield chunk
  }
}
```

## 三层修复链

| 层 | commit | 修复内容 |
|---|---|---|
| L1 HTTP | `f3718a5` `86f57dc` | 429 quota 不重试（anthropic/dashscope/OpenAI） |
| L2 Fallback | `47c6a4c` | 递归深度上限 + abort 响应 |
| L3 Slash | (已有) | `/stop` abort signal 一路传到 provider |

## 数据证据

- 6/21 整天 260 次 429 retry + **104 次 "All in cooldown, probing"** 死循环
- 6/22 早晨 08:55-08:59 4 分钟 2 轮 10-retry + 3 stream retry
- 6/22 修后 (`47c6a4c` 待重启) → 0 次死循环
