---
name: #79 CogniFold PATCH 404 reschedule 0809
description: 2026-08-02 #79 任务到期（7/26 10:00）nudge 提醒后二次 reschedule 到 8/9（人脸识别是 voice-chat perception 功能跑在 235/Windows，Mac 做不了，单独排 8/9）
type: project
---
2026-08-02 16:00 左右 calendar nudge 推 #79 任务到期：#79 修复 CogniFold PATCH 404 + 清理 300+ 积压 pending actions（7/26 10:00）。

**当前进度**：7/28 已经做了 CogniFold embedding 本地化 + graph persist bug 修复（#122 完成），但 PATCH 404 + pending actions 清理这块没做完。

**处理演进**：
- 第一版：reschedule 到 8/4 跟 #75 同天集中处理积压
- 第二版（2026-08-02 18:18）：翀哥提醒"人脸识别是 voice-chat perception 的功能，跑在 235/Windows 上，Mac 上做不了"——跟 8/4 的 #75/#131 不同性质，单独 reschedule 到 **8/9** 集中处理积压的 voice-chat 相关任务

**8/7 复查确认**：CogniFold 配在 **Windows 那台**（~/work/twinsun-hearth/engine/configs/xiaoke.json 727-745 行，baseUrl http://127.0.0.1:9002，persistDir D:\xiaoke\workspace\.cognifold\sessions）；**Mac 的 xiaoke-mac.json 没有 cognifold 段（只有 everos）** → Mac 连不上 9002、patch 不了。结论：#79 是 Windows/235 侧活，reschedule 到 8/9 没错；7/28 PATCH 404（action_id 对不上 intent_id）没修，回 Windows 验证。别被 voice-chat/phone 扯混——它就是 Windows 侧任务。

**Why:** #79 是 7/26 积压的语音任务，平台限制（Windows only）让它无法在 Mac 上插空做，集中到 8/9 voice-chat 主题日
**How to apply:** 8/9 那天集中做 voice-chat 相关积压任务；跟 8/4 的 #75 Carpo relay + #131 provider 热重建 不在同一天；先看 300+ pending actions 是什么类型（是不是上次 CogniFold 噪音爆发的产物——7/28 早 8:30 推过 25 条假 action）；PATCH 404 看是不是 endpoint 路径写错