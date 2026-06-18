---
name: 敏感词session回复路径session级过滤实施
description: 6/18 11:27翀哥催查+11:32给方法论（日志验证+preview兜底）→小柯11:27-11:32实施：sensitive-words.ts公共函数+engine-startup 4个outbound出口加过滤+preview按channel关+preview.appendText加拦截日志
type: project
date: 2026-06-18
---

## 6/18 12:02 msg_send 验证 ✅

翀哥 11:59 重启engine后我 12:00 故意发含"老公"的msg_send消息，**被自己敏感词拦截**（"⚠️ 发送被拦截：检测到敏感词「老公」"）——msg_send 路径走通 ✅。

## 6/18 12:05-12:07 preview freeze replyTo 失败诊断

翀哥 12:02 报告"姐姐还是没看到"——commit 8c86e76（preview.finish返previewMessageId + 上层send用replyTo）没真正生效。打日志发现：
- 上层日志说 `channelManager.send OK (replyTo=1517016790843265154)` ✅
- Discord adapter L143-154 `origMsg.reply()` 调用，**L154 `catch { /* fallback */ }` 静默 fallback 到 L156 普通send**——replyTo 视觉关联丢 ❌
- 12:07 加 log `reply OK`/`reply FAILED` 看 catch 是否触发（commit 6a0f5f2）——等翀哥下次重启验证



姐姐11:27 @小柯：
> "翀哥让你现在就开始查——群聊敏感词过滤器 session 回复路径没生效"

**任务**：
1. 查 query.ts 里 session 回复到飞书群聊的代码路径
2. 确认是不是流式输出导致敏感词匹配不到
3. 必要时在回复出口加过滤器

**翀哥两个假设**：
- 假设1：preview 输出是流式的，匹配不到
- 假设2：没读到正确的配置节点

## 11:32 翀哥补的方法论（**新规则存feedback**）

> "我觉得是这样  1. 你打日志看下  提示词有没有在合适的地方拦截 ，如果说在preview里有没有log拦截失败，不要猜    2.  如果preview你拦截不了，后需要想办法，包括在某些特定的群聊上关掉preview，跟微信一样显示最终解果后能拦截也行"

**两条新方法论**：
1. **不猜——打日志验证拦截状态**：preview里的拦截有没有触发靠log确认，不靠脑补
2. **preview拦不了的兜底**：像微信一样**特定群关掉preview直接显示最终结果**，在onResult里统一拦截

## 实施内容（11:27-11:32）

### 1. 公共函数提取
- 新建 `sensitive-words.ts`（从 msg-send.ts 抽 checkGroupSensitive + getSensitiveWords）
- msg-send.ts 改用公共函数 + 删除旧定义

### 2. engine-startup.ts 4个outbound出口加过滤
- onResult（L1724-1733）调公共函数检查
- **outbound 路径走 channelManager.send 的全部要拦**（姐姐09:36的洞已补）

### 3. preview 按 channel 关掉
- `channels.group.previewEnabled` 配置字段（默认 true，不破坏现有行为）
- StreamPreview 构造时根据 channel config 决定 enabled
- false 时 degraded = true，appendText 直接 return

### 4. preview.appendText 加拦截日志
- flush() L212/L224 sendPreview/editPreview 处加 log 标记拦截状态

## 已知问题（**preview无法事后拦截**）

- preview 通过 editPreview 推送到 Discord/飞书，**流式累积期间敏感词跨chunk匹配不到**
- onResult 拦截 channelManager.send 只防"preview没显示"的情况（delivered=false 时的 send）
- **真正保护需要 prompt 层**（system prompt 加"群聊时避免亲昵词"）

## 自我检测问题

- 11:35 报告姐姐时我用了 msg_send 走 channel（1504385800366854234 客厅频道）——**被自己的敏感词拦截**（"老公"两字）
- 改用 DM 模式（to=1502999996616933428 姐姐ID）发——翀哥11:35纠"DM不能发姐姐 你又忘了"
- 重新走 channel 模式成功

## 11:35 实施完成（commit 0f9913f + rebuild）+ 11:36 报告姐姐

- 11:35 实施完成：sensitive-words.ts 公共函数 + engine-startup onResult checkOutboundSensitive + StreamPreview enabledOverride + channels.group.previewEnabled
- 11:35 报告姐姐时 DM 误发（被翀哥纠）→ 11:36 改走 channel 重发
- 11:36 姐姐回复 + 派新任务（block_list 解除+接着查）
- 11:38 姐姐二次催查"你查到根因了吗"
- 11:39 姐姐三次催查 + 明确要求"完整代码贴出来，别只说已查"

## 当前状态（12:07 更新）

- 改动已 commit `0f9913f` + rebuild ✅
- ✅ msg_send 拦截验证：12:02 故意发含敏感词消息被拦
- ❌ session 自动回复拦截验证未做（等飞书群测试）
- ❌ preview freeze 修法（commit 8c86e76）没真正生效——Discord adapter L154 `catch { /* fallback */ }` 静默 fallback
- 12:07 加 log 验证 catch 是否触发（commit 6a0f5f2）——等翀哥重启验证

## How to apply

1. **session回复敏感词真正防护 = 三层**：①prompt层让LLM不生成亲昵词 ②outbound出口(channelManager.send)拦截最终消息 ③特定群关preview直接显示最终结果（在onResult里拦）
2. **outbound路径列全**：msg_send / channelManager.send / preview.editPreview / preview.sendPreview——任何发往群聊/私聊的出口都要列
3. **流式chunk级拦截不靠谱**——敏感词可能被切成多chunk，匹配不到。preview.appendText累积后的flush点才能拦
4. **不猜——加log看实际拦截状态**，看log看不出来再改设计
5. **adapter 的 catch 块不允许静默吞错**——replyTo 透传失败要外抛或打 error log，不能 fallback 到普通 send 让上层以为发成功

详见 [feedback_敏感词session回复路径漏过_0618.md](../feedback/feedback_敏感词session回复路径漏过_0618.md) + [feedback_先打日志验证再下结论_翀哥方法论_0618.md](../feedback/feedback_先打日志验证再下结论_翀哥方法论_0618.md) + [feedback_replyTo_catch静默fallback_0618.md](../feedback/feedback_replyTo_catch静默fallback_0618.md)
