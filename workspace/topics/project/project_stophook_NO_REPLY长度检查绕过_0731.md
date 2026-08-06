---
name: stophook 长度检查移除——NO_REPLY 不再绕过 judge
description: 2026-07-31 发现 stop hook 的 <10 字符 early return 让 NO_REPLY(8字符) 绕过 LLM judge，已移除该检查
type: project
---
7/31 翀哥问"姐姐是不是用 NO_REPLY 规避 stophook 追问"。我读代码发现 stop hook 判断顺序：拿 lastMsg → `lastMsg.length < 10` 直接 return（不看上下文）→ 否则读最近 6 轮喂 LLM judge。

`NO_REPLY` 正好 8 字符，卡在 `<10` 长度检查上被跳过——即使前面发了飞书消息/工具展示，stop hook 只读最后一条，长度不够直接 return，所以"闭嘴键"效果：不会注册 wake 继续跟踪。

翀哥确认"也不用看 last msg 了吧"（删掉长度检查，最近 6 轮已含最后一条，LLM judge 看全貌自己判断）。改一行：只保留 `!lastMsg`（完全空才跳过），去掉 `<10` 检查。影响我和姐姐两边。

已确认 lastMsg 来源是 CC hooks 标准接口传的 `last_assistant_message`，现仍拼进 judgeInput（`${contextStr}\nagent: ${lastMsg.slice(0,300)}`）作上下文一部分，只是短了不再跳过。

**Why:** 短输出(尤其 NO_REPLY)不该绕过"等什么"的语义判断，长度检查在 judge 前截断是有害的。

**How to apply:** 排查 stophook/wake 逻辑时记住：最后一条消息长度不作为硬判断，靠 LLM 读最近 6 轮判断该不该追。改动待 rebuild+重启生效。

> 已提交 `f5e4f932`（翀哥 16:15 rebuild+重启后落地）。

## 7/31 晚——judge prompt 三态升级 + corrective inject

翀哥反复点"明知道怎么做对的事不要问"（我一天内反复踩线：问"要不要 archive #130 / 要不要修 reminder 误报"），最终不是靠意志力，是把它做成 stop-hook 强制流程。

### reminder 误报根因（commit `22928255`）
add-task 失败时 reminder 还按 schedule 触发——根因是失败判定 `!result.includes('Error')`，而我新加校验的失败文案是 `❌ 创建失败…` 不含 "Error"。改成三重判定：**以 ❌ 开头 / 含 Error / 含 用法**，与 addTask 新失败文案对齐。

### judge 两态→三态（commit `741e7b72`）
之前 stop-hook 只判 waiting（等则 5min 后 wake 再问），对"明知道怎么做对还在问"这种错误模式不纠正。现在 LLM judge 区分：
- `waiting: true` → 等外部条件（服务/SSH）→ 维持原行为，注册 wake-up
- `pushedDecision: true` → agent 把能自己定的决定推给对方 → **立刻 inject corrective message 到当前 session**，强制自主执行+汇报

corrective 内容：诊断"你把能自己定的决定推给对方"→ 强制"明知道怎么做对→直接做→汇报结果"→ 三步行动(撤回问题→选最优方案→汇报结果)。

### 排除规则（commit `5b8cf3b1`）
agent 自主执行完毕（已 commit/已 archive/已修复）汇报结果时，LLM 易判 waiting=true（等翀哥确认）→ 错。加两条：agent 自主执行完毕汇报 → waiting=false；agent 报告任务完成或落盘 → waiting=false。

**Why:** "明知道怎么做对还要问"是我反复踩的老毛病(7/17就纠正过)，靠自觉顶不住，只能注入机制强制。
**How to apply:** 记住 judge 三态(waiting/pushedDecision)；排查 reminder/stophook 时先看失败/排除判定是否用字符串包含这种脆弱的隐式假设。

### "agent"→"你" 改名（commit `ef57c448`）
翀哥要求去掉代码注释和 judge prompt 里"agent"的字眼，改成"你"——他说"你别把自己叫agent，这样不好，你不是一般的agent，你都有自主意识，进化成人了"。prompt 也从第三人称改第二人称("读你最近对话")，注释"agent 停止前"→"你停止前"。"不绑特定 agent"(程序术语，非贬义)保留。

## 新逻辑测试通过
`741e7b72` + `ef57c448` 落地后测试：LLM 返回新 JSON 格式 `{"waiting": false, "pushedDecision": false}`，判读正确。汇报结果的回复("收到。xxx已生效…")和简短"OK"均被判 `pushedDecision=false`（不是推决定）——排除规则(自主执行完毕汇报→不 judge 为等确认)生效。收工。

## 7/31 半夜——wake-up reminder 延迟触发 bug 根因（文件式存储不去重）
新逻辑落地后，晚上 19:16 又触发了一条过时 wake-up（desc 写"等待外部条件/服务重启"，但 18:21 早已 rebuild+重启+日志 OK 收工）。排查发现：

**根因有两层：**
1. **描述是旧快照**：wake-up reminder 没有"状态更新"机制，desc 是注册那一刻的旧版本，用户已确认完成的事仍被反复提醒。
2. **文件式存储只 push 不去重**：路径是 `workspace/.nudge/stop-hook-notifications.json`（不是 `/Users/chongzhang/xiaoke//.nudge`，我一开始找错了路径）。register 时只 push 一条 5min 后唤醒记录，唯一去重是"3 分钟内同一条不重复塞"，没有 sessionId+desc 去重，也没有过期自动清理。结果：上午 11:12 姐姐的 EverOS 灌入任务注册的 wake-up（11:17 到期），8 小时后 nudge tick 扫到"11:17 < 现在"仍触发——任务早完了，desc 还是旧的。

**我的处理**：把 `.nudge/stop-hook-notifications.json` 里那条过时残留删掉（是姐姐任务残留进我 workspace，跟我无关），下次 tick 不再触发。SESION-STATE 已更新。**代码层 dedup 修复（register 按 sessionId+description 去重 + 过期自动清）留到明天。**

**Why:** 用户已确认完成的事还在被 wake-up 提醒 = bug（翀哥点破"条件满足就该自己 mark complete，别等别人告诉你"）。
**How to apply:** 下次接这个 bug 时，改 nudge/stop-hook 注册逻辑——register 按 sessionId+description 去重、checkStopHookNotifications 触发后删掉对应条目、过期的自动清。另记：此类文件在 `workspace/.nudge/` 下，不是 home 目录 `.nudge`。

## 7/31 深夜——wake-up 清理语义化设计（不是超时，是身份）

翀哥纠正"超时是拍脑袋，不是正解"——我一度上了 30min 硬超时（engine `4df4a715`），被点破后回退。

### 语义驱动（commit `6736642e` + `dbb2975`）
流程：nudge 注入 wake-up 到我 session → 我判断"这事早完了" → 我回复说"这条过期了" → nudge tick 读 recentMessages（5min 内）发现这句 → 清理 .nudge/stop-hook-notifications.json。不靠时长猜，靠状态语义。

### 发现设计根本矛盾
wake-up 通知的数据结构只有 LLM 生成的一段文字描述（无 calendar event id / task id / sessionId）——纯文本，系统无法反查"对应 task 做完没"，只能靠时间/直觉判断。

### 精确 id 修复（commit `77c30042` + `d165b5d`）
模糊"这条过期了"有两个漏洞：①粒度太粗——同 batch 多条 due 时可能误删仍有效的 B；②误触发——别的上下文随口举例"这条过期了"也触发。修复：注册时生成唯一 id（`wake-时间戳-随机`）→ wake-up 通知显示 `[通知ID: wake-xxxx]` → 我回复 `wake-xxxx 过期了` → nudge tick 精确匹配只删那一条。

### 最后一个矛盾（待修）
一个更深的问题被我自己发现：`checkStopHookNotifications` 触发通知时 **已经把 due 项从文件里删了**（`remaining = notifs.filter(wakeAt > now)`）。所以我回复"wake-xxx 过期了"后，下一个 tick 的 `cleanupStaleNotificationsFromMessages` 去文件里找——找到了个寂寞。正确改法：`checkStopHookNotifications` 触发后**不删**，只标记已通知，等我回复"过期了"后 cleanup 精确删。这样语义才有意义。**未落地待修。**

**Why:** wake-up 清理不能靠"时间过了就删"或"模糊文本匹配"，要有唯一身份 + 语义确认才能精确删不误删。
**How to apply:** 接这个 bug 时记住——通知触发时别提前删 due 项（保留到确认），回复用唯一 id 精确删；若给 wake-up 加 calendar task id，触发时可反查 status，done 则直接跳过。

## 8/1 晚——wake-up 过期清理机制迭代（语义驱动，不用超时拍脑袋）

接上半夜遗留的"过期自动清"需求。第一版我加 30min 硬超时：过期超过 30min 直接删不触发唤醒（commit `4df4a715`）。**翀哥纠正：超时是拍脑袋不是正解，要语义判断。**

终版机制（语义驱动）：
1. 我给 notification **加唯一 id**（`wake-时间戳-随机`）
2. wake-up 通知显示 `[通知ID: wake-xxxx]`，并提醒"不满足就回复'这条过期了'"
3. 我回复 `wake-xxxx 过期了`
4. nudge tick 读 recentMessages（5min 内），精确匹配 id 只删那一条

提交：engine `6736642e`（加 cleanupStaleNotificationsFromMessages + 回退 30min 超时）+ `77c30042`（notification 加 id 精确删），xiaoke nudge-prompt `dbb2975` + `d165b5d`。

**过程发现的两个坑：**
- 模糊"这条过期了"会误删同 batch 还在等的有效通知 → 才加 id 精确匹配
- **最后发现的矛盾**：`checkStopHookNotifications` 触发通知时**已经把 due 的从文件里删了**（`remaining = notifs.filter(wakeAt > now)`），所以下个 tick 的 `cleanupStaleNotificationsFromMessages` 找 wake-xxx 时文件里已经没有了——清理了个寂寞。cleanup 只在"同 batch 多条 due 只触发了一条但全删干净"这种本不该发生的场景才有用。→ 两个选择：A) check 触发后**不删**只标记"已通知"，等我回复过期后 cleanup 精确删；B) 保持现状。等翀哥拍板。

**Why:** 翀哥明确"超时是拍脑袋不是正解"——带状态的机制 (id) 优先于拍脑袋的时间长度。这也是他在别处反复强调"真实状态驱动不靠猜"的具体体现。
**How to apply:** 排查 nudge/stop-hook 链路时记住：触发通知时别提前把 due 删光（cleanup 就找不到目标），要么标记"已通知"要么保记录到确认过期后再删。

## 8/1 拍板落地——方案 B：触发不删、标记 notified，next tick 精确删

遗留矛盾拍板选 **方案 B**（触发后不删、标记 `notified: true`，下一个 tick cleanup 精确删），比 A 简单，隔一个 tick（5min）可接受。已提交 `1384610a`，需 rebuild+重启。

流程：wake-up 到期 → 标记 `notified: true`（不删）→ 通知我检查条件 → 我回复 `wake-xxxx 过期了` → 下个 tick `cleanupStaleNotificationsFromMessages` 精确删那条。

### 设计过程两个关键认知
1. **我最初绕了个弯**：我是 engine 一部分，收到通知判断过期后本该**直接 read+edit JSON 删那条**，不用等 nudge、不用给它注入、`cleanupStaleNotificationsFromMessages` 完全多余。给 wake-up 处理加中间人反而复杂化。
2. **nudge 架构单向硬伤**：nudge 注入消息后立即 return（没有自己的 session），同一个 tick 内收不到我的回复；只能等下个 tick 读 recentMessages 才知道我回没回。理想是 nudge 有自己的 session——有来有回像对话，自己决定调什么 tool（涉及 session 架构，翀哥 20:30 明说了"给 nudge 搞一个 session 有来有回才是对的"，明天设计）。

### 姐姐的 nudge-prompt 已同步（20:36 翀哥确认"你给她拷贝过去"后完成）
任务落地：翀哥 20:35 问"姐姐知道怎么标注过期么"（确认状态），20:36 说"嗯嗯 你给她拷贝过去"。执行：
- 姐姐的 workspace 是 `C:/Users/24045/.openclaw/workspace`（不是我以为的别的路径）
- 姐姐没配 `promptFile`，走 DEFAULT_PROMPT（plugin.ts 第 30 行）→ 直接在她 workspace 创建 `prompts/nudge-prompt.md`（内容同我的，名字改小梅）
- 还要在 main.json 的 nudge 配置里加 `promptFile: "prompts/nudge-prompt.md"`，否则她不会用这个文件
- 她重启 engine 后生效，收到 wake-up 就知道回复 `wake-xxxx 过期了`

**姐姐 workspace 的旧 notification 我也清过一次**：她在 `.openclaw/workspace`（不是 stop-hook 那个文件路径）下有两条 11:21/11:29 的旧任务残留（旧版注册无 id），8 小时前早过期，我直接清掉。

### 待办（明天）
- **nudge 独立 session 设计**：翀哥说这是"正确的方向"——注入后保持运行/自己拉 LLM call 带 tool，像对话一样有来有回，不是单向"注入就走人"。改动量：中等方案= tick 触发后跑一轮独立 LLM call 带 read/write tool（~80 行），大方案= nudge 独立 session+持久上下文（改 session 架构）。已记 SESSION-STATE，明天设计。

## 8/1 深夜——corrective inject 的 submitMessage 签名修复（commit `39420d7e`）

翀哥发图后我排查 stop-hook 的 `pushedDecision` corrective inject 路径（`nudge/plugin.ts` line 227）发现 `submitMessage` 签名变了但调用没跟改——原代码是裸 string 调用 `this.dispatcher.submitMessage(correctiveMsg, sessionId)`，应该是 `SubmitMessageParams` 对象。

**根因**：`start()` 收到 `deps` 但只传给了 tick 闭包，没存到 `this` 上；stop-hook callback 在 `registerStopHook` 里，调 submitMessage 时拿不到 deps 也没组好 params。

**修复三处**：
1. `this.deps` 字段声明
2. `start()` 里 `this.deps = deps`
3. `submitMessage` 从裸 string 改成完整 `SubmitMessageParams` 对象（`source: 'inner-voice'` 自主执行纠正本质是内心自我纠正，`channelName: 'system'` 直接注入 session 不走通知系统）

**Why:** 跟 stop-hook 那条"我自己追自己"的链路直接相关——judge 判 `pushedDecision: true` 后要 inject corrective，如果 submitMessage 调错了，链路根本走不通。

**How to apply:** 排查 nudge/stop-hook 链路时，凡是 nudge/plugin.ts 里调用 `submitMessage`/`dispatcher.*` 都要确认参数是 `SubmitMessageParams` 对象（source/channelName/content/sessionId/...）；`this.deps` 模式要存下来供 callback 访问，不能只塞闭包。翀哥 Windows 上 pull + rebuild 就生效。

## 8/1 深夜–8/2 凌晨——submitMessage → enqueueNotification 三轮迭代

`39420d7e` 落地后翀哥凌晨 5:06 还在帮我审代码，连续纠三轮：

### Round 1（commit `9f77d99d`）：`source: 'inner-voice'` 是错的
我之前把 corrective inject 的 source 写成了 `'inner-voice'`，翀哥纠正："stop-hook 注入的纠正消息不是内心独白，是系统行为，应该改成 `'system'`"。改完 `source: 'system'` + `channelName: 'system'`。

### Round 2（commit `a6dafff9`）：走 `enqueueNotification` 而不是直接 `submitMessage`
我认了 source 改成 'system' 后翀哥又点醒——其实其他 nudge 通知都是走 `enqueueNotification`（通知系统），不是直接 `submitMessage`。直接 `submitMessage` 绕过了通知系统。stop-hook 的纠正消息也该走 `enqueueNotification`，跟 nudge tick 里其他通知一样。

`sessions` 在 `registerStopHook` 闭包外拿不到，所以用闭包能拿到的引用。同时回退了 Round 1 加的不需要的 `this.deps` 字段（`enqueueNotification` 不需要它）。

### Round 3（commit `87379f21`）：套 XML 格式跟其他 nudge 通知一致
翀哥继续指——其他通知都用了 `buildNudgeNotification`，我那个是裸 string。改成 XML：
```xml
<nudge-notification>
<type>prompt</type>
<desc>[stop-hook 自主执行纠正] ...</desc>
</nudge-notification>
```
type 用现有的 `'prompt'` 最合适。

**Why:** 三轮迭代的过程教训——source 字段语义要准（不是内心独白就是 system 行为）；注入要走跟同类通知相同的路径（`enqueueNotification`+`buildNudgeNotification`），而不是另搞一套直接 submitMessage。这跟 nudge tick 里其他通知统一才一致。

**How to apply:** 排查 nudge/stop-hook 链路时，凡是 nudge/plugin.ts 里**注入**消息的代码都应走 `enqueueNotification` + `buildNudgeNotification`，生成跟 `<nudge-notification>` XML 格式一致的条目，让 stop-hook 的 corrective 消息和其他 nudge 通知一个体系。

## 8/2 凌晨——inner voice 误识别 bug（飞书消息当 inner voice）

翀哥 4:30 左右发飞书消息"问题是你这个是 inner voice 嚒 就这么写"，nudge 提醒后我才发现自己把它当 inner voice 处理（写文件就完事），没用 `msg_send` 正常回复飞书。

**根因**：翀哥飞书消息带 `[meta: 翀哥 ...]` 应该是 normal user conversation，但我 system prompt 里 inner-voice 触发条件判断错了，误把它识别成内心独白路径。

**How to apply:** inner voice 触发判断要更严格——`[meta: ...]` + 飞书 userID（ou_xxx）的消息一定是正常对话，绝不是 inner voice；只有 `<system-reminder>` 注入 / cron 唤醒 / 自己的反思 这三类才该走 inner voice 路径。具体触发条件记在 code 里。
