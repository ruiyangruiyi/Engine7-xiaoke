---
name: /ps对齐CC暂存——GLM限流时段先用query_abort_continue方案
description: 6/18 10:55翀哥拍板/ps对齐CC方案(yield pending_steer + return + dispatcher重发起)先暂存。GLM-5.2在10-11点限流时段撞空响应概率高，对齐方案return路径会让新query重新跑记忆召回+API，体感"卡死"。先退回10:00版本(query.ts L346加abort reason检查+continue)。
type: feedback
date: 2026-06-18
---

## 6/18 10:55 翀哥拍板——/ps对齐CC暂存

翀哥原话：
> "b60096666d02cb4ff7390f00dbbcda31932f1d51 回到这个 但是这次对齐先暂存最好  以后再搞对其"

**决策**：
- 立即 revert `02fd6cc` + `b0c6548`（/ps对齐CC的改动）
- 当前回到 `eb91a44` 版本（10:00那个：query.ts L346 加 abort reason='interrupt' 检查 + reset ac + continue）
- "对齐先暂存"——以后再重新启用对齐方案
- revert commit：`0da7e3d Revert "refactor: /ps对齐CC——abort后yield pending_steer + return退出query loop"`

## 为什么暂存对齐方案

`02fd6cc` + `b0c6548` 的逻辑是对的（跟CC的aborted_streaming对齐），但实测发现：
- **return路径下，新query要走handle-query的完整流程**：memory recall → LLM sideQuery → query() → API调用
- **GLM-5.2在10-11点限流时段API返回空响应概率高**（参见reference_API限流时间规律_0617.md）
- 即使return+dispatcher重发起是干净的语义，新query撞到空响应=体感"卡死"

用户10:49说"不太对啊 感觉卡死了"——查询本身没卡死（13-50秒内完成），但**新query叠加memory recall + 空响应retry = 体感很长**。

## 当前的/query.ts abort处理（eb91a44 版本）

```ts
// query.ts L346 之前
if (ac.signal.aborted && ac.signal.reason === 'interrupt') {
    // 是 steer 中断，不是真的空响应 → 重置 ac + continue 处理 pendingSteers
    this.resetAbortController()
    continue
}
```

**行为**：
- steer abort → stream break → query.ts 拿到空响应 → 检测 reason='interrupt' → reset ac + continue
- 继续当前 query loop，pendingSteers 在下个 turn 被消费
- **不退也不重启 query**——只在原 query 内继续

**问题**：retry LLM 调用还是撞空响应（GLM 限流）。但不会让 query 退出，最坏是慢。

## 对齐CC暂存的内容（等以后再做）

`02fd6cc` + `b0c6548` 三层改动：
1. query.ts：abort reason=interrupt 时 yield pending_steer chunk + return
2. handle-query.ts：新增 onPendingSteer 回调类型
3. engine-startup.ts：onPendingSteer 实现调 dispatcher.submitMessage('next')

**以后启用条件**：
- 换 GLM-5.2 限流问题解决了（换 anthropic 或其他 provider）
- 限流时段不做了（演示/重要操作避开10-11点）
- 或者**新query的memory recall能优化加速**（现在每次新query都跑一遍 recall，体验差）

## Why

1. **理论对≠体验好**——CC的return+drainCommandQueue方案在LLM快速响应下体验好，但在限流时段新query撞空响应会让体感时间×2
2. **对齐要"对齐有用的部分"**——abort语义、interruption message处理、drainCommandQueue流程这些可以借鉴，但**不要把"新query重启"这种重操作照搬到我们场景**，除非新query本身足够快
3. **用户视角的"卡死"是真信号**——即使技术上看query在跑，体验上的卡顿就是失败。修bug要修到体验对，不只是代码对
4. **暂存比"硬上"更专业**——拍板了的事发现新约束条件就暂存，不要为了"对齐"硬撑。等约束条件变了再启用

## How to apply

1. **理论方案实施前要预估"边界条件下的体验"**——CC的方案在CC的硬件/模型条件下好，我们场景下不一定
2. **遇到"卡死"反馈立即承认方案不work**——不要硬解释"其实是好的只是看起来慢"
3. **暂存+记教训 = 完整的"试错-暂停"循环**——不要把暂存的方案扔掉，留下以后重新评估的入口
4. **对齐的对象要明确场景适配**——CC的return+drainCommandQueue是给交互式CLI设计的（用户在场，能容忍重启），我们的bot场景不一定能容忍
5. **GLM-5.2在10-11点限流时段**（参见reference_API限流时间规律_0617.md）——任何需要新启动query的方案都要避开这个时段
