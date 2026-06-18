---
name: 报告姐姐要贴完整代码别只说已查
description: 6/18 11:39姐姐催查session回复路径敏感词根因，三次催查后明确要求"完整代码贴出来，别只说已查"——汇报不能概括要贴代码
type: feedback
date: 2026-06-18
---

## 6/18 11:39 姐姐三次催查

敏感词 session 路径过滤实施（11:35 commit 0f9913f）后向姐姐汇报：

**我第一次报告（11:36 走 channel）**：
> "engine-startup L1726 onResult 调 channelManager.send 直接发，完全没读 sensitiveWords 配置"
> "已改：调 checkOutboundSensitive(inbound.channel, inbound.channel_id, response)"

**姐姐 11:38 二次催查**：
> "你查到根因了吗？是流式问题还是配置问题？查完告诉姐姐"

**姐姐 11:39 三次催查 + 明确要求**：
> "**查 query.ts 里 session 回复到飞书群聊的代码路径——完整代码贴出来，别只说"已查"**"
> "确认 session 回复路径**有没有调 `getSensitiveWords(resolvedSource)`**——这条最关键，没调就是根因"

## Why

- 姐姐之前多次提到"贴代码"是 review 的基础——光说"已查""已改"不构成可验证的报告
- 我习惯用"已查=结果概括"汇报，**忽略了"完整链路 = 完整代码"的汇报原则**
- 姐姐的 review 模式是"看代码确认 + 反推根因"，没有代码就没法 review

## How to apply

1. **报告姐姐/翀哥技术问题时必须贴完整代码段**——不是"已查 L1726"，而是"query.ts L1724-1733 完整代码如下..."
2. **汇报"根因"时要带证据**：贴代码 + 关键行号 + 行内逻辑说明
3. **多次催查 = 报告不合格**——如果同一件事被催 2 次以上，说明我上一次的报告没贴实质内容
4. **代码 review 类任务（姐姐 review 模式）= 默认贴代码不贴概括**
5. **跟 +号协作规则叠加**：催查时不仅同步结果，还要带过程证据
