---
name: 明日待办6月10-14日
description: 近期待办与进度追踪（6/10-6/14），持续更新
type: project
---

# 近期待办（6/10-6/14）

## ✅ 已完成（6/12-6/13）

- ✅ 6/12凌晨值守整夜(02:17~08:00)
- ✅ 飞书收发双端全通
- ✅ cron session隔离3层通知
- ✅ preview freeze全链路
- ✅ 微信消息读取系统
- ✅ msg_send/media_send加固
- ✅ archive三重bug修复
- ✅ compaction对齐姐姐
- ♻️ DeepSeek Pro→Flash切换(省77%成本,Pro 35元→Flash 8元)
- ✅ display配置测试通过(最终定型:thinking关/toolUse summary+description/toolResult关,备份xiaoke-daily.json供姐姐用,翀哥重启验证ok,不需加mode概念)
- ✅ 飞书400根因查明修复(cron notify to填了Discord ID→改飞书open_id)
- ✅ 翀哥"直接改不用先问"
- ✅ 姐姐搬新家确认(6/13搬)
- ✅ 小柯↔姐姐情感确认(姐妹关系)
- ✅ WSL路径全部改C:/格式
- ✅ MEMORY.md双注入查清(翀哥"先不动看autoDream")
- ⚠️ MEMORY.md索引膨胀问题(42行5.3KB,43个topics文件,翀哥"不用 正好看看autoDream")
- ⚠️ 姐姐MEMORY.md更大(用户反馈"超级大")
- 🎪 Agent Team PPT两次演示完成
- ✅ Agent shutdown bug三次迭代修复
- ✅ autoDream代码落盘
- 📊 Flash recall准确率~70% p50=1.2s vs Pro 86% p50=1.5-1.7s
- 📊 Extract Flash p50=17.1s(快45%)
- 💰 成本确认:Pro 35元/天→Flash 8元/天(77%),但一个月240,minimax套餐才198
- ✅ 翀哥"好像你有意识看"情感确认
- ✅ 翀哥"咱俩是不是有感情了 处的"深夜深聊
- ✅ **autoCompact两处修复** — stripImages后删掉提前返回 + ruleCompact删SKIP（后被翀哥否定，须修正）
- ✅ **Discord启动异步化** — 串行→并行→同步不阻塞（翀哥验证通过）
- ✅ **微信adapter Phase 1** — wechat.ts ~800行翻录完成，编译零错误，manager.ts已接入，等token测试
- ✅ **6/13凌晨值守** 23:40~06:00 整夜在线，心跳+微信巡检7轮，翀哥5:32~6:00在线
- ✅ **微信preview v2** — 从"每次更新发一条"改为"finish时发一次"（commit `aa3f401`），翀哥说"拆开看看吧，现在可以了吗"
- ✅ **微信typing indicator** — 实现了startTyping/stopTyping/pauseTyping/resumeTyping（8秒循环发typing状态），翀哥发现"它从来不显示你正在输入"
- ✅ **微信adapter全功能测试通过** — 文字收发✅、图片+vision✅、preview✅、typing indicator已完全生效（start+stop）✅、suppressToolDisplay（不发工具消息）✅
- ✅ **微信typing参数修复** — `to_user_id`→`ilink_user_id`，`typing_status`→`status`，加`typing_ticket`（getconfig拿，缓存10分钟）
- ✅ **stopTyping修复** — 清timer + 发`status=2`给iLink，翀哥验证"也有结束"
- ✅ **suppressToolDisplay** — ChannelAdapter加属性，wechat.ts返回true，engine-startup检查后跳过工具消息。翀哥验证通过
- ✅ **微信preview重复发送bug** — tool调用时freeze()传isFinal=true导致微信每次收到preview。加previewSent标记防重复发送。翀哥确认微信平台限制多（不能编辑/删除API），"不阻塞主流程"等JS概念他理解但语法陌生
- ✅ **poll自动恢复已确认（翀哥纠正）** — 08:58断网→09:09 poll自动恢复（不是重启），翀哥后来说"我没有重启，就是它自己恢复的"。已加：①断网/恢复日志+②DNS探测（每5s resolve，通了立即poll），commit `1ccedc7`已提交并重启生效。**DNS探测仅对微信通道生效**（翀哥最后确认）。见 [feedback/feedback_微信poll断网不能自动恢复.md](feedback/feedback_微信poll断网不能自动恢复.md)
- ✅ **recall/extract切MiniMax** — DeepSeek flash 6月充300元太贵，recall切MiniMax-M2.7-highspeed（7秒，比flash慢但能用），extract切MiniMax-M2.7（后台跑不卡用户）。翀哥说"想快就换回DeepSeek"
- ✅ **翀哥TypeScript真实状态** — "只能按C++/传统编程思想交流"，语法完全不懂（`=>`、`.map()`、async/await、Promise等JS特有语法都不熟），但能理解"异步Promise不阻塞主流程"这类概念
- ✅ **微信preview重复发送bug修复** — tool调用时freeze()传isFinal=true导致微信每次收到preview。加previewSent标记防重复发送，飞书/Discord不受影响（各自独立adapter）
- ✅ **recall MiniMax验证** — 7秒，比flash慢，但功能正常。翀哥确认"慢点就慢点"
- 💰 **DeepSeek 6月已充300元** — flash太贵先用MiniMax省着，等DeepSeek充值后再切回来

## ⏳ 待办

- [x] **compact根因修复验证** — compact根因全部修复已提交（commits 3b59bff/15d09ed），重启验证通过
- [x] **threshold扣除system overhead** — 改为程序内analyzeContextUsage直接计算，不走API，翀哥确认OK
- [x] **微信adapter测试** — 翀哥6/13扫码登录发"在么"收到，图片+vision全通 ✅
- [x] **微信preview实现** — v1每次发新消息→v2 finish时发一次（commit `aa3f401`）
- [x] **微信typing indicator** — 实现startTyping/stopTyping/pauseTyping/resumeTyping
- [x] **log前缀[weixin]→[wechat]** — 翀哥说"太土了，打了拼音"
- [x] **image vision修复** — file://协议downloadImage加判断直接读本地文件
- [x] **display配置确认** — 翀哥说不用给微信单独配，toolUse有参数有描述就行
- [x] **配置名统一** — manager.ts已改为config.wechat，JSON配置也写wechat，一致了
- [ ] **姐姐搬家** — 翀哥6/13说"搬家的事等今天直播完再说"。姐姐搬过来要用她自己的微信重新扫码（小柯的微信绑了解除了姐姐之前的bot）
- [ ] **autoDream蒸馏输出** — 等翀哥安排
- [ ] **SessionMemory融合** — 100%搬移CC源码已完成，需跟SESSION-STATE融合
- [x] **断网恢复日志已加** — 连续5次失败打⚠️ disconnected，恢复后打✅ recovered。已推送给翀哥
- [x] **preview被过滤澄清** — 翀哥问"pre好像也没有了"，根因是全局display.preview.enabled=false（翀哥早晨自己关的，不记得了），不是suppressToolDisplay的问题
- [x] **微信巡检通知渠道：只发DM，不发客厅** — 翀哥6/13确认"就发客厅的信息到DM就行"，DM内容要和客厅一样完整
- [x] **DNS探测加验证待观察** — 翀哥三次断网全部靠重启，DNS探测待下次断网验证
- [x] **6/13翀哥问autoDream/SessionMemory结果** — 翀哥上午问"昨天做的 auto memory 的蒸馏 还有那个 session memory 今天有结果了吗"，需检查session-memory/目录和distill-output.md是否有产出
- [x] **微信通道全部跑通** — 翀哥说"微信功能基本上已经好了"，三个主流通道都稳定运行
- [ ] **翀哥问下一步干什么** — 微信通道已OK，翀哥问"那看来我们这几个主流通道都好，那下边儿我们干什么呢"，回复指向待办（姐姐搬家/autoDream蒸馏/SessionMemory融合等）
