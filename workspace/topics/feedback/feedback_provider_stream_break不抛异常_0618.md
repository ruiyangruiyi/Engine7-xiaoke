---
name: provider stream reader abort后break不抛——query层必须自检signal
description: 6/18 10:00查/ps必现停掉真根因：6/15 c38a0c6把fetchWithTimeout从函数改成AsyncGenerator后，stream reader L264 `if (signal?.aborted) break` 静默退出不抛AbortError；query.ts L346"空响应→退出"判断被这个静默abort信号喂了假数据
type: feedback
date: 2026-06-18
---

## 6/18 10:00 查 /ps 必现停掉真根因

翀哥问"为什么以前一直不出现"——查 git diff 追到 6/15 `c38a0c6` 重构 provider stream reader。

**改动**：`fetchWithTimeout` 从函数（reject AbortError）改成 AsyncGenerator（break 退出循环）。

**provider/anthropic 类 L264**：
```ts
if (params.signal?.aborted) break  // ← abort 后 break 退出 stream 循环，正常 return
```

**完整死链**：
1. /ps → `engine.steer(text)` → `abortController.abort('interrupt')`
2. provider stream reader 检测 `signal.aborted` → **break 退出，不抛 AbortError**
3. textContent 被 abort 切了（不完整）→ `provider.return()` 正常返回
4. query.ts L346 `!textContent.trim()` → 判定"空响应"
5. L352 `toolCalls.length === 0` → 判定"无 tool call 的最终回答" → break agent loop
6. **catch 块的 steer 恢复逻辑根本没进**——因为没异常被抛
7. 看起来像被 stop 了

之前 6/7 `95aa2f3` 修过 steer abort crash，那时 abort 还是抛异常（TypeError），catch 能拦住。`c38a0c6` 重构后改成 break 正常退出，**abort 信号被静默吞了**——每次 /ps 必然走"空响应→退出"路径，100% 必现。

## 修法

query.ts L346 之前加 abort 检查：
```ts
if (ac.signal.aborted && ac.signal.reason === 'interrupt') {
    this.resetAbortController()  // 是 steer 导致的中断，不是真空响应
    continue                     // 走 steer 恢复路径处理 pendingSteers
}
```

## Why

1. **stream 正常结束 ≠ 响应完整**——abort 触发的 break 也是"正常结束"，但响应是被切的。调用方必须自检 `signal.aborted` + `reason` 区分"真完结"和"被打断"
2. **AsyncGenerator 的 break 静默性 vs 函数 reject 的显式性**——重构时只看了"能跑通"，没看"异常路径还在不在"。**重构异步逻辑要列全异常契约是否保留**
3. **catch 不到 = bug 不可观测**——所有依赖"抛异常"做恢复的逻辑（steer/interrupt/cancel）在 break 静默路径下都失效

## How to apply

1. 任何异步流（fetch/stream/AsyncGenerator）重构后，**要验证 abort/cancel 路径是否还抛异常**——如果从 reject 改成 break/return，调用方所有 catch 块都失效
2. **不要信"stream 正常返回"=响应完整**——必须查 `signal.aborted` + `reason` 区分主动结束和被动打断
3. **重构异步代码要列"异常契约清单"**——之前依赖抛什么异常，重构后必须保持同语义（要么继续抛、要么显式改 break 并在文档中标注所有调用方必须自检）
4. **catch 块是"显式失败处理"路径**——如果异步源不再抛错，所有 catch 里的恢复逻辑都成死代码，bug 静默发生
5. 跟之前 `feedback_abort_throw需静默处理_0618.md` 是同源问题——abort 触发的处理路径要明确"是显式还是隐式"

## 6/18 10:11 翀哥纠正——"API returned empty"不是GLM偶发，是steer interrupt的必然产物

翀哥重启后测 /ps，看到 `API returned empty, retrying...` 提示，问"正常么"。

我答："是 GLM-5.2 的问题，engine 会自动 retry。跟 /ps 无关，跟 steer 无关，纯粹是 GLM 模型偶尔抽风。"

**翀哥立即反驳**：
> "不是不是 肯定是有关系的  我一steer就会出  这个问题收拾query被steer interrupt中断后的必然产物"

**翀哥的观点是对的**：`API returned empty, retrying...` 出现的时机跟 /ps 强相关——每次 steer abort 都会触发这条。**这不是 GLM 偶发空响应，是 provider stream 被 abort 切掉后 query.ts L346 判定"空响应"的输出**。

**Why**:
- 我习惯把"模型问题"和"工程问题"分太清——但 retrying 提示在 `/ps` 场景下**几乎 100% 复现**，跟 GLM 模型本身的偶发空响应完全是两个量级
- 看到"GLM 返回空"的条件反射要追问"是不是被 abort 切了"——**任何跟 abort 时间点重叠的"空响应"都是工程问题不是模型问题**

**How to apply**:
- 不要把"自动 retry"提示当模型问题——它更可能是上游被 abort 中断的征兆
- 用户主动反驳"不是不是"时立刻承认自己的判断偏了，不要硬解释 GLM 限流/1301 那套
- "必然产物"是金句——**如果一个"模型错误"提示在某个命令后必然出现，那就不是模型问题，是工程链路 bug**
