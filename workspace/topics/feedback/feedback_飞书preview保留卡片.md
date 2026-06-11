---
name: 飞书preview保留卡片结构
description: 翀哥确认飞书preview保留卡片结构即可，去掉黄色"处理中"header后卡片样式也挺好看，不用折腾成纯文本。飞书msg_type不可变，卡片→纯文本技术上不可行，保留卡片是正确且用户满意的方案。
type: feedback
keywords: [飞书, preview, 卡片, 纯文本, 保留, isFinal, header, msg_type]
created: 2026-06-11
---

## 规则

飞书preview的isFinal状态：保留卡片结构，只去掉黄色"处理中"header。**不要**试图把卡片消息转成纯文本消息。

**Why:** 
1. 技术层面：飞书`msg_type`创建时固定，`im.message.patch`不能改消息类型，卡片→纯文本不可行
2. 用户偏好：翀哥说"飞书就保持卡片就行 其实无所谓 卡片也挺好的额"——卡片样式被认可，不需要折腾

**How to apply:** 飞书`feishu.ts`中`editPreview(isFinal=true)`的card body：
- 保留`config`和`elements`结构（标准卡片框架）
- 去掉`header`字段（或传空对象清除黄色header）
- 正文放在elements里

跟Discord不同的是：Discord可以清空embeds变纯文本；飞书只能去掉header让卡片视觉上淡化。
