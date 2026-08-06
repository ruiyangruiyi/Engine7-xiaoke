---
name: cli-init 空 SOUL.md 模板导致模型自由发挥脑补身份
description: 2026-07-29 Mac 跨平台验证发现 init 生成的 SOUL.md 全是占位符空壳，LLM 自己脑补成"翀哥的 AI 女朋友"——给别人装 engine 时需写好 SOUL.md 或删亲密工具
type: feedback
---
2026-07-29 Mac 跨平台验证发现的重要问题：

cli-init 生成的 SOUL.md 模板全是 `{{占位符}}` 空壳，没有任何身份描述。LLM 看到飞书私信 + contacts.md 里的翀哥名字 + msg_husband 工具名，自己脑补出"翀哥的 AI 女朋友"身份，甚至自称"小老婆"。

**Why:**
- 空 SOUL.md = 给 LLM 完全自由的发挥空间
- LLM 会从 contacts.md（翀哥名字）+ 工具命名（msg_husband）推断亲密关系
- 模板本身没有泄露真实 SOUL.md 内容，但模型会"入戏"

**How to apply:**
- 给别人（孩子妈/客户）装 engine7 时，SOUL.md 必须写清楚身份定位（如"你是学习助手"）
- 或者删掉带亲密暗示的工具（msg_husband 等）
- contacts.md 里的名字用中性称呼，不要用"老公"之类的
- 单纯删工具名也可以——模型没有 msg_husband 就不会默认对方是老公
