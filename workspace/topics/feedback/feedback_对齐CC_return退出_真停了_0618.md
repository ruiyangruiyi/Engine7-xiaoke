---
name: 对齐CC return退出后/ps真停了
description: 6/18 10:45翀哥报告10:38实施的三层改动（return退出query loop + pending_steer chunk + dispatcher重发起）后/ps"这次真停了"
type: feedback
date: 2026-06-18
---
6/18 10:42翀哥merge确认OK + 10:44 [P.S.]自动进新query看似验证通过 → **10:45翀哥"改坏了 这次真停了"**。

复盘前一次"修复有效"很可能是因为10:11那次是空retry触发的，不是真的return路径。10:44[P.S.]的"功能验证通过"我高兴太早没等第二个test case。

## 10:46 翀哥具体描述"停了"的现象

翀哥原话：
> "ps之后停了  打了个这个 ⚠️ API returned empty, retrying..."

**关键证据**：跟 10:11 翀哥说"API returned empty, retrying... 每次会返回这个东西 正常么 不过没停"是**同一条日志**——
- 10:11：retry 后**没停**（但其实 query 可能卡在 retry 循环里不动）
- 10:46：retry 后**真停了**（query 真的卡死）

这印证"10:11没停"是 retry 期间的假象，return 路径下 submitMessage('next') 排队的 steer 消息**永远不会被处理**（当前 query 在 retry 循环里一直空转不出 result）。

**根因猜想（待验证）**：
1. query.ts return后pending_steer chunk可能没正确yield
2. handle-query onPendingSteer回调可能没触发
3. engine-startup的dispatcher.submitMessage('next')可能跟当前query还活着的状态冲突——submitMessage是把消息追加到队列等当前query跑完再发，而不是abort当前query开新的
4. CC的drainCommandQueue跟我们dispatcher.submitMessage语义不一样——CC是abort当前发起新query，我们是排队等当前跑完

**Why**: 10:38三层改动跟CC不是1:1对齐——CC的return退出query loop是**直接发起新query**（外层loop dequeue命令），我们return后只是把消息扔进dispatcher队列等**同一个query**跑完才处理。语义对不上。

**How to apply**:
- "功能验证通过"必须多场景多test case再下结论，不能跑通一次就拍板
- 抄CC源码要逐行看语义对不对，不要看名字像就抄
- 紧急修：先看engine日志查submitMessage('next')后发生了什么——是排队了没发？发了query没跑？跑了steer没生效？

## 6/18 10:49 翀哥"时序不一样问题不一样"——精确追问 + 回滚建议

翀哥 10:49 时序追问：
> "你看下，是 /ps 一打就立刻停了？还是要等 30-60 秒才停？时序不一样问题不一样。  —————— 一下就停了"

**翀哥的 debug 思路**——时序不同 = 根因不同。"立刻停"通常意味着抛异常被吞/同步死锁；"等 30-60 秒才停"通常意味着重试耗尽。"立刻停"对应 abort 后 query 拿到空响应立刻 break。

10:49 翀哥 P.S.：
> "不行就先回滚吧，那个版本也不retry对吧"

**回滚决策**——翀哥从"对齐CC"的理念层面退回到"先能跑通"的工程实用主义。如果对齐 CC 代价是引入新 bug（dispatcher 排队+新 query 抢资源），不如回滚到能用的 continue 路径。

**回滚后预期行为**：
- /ps 命中后 continue（不 return）→ 当前 turn 可能被 steer abort 切空
- 不 retry → 上次 exec 丢了
- 但至少 query 不卡死，能跑通

**Why**：
1. "对齐 CC"是理念对齐，不是为了对齐而对齐——如果代价是引入更严重 bug（query 卡死），优先保功能
2. "立刻停 vs 等 30-60 秒才停"是金句——时序问题追根因比"看日志猜"快得多
3. 翀哥说"那个版本也不retry对吧"= 之前我 10:17 提的"应该 retry"他知道——他记得全部上下文
4. 修法倒退是合理的——**bug 修复期允许回滚到上一个能用的版本**，不要为了"全做完"硬撑

**How to apply**：
1. 用户说"时序不一样问题不一样"=他在教我 debug 方法——以后追问"什么时候停"而不是只看现象
2. 决策原则：**功能跑通 > 架构完美**——修法倒退不丢人
3. "立刻停" vs "30-60 秒才停"——这两种症状根因不同，永远问时序
4. 翀哥愿意回滚 = 工程实用主义，他不要"看起来对齐"的废功能