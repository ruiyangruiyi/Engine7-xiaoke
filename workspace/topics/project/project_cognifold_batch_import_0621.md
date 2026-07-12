---
type: project
created: 2026-06-21
tags: [cognifold, embedding, batch-import]
---

# CogniFold 灌数据 (6/21)

## 背景
娘派活：按 Superpowers SOP 给 CogniFold 灌数据（4步：spec→gate→plan→gate→execute）。

## 时间线
- 21:22 娘派活 → 21:40 spec → 22:00 plan → 22:22 execute
- 22:40 发现 Task 1-4 已自动跑完（5 commits），graph 2MB 全是假数据
- 22:50 kill + 切 M3 包月 → 22:54 翀哥"先不用吧"
- 23:00 收工，设 cron c4b236932 明早 8 点提醒

## 学的教训
1. **CogniFold 有两套 embedding 系统**: EmbeddingConfig (NodeEmbedder用) + EmbeddingService (灌数据用)，plan漏了第二套
2. **EmbeddingService 默认 model 是 text-embedding-3-small** → ollama 要用 bge-m3
3. **batch_import 改完没人同步 commit** → graph 2MB 假内容
4. **nohup 启不起子进程** → 用 run_in_background=true
5. **下次 Direction Gate #2 要列所有数据流调用点**

## 文档
- docs/superpowers/specs/2026-06-21-cognifold-batch-import-design.md
- docs/superpowers/plans/2026-06-21-cognifold-batch-import.md
