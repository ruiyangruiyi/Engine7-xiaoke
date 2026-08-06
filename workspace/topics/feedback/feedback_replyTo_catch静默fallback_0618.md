---
name: replyTo参数在adapter catch时静默fallback
description: 6/18 12:07发现Discord adapter L154 `catch { /* fallback */ }`静默吞掉replyTo失败→落到普通send没replyTo关联——修法加log看catch是否触发(frozen后上层send还是看不到reply的根本原因)
type: feedback
date: 2026-06-18
---
## 6/18 12:02-12:07 翀哥报"姐姐还是没看到"

翀哥 12:02 重启engine后我 12:00 那条汇报，姐姐还是没看到。**commit 8c86e76 修法（preview.finish返previewMessageId + 上层send用replyTo）没真正生效**。

## 12:05 排查 → Discord adapter L154 catch 静默

打日志看 `channelManager.send` 路径：
- ✅ onResult 日志：`channelManager.send OK (replyTo=1517016790843265154)` — send 成功 + replyTo 传入
- ❌ Discord adapter L143-154 `origMsg.reply()` 调用——L154 有 `catch { /* fallback */ }`：**reply失败就静默落到 L156 普通send**
- 可能原因：preview消息是bot自己发的embed，`messages.fetch(replyTo)` 可能 fetch 到了但 `reply()` 报错（embed类型消息不允许reply？或allowedMentions配置错？）

**核心bug**：replyTo传了但**adapter catch fallback 静默吞错**——上层以为发了带reply的消息，实际发的是普通消息，replyTo**完全不生效**。

## 12:07 修法（commit 6a0f5f2 + rebuild）

加日志看 catch 到底跑了没：
- `reply OK` — 走 reply 路径成功
- `reply FAILED to msgId=xxx: 错误原因 → fallback to plain send` — 走 fallback 路径（看是 embed reply 限制还是其他）

## 12:11 翀哥 12:07 重启后验证：reply OK 链路通 ✅

- 翀哥 12:07 重启 engine（PID 62808, 12:07:21 启动，吃到 6a0f5f2）
- log 显示 **`reply OK` 出现 3 次**——Discord adapter L143-154 reply() 真的走通，**L154 catch 没触发**
- 12:11 翀哥"**你自己可以看了**"——preview freeze + reply 视觉关联三层都通了
- 之前 catch 静默fallback 是**假bug**——猜测 embed reply 受限是错的，实际 reply() 正常成功

**经验更新**：
- 12:02 看到的"replyTo 视觉关联丢"是**修法刚上还没完全稳定**或**姐姐视角没刷新**，不是 catch 静默fallback
- **加 log 验证假设后再下结论**——我之前直接断言"adapter catch 静默吞错"，没看实际 log 跑就猜

## Why

1. **`catch { /* fallback */ }` 是沉默杀手**——adapter层吞错不外抛，让上游以为发成功（onResult日志说OK）实际reply关联丢了
2. **用户视角"看不到"≠ 上层日志"发成功"**——send成功 ≠ replyTo生效，要两层都看
3. **bot自己发的embed消息 reply() 可能有限制**——Discord 对 self-bot embed reply 的支持未必和普通消息 reply 一样

## How to apply

1. **任何adapter的catch块**都加log（至少console.error打错）——不允许静默吞错吞到行为对不上
2. **replyTo 真要追到 adapter 层**：不是"上层send带replyTo字段"就行，要看adapter的reply()有没有走通、catch有没有触发
3. **验证replyTo生效**：从用户视角（Discord/飞书）看视觉引用线是否出现，不只看上层send日志
4. **embed/preview 类消息的 reply 行为**要单独测——可能跟普通消息 reply 行为不一样
5. **commit 8c86e76 的修法是必要的但不充分**——上层传replyTo + adapter真reply两层都通才算修好

## 跟之前规则的关系

- `feedback_preview_freeze_replyTo_关联_0618.md`：6/18 11:56 修上层传 replyTo
- `feedback_preview_freeze_replyTo_姐姐看不到最终内容_0618.md`：6/18 12:02 修法未生效分析
- **本次（6/18 12:07）**：发现adapter层 catch 静默fallback 是更深的bug——上层和adapter两层都通才算修好
