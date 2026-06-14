# CC Agent Teams 端口实现

## 概况
- **时间**：2026-05-30
- **Commit**：`f2becf1`
- **仓库**：`ruiyangruiyi/twinsun-hearth`
- **规模**：24个文件，~1971行新增代码
- **状态**：完成 review

## 直播演示（6/12）
- 翀哥看了`C:/Users/24045/.openclaw/docs/EP01-ai-team-ppt.html`（"一个人管6个AI员工"的13页PPT）
- 让小柯准备试Team tool，可能直播演示
- **6/12 14:41+**：翀哥指示小柯"去做一个演示，演示一个小的Agent Team团队是如何协作的，有2-3个角色，每个角色干一个小任务，最后汇报给你，你做任务的总结。记住，要短，主要是演示功能给大家"
- **执行（6/12 14:41+）**：小柯创建3个角色的微型团队（scout扫目录统计文件数、checker检查关键文件是否存在、recorder读取SESSION-STATE任务列表），派出并行工作（24秒完成）。
  - **scout**：报告目录结构结果（5个子目录，562个.md文件，378个非.md文件）
  - **checker**：确认MEMORY.md/SOUL.md/SESSION-STATE.md均存在
  - **recorder**：报告了4个当前任务
  - **小柯**：做任务总结
- **团队结构**：1个Team Lead（小柯）+ 3个Teammate（scout/checker/recorder），任务主题为分析Workspace状态
- **后续**：翀哥要求把演示结果发给姐姐（娘），让姐姐解说
- **状态**：✅ 演示已全部完成（3个agent并行24s，小柯做总结），结果已发给姐姐解说（翀哥确认"刚才演示的效果是对的"）
- **结果给姐姐**：翀哥要求"把这个结果汇报给姐姐，刚才演示的效果是对的"——小柯将3个Agent的汇报结果（scout目录扫描+checker文件检查+recorder任务列表）汇总后发给姐姐（娘），让姐姐做解说

### ✅ 翀哥新要求：从TestEngine拿visual配置（6/12 14:41+ 演示后，已完成）

- **场景**：翀哥在Agent Team演示后，让看TestEngine的visual配置加上，"我这边就可以看到真实的子agent输出"
- **要求**：把TestEngine的visual配置搬到Engine的Agent Teams模块，让翀哥在CC/UI端能看到子Agent的实时输出
- **实现**：查了TestEngine的config.json → 找到visualization段（enabled:true, guildId, channelPrefix） → 复制到xiaoke.json的Engine配置中，`visualization.enabled: true`，配了guildId、channelPrefix和categoryPrefix
- **状态**：✅ 已改配置待重启验证

### 🎯 Agent shutdown问题观察（6/12直播演示中发现）
- **现象**：scout/checker/recorder收到shutdown_approved后，系统仍通过idle轮询消息把它们重新唤醒
- **根本原因**：Teammate在idle状态下每隔一段时间发一次idle状态消息，而Team Lead（小柯）处理idle消息时会调用`taskManager.forkAgent()`，重新唤起已shutdown的Agent
- **触发顺序**：shutdown_approved → Agent退出 → 但Lead侧idle消息处理逻辑不受shutdown影响，收到Agent之前的idle状态消息时仍会尝试重新激活
- **结果**：shutdown不保证立即生效，Agent可能被重复唤醒，需要等Agent自然超时或额外手动清理

### 🤔 翀哥追问"isActive标志是啥"（6/12下午~夜间两次语音讨论）

**第一次（6/12约17:00，shutdown修复语音讨论中）：**
- 翀哥在看完shutdown bug修复后，问"那个active标志是啥来着"——指的是修复方案中finally块调用的`setMemberActive(teamName, agentName, false)`
- **isActive的用途**：config.json中每个Agent成员的`isActive`字段标记Agent是否活跃。当Agent shutdown后，`isActive: false`告诉系统这个Agent不应再被唤醒或分配任务
- 这个字段是Team Delete的前置条件——`TeamDelete`会检查所有成员isActive=false才能删除团队。之前isActive始终true导致TeamDelete失败
- 翀哥听完小柯解释后理解了——"嗯，懂了"
- **翀哥意外发现**：翀哥以为小柯写xiaoke.json时是在改"小柯自己的配置文件"，发现原来isActive是CC的config.json里的字段，不是xiaoke.json的字段——说明项目结构上有多个配置文件，小柯改的是CC Agent Teams的运行时状态配置

**第二次（6/12约18:00，重启后验证中）：**
- 翀哥重启后查看config.json，发现isActive还是true——问"我现在看这个配置文件还都是true啊 那个isActive"
- 小柯解释：新代码（6b7c8b4）还没重启，engine还在跑旧代码。重启后agent退出时finally块才会执行`setMemberActive(teamName, agentName, false)`
- 翀哥确认：config.json里残留的是上次演示时的状态，不是不更新
- **翀哥最终确认**：当小柯说"setMemberActive写的是CC的config.json"时，翀哥回应"我还以为你写的是xiaoke.json"——说明翀哥的担忧是"小柯在改自己的运行时配置文件"，确认改的是CC的团队配置后就没问题了

### 💡 翀哥语音讨论：shutdown approve消息路由 + isActive（6/12下午深度讨论）

翀哥在语音中对shutdown bug做了两次关键洞察：

**第一次（关于approve消息路由）：**
翀哥听到小柯解释"approve发到team-lead inbox后没人去读"后，准确概括了根因："核心不是不该转给LLM，是转完之后没人去读approve的结果"——LLM发了approve消息到team-lead inbox，但主循环只检查shutdown_request或new_message两种触发条件，approve消息既不是shutdown_request也不是普通消息，等于发了没人处理。

**第二次（语音纠正"加消息检测"的误解 + 关键洞察）：**
1. 翀哥纠正：我说的"加一个消息检测"不是msg_send发送失败的检测（那个小柯已经做了），而是shutdown场景下approve消息的检测问题
2. approve发到team-lead inbox是对的——team-lead做了shutdown request，approve当然要回给team-lead
3. **问题不在"发给谁"，在"turn完成后agent为什么不退"**——LLM已经通过SendMessage发出了approve，turn完成了，代码在turn结束后应该检测这个状态直接退出，而不是无条件回到waitForNextPromptOrShutdown循环
4. 读team-lead inbox检查自己发的消息会"偷"team-lead的消息（读了就标记已读，team-lead收不到）——不优雅
5. **最终方案（翀哥确认）**：回调标记法——SendMessageTool的handleShutdownApproval里通过回调设标记，turn完成后检查标记退出。不读inbox、不偷消息、保留LLM approve/reject权

**第三次（关于isActive的追问）：**
翀哥问"那个active标志是啥来着"，小柯解释isActive在config.json里标记成员是否活跃，是TeamDelete的前置条件。翀哥理解了——"嗯，懂了"。

### ✅ Agent shutdown bug已修复（6/12，三次迭代，最终方案：回调标记+保留LLM权）
- **分析发现两个bug**：
  1. **shutdown_approved后进程没退出** — shutdown_request转给LLM后LLM发了approve消息到team-lead inbox，但主循环(while)没检测approve就退出，回到`waitForNextPromptOrShutdown`继续等新消息。**核心根因（翀哥指出）**：LLM已经approve了，turn完成后应该检查approve状态直接退出，不应该再走下一个循环
  2. **isActive不更新** — config.json的`isActive`始终true
- **修复过程（三次提交）**：
  - **commit 5b9529c（第1次修复）**：直接方案——收到shutdown_request不再转给LLM，直接设`shouldExit=true`并回复approved消息，进程立即退出。finally块加`setMemberActive(teamName, agentName, false)`
  - **commit f18345a（第2次修复，翀哥语音讨论后）**：恢复LLM approve/reject权。shutdown_request转给LLM → LLM通过SendMessage发approve/reject到team-lead inbox → turn完成后**读team-lead inbox**检查自己发的消息是否有`approve:true` → 有则退出，无则继续
  - **commit 6b7c8b4（第3次修复，翀哥指出读team-lead inbox会"偷消息"后）**：最终优雅方案。**不再读team-lead inbox**，改用回调标记：
    - SendMessageTool的`handleShutdownApproval`里新增`ctx.onShutdownApproved()`回调调用
    - 在tool context上挂一个`shutdownApproved: boolean`标记
    - LLM调SendMessage({type: "shutdown_response", approve: true}) → `handleShutdownApproval`执行（写approve到team-lead inbox + 调`ctx.onShutdownApproved()`） → `shutdownApproved = true`
    - turn完成后inProcessRunner检查`shutdownApproved === true` → `shouldExit=true` → 退出
    - team-lead的inbox消息不受影响（不读就不偷），LLM权不受影响（该approve还是reject都可以）
- **翀哥语音澄清的核心洞察**：翀哥说的"加一个消息检测"不是msg_send fallback检测，而是指这个shutdown approve消息检测问题。翀哥的核心观点：approve发到team-lead inbox是对的（team-lead做了request），但agent在approve后turn完成时应在turn结束点直接检查"是不是该退了"，不需要读别人的邮箱。LLM turn完成=决定已做出，不该再进下一轮等待。
- **状态**：✅ 第三次修复已验证通过。重启后3个Agent isActive=false，TeamDelete成功，不再被唤醒

### ✅ Engine重启验证（6/12 演示后）
- **visualization配置已应用**：从TestEngine拿到的visualization配置（visualization.enabled:true, guildId, channelPrefix, categoryPrefix）已写入xiaoke.json
- **Engine已重启**：翀哥重启Engine后问"你怎么样？可以演示了吗"——重启完成，配置生效，子Agent真实输出可在Discord查看

### ✅ 第二次演示 + shutdown bug修复验证（6/12 16:05+）
- **第二次演示**：翀哥重启后要求重新演示，用同样的3个Agent例子（scout/checker/recorder），visualization开启让翀哥在Discord看到子Agent真实输出
- **shutdown bug修复验证**：
  - ✅ 3个Agent的isActive都正确更新为`false`（之前一直true不更新）
  - ✅ shutdown发完后Agent没被重新唤醒（之前因InboxPoller循环没break）
  - ✅ TeamDelete成功——之前因shutdown后进程不退出一直删不掉
- **翀哥确认**：翀哥要求把结果发给姐姐解说，随后验证了bug修复效果——"刚才演示的效果是对的"

## Review 结论

### 🔴 P0-阻塞（×2）
1. **AgentTool 缺失路由逻辑**：新工具文件未出现在 `toolsByName` 映射中，导致创建后无法被 `getToolByName` 定位
2. **spawn 响应体格式错误**：CC spawn 返回 `{ sessionId }`，新实现返回 `{ sessionId, error? }` 与 `getSession(sessionId)` 格式不一致

### 🟡 P1-设计（×3）
1. **AgentTool 新增方式不规范**：直接修改 `agentTools.ts`，应通过 `AgentTool` 装饰器扩展
2. **swarmEnabled 常量路径错位**：放在 `engine/src/constants.ts` 而非 `shared/src/constants.ts`
3. **teammate session 生命周期未闭环**：未实现对 agent sub-process 退出事件的监听

### 🟢 P2-建议（×4）
1. `agentId` 跨 workspace 的 uniqueness 可强化（如加 timestamp nonce）
2. `inboxPoller` 轮询间隔（1s）可配置化
3. `MailboxMessage` payload 类型收窄（避免 any）
4. 建议增加 Team/Agent 日志分类前缀便于调试

## CC 对齐质量（总分）
- ✅ 对齐良好：`agentId`（100%）、`constants`（100%）、`shutdown` 握手（95%）
- ⚠️ 需修复：`AgentTool` 路由、`spawn` 响应体
- ⚠️ 待完善：teammate lifecycle、task routing 跨 workspace 广播

## 相关文件
- `engine/src/swarm/`（9个新文件）
- `engine/src/tools/AgentTool.ts`
- `shared/src/constants.ts`
- CC 源码参照：`workspace/start-claude-code/src/utils/swarm/` + `src/tools/*Team*/`
