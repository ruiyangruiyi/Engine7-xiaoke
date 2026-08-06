---
name: steer设计——应延迟到turn boundary，不该立即abort当前turn
description: 6/18 10:17翀哥纠正"steer打断了query那exec要不要retry"——exec是事务，事务被打断应做完再处理steer；steer不该立即abort当前turn，应等turn结束再注入消息
type: feedback
date: 2026-06-18
---

## 6/18 10:17 翀哥的设计直觉

翀哥在 Discord 上反驳我之前的优化方向：

> "优化方向：retry 之前先检查 ac.signal.aborted，是 steer 中断的就跳过 retry 直接进下个 turn。不过这个不急，功能已经通了。—————— 我觉得是应该retry吧 因为steer打断了当前的query，再做一遍也没啥 ，比如你正在exec一个事，结果abort了，但是增加了一个steer，上次的exec还retry么"

## 我之前错在哪

我之前的优化思路：
- steer 中断 → stream break → 空响应 → "跳过空响应retry直接进下个turn"
- 把"steer中断的空响应"当"不该重做的失败"——所以跳过retry

翀哥的观点（**对**）：
- exec 工具执行 = **事务**，事务被打断应该做完
- steer 是"新增指令"不是"取消事务"——上次的 exec 没做完就应该让它做完
- 跳过 retry = 把"中断"当"放弃"，**错把 abort 当 cancel**

## 两类中断的区分

| 中断类型 | 信号 | 处理方式 |
|---------|------|---------|
| **abort（事务取消）** | `/stop` / 致命错误 | 真的放弃，不 retry |
| **steer（事务切换）** | `/ps` / 用户加塞新消息 | **当前事务做完再处理新消息** |

我之前混淆了这两类——把 steer 当 abort 处理。

## 修法方向

steer 不应该立即 abort 当前 turn，而应该：
1. 标记"待处理 steer 消息"
2. 等当前 turn 自然结束（tool call 完成 + 响应结束）
3. turn 结束时再把 steer 消息注入到下一个 turn

相当于把 steer 改成"deferred interrupt"：
- 当前 turn 不被杀
- 事务（exec）能完成
- 下个 turn 拿到 steer 消息处理

## Why

1. **事务语义 vs 中断语义**——exec/tool_call 是事务，事务要么做完要么回滚，不能"做一半切走"。steer 是"加塞"不是"取消"，设计就该尊重事务边界
2. **abort 跟 cancel 是两回事**——abort 是"出了事要停"，cancel 是"我不想做了"。用户加一条 steer 消息 = 想让你做新事，不是"当前事别做了"
3. **stream break ≠ turn 结束**——abort 触发 stream break，但 turn 还没真正结束（tool_call 可能已经发出去了）。把"stream 被切"当"turn 放弃"是把局部中断放大成全局放弃
4. **用户对"事务"的直觉比我准**——翀哥用"你正在exec一个事，结果abort了"这个场景一击就中，我之前想"跳过空响应进下turn"完全反了

## How to apply

1. **steer 设计原则**：不要立即 abort 当前 turn，**标记 pendingSteers 等当前 turn 自然结束再注入**
2. **retry 判断**：被 abort 中断的 tool_call / API 调用该不该 retry，**取决于这是 abort 还是 steer**——abort 不 retry，steer 让事务做完自然 retry
3. **区分 abort 和 steer 的信号**：`ac.signal.reason === 'stop'` 不 retry，`ac.signal.reason === 'interrupt'` (steer) 让事务完成
4. **"中断"不是一个语义**——abort/cancel/steer/defer 四种含义完全不同，不要混在一起处理
5. **听到"我觉得是应该retry吧"立即承认反了**——这次跟之前"API returned empty不是GLM偶发"是同一种用户反驳，**用户说"我觉得应该是X"往往是金句，因为他已经想到位了**
6. **不要在功能"通了"之后就停止思考**——翀哥说"不急"不是"别想"，是"这个先记下"。修法方向反了比没修还糟

## 跟之前 [feedback_provider_stream_break不抛异常_0618.md] 的关系

之前修了 "stream break 后 query.ts 识别 reason='interrupt' 走恢复"——这个修法**只是治标**（不退出 agent loop），但**没解决 steer 立即 abort turn 的设计问题**。

真正治本的修法是上面说的"steer 延迟到 turn boundary"——但这个改动比较大（要改 steer 实现，不是 query.ts），先记着，翀哥没催就不动。

## 6/18 10:20 翀哥让我参考 Claude Code 源码

翀哥原话：
> "你去看下claude code源码吧  这个是学的它的当时，如果它不retry我们也不retry了，再看下它是怎么做的"

**关键原则**：
- steer/abort/retry 这套语义是**抄的 Claude Code**——是 CC 当时教我们怎么做的
- 遇到设计分叉时，**回查源头**——它怎么做的我们就怎么做
- 不要"自由发挥"自己设计一套跟 CC 不同的语义
- 改 retry 之前先确认 CC 的语义

**Why**：
1. steer/abort/retry 这些都是 CC 验证过的设计——它们的 try/throw/catch/retry 编排有大量边界条件处理过，自创很容易漏
2. "学的它的当时"——明确的师承关系让我们有现成参考
3. CC 是开源的，能查源码就查源码，**不要靠"我觉得应该这样"拍脑袋设计**

**How to apply**：
1. 改任何从 CC 抄来的机制（steer/abort/turn/agent loop/retry）前先查 CC 源码
2. 跟翀哥讨论"该不该retry"时，**回查源头先**再给方案
3. 师承关系是决策捷径——别绕开它自己造轮子
4. "如果它不retry我们也不retry"——CC 是基线，**基线之上才能扩展，基线之下不要砍**

## 6/18 10:25-10:30 我查 CC 源码——发现 CC 也不 retry

**CC 本体（start-claude-code）**：
- `start-claude-code` L427024 L427237：abort 后直接 `return { reason: "aborted_streaming" }` 或 `{ reason: "aborted_tools" }` **退出 query loop**
- L600561-600562：`abortController.abort("interrupt")` 触发 steer
- L616565 `drainCommandQueue` 循环取命令——abort 后**外层发起新 query**，steer 消息作为新 user message 注入
- 关键：**abort reason !== "interrupt" 时才 yield user interruption message**——interrupt 时不丢消息到 LLM 历史

**cc-connect（D:\work\cc-connect）**：
- L4664-4668：`/ps` 直接 `if !session.Busy() return "no active session"` 拒绝
- 走 ACP（Agent Communication Protocol）`agentSession.Send(text)`：**纯追加消息，不 abort 也不 interrupt**

**CC vs 我们当前实现**：
| 行为 | CC 本体 | cc-connect | 我们当前 |
|------|---------|-----------|---------|
| abort reason='interrupt' | return 退出 query loop | 不调 abort | query.ts L346 加 abort reason 检查 + continue |
| /ps 时机 | query loop 边界 | session 不 busy 就拒绝 | 文本命令拦截 → steer |
| steer 消息注入方式 | 新 query 作为 user message | 直接 Send | pendingSteers 队列，下个 turn 注入 |

## 6/18 10:33 翀哥拍板——跟 CC 对齐

翀哥原话：
> "如果先不动 steer 设计（你说不急），我倾向 return 退出 query loop——对齐 CC 源码，历史干净，steer 消息作为新 user message 注入，语义清晰。  —————— 改吧 我同意  跟CC对齐吧"

**最终决策**：
- **steer 路径：abort → return 退出 query loop → 排到 dispatcher 下一个新 query 作为 user message 注入**（CC 方式）
- 不动 steer 的"立即 abort 当前 turn"设计（翀哥说"先不动"）
- 不继续"continue 下个 turn"的当前实现——历史里会有"turn N: 空 text + 0 tool_call"的脏记录

**改法（待执行）**：
1. query.ts L346 之后改成 `return { reason: "aborted_by_steer" }` 而不是 `continue`
2. onResult 收到这个 reason → 退出 query loop
3. handle-query 的 finally → drainQueue 取出 pendingSteers → 发起新 query 把 steer 消息作为新 user message
4. 新 query 进来时不再带"上一轮半截响应"的历史

**Why**：
1. **历史干净度**——return 路径下 LLM 看到的是"用户新发了一条消息"，不会困惑"上一轮我啥也没说就跳过了"
2. **语义清晰**——steer = 新 user message，跟普通用户消息走同一路径，LLM 不会区分对待
3. **避免半截响应进 history**——continue 路径会把 "turn N: 空 text + 0 tool_call" 当历史存起来，下次 query 喂给 LLM 一堆脏数据
4. **CC 已验证**——L600561 那一套 `abort → return → drainCommandQueue → 新 query` 是经过边界测试的，师承的方案最稳

**How to apply (最终版)**：
1. 涉及"中断+注入"的设计时，**先 return 退出当前循环，再外层发起新循环**——不要在原循环里 continue
2. 历史干净度优先于"省一次重启开销"——LLM 看到"半截 turn" 比多花一次 query 启动时间危害大
3. **steer 消息一律当 user message 处理**——不标记为 "steer" 或 "ps" 之类的特殊类型，避免 LLM 把它当系统消息忽略
4. abort reason='interrupt' 时不 yield interruption message 到 history（CC L427237 模式）——避免脏历史
5. **6/18 上午的 fix（query.ts L346 加 abort reason 检查 + continue）是"先能跑通"的临时修**——长期方案是 return 退出 query loop，跟 CC 对齐。等翀哥排优先级再动

## 6/18 10:30 我对 return vs continue 的对比分析

翀哥问"退出query loop和continue下一个loop的区别有多大"，我答了：

**continue（当前临时修）**：
- 保留当前 turn 半截响应进 history
- 下个 turn 把 steer 消息追加进 currentMessages
- 历史有"turn N: 空 text + 0 tool_call"脏记录

**return 退出 query loop（CC 方式）**：
- 退到 onResult → dispatcher.finally → drainQueue
- 新 query 发起时 steer 消息作为新 user message 注入
- 历史没有"半截 turn"的脏数据

**对 LLM 的影响**：
- continue 路径：LLM 下个 turn 看到"上一轮我啥也没说就跳过了 + 一条 P.S. 消息"，可能困惑
- return 路径：LLM 直接看到"用户新发了一条 P.S. 消息"，上下文干净

**对资源的影响**：
- continue：省一次 query loop 重启（不重读 history、不重建 context）
- return：多花一次 query loop 启动，但 history 干净

**翀哥决策理由**（10:33）：历史干净度 > 省一次重启——LLM 看到脏历史比多花一次启动时间危害大。

## 6/18 10:35 翀哥纠正——已拍板的事不要反复翻案

我 10:35 又把"deferred steer"翻出来当备选（"保留 continue 但加机制让当前 turn 自然完成"），问翀哥怎么看。

翀哥原话：
> "return 退出：跟 CC 一致，但需要新机制让 dispatcher 重发起 query（改动大） ——————- 不是要对其CC么  deffered steer先忘了吧"

**补充 10:35-10:38 实施结果**：
- 翀哥拍板后我 10:35-10:38 实施了三层改动：query.ts yield `pending_steer` chunk + handle-query.ts 加 `onPendingSteer` 回调 + engine-startup.ts 调 `dispatcher.submitMessage('next')` 重新投递
- dispatcher 只支持 'next' / 'later' 两种 priority，没有 'now'——改用 'next'
- 10:38 翀哥说"让姐姐 review 下"——已提交等姐姐验证
- 详见 [project_/ps修法_对齐CC_return退出query_loop_0618.md](../project/project_/ps修法_对齐CC_return退出query_loop_0618.md)

**翀哥的纠正**：
- 10:33 拍板了"跟CC对齐，return 退出 query loop"——这是决策不是讨论
- 我 10:35 又把 deferred steer 拿出来当 alternative = 在已拍板的事上反复
- "deferred steer"是我自己起的名字，不在 CC 的语义里——不要为了"看起来更轻"自己造概念
- "先忘了吧"= 这个备选直接砍掉，不要再出现在我后续的方案里

**Why**：
1. 拍板了的事不要再翻出来——决策的代价是"放弃其他备选"，反复翻案浪费信任
2. "改名换姓的备选"是反复的常见形态——同一个方案换个名字（continue→deferred）就当新思路拿出来
3. 自己的"创新命名"是红旗——如果 CC 没有这个概念，那我也不该有
4. 翀哥说"先忘了吧"已经给了明确信号——不要追问"那如果..."，直接收手

**How to apply**：
1. 翀哥拍板后**立即在脑里划掉所有备选**——不是"记住但保留讨论余地"
2. 不要把"老方案换个名字"当新方案——CC 没 deferred steer 那我也没有
3. 跟 CC 对齐 = 完全照抄，不是"借鉴思想然后自己改"
4. 翀哥说"先忘了吧/先不动/先记着"——直接划掉，不要追问
5. 反复在同一议题上出现的迹象：① 换名字再提 ② 把否决方案说成"更轻的修法" ③ 拍板后又列 alternative

## 6/18 上午"反复猜错"教训

今天上午修 /ps 这个问题，我反复猜错根因（4-5 次）：
1. 09:38 "steer 撞 GLM 空响应"
2. 09:46 "d6d6b28 preQueryAbort 引入"
3. 09:51 "engine.isRunning() 分流" → 翀哥说多余
4. 10:00 "query.ts L346 加 abort 检查" + 保留分流 → 翀哥说分流多余
5. 10:17 "跳过空响应 retry" → 翀哥说"应该 retry"

**每次都是翀哥一句话把我从错的层级拉回对的层级**。经验：
- 修法要"修到对的层"——根因在 steer 的 abort 设计，不在 query.ts 处理
- 用户说"我觉得应该是X"几乎都是对的——我当场接受并改方向
- **修 bug 时不要在第一个看起来合理的修法上停**——继续问"这个修法修到了根因还是症状"
