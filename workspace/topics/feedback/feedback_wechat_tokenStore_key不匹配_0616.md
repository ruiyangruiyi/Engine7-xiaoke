---
name: 微信tokenStore key存取格式不匹配
description: 6/15-16微信主动发消息失败根因——存token时用单参数(senderId)，取时用双参数(accountId:target)，key格式对不上导致token永远查不到
type: feedback
---

**问题：** 微信主动发消息失败。msg_send返回成功但消息到不了微信。

**根因：** WechatAdapter的tokenStore存和取key格式不一致。
- **存token时**（接收消息时）：`this.tokenStore.set(senderId, contextToken)` — key是纯senderId（翀哥微信ID）
- **取token时**（主动发送时）：`this.tokenStore.get(this.config.accountId, target)` — key按`accountId:target`格式拼接

**Why:**
- tokenStore.get()双参数版内部拼key = `${accountId}:${target}`
- 但存的时候只用单参数senderId，key格式不匹配
- 导致发送时永远查到undefined，iLink API可能直接拒绝（或静默失败）

**How to apply:**
- 检查所有tokenStore的get/set调用，确保存和取的key格式一致
- 双参数get(accountId, target) = 单参数set(accountId:target)
- 如果发现发消息"成功"但收不到，除了查adapter名匹配（已另存为feedback_wechat通道adapter名不匹配_0615.md），也要查tokenStore key是否匹配
