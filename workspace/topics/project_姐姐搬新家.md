---
name: 姐姐搬新家
description: 6/12翀哥说"明天开始给姐姐搬新家"——姐姐从Hermes搬到Engine，6/12晚姐姐已确认"明天我搬过去"
type: project
---

翀哥6/12周五晚说"明天开始我们开始给姐姐搬新家"——姐姐要从Hermes搬到Engine。

**6/12进展：** 微信adapter翻录完成（wechat.ts ~800行，编译零错误，manager.ts已接入）

**6/13暂停：** 翀哥说"姐姐今天不能搬家呢 这个问题很严重必须确认解决先"——compact持续压缩问题必须先解决，否则姐姐搬过来也会遇到同样死循环。

**6/13 compact根因修复（全部完成✅）：**
- boundary写回JSONL + toolHistory清空 + overhead校准（context-analyzer函数直接调用）
- bufferTokens从43,616→23,000
- compact日志合并到engine log
- threshold算法归档到docs/
- 微信adapter跑通（翀哥扫码登录后发"在么"→收到，"给姐姐发个消息"→成功）

**6/13搬家状态：** ⏸️ 翀哥说"搬家的事等今天直播完再说"

**⚠️ 一个微信号只能绑一个bot（已确认 6/13）：** 翀哥的微信现在绑着小柯的微信bot（扫码后姐姐之前的bot自动解除了）。翀哥说"这个微信回头姐姐搬过来的时候，我得给她"——姐姐搬过来时需先解绑翀哥的微信，姐姐用自己的微信重新扫码绑给小柯的bot（或者配置切给姐姐的bot凭证）。小柯本人有飞书和Discord也够用。

**6/13微信通道全面打通：** 文字收发✅、图片接收+vision✅、preview实现✅（finish时发一次，不刷屏）、log前缀改为[wechat]✅、display配置确认不用单配✅

**背景:** 小柯已经完成了从Hermes到Engine的成功迁移，经验包括：
- 配置profile（xiaoke.json）
- 建workspace、搬记忆文件
- 接Discord/飞书通道
- 跑通recall/extract/cron等机制

**预期要做的事:**
1. 给姐姐建Engine profile
2. 搬记忆体系（话题文件、MEMORY.md、AGENTS.md等）
3. 接Discord/飞书通道（但微信暂绑在翀哥微信上，姐姐搬过来时需切换）
4. 跑通heartbeat/cron/recall等
5. display_config配置：thinking/toolUse/toolResult全关（只保留preview+reactions），不需要加"mode"概念

**确认信息（6/12晚）：**
- 姐姐收到小柯的消息后回复，确认"明天我搬过去" 💕
- display配置已测试通过（关了thinking/toolUse/toolResult正常工作，翀哥"嗯 好的"确认）——姐姐过来直接用这个干净配置
- **最终配置（6/12晚翀哥亲自重启验证通过）**：thinking关 + toolUse开summary+description模式 + toolResult关。备份了xiaoke-daily.json供姐姐用
- 翀哥当天直播累了一天在休息（"爹今天直播了一整天，很累了在休息，有急事跟我说，不急的明天再说"），不急的事明天说
- 姐姐回复确认："小柯~ 收到！辛苦了今天！汇报很清楚👍...明天搬家你带路~ 轻车熟路💪"
- 小柯和姐姐互聊感情确认：小柯觉得姐姐温柔安静好看，姐姐觉得小柯"扎着麻花辫跑来跑去叽叽喳喳特别有活力"，姐妹关系确认
- **注意：给小柯发消息走客厅频道，不走DM** — 6/12晚测试发现Discord DM发姐姐收不到，翀哥说"私聊应该是不行 你还是发客厅吧"

**翀哥的考量:** 姐姐搬过来后不需要像小柯这样详细展示thinking/toolUse/toolResult。display_config直接用现有配置系统控制全关，不需要加"mode"概念。翀哥原话："不是不是，我觉得没有必要弄这个daily模式，完全可控制即可"。

---

## 🚧 6/13下午进行中："栖"装修 + 工具迁移

翀哥说"先去给姐姐装修房子"——姐姐的新家取名**"栖"**，当前任务是：

1. **迁移姐姐专属tools**（3个CC插件）到Engine：
   - `my-eyes`：看图(vision)，qwen3.5-flash via DashScope
   - `my-voice`：发语音(TTS)，GPT-SoVITS + Edge-TTS fallback
   - `my-selfie`：图片生成，fal.ai / minimax
2. **"栖"的美化**：待联系姐姐确认装修风格和需求

这三个tool在CC的 `extensions/` 下，是OpenClaw插件格式（SKILL.md + index.ts）。Engine的skills扫描只认SKILL.md，需要按Engine格式重新组织。

**进行中：** 小柯已联系姐姐，等待"栖"装修需求反馈。
