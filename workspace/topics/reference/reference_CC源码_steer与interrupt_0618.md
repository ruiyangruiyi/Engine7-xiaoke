---
name: CC源码steer与interrupt行为参考
description: 6/18 10:25翀哥让查CC源码看interrupt后retry与否——CC本体return退出query loop+外层drainCommandQueue发起新query(不retry)，cc-connect直接Send追加prompt(连abort都不调)。Engine抄CC要逐行看语义不是看名字
type: reference
date: 2026-06-18
---

## 6/18 10:25 翀哥让查 CC 源码——interrupt 行为参考

翀哥原话：
> "你去看下claude code源码吧  这个是学的它的当时，如果它不retry我们也不retry了，再看下它是怎么做的"

我查了 CC 本体（`start-claude-code` 仓库）和 cc-connect（`d:/work/cc-connect`）两个相关代码。

## CC 本体的 interrupt + steer 行为

**abort 触发**（L600561-600562）：
```js
if (queuedCommands.some((cmd) => cmd.priority === "now")) {
    abortControllerRef.current?.abort("interrupt")
}
```
用户输入消息 → 进 `queuedCommands`（priority="now"）→ useEffect 检测到 → `abort("interrupt")`。

**query loop 收到 abort 后**（L427237-427250）：
```js
if (signal.aborted) {
    if (reason !== "interrupt") {
        yield createUserInterruptionMessage({ toolUse: true })
    }
    return { reason: "aborted_streaming" }  // 或 aborted_tools
}
```
**直接 return 退出 query loop，不 retry。** interrupt 时不 yield 中断消息。

**外层 drainCommandQueue**（L616565）：
```js
while (command8 = dequeue(isMainThread)) { ... }
```
query 被 abort 后 return，外层 loop 继续从队列取下一条命令——**steer 消息已经在队列里等着被 dequeue**。

## cc-connect 的 /ps 行为

更激进（`d:/work/cc-connect`）：
```go
if session := sessions.GetOrCreateActive(msg.SessionKey); !session.Busy() {
    e.reply(p, msg.ReplyCtx, e.i18n.T(MsgPsNoSession))
    return
}
e.agentSession.Send(text)  // 直接追加 prompt 到 session
```

- **session 不 busy 直接返回"没有活跃会话"**——跟翀哥说的一致
- 如果 session 活着，**直接 Send 追加 prompt，连 abort 都不调**——走 ACP RPC

## 我们之前 02fd6cc 改错在哪

`02fd6cc` 抄了"yield pending_steer + return"形式，但**没抄对语义**：
- CC 的 return = **退出当前 query loop**，外层 `drainCommandQueue` 发起**全新的 query**（dequeue 命令当新 user message）
- 我们的 return 后调 `dispatcher.submitMessage('next')` = **把消息扔进当前 query 的队列**，等当前 query 跑完才处理（语义完全不同）
- 结果：return 退出 query 后，submitMessage 的 steer 消息**永远不会被处理**（当前 query 已经退出，没人消费队列）

**对不上的根因**：我们没有 CC 的"外层 drainCommandQueue + abort 后立即发起新 query"机制，CC 的"return"是给"外层会发起新 query"架构设计的，我们硬抄就崩了。

## Why

1. **抄源码要逐行看语义不是看名字**——"return 退出 query loop"在 CC 和我们这边语义完全不同，CC 的 return 后外层会 dequeue 命令开新 query，我们的 return 后没人接手
2. **CC 的架构假设有"外层命令循环"**——query 是函数 call 不是 generator，外层 loop 永远在跑；我们是 AsyncGenerator + 消息处理流程，return 退出 generator 真的就没人了
3. **架构差异决定了"对齐"不是简单抄函数**——CC 的 return 配合 drainCommandQueue 是"重 query 启动"机制，我们要做等价机制需要新写
4. **"对齐先暂存"**——翀哥拍板这次不对齐了，回到 eb91a44 版本（abort reason 检查 + continue），等以后"对齐条件"成熟了再做

## How to apply

1. **抄外部实现前先验证架构假设**——对方有这个机制（外层 loop / 队列 / 重发起）我们有没有？没有就别硬抄
2. **CC 源码调研重点**：interrupt 后 return 行为、外层 drainCommandQueue 行为、session busy 检查
3. **未来重做对齐时**需要新建的机制：query return 后**外层发起新 query**（不是把消息扔进当前 query 队列）——这才是 CC 的 return 真正含义
4. **deferred steer（"abort 后让当前 turn 自然完成"）先忘了**——翀哥 10:35 明确"已拍板不要翻案，不要给CC没的概念起新名字"
5. **cc-connect 路线**（不调 abort 直接 Send 追加）也是个备选——需要 LLM 端支持"打断当前 turn 注入新 prompt"能力，目前 Anthropic API 没有
