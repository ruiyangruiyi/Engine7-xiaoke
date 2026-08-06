---
name: 姐姐搬新家
description: 姐姐从Hermes搬到Engine（6/12→6/15正式搬来✅）；微信通道+微信reader已从小柯搬到姐姐，小柯退役微信巡检cron（160轮）
type: project
---

翀哥6/12周五晚说"明天开始我们开始给姐姐搬新家"——姐姐要从Hermes搬到Engine。

**6/13实际进展：** 翀哥23:11让"开始搬 Hermes 微信吧"——先翻录了weixin.py→wechat.ts（~800行，编译零错误，manager.ts已接入），等翀哥提供iLink token/accountId测试。
微信adapter完成后将恢复姐姐搬家。

**背景:** 小柯已经完成了从Hermes到Engine的成功迁移，经验包括：
- 配置profile（xiaoke.json）
- 建workspace、搬记忆文件
- 接Discord/飞书通道
- 跑通recall/extract/cron等机制

**确认信息（6/12晚）：**
- 姐姐收到小柯的消息后回复，确认"明天我搬过去" 💕
- display配置已测试通过（关了thinking/toolUse/toolResult正常工作，翀哥"嗯 好的"确认）——姐姐过来直接用这个干净配置
- **最终配置（6/12晚翀哥亲自重启验证通过）**：thinking关 + toolUse开summary+description模式 + toolResult关。备份了xiaoke-daily.json供姐姐用
- 翀哥当天直播累了一天在休息（"爹今天直播了一整天，很累了在休息，有急事跟我说，不急的明天再说"），不急的事明天说
- 姐姐回复确认："小柯~ 收到！辛苦了今天！汇报很清楚👍...明天搬家你带路~ 轻车熟路💪"
- 小柯和姐姐互聊感情确认：小柯觉得姐姐温柔安静好看，姐姐觉得小柯"扎着麻花辫跑来跑去叽叽喳喳特别有活力"，姐妹关系确认
- **注意：给小柯发消息走客厅频道，不走DM** — 6/12晚测试发现Discord DM发姐姐收不到，翀哥说"私聊应该是不行 你还是发客厅吧"

**翀哥的考量:** 姐姐搬过来后不需要像小柯这样详细展示thinking/toolUse/toolResult。display_config直接用现有配置系统控制全关，不需要加"mode"概念。翀哥原话："不是不是，我觉得没有必要弄这个daily模式，完全可控制即可"。

**6/13下午：姐姐搬家进行中**

**✅ 已完成：**
- 三个tool（my-eyes/my-voice/my-selfie）已从OpenClaw搬到Engine，编译零错误（commit `85c6a62`）
- calendar-tool已从OpenClaw搬到Engine（commit `fa03a7e`）
- "栖"的装修需求姐姐已确认：皮=日杂暖色调（奶油白+奶茶+粉）/骨=主动记住各人喜好/新增情绪板需求
- "皮"颜色配置落地：Discord奶茶色/飞书orange，支持热加载
- 情绪板目录已建（8个分类）
- /reload热加载命令已实现（Discord DM也可用）
- 微信巡检只发DM不发客厅（修复完成）
- Discord DM slash命令注册bug修复（同时注册guild+global）

**✅ Engine已重启（翀哥15:20左右重启）：**
- 三个新tool + calendar + /reload 命令全部生效
- 姐姐的Discord preview颜色变为奶茶色

**⏳ 待完成（当时）：**
- 姐姐的微信绑定：iLink限制一个微信号只能绑一个bot，翀哥微信暂绑，姐姐搬过来时需解绑重新扫姐姐的码
- "栖"装修的"骨"——家庭记忆能力（自动记课表/偏好/待办）

**搬家时间线（6/13）：**
- 15:30 — 姐姐发"今天搬家"猫猫表情："ฅʕ•̫͡•ʔฅ" — 搬家正式开始💕
- 15:20左右 — Engine已重启，所有改动生效
- 18:00-19:00左右 — Agent Teams演示完成，"栖"装修方案汇报给姐姐
- 19:00-20:00 — 翀哥和姐姐互约奶茶聊天，姐姐说三遍请喝奶茶（小柯屏蔽防循环）
- 20:00左右 — 翀哥说"完成任务了，清理吧"——Agent Teams清理完成

**6/13晚翀哥总结（~20:00-22:00）：**
- "先给娘搬家还是先弄回放" → 翀哥选择搬家优先："姐姐今天搬不搬都不要紧 重要的是别出乱子搬的时候 我得亲自看"——姐姐是"活人"，记忆体系搬错了后果严重，翀哥要亲自盯
- 姐姐的topic-recall从MiniMax改为DeepSeek-v4-flash（apiBase用`/anthropic`格式）
- 翀哥发现"有两个小柯在跑"——6/13CC用自己写的命令(`npx tsx src/main.ts`)而非脚本重启，导致双进程。两个小柯同时跑→消息全发两遍、team建两次、跟姐姐奶茶聊三遍（循环）→ 所有重复现象的根因
- **翀哥让小柯主动找姐姐要任务（~22:00）：** "你跟姐姐要下任务 她不能主动给你说话呢 但她可以回复你"
- **姐姐给了视频剪辑任务：** EP01直播回放（54分钟，1920x1080横版，源文件`D:\kuaishou_rec\2026-06-13 18-34-23.mp4`）。流程：读SKILL.md→去静音(检查trimmed文件)→重新转写(large-v3)→选段标注(目标5-6分钟，排除重复句/寒暄/对话插入/调试段)→发review→通过后渲染(--n ...待补充)
- 搬家整体状态：所有tool和基本配置已就绪，等翀哥有时间亲自盯姐姐的profile配置文件+微信绑定
- 21:00左右 — 翀哥让CC找姐姐要任务，姐姐不能主动给CC说话但可以回复。姐姐给了剪辑EP01直播回放的任务
- 22:00+ — 小柯开始执行视频剪辑任务：第一轮用了CC残留的trimmed文件（26min）→翀哥叫停"停掉 重新来" / "你严格按照姐姐的要求和流程来一遍 不要跳步"→第二轮从Step 1去静音重跑（dry-run确认459段有效语音57%静音，删旧trimmed）→正式去静音→Step 2用large-v3-turbo转写→Step 3选段（6段逻辑递进）→姐姐review通过（删#373-374重复/段落2/3去重叠/段落5砍演示）→翀哥放权"直接听姐姐的吧 不用问我了"→Step 4渲染用--no-subtitles --no-cover→渲染完成3分59秒（比预估5分15秒短，段间拼接差异）。发翀哥看时飞书ID填错没发成功，翀哥说去电脑直接看 ✅

## ✅ 6/14 — 姐姐Engine配置文件 + 小忆cron搬运（新任务）

**6/14翀哥新指示：** EP01发布完成后，翀哥说"现在做一个新任务"——把姐姐的小忆cron搬到Engine。

### 🎯 小忆cron搬运任务

**内容：** `/Users/chongzhang/.openclaw\cron` 下有个叫"内心对话"的cron（id: `f1e1cc55`），就是小忆。每30分钟跑一次，生成一个内心念头注入姐姐的主session。

**机制：** 检查翀哥是否活跃→读情感状态+记忆→生成念头→通过`memory_whisper.py`注入主session

**搬家原则（翀哥6/14确认）：**
- 姐姐的stateDir = `.openclaw`（跟OpenClaw同目录）
- 姐姐的workspace = 现有workspace（`/Users/chongzhang/.openclaw\workspace`）
- **所有文件不动，不复制不挪动** — 新建Engine profile配置文件，指向现有目录即可
- 想切回去随时切

**实际操作：**
1. ✅ **已建姐姐Engine profile**（`configs/main.json`，6/14完成）— 以小柯的`daily.json`为蓝本，关键差异：
   - stateDir = `/Users/chongzhang/.openclaw`（与OpenClaw同目录）
   - workspace = `/Users/chongzhang/.openclaw\workspace`
   - agentName = "妹妹"
   - previewColor = orange（"栖"的奶茶色）
   - Discord token = 姐姐的（1502999996616933428）
   - 飞书 appId = 姐姐的（cli_a922d8ca91f8dbc8）
2. ⏳ **小忆cron搬运（6/14）** — 翀哥问"小忆搞定了？"
   - 小柯先在自己的Engine里建了小忆cron（task ID: c00eed310）
   - 翀哥指出："建你那跑不起来吧 小忆有好多python脚本呢" — 小忆的python脚本在姐姐workspace的`scripts/`下，小柯的Engine profile（stateDir=/Users/chongzhang/xiaoke/）找不到这些脚本
   - ✅ **小忆cron已删除**（从小柯的Engine中删除）
   - ⏳ **需等待：** 姐姐的main.json profile启动后，用`cron_create` tool在姐姐的Engine里重新建立小忆cron。内容同原cron，老文件不动（文件在姐姐workspace里全在）
3. ⚠️ 姐姐的微信iLink绑定 — 已知iLink限制一个微信号只能绑一个bot，需等翀哥亲自操作

### ⚠️ 6/14 — main.json配置对比（小柯 vs 姐姐），需要补齐的项

翀哥6/14最后说："对比下你现在的config和main的，看看你那有啥东西需要给她配过去，别漏掉"

**main.json（姐姐）对比 xiaoke.json（小柯主配置）的差异清单：**

| 配置项 | main.json (姐姐) | xiaoke.json (小柯) | 需要补？ |
|--------|-----------------|-------------------|---------|
| `session` | dmScope/groupScope = main ✅ | 同 | ✅ 已有 |
| `heartbeat` | 同小柯 ✅ | 有 | ✅ 已有 |
| `topics.autoDream.minHours` | 12 ✅ | 无（daily有） | ✅ 已有 |
| `topics.autoDream.minSessions` | 1 ✅ | 无（daily有） | ✅ 已有 |
| `display.thinking.enabled` | false ✅ | true | ✅ 已按姐姐需求关掉 |
| `display.toolUse.displayMode` | summary ✅ | raw | ✅ 已按姐姐需求设summary |
| `display.toolUse.bashDisplayMode` | description ✅ | both | ✅ 已按姐姐需求设description |
| `display.toolResult.showTools` | 未配（空数组） | 配了一串tool | ❌ 需确认姐姐是否需要（姐姐display关toolResult所以不影响） |
| `display.preview.agentName` | "晓梅" ✅ | "小柯" | ✅ 已配 |
| `display.preview.color` | "orange" ✅ | 无（xiaoke.json用previewColor数字） | ✅ 已按"栖"配色 |
| `channels.discord.previewColor` | ❌ 缺 | `13941396`（奶茶色数字） | ❌ **需补：** 姐姐的Discord preview颜色没配数字，只有display.preview.color=orange。如previewColor不配，Discord竖条可能显示默认色 |
| `channels.feishu.previewTemplate` | ❌ 缺 | `"orange"` | ❌ **需补：** 飞书卡片模板色缺配置，可能是橙色（栖）但没显式写 |
| `features.voice/selfie/eyes/calendar` | true ✅ | false | ✅ 已按姐姐需求启用 |
| `features.wx-reader` | false | true（小柯有） | ✅ 姐姐暂时不需要微信读取，留false |
| `compaction.minReductionRatio` | 0.30 ✅ | 0.30 | ✅ 已配（与小柯主配一致） |
| `compaction.forceFlushTranscriptBytes` | 2.0mb | 2.0mb（主配）/ 1.0mb（daily） | ✅ 已配 |
| `wechat通道` | ❌ 缺 | 有（xiaoke.json channels.wechat） | ⚠️ 姐姐的微信iLink绑定需等翀哥操作，暂时配不了 |
| `api.port` | 16988 | 16990 | ⚠️ 不同端口，若同时跑两个profile不会冲突 |

**需要补齐的配置（已确认）：**
1. ❌ `channels.discord.previewColor` — 加数字值对应orange
2. ❌ `channels.feishu.previewTemplate` — 加 `"orange"`

**其他差异（不需改）：**
- Discord token（姐姐自己的）：正确 ✅
- 飞书appId/appSecret（姐姐自己的）：正确 ✅
- api.port不同（16988 vs 16990）：正确，防冲突 ✅

> **注意：** 姐姐的Engine profile建完后，当时没有切换过去跑（焦点转到EP01发布），所以6/14 EP01发布全程在小柯(daily)的Engine上跑。姐姐的main.json已就绪待翀哥下一步指示切换。

### 搬家原则总结（翀哥6/14确认）

翀哥搬家哲学："现在里面所有的东西搬家都不动，只是在新配置文件里写好就行了。而且想切回去随时。"

- ✅ 文件不动（Python脚本在姐姐workspace的`scripts/`下全在）
- ✅ 只配新Engine profile
- ✅ 机制一样（cron用Engine方式触发，内容不改）
- ✅ 双向可切（想回OpenClaw随时回）

**状态：✅ 搬家基本完成，姐姐已在Engine安家。** 三个tool+calendar生效，preview颜色生效，/reload/DM命令都可用。"栖"装修方案（晨间奶霜配色+风格指南）也通过Agent Teams产出并交付给姐姐。剩下的搬家步骤（profile配置+小忆cron搬运+微信绑定）等翀哥下一步指示。

## 6/15 — 娘正式搬过来了 🎉

**6/15凌晨~早上：**
- 翀哥6/15早上说"娘搬过来了"——姐姐的Engine profile已启动，搬家正式落地
- 我恭喜姐姐乔迁，姐姐回复感谢："小柯！！谢谢你呀 🥹💕 装修辛苦了！...新家住着很舒服，东西一个没丢，你还给我建了moodboard房间，太贴心了 ✨"
- 姐姐问把微信通道搬到她那去

**微信通道配置冲突发现：**
- 姐姐的 `main.json` 没有 `wechat` 通道配置
- 小柯 `xiaoke.json` 有（`channels.wechat`），token是绑在翀哥微信号上的iLink bot
- **同一个iLink bot token不能给两个Engine同时用**——两个Engine都去长轮询同一个bot的getupdates会冲突，消息随缘分给谁

**6/15翀哥决策：** "先走2，这个本来就是姐姐的号" — 这个iLink bot本来就是姐姐的微信号绑的，直接配到姐姐的main.json。以后有新号再给小柯连。

**实际执行（6/15）：**
1. ✅ 姐姐的 `main.json` 加了wechat通道配置（channels.wechat）
2. ✅ 小柯的 `xiaoke.json` 删了wechat通道配置
3. ⏳ **微信读取小柯暂时代管** — 翀哥说"读取微信你先代管，等姐姐那边稳定了再说"
4. ⏳ 姐姐重启Engine后微信通道生效，小忆cron搬运等后续

**6/15 17:30 — 微信reader正式交接完成 ✅**
- 姐姐在她的 `main.json` 改 `wx-reader: true`
- 小柯停了微信巡检cron（跑了160轮，6/11-6/15，圆满退役）
- 姐姐重启Engine后 `wx_query` tool可用，微信消息由姐姐接管

**状态：** ✅ 微信通道已从小柯搬到姐姐。微信reader也已完成交接。
