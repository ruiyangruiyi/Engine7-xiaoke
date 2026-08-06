---
name: ollama CPU 单 slot + cascade 大文件 embedding 内存不够崩
description: 2026-08-04 上午 EverOS 导入 episode 大文件时——ollama 单 slot 被占→搜索 500/超时；llama-server 内存不够崩自动重试
type: reference
date: 2026-08-04
---

# ollama CPU 单 slot + cascade 大文件 embedding 内存不够崩

2026-08-04 上午 EverOS 索引过程中的两个 ollama 资源问题：

## 问题 1：ollama 单 slot 互抢

CPU 跑的 ollama 只有 **1 个 slot**（默认并行 1）。
- cascade 正在 embed episode 大文件 → 占着 slot
- 此时 agentic server 来搜 → query embedding 排队 → **60s 超时 → 500**
- 表现：atomic_fact 索引好了也搜不到 episode

**Why:** ollama 默认 `OLLAMA_NUM_PARALLEL=1`，CPU 推理慢+单 slot 不能并发。

**How to apply:**
- 不要在 cascade 灌数据时测搜索——会看到假象（搜到 atomic_fact 但 episode 搜不到）
- 想并发：调 `OLLAMA_NUM_PARALLEL` 但 CPU 会更慢不一定划算
- **正确姿势**：等 cascade episode 跑完（或暂停 episode 导入）再测搜索

## 问题 2（已修正）：episode 大文件触发但真根因是 Docker VM 内存太小

> ⚠️ 2026-08-04 下午查到真正根因——**不是文件太大，是 Docker VM 内存 1.94GB 装不下 bge-m3**。
> 详细见 @see reference_EverOS_Docker_VM内存1.94G_bge-m3装不下_0804

episode md 文件 3899 行确实更容易触发，但即使小文件，模型随时 reload 也会崩。**真根因是 VM 内存**。

**修正后的 How to apply:**
- 日志看到 `unable to fit model into system memory` 或 `signal: killed` → 100% VM 内存不够，先调大 Docker Desktop 内存（≥8GB）
- 不要只去切小 episode 文件——VM 内存小，啥文件都跑不稳
- 调完 VM 内存后 episode 大文件自然能跑

## 关联

- 8/4 上午 cascade + lancedb 重建完整流程 @see project_EverOS_数据清空后恢复_0804
- bge-m3 CPU 443ms/条 @see reference_EverOS_ollama_bge-m3_容器内跑通_0804