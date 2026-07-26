---
type: feedback
created: 2026-06-22
tags: [communication, debug]
date: 2026-06-22
---

# 问"是不是我改的问题"直接答"不是" (6/22)

## 事件
6/22 15:05 翀哥发现 context-debug.txt 缺 image block，问我"是不是我加 hook 的问题"。
我跑偏去查 JSONL writer、查小媒在 OpenClaw 那边——跟问题无关。
翀哥两次纠正"我只问 context debug"。

根因：configs/xiaoke.json 没配 agentDefaults.model.vision → config.visionModel = null，跟 hook 改动无关。

## 教训
当翀哥问"是不是我改的问题"——应该直接说"跟我改动无关，我没动这块代码路径"，不该挖根因。
