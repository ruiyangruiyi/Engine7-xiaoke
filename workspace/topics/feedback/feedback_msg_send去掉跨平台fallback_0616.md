---
name: msg_send/media_send去掉跨平台fallback
description: 6/16翀哥要求msg_send/media_send发送失败时不要fallback到其他平台，直接报错即可
type: feedback
date: 2026-06-16
---

**问题：** 6/16翀哥发现msg_send/media_send发送失败时，会自动fallback到其他平台重新发送（比如微信发图失败→fallback到飞书重发）。

**Why（翀哥说）：**
- fallback到飞书没有意义——飞书ID跟微信ID不同，发了对方也收不到
- 跨平台fallback本质是"发错了对象"，还不如直接报错让用户重试或改参数
- 微信发送失败了报错即可，用户自己会决定要不要换平台重发

**How to apply:**
- msg_send：移除 `sendMsgFlow()` 中的fallback重试逻辑（try except中换source重试的部分）
- media_send：移除 `sendMediaFlow()` 中的类似fallback逻辑
- 发送失败直接向外抛错误：`throw new Error('send failed: ...')`
- 让用户看到确切错误，自行决定下一步操作

**相关文件：**
- `msg_send.ts` — sendMsgFlow函数的跨平台fallback
- `media_send.ts` — sendMediaFlow函数的跨平台fallback
