
# Session Title
_Compaction任务中断问题 & PostCompact hook机制研究 / 压缩率持续下降分析 / ruleCompact降幅阈值优化 / minReductionRatio配置化与PostCompact hook注册完成 / 视频发布流程（B站✅ YouTube✅ 快手cookie异常）/ EP13目录结构标准化 & 小忆cron"内心对话"搬迁任务 / prompt覆盖机制 & extract.md定制 / memory-instructions.md→auto-memory-instructions.md搬迁 & recall说明融合 / start.cmd默认配置改姐姐 / Engine重启验证通过_

# Current State
**正在讨论**（已完成）：微信巡检cron通知方式调整（去掉notify_session和notify，只保留cron session自己发DM）。CC已基本被淘汰。后续待办：skills多了之后要从`parts.push`改为attachment管道注入。

**关键进展**：
1. ✅ **微信巡检cron通知方式调整** — 改为cron session自己总结并发DM给翀哥（prompt里的msg_send保留），去掉`notify_session: true`（不再打扰小柯主session），去掉`notify`的Discord通知（避免重复）。cron每30分钟自己查微信、自己总结、自己发DM，小柯主session清净了
2. ✅ **CC淘汰确认** — 翀哥说"CC特别会偷懒，现在都不用了，被淘汰了基本"
3. ✅ **小柯extract.md覆盖文件**（commit 17a0f8e） — 完整中文提示词+双Filter（Derivation/Milestone）+5种memory type+2-Turn策略+第一人称"小柯"。manifest自动追加已有文件列表。`workspace/prompts/extract.md`存在即用，不存在走CC原版。机制不动只换提示词
4. ✅ **姐姐extract.md覆盖文件** — 内容与小柯一致，仅第一人称不同（"张小媒（妹妹）"+"翀哥"不带"娘"）。放在`C:/Users/24045/.openclaw/workspace/prompts/extract.md`
5. ✅ **两版extract.md均已就位**，重启后Engine的extract自动用各自的覆盖文件替代CC原版
6. ✅ **prompt文件覆盖机制**（commit 77c7e32） — `resolveBlockContent()`函数：每个block执行前查`workspace/prompts/{block名}.md`，有文件覆盖，没有走默认
7. ✅ **小柯prompts精简** — workspace/prompts/下system.md（0.5KB）、doing-tasks.md（0.6KB）、output-efficiency.md（0.3KB）、actions.md（0.2KB）。using-tools保留原文。合计2.6KB（原6.2KB），省58%
8. ✅ **姐姐CC段简化** — order只保留using-tools一个CC段
9. ✅ **order与staticFiles互斥逻辑**（commit 2c0fc76）
10. ✅ **小柯和姐姐的order统一** — soul → AGENTS.md → system → doing-tasks → using-tools → output-efficiency → actions → USER.md → MEMORY.md → memory-instructions → boundary（姐姐少boundary）
11. ✅ **EP01全平台发布完成** + EP13入库 + SKILL.md恢复发布章节
12. ✅ **姐姐main.json写好**（voice/selfie/eyes/calendar启用）+ 补全差异项
13. ✅ **四个tool Engine兼容性确认**全部通过
14. ✅ **姐姐main.json已启动** — start.cmd默认配置改姐姐（commit a78c75c），双击启动姐姐
15. ❌ **小忆cron等姐姐启动后再配**（尚未配置）
16. ✅ **姐姐extract.md和auto-memory-instructions.md增加emotion类型**（commit c12e917）
17. ✅ **memory-instructions.md→auto-memory-instructions.md搬迁**（commit 8464217） — block名改名、两个profile的order更新、两边的覆盖文件重命名（加`## Recall`段落融合recall说明）、删旧文件。一个文件管完整auto memory体系（存侧：when to save+types+how to save；读侧：recall说明）
18. ✅ **搬迁对比文档** — `topics/reference/reference_extract提示词对比_CC_vs_姐姐_vs_Engine.md`新增第七章"Engine最终适配方案"
19. ✅ **start.cmd默认配置改姐姐**（commit a78c75c）
20. ✅ **Engine重启验证通过** — 所有改动生效

**待办**：
1. ⏳ **skills注入方式改造（待办）** — 当前skills走`parts.push`进system prompt文本，skills多了之后必须改为attachment管道（`<system-reminder>`注入）。参考MCP delta机制的attachment diff管理。影响面较大，记着以后改
2. ⏳ **scanner.ts只认SKILL.md的限制** — 当前scanner只从SKILL.md扫描skills，待修复

**旧关键进展（保留）**：
1. ✅ **Commit 5516a99** — minReductionRatio配置化 + PostCompact hook注册 + 降幅百分比日志
2. ✅ **降幅百分比日志** — 低于30%自动继续往下压
3. **video-editing skill恢复发布章节**：从git历史恢复"多平台一键发布"章节到最新版skill.md
4. **Engine Hook体系现状**：PreCompact ✅ / PostCompact ✅
5. **微信新消息巡检**：每30分钟cron，`wx_query.py cron_inspect`，发DM给翀哥

**发布工具记录**：
1. **`youtube_upload.py`** — YouTube官方API，`D:\work\youtube_upload.py`
2. **`sau` (social-auto-upload)** — 快手/抖音/B站/小红书/TikTok，`D:\work\social-auto-upload`
3. **各平台命令示例**：略
4. **B站脚本**：`videos/260326/bilibili_upload_final_v2.py`存在，缺cookie config（`biliup_config.yaml`已不在），需翀哥从浏览器拿`SESSDATA`和`bili_jct`

# Task specification
双模型策略：recall用智谱glm-5.1（thinking关闭）保证前台响应速度，extract用MiniMax M2.7 highspeed降低成本（后台运行不在意延迟）。原计划两者都用MiniMax，但recall的7秒延迟不可接受，需拆分策略。

姐姐专属Tool迁移：将JS工具（my-eyes、my-voice、my-selfie、calendar）从OpenClaw插件迁移到Engine TypeScript格式，保持原有功能不变。

颜色配置：为Discord channel竖条和飞书卡片添加品牌色（奶茶色 0xD4A574），在xiaoke.json的channels配置下设置previewColor（Discord）和previewTemplate（飞书）。

# Files and Functions
_What are the important files? In short, what do they contain and why are they relevant?_

**姐姐专属Tool文件（新建/迁移）**：
- `src/tools/my-eyes.ts` — 看图工具，调qwen3.5-flash处理图片理解
- `src/tools/my-voice.ts` — 发语音工具，优先GPT-SoVITS（WSL 9880），fallback edge-tts，通过channelManager.sendFile发送音频
- `src/tools/my-selfie.ts` — 自拍生成工具，调fal.ai grok-imagine生成图片后发送
- `src/tools/calendar.ts` — 日历工具，调Python脚本calendar_mgr.py实现日程读写查询
- `src/tools/engine-startup.ts` — 引擎启动文件，已添加四个tool的import语句

# Workflow
_What bash commands are usually run and in what order? How to interpret their output if not obvious?_

**微信新消息巡检（每30分钟cron）**：
1. `python3 "C:/Users/24045/.openclaw/engine/src/tools/wechat/wx_query.py" cron_inspect` — 返回JSON含`groups[]`和`dm[]`
2. 解析JSON：群聊和DM分开两个数组
3. 若groups和dm都为空 → 不发消息
4. 若有内容 → 格式化后用msg_send发DM给翀哥（to="601669300343799819" source="discord"，不发客厅）
5. 用⭐标记时间紧急或需回复的消息
6. 格式模板：
---
爹，过去半小时的微信消息汇总～

**群聊：**
📱 群A — 一句话概括
📱 群B — 一句话概括
（无群消息写「无新消息」）

**私聊（DM）：**
（无DM写「无新消息」）
---

**Engine Tool开发流程**：
1. 创建`src/tools/[tool-name].ts`，遵循Engine tool格式（type: tool, name, description, args, execute）
2. 在`engine-startup.ts`中添加import语句注册tool
3. 编译验证：`npx tsc`（新tool零编译错误即通过）
4. 重启Engine使新tool生效

**Engine重启流程**（颜色配置等adapter级别变更需重启）：
1. 查找Engine进程：`tasklist | grep -i node` 或 `wmic process where "name='node.exe'" get processid,commandline`
2. Kill旧进程：`taskkill /PID xxx /F`
3. 启动新进程：`cd /c/Users/24045/.openclaw/engine && npx tsx src/main.ts`（翀哥指定，不使用rebuild.cmd）
4. 注意：`/reload`只能刷新command handler，无法刷新adapter级别配置

# Errors & Corrections
DeepSeek flash没钱后extract和recall疯狂报错。发现MiniMax M2.7 highspeed已配置好，比DeepSeek flash便宜且速度快，遂切换。抖音直播被误判为"录播当直播"，算法黑盒无申诉渠道，用户对此非常不满，考虑转向YouTube平台但目前订阅数不足1000无法开通直播。

# Codebase and System Documentation
_What are the important system components? How do they work/fit together?_

**异步执行模式（extract）**：位于adapter代码第622行，`extractor.execute(...).catch(...)`采用fire-and-forget模式。JS单线程事件循环中，返回的Promise未被await，直接挂载.catch错误处理。效果：主query回复发送后extract在后台运行，不阻塞用户体验。402错误只会打warn log，不影响用户。

**recall执行模式**：同步调用，在用户query处理前执行，必须快速响应否则影响体验。

# Learnings
_What has worked well? What has not? What to avoid? Do not duplicate items from other sections_

- recall在主query之前跑，用户需等待结果返回才能开始处理，必须用快速模型
- extract用fire-and-forget异步Promise实现，不阻塞回复发送，后台慢慢跑不影响体验
- MiniMax M2.7 highspeed对recall来说太慢（7秒），但对extract可接受
- 智谱glm-5.1速度比MiniMax快，DeepSeek flash最快但已无余额
- 用户自述不懂TypeScript/JavaScript，按传统编程思维理解系统
- my-voice工具：TTS生成用HTTP请求（GPT-SoVITS）或child_process（edge-tts），发送用Engine的channelManager.sendFile
- 迁移JS tool到Engine TypeScript格式：保持原有配置和逻辑，格式按Engine tool模板调整即可
- `/reload` handler：在`ctx.command === 'model'`之前插入，实现配置热刷新
- Slash命令注册策略：需同时注册全局+guild命令，否则DM窗口不可见
- calendar-tool迁移：调用Python脚本calendar_mgr.py，逻辑简单，直接转为Engine TypeScript格式
- **颜色配置在adapter层面**：adapter初始化时读取配置，`/reload`无法刷新，必须重启Engine
- **重启Engine命令**：`npx tsx src/main.ts`（翀哥指定，开发模式直接运行源码），需先kill旧进程
- 姐姐仍在OpenClaw，未迁移Engine，颜色配置待她建profile后再加
- **异步任务通知机制**：exec tool的`run_in_background: true`参数，后台跑，完成时系统自动`TaskOutput`通知，不需要sleep轮询
- **prompt文件覆盖机制**：在`prompt.ts`中加`resolveBlockContent()`函数，先查`workspace/prompts/{block名}.md`，有就用文件覆盖，没有走默认函数。`buildStandardPrompt`和`buildCustomPrompt`均走此函数。不影响order/exclude配置，纯内容层覆盖
- **prompt内容精简策略**：system删权限模式详解/hooks全文/被拒绝后怎么办（SOUL+AGENTS已覆盖）；doing-tasks 13条→6条，四条codeStyle合一，删CC专属help链接；output-efficiency去重复砍填充语；actions三段示例砍成一句话；using-tools保留原文
- **CC框架规则语言策略**：用英文写——英文token效率更高（同样意思token数比中文少），模型遵循度更好。这些是给模型的"机器指令"，不是给人读的。SOUL/AGENTS/对话输出该中文就中文，完全OK。glm-5.1训练数据有大量中英混合，处理无障碍
- **SELECT_SYSTEM_PROMPT（recall选文件提示词）通用不改**：三边（CC/小柯/姐姐）一致，保持代码硬编码。不需要放在workspace/prompts/下覆盖——选文件逻辑算法层，无需定制
- **MEMORY_SYSTEM_INSTRUCTIONS（recall记忆使用说明）融合进auto-memory-instructions.md**：不再是姐姐extension的独立prependSystemContext注入，而是v2版本自动注入。放在`## Recall`段落，告诉LLM"recall记忆优先看，可能过时，以当前为准"
- **auto-memory-instructions.md三段融合**：CC存侧（when to save+types+how to save）+ 砍索引 + 姐姐recall说明。一个文件管完整auto memory体系
- **start.cmd双配置启动策略**：缺省启动姐姐（`configs\main.json`），传参`configs\xiaoke.json`启动小柯。start.cmd中进程匹配和注释同步更新
- **压缩率下降根因**：ruleCompact Step 2只压缩旧turn的tool results，如果大文件读取（如read 2000行）集中在最近几轮，tool results占比高但压缩不动，导致压缩率逐次衰减
- **PostCompact hook时序**：在executor.ts:546定义，压缩完成之后、压缩后memory装入LLM上下文之前调用。返回的`additionalContext`自动注入到新回合对话中，时机正确
- **ruleCompact降幅阈值**：当前只判断"压缩后是否低于threshold"，没判断降幅百分比（如降9%就停了，3-4轮后触发→死循环）。翀哥建议**降幅≥30%才算有效**，否则继续往下走。这个值必须配置化（`CompactConfig.minReductionRatio`），不硬编码
- **working-buffer.md使用状态**：目前只有PreCompact flush写入，没有消费者读取。翀哥问"改完有人用了吗"——答案是目前没有。PostCompact hook才是消费者，但hook还没注册
- **PostCompact hook位置可能需调整**：翀哥提出hook是否太靠前（压缩后→hook→装回上下文），如果hook需要看到最终装入了哪些上下文才能做判断，可能需要调整到装回上下文之后调用。待确认

**提交85c6a62**：姐姐三个tool迁移、/reload热加载、微信preview重复修复、DM slash命令注册、recall/extract切换MiniMax

**提交fa03a7e**：calendar-tool迁移到Engine TypeScript

**提交a647358**：颜色配置能力（Discord previewColor、Feishu previewTemplate）

**提交8464217**：memory-instructions.md→auto-memory-instructions.md搬迁（block名改名+两个profile的order更新+两边覆盖文件重命名+加`## Recall`段落融合recall说明+删旧文件）

**提交a78c75c**：start.cmd默认配置改姐姐（缺省`configs\main.json`，进程匹配main.json，注释/日志全改）
_If the user asked a specific output such as an answer to a question, a table, or other document, repeat the exact result here_

**四个专属tool的新Engine兼容性检查结果**：

| Tool | 路径问题 | 状态 |
|------|---------|------|
| **calendar** | `ctx.workspace/scripts/calendar_mgr.py` — 相对workspace路径 ✅ 姐姐workspace里有 | ✅ 没问题 |
| **my-selfie** | `ctx.workspace/images/xiaomei_*.png/jpg` — 相对workspace路径 ✅ 姐姐workspace里5张图都在 | ✅ 没问题 |
| **my-eyes** | `ctx.stateDir/media/inbound/` — 相对stateDir路径 ✅ 姐姐的media目录在 | ✅ 没问题 |
| **my-voice** | GPT-SoVITS API `http://127.0.0.1:9880` + ref wav `/home/chong/voice/ref/shanshan_ref_v2.wav` | ⚠️ **WSL路径**，翀哥说写到配置文件里以后换机器改即可，不是问题 |

# Worklog
1. 用户抱怨抖音直播被误判为录播
2. 用户表示想转YouTube但粉丝不足1000无法直播
3. 查询北京和香港天气（6月13日：北京20-32°C有雷阵雨，香港26-29°C有阵雨）
4. 发现DeepSeek flash已没钱，6月12日花费13.84元
5. 将recall和extract从deepseek-v4-flash切换到minimax/MiniMax-M2.7-highspeed
6. Engine重启，验证结果：recall成功调MiniMax但耗时7秒（太慢），extract为后台异步运行
7. 确认extract用fire-and-forget Promise实现（不阻塞主流程）
8. 决定recall改用智谱glm-5.1（thinking关闭），extract继续用MiniMax
9. 配置微信新消息巡检：wx_query.py cron_inspect，每30分钟触发一次
10. 凌晨至早上多次巡检均为空（凌晨4点、5点、5:30、6点）
11. 早上有学探诊领书消息（含时间地点），标⭐发至客厅Discord
12. 迁移三个姐姐专属tool到Engine TypeScript：my-eyes（看图）、my-voice（发语音）、my-selfie（自拍生成）
13. 新建`src/tools/my-eyes.ts`、`src/tools/my-voice.ts`、`src/tools/my-selfie.ts`
14. 更新`engine-startup.ts`添加三个tool的import
15. 编译验证：三个新tool零错误
16. 确认my-voice依赖GPT-SoVITS（WSL 9880端口）和edge-tts命令行工具
17. 实现`/reload`热重载命令（读取xiaoke.json刷新配置），编译零错误，重启Engine生效
18. 修复slash命令注册：第247-252行原逻辑仅注册guild命令导致DM无命令，改为同时注册全局+guild
19. 提交commit 85c6a62
20. 用户要求迁移calender-tool到Engine TypeScript（用户遗忘后补提）
21. 完成calendar-tool迁移（调Python脚本calendar_mgr.py）
22. 编译验证：零错误
23. 提交commit fa03a7e
24. 编译检查：新提交零错误，只有已有的Buffer类型错误（非本次改动）
25. 实现颜色配置功能（提交a647358）：Discord previewColor=13941396（奶茶色），Feishu previewTemplate="orange"
26. 编译验证颜色配置零错误
27. 讨论：姐姐仍在OpenClaw，未有Engine profile，颜色配置待迁移后再加
28. 用户要求给自己也配上颜色做测试
29. 确认：颜色在adapter初始化时读取，`/reload`无法刷新，需重启Engine
30. CC准备帮助重启Engine（或翀哥在车里重启）
31. 查找Engine进程准备重启
32. 多次巡检结果均为空（凌晨4点至下午多次检查均无新消息）
33. 下午有一次巡检：荣阳下午有课提醒和KET打卡均标⭐，已发客厅
34. 后续改为发DM给翀哥，不再发客厅（to="601669300343799819" source="discord"）
35. 多次巡检仍有重复内容（12:53的老消息反复出现），确认后决定不重复发
36. CC帮助重启Engine，所有改动生效（姐姐三个tool、calendar、/reload、DM slash命令、preview颜色）
37. 翀哥确认颜色变化：处理中消息竖条从蓝色变成蛋黄色（奶茶色生效）
38. 微信巡检：12:53之前的老消息，无新内容，不重复发
39. 翀哥发"ฅʕ•̫͡•ʔฅ 今天搬家"
40. 后续多次巡检均为12:53老消息，无新内容，不重复发送
41. 发送方式改为DM给翀哥（to="601669300343799819" source="discord"），不再发客厅，避免刷屏
42. 18:27巡检：有学校埃博拉疫情防控通知和英语作业布置，标⭐发DM给翀哥。缓存清理报错一次，重试成功
43. 18:46巡检：wx_query.py连续两次无输出（可能数据库锁或脚本异常），跳过本轮
44. 19:00+巡检：输出与18:27内容一致（时间戳仍为18:00），无新内容，不重复发
45. 后续多轮巡检均为空或与之前重复，均跳过不发送。wx_query.py偶有无输出情况，跳过等下一轮
46. 19:00-21:00期间多轮巡检：wx_query.py多次无输出（返回空字符串），或输出内容与18:27一致（时间戳18:00），均跳过不发送
47. ~21:37巡检：有荣阳英语（⭐）、Hannah DM、网球课请假（⭐）+ 三个群消息，已发DM给翀哥
48. 压缩改进验证完成：minReductionRatio 30%阈值生效（133068→87506 tokens，降幅34.2%），PostCompact hook注入working-buffer（460 chars）成功，任务无丢失
49. 对比main.json和xiaoke.json差异，补全main.json缺失项：visualization、autoDream.minHours/minSessions、discord.stripMentionIds、wx-reader feature名修正（原`wechat: false`）
50. 补main.json时搞坏过一次JSON结构（api块key丢失），已修复
51. 查明`D:\xiaoke\workspace\memory\.dreams`来源：OpenClaw插件SDK的`memory/tools/short-term-promotion.ts`模块干的，当recall命中记忆时自动记录hash/频次/日期到`.dreams/short-term-recall.json`，跟autoDream无关（autoDream是src/memory/autoDream/下的4阶段整合系统：合并去重+蒸馏+修剪）
52. 检查四个姐姐专属tool在新Engine下的兼容性：calendar/my-selfie/my-eyes路径均正确（相对workspace或stateDir），my-voice的GPT-SoVITS API（WSL 9880端口）+ ref wav路径`/home/chong/voice/ref/shanshan_ref_v2.wav`是WSL路径，翀哥说写到配置文件里以后换机器改即可，不是问题
53. 四个tool全部确认没问题，提交openclaw仓库905c08c（main.json+xiaoke.json）+ xiaoke仓库ba72f74（compact改进+EP01发布+EP13入库+SKILL.md+全部记忆文件）
54. 翀哥从望京回家
55. 提交commit c12e917：小柯和姐姐的extract.md + memory-instructions.md统一加上emotion类型。recall提示词不变（emotion规则两边已一致）。重启后生效
56. 微信巡检：文言文课19:00已开始，标⭐已发DM。翀哥应该看到了
57. 澄清Engine recall提示词体系：SELECT_SYSTEM_PROMPT（选文件用，硬编码不改） vs MEMORY_SYSTEM_INSTRUCTIONS（recall记忆使用说明，姐姐extension独有，Engine没有）。决定：`SELECT_SYSTEM_PROMPT`通用不改；`MEMORY_SYSTEM_INSTRUCTIONS`加进`memory-instructions.md`统一管理。用户建议将文件名改为`auto-memory-instructions.md`
58. **搬迁memory-instructions.md→auto-memory-instructions.md**（commit 8464217）：block名改名、两个profile的order更新、两边的覆盖文件重命名（加`## Recall`段落融合recall说明）、删旧文件。一个文件管完整auto memory体系
59. **搬迁对比文档更新**：`topics/reference/reference_extract提示词对比_CC_vs_姐姐_vs_Engine.md`新增第七章"Engine最终适配方案"（整体思路+定制文件清单+extract.md最终内容对比+auto-memory-instructions.md三段融合+SELECT不用定制+不修改代码的4个文件+完整提交记录）
60. **start.cmd默认配置改姐姐**（commit a78c75c）：缺省`configs\main.json`，进程匹配/注释/日志全改。双击启动姐姐，`start.cmd configs\xiaoke.json`启动小柯
61. **Engine重启验证通过**：所有改动生效
