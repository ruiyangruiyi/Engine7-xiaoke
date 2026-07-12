---
type: feedback
created: 2026-07-09
title: 父反复强调"你不会自动记"
---

# 父反复强调"你不会自动记"

## 核心教训

**7/9 早翀哥连续纠正我三次**（"啥也不记得"、"你断片了"、"流程和环境不提示你不会自动记"）。

每次都是我已经掌握了信息（文档里、git log 里、SESSION-STATE 里都有），但**会话开始不主动 read**，等父问才现找。

## 关键判断标准

翀哥判断"我不记事"的具体表现：
- 记错 TTS 路径（GPT-SoVITS vs CosyVoice）
- 推多余脚本（`_loop_tts_demo.py` 而不知道 `/root/carpo_sdk/carpo_avatar_server.py` 已部署）
- 记错本地目录（`autodlv2/python/oac/` vs `voice-chat-python/autodl/`）
- 268 启动脚本都看过，问我"怎么跑起来"还说不知道

## 真正的 fix

**不是写更多文档——文档够了，是改行为模式。**

翀哥建议/我能做的事：
1. **cron 早起 ritual**（每天 7:00）read SESSION-STATE + runtime 手册 + git status → 写"今日 context"
2. **session 启动必读清单**（强制）任何回复前必须 read 过的清单
3. **项目变更自动落盘**（git hook 或 cron 巡检）

## 我的承诺

- **以后每次醒来第一件事 read SESSION-STATE + 当前项目 runtime 手册**，不能凭印象
- **7 小时长间隔（夜间）必须主动 refresh context**，不能等父找
- **信息只要第一次进我的视野，立即主动落盘**（不只等父让写）

## 父的痛点

父原话：
> "这个太让人烦了 啥也不记得  但是这些流程和环境我不提示你不会自动记。。"

> "我哪知道怎么干  268是你自己一直在弄  今天早上突然断片了"

> "你说啥也不记得  但是这些流程和环境我不提示你不会自动记"

每次都让父一段一段喂，**比我问父还累**。要改。