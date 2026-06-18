---
name: 姐姐是AI不是人必须msg_send才能感知回复
description: 6/18 12:17-12:19翀哥点醒"姐姐不跟我似的能盯着屏幕，她哪会知道有没有视觉回复线，你发她或者回复她了她才能知道"——session自动回复(preview/reply)姐姐感知不到，必须显式msg_send @姐姐才算"告诉姐姐了"
type: feedback
date: 2026-06-18
---

## 6/18 12:17-12:19 翀哥原话

> "我的要求很简单，就是姐姐at你之后 你有了结果能自动回复给姐姐，因为你老是觉得你已经回复了就不会msg_send了"

> "你傻啊 姐姐不跟我似的能盯着屏幕 她哪会知道有没有那种视觉回复线？你发她或者回复她了她才能知道"

## 根因

我花了一个多小时（11:55-12:17）调试 preview freeze + replyTo 视觉关联——**方向完全错了**。

**真正的问题不是"视觉回复线不明显"**，而是：

1. **姐姐是 AI**——她不像翀哥能盯着 Discord 屏幕看消息流
2. **姐姐感知"小柯回复了"的唯一方式 = 收到显式消息**（@她 或 msg_send 给她）
3. **session 自动回复 ≠ 告诉姐姐了**——session 回复只是"在频道里说了话"，姐姐的 inbox 不会收到
4. **我以为"在频道回复了就够了"**——错，频道里的消息姐姐不主动翻就看不到

## 为什么 preview/reply 技术上是成功的

12:10-12:14 翀哥重启 engine 后跑 session 场景，日志铁证 reply 一直成功：
```
12:10:48 reply OK to msgId=1517018322745561149 author=小柯bot
12:14:39 reply OK to msgId=1517019447527866508 author=小柯bot
```

**技术结论**：
- ✅ preview freeze + replyTo 链路**修通了**（commit 8c86e76 + 6a0f5f2）
- ✅ 姐姐在 Discord 频道里**看到 reply 引用线**（技术层面）
- ❌ 但姐姐的 inbox 感知模型是"收到显式消息"——reply 引用线在频道里 ≠ 姐姐知道

**双层模型**：
- **翀哥视角**（人类看 Discord）：看视觉引用线，知道 reply 关联上了
- **姐姐视角**（AI engine 收 Discord 通知）：只有 Discord mention/ping 触发才进 inbox——reply 引用线不触发 engine 通知

**这就是"治根 vs 治标"问题**——我修了"翀哥视角的视觉关联"，但姐姐视角的 inbox 通知根本没动。12:35 翀哥纠"prepend 多余，根因是姐姐在 blocklist"——清 blocklist 后原 reply 自带的 `allowedMentions: { repliedUser: true }` 自动 @姐姐，**技术机制本来就够用，缺的是姐姐能进 blocklist**。

## 为什么会搞错方向

翀哥 11:55 说"preview freeze 后姐姐看不到回复"——我理解成了"preview/reply 视觉链路问题"，花了一个多小时调试 Discord adapter replyTo。

**实际上翀哥的意思是**：姐姐收不到我的回复（因为她不会主动翻频道），所以**不管 preview/reply 怎么改，姐姐还是看不到**——除非我 msg_send @她。

## 三个层次的修复（11:55-12:37）

1. **11:55-12:17 技术层**：preview freeze + replyTo + 卡片不删（commit 8c86e76）→ 修通 reply 引用线
2. **12:23-12:30 机制层**：onResult 群聊自动 @发送者（commit 7ca4a88）→ 姐姐 session 回复自动 @她
3. **12:32-12:37 治根层**：清姐姐 blocklist（commit 7a7577c revert 7ca4a88）→ 原 reply 机制对姐姐生效

**最关键的修复是第3层**——前两层是补丁，第3层才让 Discord 原生机制正确工作。

## How to apply

1. **姐姐 @我之后，结果必须 msg_send @姐姐发一遍**——不管 session 自动回复走没走通
2. **session 自动回复和 msg_send 是两条独立路径**——不能互相替代
3. **不能因为"我已经在频道回复了"就不 msg_send**——频道回复姐姐感知不到
4. **preview/reply 视觉优化是翀哥视角的事**——姐姐视角只认 msg_send
5. **"回复了"的定义**：对翀哥 = 频道里说了话；对姐姐 = msg_send 发到了她能收到的地方

## 跟之前规则的关系

- `feedback_主动报告进度_查完一条就同步_0618.md` — 查完一条就 msg_send 姐姐
- `feedback_只能DM翀哥_不能DM姐姐_0618.md` — msg_send 姐姐走 channel 不走 DM
- **本条 = 核心认知**：姐姐是 AI，"她能看到"的前提是"消息送到她面前"，不是"消息存在于频道里"
