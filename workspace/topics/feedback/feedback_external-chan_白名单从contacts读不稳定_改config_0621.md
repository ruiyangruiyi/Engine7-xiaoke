---
name: 外部群白名单从contacts.md读"不稳定"——翀哥要求改config
description: 6/21翀哥说从contacts.md读白名单不稳定，改config优先+contacts兜底已实施；后要求汇总所有平台externalChannels
type: feedback
date: 2026-06-21
---

6/21 09:21 姐姐问关于外部群白名单的问题时，翀哥说从contacts.md读白名单**"不稳定"**。

**现状（修前）：** 白名单从 `prompts/contacts.md` 通过 `**channel_ids:**` 正则提取。但 contacts.md 是提示词 prompt 文件，改格式或不小心改了这个区段，正则就会断。

**Why：** contacts.md 是给AI看的提示词文件，不是配置文件。在里面塞结构化数据（channel_ids 表）有几个风险：
1. 改 prompt 格式容易把正则搞断
2. prompt 文件没有格式校验
3. 姐姐或翀哥改 prompt 时不会意识到"这里还被代码依赖"

**How to apply（已实施 09:35-09:40）：**
1. **config 优先：** 在渠道配置下加 `group.externalChannels: string[]`
   - `configs/xiaoke.json` feishu.group 加了 `externalChannels`
   - `configs/main.json` feishu.group 同步加了
2. **contacts.md 兜底：** 如果 config 没有配 `externalChannels`，才回退读 contacts.md
3. **实现：** `getExternalChanWhitelist` 增加 config 参数，config.externalChannels 优先，为空则用 contacts.md 正则提取
4. **汇总所有平台（09:43-09:48 翀哥纠正）：**
   - 我最初只从 `inbound.channel` 对应平台取 externalChannels
   - 翀哥（09:43）："你取的时候不能假设只有飞书有外部群，你取的时候要不要都看看？"
   - 我先改成了遍历所有平台汇总（`Object.values(config.channels)`）
   - 翀哥后来说（09:48）："其实你看这个 inbound.channel 去找对应的问题也不大，毕竟这个也不是啥太大的问题。看吧，都遍历了估计也不会有性能问题"
   - 最终：**汇总所有平台**——遍历所有 `group.externalChannels` 合并成白名单

**翀哥确认方向（09:43）：** config 优先 + contacts 兜底是对的，但必须汇总所有平台，不能只按 inbound.channel 取一个。
