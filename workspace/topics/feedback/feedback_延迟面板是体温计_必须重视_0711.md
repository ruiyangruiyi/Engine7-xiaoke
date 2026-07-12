---
type: feedback
date: 2026-07-11
tags: [voice-chat, timing, 延迟面板, 优化, 核心原则]
---

# 延迟面板是体温计 — 没有数据就没法优化

## 翀哥原话
> "这些东西你不要忽视，这些东西就像体温计，没有这些优化不了的"

## 背景
7/11 下午调试 voice-chat 时，235 端 timing 面板（235 total / TTS→首chunk）全是横线。
翀哥反复强调要修好，我当时一度觉得"timing 显示不重要，先修 SSH"，差点忽略。

## 核心原则
- **延迟数据 = 体温计**：没有量化数据，所有"优化"都是瞎猜
- timing 面板的每一个字段（total、首chunk、last chunk）都有意义
- 字段显示不出来 = bug，必须修，不能跳过
- 翀哥重视这些数据不是"吹毛求疵"，是工程师的基本素养

## 教训
1. 不要因为"次要"就忽略面板/监控数据的问题
2. timing bug 当天修，不留到第二天
3. key 名不匹配这种低级 bug（`t_start` vs `t_request_received`）最浪费时间
