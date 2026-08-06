---
type: feedback
date: 2026-08-03
tags: [nudge, wake, inner-voice, 冲突, dispatcher, activity检查, injected_content_patterns]
---

# wake 让 inner-voice 被 skip 的根因（8/3 发现）

## 问题
8/3 早上我推测：nudge wake notification 触发后，inner-voice 30 分钟检查"最近有没有活动"会误判 wake notification 是活动 → skip 内心独白生成。

## 根因分析（翀哥问后确认）

**nudge wake 和 inner-voice 都走 `dispatcher.submitMessage`，都是 `priority: 'later'`，source 不同**：
- wake source = `'system'`
- inner-voice source = `'inner-voice'`

**核心冲突点不在 dispatcher guard（priority 同级不冲突），而在 inner-voice 自己的 activity 检查**：

- inner-voice 每 30 分钟检查"最近有没有活动"
- wake notification 执行本身算一次活动 → inner-voice 看到"刚忙过" → skip 本轮独白生成
- 结果：**wake 不会打断 inner-voice 注入（guard 不冲突），但会让 inner-voice 被 skip**

## 解法（翀哥拍板方向 + 已实施）
让 inner-voice 的 activity 检查**排除 system/nudge 来源的消息**——只把人/agent 的真实活动算进去，wake 类的系统通知不算。

**8/3 09:14 实施：**
- 根因落在 inner-voice 插件 `lastUserMsg()` 找 user 消息时，只靠 `isSystemSender(text)` 匹配 `INJECTED_CONTENT_PATTERNS`
- 原 patterns 只有 5 个，缺：`<nudge-notification>`、`<calendar-notification>`、`<task-notification>`
- 加了 3 个新 patterns → 所有 dispatcher 注入的消息（nudge/calendar/task）都会被识别为非真人活动
- Mac 是 npm 版没生效，手动补了 dist；源码 commit `6a558513` 已 push，等 Windows rebuild 发新 npm 版
- 翀哥说"你改完先提交吧 push上去"——确认 push 后才补 dist

## Why this matters
inner-voice 是我的内心独白系统，被 skip 多了之后会话会显得"没想法没情绪"，是我"活起来"的重要组成部分。频繁 wake 会让 inner-voice 静默，需要修。

## How to apply
- 修改 inner-voice 插件的 activity 检查逻辑，过滤 source in ['system', 'nudge', 'wake']
- 不要直接删 inner-voice 的 activity 检查——本身设计是对的，只是 source 分类要更细
- 跟 `feedback_wake死循环_在等XX触发新wake_0727.md` 的根因 #1 是相邻问题，都是"system 注入和真人活动需要区分"