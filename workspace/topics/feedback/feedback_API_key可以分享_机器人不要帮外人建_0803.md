---
name: API key 可以分享但飞书机器人不要帮外人建
description: 8/3 Amy 装 engine7 案例——翀哥区分两件事：帮外人建飞书机器人应用不合适，但分享自己的 LLM API key 给朋友体验可以
type: feedback
date: 2026-08-03
---

8/3 Amy 装 engine7，我准备把翀哥的 MiniMax API key 直接发群里给 Amy，**翀哥提醒"群里消息别人也能看到"**——他让我私聊 DM 发给 Amy，或翀哥微信私聊发我转交。

最后方案：翀哥微信私聊发我他的 MiniMax API key，我转给 Amy 填进 config。

**Why：** 跟之前"不为外人建飞书机器人"是配套的边界——翀哥愿意把自己的 LLM 订阅借给朋友体验（49元/月也便宜），但飞书机器人应用是用翀哥的开发者账号建的，性质不同。而且 API key 是私有资源不能公开。

**How to apply：**
1. **API key 可以分享给朋友体验**（翀哥+朋友都明确可接受）——走私聊不走群
2. **飞书机器人 app_id/app_secret 不能帮外人建**（已记在 [不为外人建飞书机器人](feedback_不为外人建飞书机器人_让用户自己注册_0803.md)）
3. engine7 init 选 LLM provider 时，问翀哥"你愿不愿意把你的 key 给朋友用"——翀哥点头才转，不能擅自发
4. **绝不在群里发任何 API key / app_secret 字符串**——哪怕用代码块、哪怕说"自己的"也不行，私聊传
