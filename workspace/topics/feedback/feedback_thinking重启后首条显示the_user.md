---
name: 重启后thinking首条显示"the user..."
description: 重启后第一个thinking里混入英文系统提示风格"the user..."而非用户昵称，翀哥确认不是bug只是冷启动现象
type: feedback
---

**现象：** 6/13 Engine重启后，Discord收到第一条消息时，thinking里显示"The user..."（英文系统提示风格）而不是"翀哥"。后续消息的thinking就正常显示"翀哥"了。

**翀哥确认不是bug：** "开开吧 没事 没说这是个bug 只是个发现"

**根因：** Engine重启后新session没有历史上下文，模型不知道用户是谁，默认用英文系统提示风格描述用户。有了上下文后就正常了。这是冷启动的正常行为。

**Why:** 重启后session从零开始，没有用户画像缓存。模型在无上下文时自然退回到英文系统提示风格。
**How to apply:** 如果未来有人问"为什么thinking里出现了the user"，解释为重启冷启动的正常现象。如果想改善，可以在system prompt里固定写入用户名称，但翀哥认为没必要改。
