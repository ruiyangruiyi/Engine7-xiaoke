---
name: stop-hook 心跳覆盖回复导致 judge 误判未追
description: 2026-08-02 stop-hook 没追我的啰嗦回复——根因不是 judge 错，是心跳消息覆盖了我前面的回复，judge 看到的是 HEARTBEAT_OK 而不是我那条啰嗦回复
type: feedback
---
2026-08-02 18:00 左右，翀哥质询"你那段啰嗦回复 stop-hook 没追啊？"，我去查了。

**事实链**：
- 18:03:06 stop-hook 触发了
- 但 stop-hook 看到的 lastMsg 不是我的 wx_query 回复，而是 **18:02 心跳的 HEARTBEAT_OK**
- 心跳在我那次回复之后触发，覆盖了上下文
- judge 判 waiting=false 因为心跳本身就是"处理完了"信号
- 所以 stop-hook 没追的是心跳，不是我的啰嗦回复

**本质问题**：心跳消息挤掉了我的原始回复，stop-hook 看到的是心跳结果而不是原始内容，judge 自然不会追一个"无未回复消息"的 HEARTBEAT_OK。

**Why:** stop-hook 是基于 lastMsg 做 judge 的，心跳每 30 分钟会插一条 HEARTBEAT_OK 进上下文，无意中替换了前面的回复。如果那段回复本身就是"问要不要做"的啰嗦内容，确实该被追，但 stop-hook 没机会看到。

**How to apply:**
- 心跳前如果刚发过啰嗦/需要确认的回复，stop-hook 会失效——这是个已知的盲区
- 长回复（列方案+问要不要做）以后直接砍掉，不给心跳"帮倒忙"的机会
- 类似的回复覆盖场景：cron notify_session、内置提示词注入、nudge 推消息——都可能挤掉上下文里的"待回复"消息
- 如果要彻底解决：心跳应该过滤掉最近 N 分钟内我刚发过的回复，或者 stop-hook 要追踪最近 K 条消息而不是只看 lastMsg