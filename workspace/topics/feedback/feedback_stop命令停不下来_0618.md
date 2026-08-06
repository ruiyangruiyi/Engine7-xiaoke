---
name: /stop命令停不下来+command提前到LLM前导致abort空窗
description: 6/18 08:32翀哥报告/stop停不掉→根因是abortController只在query()开始时建，但handle-query前面有memory recall阶段是空窗；根因是6/18凌晨把文本命令提前到LLM前，session路由就绪时engine还没拿到abort能力
type: feedback
date: 2026-06-18
---

## 6/18 08:32 翀哥报告

翀哥：
> "你看下我刚才/stop好几次你为啥停不下来呢"

**08:40 翀哥一句话点中根因**：
> "这个是不是因为我们昨天把command提前了导致的 因为放到了LLM前面"

## 根因（08:39 已定位）

**abortController 只在 `engine.query()` 开始时创建**（QueryEngine L97-98），但 handle-query 在 `engine.query()` 之前还有一个 **memory recall 阶段**（日志显示花 25 秒）。这段时间 `engine.abortController = null`。

`/stop` 走 slash command → `engine.interrupt()` → 读 `this.abortController` → 是 null → 空操作。

日志铁证：
```
08:29:30 interrupt() called: hasAbortController=false alreadyAborted=undefined
08:30:07 interrupt() called: hasAbortController=false alreadyAborted=undefined
08:30:30 interrupt() called: hasAbortController=false alreadyAborted=undefined
```

## 为什么是 command 提前导致的

6/17 把 `/model` 之类文本命令从"送进LLM"改成"在ChannelManager.handleInbound统一拦截提前处理"——这意味着：

- 旧流程：消息进LLM → slash command触发 interrupt → 此时 query 已经在跑、abortController 已就绪
- 新流程：slash command 走提前拦截通道 → 调用 `engine.interrupt()` → **但 query 还没真正进 engine.query()**（卡在 memory recall）→ abortController 还是 null

**session 路由的就绪时点 ≠ abortController 就绪时点**。命令前置把这两者的时序错开了。

## 已实施的修复

加了 `preQueryAbort` 机制：
1. QueryEngine 新增 `setPreQueryAbort(controller)` 和 `clearPreQueryAbort()`
2. `interrupt()` 改成：先看 `preQueryAbort?.signal?.aborted`，再查 `this.abortController`
3. handle-query L119 之后立即调 `setPreQueryAbort(queryAbortController)`
4. handle-query 结束时清 `preQueryAbort`
5. query() 开始后内部清 `preQueryAbort`

**Why:** 6/17把文本命令拦截从LLM前移出来是为了欠费时能切模型，但没考虑interrupt的abortController就绪时机——session路由的"已注册"和engine的"正在跑"是两个独立状态。

**How to apply:**
1. 任何"提前拦截"的链路（文本命令/系统注入/外部脚本）如果调engine方法，必须先确认该方法的依赖（abortController / session state / 模型句柄等）已就绪
2. abort能力应该分成两层：preQueryAbort（注册即生效）+ queryAbortController（query开始时接管）
3. 以后改流程时序（提前/延后），画个时序图确认：每个回调触发时，依赖的所有state都ready了吗
4. 杀进程逻辑应该跟start.cmd共用同一个powershell script block，重复实现=bug重复（这条是从start.cmd自匹配bug继承的经验）
