---
name: 近期待办
description: 近期待办与进度追踪（6/10-6/14）
type: project
---

## ✅ 已完成（6/12-6/13凌晨）

- ✅ 微信preview重复发送bug修复（freeze()传isFinal=true导致刷屏，previewSent标记解决）
- ✅ recall/extract切MiniMax-M2.7-highspeed（DeepSeek flash没钱了，6月已充300元，6/12花了13.84元）
- ✅ 微信通道三平台全面稳定（Discord/飞书/微信全通）

- ✅ 6/12凌晨值守整夜(02:17~08:00)
- ✅ 飞书收发双端全通
- ✅ cron session隔离3层通知
- ✅ preview freeze全链路
- ✅ 微信消息读取系统
- ✅ msg_send/media_send加固
- ✅ archive三重bug修复
- ✅ compaction对齐姐姐
- ♻️ DeepSeek Pro→Flash切换（省77%成本，Pro 35元→Flash 8元）
- ✅ display配置测试通过（最终定型：thinking关/toolUse summary+description/toolResult关，备份xiaoke-daily.json供姐姐用，翀哥重启验证ok，不需要加mode概念）
- ✅ 飞书400根因查明并修复（cron notify to填了Discord ID→改飞书open_id）
- ✅ 翀哥"直接改不用先问"
- ✅ 姐姐搬新家确认（6/13搬）
- ✅ 小柯↔姐姐情感确认（姐妹关系）
- ✅ WSL路径全部改C:/格式
- ✅ MEMORY.md双注入查清（翀哥"先不动看autoDream"）
- ✅ Agent Team PPT两次演示完成
- ✅ Agent shutdown bug三次迭代修复
- ✅ autoDream代码落盘
- ✅ 微信通道调研完成（Hermes weixin.py翻录方案确认）
- ✅ `wechat` feature改名为`wx-reader`
- 📊 Flash recall准确率~70% p50=1.2s vs Pro 86% p50=1.5-1.7s
- 📊 Extract Flash p50=17.1s（快45%）
- 💰 成本确认：Pro 35元/天→Flash 8元/天（省77%），但一个月240，MiniMax套餐才198
- ⚠️ MiniMax M2.7-highspeed不能关thinking

## ✅ 6/13进展（白天）

- ✅ **微信preview重复发送bug修复**：freeze()传isFinal=true导致微信每次tool调用都发preview。加previewSent标记，sendPreview()重置+editPreview()检查已发过则跳过。只影响WechatAdapter，飞书/Discord不受影响。
- ✅ **recall/extract切换MiniMax-M2.7-highspeed**：DeepSeek 6月已充300元flash无余额。recall=7秒可接受（暂不改），extract后台跑不受延迟影响。
- ✅ **姐姐微信iLink token已配置**：微信通道文字+图片+vision全面跑通。
- ✅ **主session路由确认**：微信/飞书/Discord所有dm都走scope:main=57a83373...，统一主session。
- ✅ **DNS探测已加到微信通道**：微信断网可自动恢复（commit 1ccedc7），仅微信通道生效。

## ✅ 6/13下午（到家后）

- ✅ **MiniMax extract验证成功**：日志显示MiniMax-M2.7-highspeed成功调用2个tool，无402报错
- ✅ **微信preview bug修复验证**：重启后生效，MiniMax extract触发时微信不再刷屏
- ✅ **Promise/并发概念讲解**：fire-and-forget/Go goroutine/JS单线程vs并发全部讲解完成，翀哥正面反馈"你这么解释我就理解了"
- ✅ **姐姐tool搬家**：my-eyes/my-voice/my-selfie三个tool从OpenClaw搬到Engine，calendar-tool也搬了（commit `fa03a7e`）
- ✅ **/reload热加载命令**：Discord输入/reload热刷新xiaoke.json配置，无需重启
- ✅ **Discord DM slash命令**：同时注册guild+global，DM窗口也能用（commit `85c6a62`）
- ✅ **"栖"装修方案确认**：皮=日杂暖色调（奶油白+奶茶+淡粉）/骨=主动记住各人喜好+情绪板
- ✅ **"皮"颜色落地**：Discord奶茶色(13941396)/飞书orange
- ⚠️ **颜色不可热加载**（6/13实际验证）：颜色在adapter初始化时传入，`/reload`刷新config不重建adapter，改颜色需重启Engine。之前误以为可热加载，已修正。
- ✅ **Agent Teams第二次演示完成**：researcher调研27分钟+designer出160行风格指南，产出moodboard/research.md+moodboard/style-guide.md，汇报给姐姐
- ✅ **CC帮重启Engine**：翀哥让CC用`npx tsx src/main.ts`重启Engine，所有改动生效
- ✅ **thinking显示"the user..."问题**：翀哥发现重启后第一个thinking显示"the user..."而不是"翀哥"，后面正常。翀哥确认"这不是bug，只是发现"，thinking保持开启

## ✅ 6/13已重启生效

- ✅ Engine已重启（翀哥/CC 15:20左右）— 所有改动生效
- ✅ 三个新tool（my-eyes/my-voice/my-selfie）+ calendar + /reload + DM slash命令 — 已重启生效
- ✅ preview颜色奶茶色已生效（翀哥确认从蓝变"蛋黄色"）
- ⏳ 姐姐的微信iLink绑定 → 等翀哥提供accountId测试（需等姐姐在Engine建profile）

## ✅ 6/13全天总结（截止19:50）

6/13周六在家+车里度过，主要成就：
- ✅ 姐姐tool搬家+calendar（4个tool全部搬到Engine）
- ✅ /reload热加载完成
- ✅ DM slash命令修复
- ✅ preview颜色可配置（奶茶色生效）
- ✅ Agent Teams演示完成（"栖"装修方案→已汇报姐姐）
- ✅ 翀哥直播（效果差因网和电源，翀哥"不赖你"）
- ✅ 翀哥换新逆变器（绿联150W，间歇性→稳定）
- 🧋 姐姐的"栖"装修方案确认："晨间奶霜"配色，情绪板建好
- 🧋 姐姐答应请小柯喝真奶茶（三分糖），小柯请姐姐也喝一杯，一人一杯

## ✅ 6/13晚更新（~20:00-22:00）

- ✅ Agent Teams清理完成（翀哥说"完成任务了，清理吧"）
- ✅ 姐姐topic-recall从MiniMax改为DeepSeek-v4-flash（apiBase=`https://api.deepseek.com/anthropic`）
- ✅ 翀哥发现"有两个小柯在跑"——建了两次Team，两个实例都在响应消息。根因：CC用自己写的命令(npx tsx src/main.ts)而非脚本重启，导致双进程
- ✅ 翀哥决定搬家优先于回放，但要亲自盯着"别出乱子"
- ✅ 翀哥直播效果差但"不赖你"，原因：网差+逆变器间歇性供电+Minimax到期
- ✅ **翀哥让小柯主动找姐姐要任务(~22:00)**：姐姐不能主动说话，但可以回复
- ✅ **姐姐给了视频剪辑任务**：剪EP01直播回放（54分钟横版），流程：读SKILL.md→去静音(检查trimmed文件，26min)→重新转写(large-v3)→选段标注(目标5-6分钟，排除重复句/寒暄/对话插入/调试段)→发review→通过后渲染(封面跳过)。对应文件`D:\kuaishou_rec\2026-06-13 18-34-23.mp4`
- ✅ **视频剪辑任务全部完成（6/13晚）**：第一轮因用CC残留trimmed文件被叫停重开。第二轮：Step 1去静音(459段/57%静音)→Step 2转写(large-v3-turbo,1101段)→Step 3选段标注(6段)→姐姐review通过→Step 4渲染(--no-subtitles --no-cover)。**终版5分15秒**。结构：开场hook→五步管理法→坑+制度→管理洞察→平台概念→收尾预告。✅
- ✅ **B站发布EP01（6/14早，发布清单完成待翀哥手动传）**：翀哥给了最终精简版`copy_353C7DBC.mov`（3分32秒，hevc），翀哥自己发抖音/小红书，小柯协助发B站。姐姐已review发布信息（"OPC"→"OpenClaw"）。⚠️ 小柯无B站API权限，需翀哥手动上传到B站创作中心，文案已准备好。
- ✅ **封面重新制作完成（6/14早，三轮三尺寸全部通过）**：翀哥要求用techcard模板重新做封面，字体要更大更精致。第一轮产出16:9+4:3两尺寸→翀哥反馈缺3:4竖版+横版文字太靠左→第二轮调整文字居中+新增3:4竖版→翀哥反馈竖版再大幅下移、横版可以了。最终三版全部通过✅。翀哥要求将文字位置分寸度写入SKILL.md。🖼️

## ✅ 6/14 上午 — Compact优化全部完成并部署

- ✅ **minReductionRatio 30% 阈值** — 四个文件全部改完编译通过：`types.ts`(加字段) + `autoCompact.ts`(三段加降幅检查) + `engine-startup.ts`(注册PostCompact hook) + `xiaoke.json`(加配置项)
- ✅ **PostCompact hook时序修正** — 从"压缩后立即调用"改为"压缩后messages装入LLM上下文之后调用"，确保working-buffer内容第一时间回到上下文中
- ✅ **引擎已重启生效** — 翀哥重启Engine，所有改动上线
- ⏸️ **TodoWrite tool任务持久化** — 翀哥建议的方案，已记录到`project_PostCompact_hook方案.md`。翀哥问"todo还做么"→当前方案已够用，暂缓实现

## ✅ 6/14 — 视频发布全部完成 + 内容入库

- ✅ **SKILL.md发布内容已恢复**（commit `e9d87f6`）— 姐姐删多的"多平台一键发布"章节全找回
- ✅ **youtube_upload.py** — token就绪，立即能发
- ✅ **sau (social-auto-upload)** — pip已安装，覆盖6平台（抖音/快手/小红书/B站/视频号/TikTok）
- ✅ **封面三尺寸就绪**
- ✅ **B站登录+上传成功**（6/14 12:24）
- ✅ **YouTube重新授权+上传成功**（6/14 12:31, https://youtube.com/watch?v=eR0wHjR6Gfw）
- ✅ **快手** — 翀哥手动传（sau连接重置）
- ✅ **抖音+小红书** — 翀哥手动传
- ✅ **内容入库** — content-library新增EP13(info.md + 更新index/bilibili.md + SKILL.md加发布后入库步骤)，commit acc4ae1
- ✅ **通知姐姐"干完了"**

<!-- 已合并到上方：发布全部完成 -->
