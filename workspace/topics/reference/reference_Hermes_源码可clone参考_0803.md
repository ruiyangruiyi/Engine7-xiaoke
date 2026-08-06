---
name: Hermes 源码可以 clone 下来当参考
description: 翀哥 8/3 让我下 Hermes 源码——"早晚得下还是不错的参考"；Hermes 跟 OpenClaw 一样都是 OAuth Device-Code Flow 默认全权限
type: reference
date: 2026-08-03
---

# Hermes 源码 — 早晚得下当参考

**2026-08-03 17:53 翀哥飞书原话：** "没有，你可以搜啊，clone 下来就行了，这个早晚得下，还是挺不错的参考呢。"

## 关键信息

- Hermes 源码是公开可 clone 的（不在本地工作区，需要搜/下）
- 翀哥明确建议下载当**长期参考**——他重视多项目互参
- Hermes 跟 OpenClaw 一样用 **OAuth Device-Code Flow**（archetype: PersonalAgent），扫码默认全开权限

## 为什么值得下

- 我们 engine7 init 的飞书扫码功能就是抄 OpenClaw Device-Code 方案，Hermes 是另一个同源实现，可以交叉验证
- Hermes 的 `cli_a922d8ca91f8dbc8`（姐姐的商店应用）跟 OpenClaw 同 archetype，扫码建号权限对比的好样本
- 翀哥说"上次一扫全开了"——Hermes 源码能看到 PersonalAgent 模板到底默认开了哪些 scope

## How to apply

- 等翀哥回 Win 有空时 clone Hermes 源码到本地 workspace 参考
- clone 后扫一下 OAuth Device-Code 部分，对比 OpenClaw 实现是否一致
- 重点看 PersonalAgent archetype 创建后是否还有额外权限/事件订阅的初始化代码（验证"默认全开"是纯 OAuth 默认还是 Hermes 额外补了一步）