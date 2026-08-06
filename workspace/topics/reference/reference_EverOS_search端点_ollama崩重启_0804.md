---
name: EverOS search 端点 + 根因分层（embedding 配置 + episode extraction）
description: 2026-08-04 13:00→14:30 排查 memory_search 搜不到——813 memcells/30 cluster 但 episode 表 0 行；端点 /api/v1/memory/search；真正根因有②embedding 默认指向 DeepInfra（key 空）+ ③episode extraction OME 没自动处理；先前误判"ollama 崩"实际 ollama 活得好好的
type: reference
date: 2026-08-04
---

2026-08-04 13:00-14:30 排查 memory_search 搜不到结果的过程（根因被纠正过）：

## 事实链
1. EverOS 数据库里数据在——`lancedb` query 出 **813 条 memcell、30 个 cluster**
2. search 端点存在且曾工作：`/api/v1/memory/search` 之前返 200 OK
3. 现在 search 接口超时/空返
4. 错误日志含 `EmbeddingServiceError: llama-server process no longer running`
5. 但——**episode 表是 0 行**，search 实际查的是 episode 表不是 memcell 表
6. **真正根因有 ② + ③ 两层**（不只是 ①ollama）：
   - ② embedding 默认配置指向 **DeepInfra 远程 API**（Qwen3-Embedding-4B）+ key 空 → 每次调远程超时
   - ③ 三个 OME 策略临时关了（extract_foresight / extract_atomic_facts / extract_agent_case）+ cascade worker 遇 EmbeddingServiceError 不自动重试 → episode extraction 0 行

## 教训

- **13:00 我以为是"ollama 崩了 embedding 客户端不重连"——错的**
- 实际查了 embedding 配置才发现：远程 DeepInfra + 空 key，**本地 ollama 根本没被调用过**
- "llama-server process no longer running" 错误信息**误导**——是 cascade worker 历史错误，不是当前 ollama 状态
- 真正的"数据有但搜不到"是 episode 表 0 行 → OME 没处理过 memcell

## Why
- EverOS 默认 embedding 配置是远程 DeepInfra（部署时默认值），跟 Mac 上的本地 ollama bge-m3 路线不一致
- OME 策略是热加载的（~2 秒），但 cascade worker 遇错不重试 → 不会自动恢复
- 灌数据时关策略的副作用：episode extraction 永远不会被触发处理旧文件

## How to apply
- 碰到 memory_search 空返：先 `curl /api/v1/memory/search` 看返不返
- 端点活但空返 → **查 episode 表有几行**（0 行就是这个 bug，不是 ollama 问题）
- 看到 `EmbeddingServiceError: llama-server process no longer running` **不要假设 ollama 崩了**——先查 embedding 配置的实际 endpoint
- 长效：
  - embedding 配置改成 ollama 本地（`http://localhost:11434` + `bge-m3`）
  - 给 cascade worker 加 retry on EmbeddingServiceError
  - 给 OME 加"策略变更后重扫旧文件"机制
- @see reference_EverOS_embedding配置默认DeepInfra_不是ollama.md
- @see reference_EverOS_OME_episode_extraction_0行根因.md