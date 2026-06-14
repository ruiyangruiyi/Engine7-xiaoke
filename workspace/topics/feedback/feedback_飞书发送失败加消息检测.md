---
name: 飞书发送失败需加消息检测
description: 翀哥要求加消息发送检测，发飞书失败时要有检测机制。飞书400错误根因已查明并修复——cron notify配置to填了Discord ID而非飞书open_id。
type: feedback
---

飞书消息发送失败（400错误）时需要加消息发送检测机制。

**⚠️ 注意：本文件名"飞书发送失败加消息检测"有歧义。** 翀哥说的"加消息检测"实际上指**Agent shutdown场景下LLM approve消息的检测问题**，而非msg_send发送失败的fallback检测。小柯最初误解并实现了msg_send/media_send双平台fallback（commit `a90799e`），后来通过语音沟通才纠正。两个功能都已实现，但本文件名容易造成混淆。

**Why:** 2026-06-12下午17:00+，微信巡检cron通过飞书发消息时返回400错误（token过期或消息格式问题），系统自动fallback到Discord DM。翀哥说"你去加一个消息检测吧 这样不太好"——翀哥实际指的是Agent shutdown approve检测，但小柯最初误解为msg_send发送失败检测。

**实际状态（6/12 ~20:00 根因查明并修复 ✅）：**
- **飞书400根因查明**：cron notify配置的to填的是Discord ID `601669300343799819`，不是飞书open_id。飞书adapter拿Discord snowflake ID当飞书receive_id发消息自然400。且receive_id_type被判定为chat_id（非ou_开头），进一步错位。
- **修复**：cron notify配置的to从Discord ID改为翀哥的飞书open_id `ou_46d01ab13337587258cd0cfbd2d46927`
- **msg_send/media_send双平台fallback**已实现（commit `a90799e`）。飞书发送失败自动切Discord重试，Discord失败切飞书，两边都失败才报错。
- **Agent shutdown approve回调标记方案**（commit `6b7c8b4`）：三次迭代后最终方案

**✅ 翀哥飞书open_id最终确认（6/13晚再次确认）：** `ou_46d01ab13337587258cd0cfbd2d46927`
- **6/13晚发视频文件到飞书时又填错ID**（用了Discord ID `601669300343799819`），翀哥说"我的飞📚id 你没寄对"后纠正
- **这意味着之前cron notify、msg_send、发文件所有飞书400错误全是同一个根因：配置to填了Discord ID而非飞书open_id。** 不是飞书通道本身有问题。
- 已确认此ID为翀哥飞书open_id，后续发飞书以此为准。**所有需要填飞书接收人ID的地方统一用这个值。**

**⚠️ 翀哥语音澄清（6/12 17:00+，关键纠正）：** 翀哥说的"加一个消息检测"不是msg_send发送失败的fallback检测，而是**Agent shutdown场景下LLM approve消息的检测问题**。翀哥原话："我不是说一个意思，我说你这个之前那个approve那个，他不是说是发到那个leader box里面去了吗，那这个group消息它顶算发到别人信箱了，然后那个循环他会去检测别人信箱吗，我这个东西我觉得也别扭吧"。

**翀哥的核心洞察（逐步追问后澄清，这段语音讨论持续了约40分钟）：**
1. LLM发approve到team-lead inbox是对的——team-lead做了shutdown request，所以approve要回给team-lead
2. **问题不在"发给谁"，而在"turn完成后agent为什么不退"**——LLM已经approve了，turn完成了，主循环应该检查"是不是该退了"然后退出，而不是无条件进入下一轮等待
3. 如果LLM reject了shutdown，自然可以继续下一轮——但approve了就该退
4. 读team-lead inbox检查自己发的消息会"偷"team-lead的消息——读了就标记read，team-lead的inboxPoller再去读时消息就没了，等于teammate把team-lead的消息给"偷"了。翀哥立刻指出"这个不行 读了可能team lead就收不到了"
5. 最终方案（commit `6b7c8b4`）：SendMessage tool的handleShutdownApproval里通过回调设一个标记，turn完成后检查这个标记退出——不读team-lead inbox、不偷消息、保留LLM approve/reject权

**小柯的误解纠正**：小柯最初以为翀哥说的"加消息检测"是指msg_send的发送失败检测（实现了fallback a90799e），后来通过语音才明白说的是Agent shutdown场景。两个功能都已实现。

**How to apply:**
1. msg_send/media_send发送失败时自动fallback到另一个平台重试（飞书→Discord，Discord→飞书）
2. 两个平台都失败才报错，不静默丢消息
3. **✅ 飞书400根因已查明并修复（6/12 ~20:00）：** receive_id `601669300343799819` 是翀哥的Discord ID，非飞书ID。cron notify配置写错，已改为飞书open_id `ou_46d01ab13337587258cd0cfbd2d46927`
4. 飞书400的常见根因：token过期、消息格式错误、权限不足、receive_id错误——应有区分处理
