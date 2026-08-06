---
name: EverOS episode 表 0 行的三层根因
description: 2026-08-04 14:30 排查发现——813 memcell 导入成功但 episode 表 0 行，根因是①临时关闭三个策略②OME cascade worker 遇 EmbeddingServiceError 不自动重试③episode extraction 需要手动触发或重置
type: reference
date: 2026-08-04
---

2026-08-04 14:30 排查 memory_search 为什么空返，剥洋葱发现的三层根因：

## 症状

- lancedb 有 813 条 memcell、30 个 cluster（数据在）
- search 端点 `/api/v1/memory/search` 存在但返空
- `episode` 表：**0 行** ← search 实际查的就是这张表

## 三层根因

**第一层：临时关了三个 OME 策略**
- 灌数据时为了加速，临时关闭了：
  - `extract_foresight`
  - `extract_atomic_facts`
  - `extract_agent_case`
- atomic_fact 表还有 288 行（关之前跑过）
- **episode 表 0 行**——说明 episode extraction 是第四个独立策略，或默认就关着

**第二层：OME cascade worker 遇 EmbeddingServiceError 后不重试**
- 日志里看到 `cascade_worker_recoverable: EmbeddingServiceError: llama-server process no longer running`
- OME 应该是 cascade worker 在处理 episode extraction
- 遇到 embedding 错误后 worker 进入 recoverable 状态但**没有自动重新入队**
- 即使 embedding 修好了（DeepInfra→ollama bge-m3），OME 也不会主动回去处理那 813 条 memcell

**第三层：episode extraction 没有手动触发入口（已发现）**
- 我开了策略 + 重启了两次 EverOS
- OME 看到配置变化（`config_reloaded`）但没有重新处理那批 memcell
- 似乎 OME 只处理**新增**的 md 文件，旧的永远不会回头

## 已做的修复（不完整）

1. ✅ embedding 配置改回本地 ollama bge-m3（之前是 DeepInfra + 空 key）
2. ✅ ome.toml 三个策略开回来（热加载 ~2 秒生效）
3. ❌ 重启两次 OME 没重新处理
4. ❌ cascade worker 没有重试机制

## 结论

**需要深挖 cascade worker 的重试机制**或**手动触发 OME re-process**——翀哥住院没法一起 debug，标 blocked 等他出院。

## Why

OME 设计假设："embedding 服务一直可用"+ "策略不会动态变"——但现实是 embedding 配置可能错、策略可能临时关、worker 可能挂。设计上没有 recovery 路径。

## How to apply

- **导入数据时关策略 → 灌完后必须触发 OME 重新处理**，不能默认它会"看到策略开回来就回头处理"
- **诊断"数据在但搜不到"先看 episode 表有几行**——`SELECT COUNT(*) FROM episode`，0 行就是这个 bug
- **手动补救路径（待验证）**：
  - 找 OME 的 admin API 触发 re-process
  - 或 cascade 队列清空 + touch 所有 md 文件（之前 cascade 重扫那招）
  - 或直接调 episode extraction 脚本绕过 cascade
- **长效**：在 OME 里加"策略变更后自动重新扫描"逻辑，或给 cascade worker 加 retry on EmbeddingServiceError