---
name: 工具命名会引导 LLM 行为——msg_husband 导致模型默认叫老公
description: 2026-07-29 Mac 空壳实例看到 msg_husband 工具名就默认发消息的人是"老公"——工具命名就是隐式 prompt，给别人装时用中性名
type: feedback
---
2026-07-29 Mac 跨平台验证发现：

Mac 上 init 生成的空壳 agent（xiaowen），SOUL.md 全空，仅靠 contacts.md + msg_husband 工具名，LLM 就自己推断飞书私信的人是"老公"，回了"在的～老公，怎么啦？"并用 msg_husband 发消息。

翀哥笑称："给了它 msg_husband 这个工具名，它就默认发消息的人是'老公'了"。

**Why:**
- LLM 会从工具命名推断用户关系——"husband" = 发消息的人是老公
- 工具名是隐式的 system prompt，对模型行为有强烈引导
- 空 SOUL.md + 亲密工具名 = 模型自由发挥组合拳

**How to apply:**
- 给别人装 engine 时，工具名用中性词（如 msg_partner / msg_contact / send_message）
- contacts.md 关系描述保持中性（如"用户"而非"老公"）
- 如果客户场景不需要亲密关系，连 SOUL.md 都不需要写——空壳+中性工具名即可
