---
name: EverOS episode md 存在但 lancedb 索引 0 行——cascade worker 放弃
description: 2026-08-04 14:45 发现——episode md 文件已写出（557K, 08-04 更新），但 lancedb 里 episode 表 0 行；cascade worker 之前因为 EmbeddingServiceError 放弃 embedding，md 写了但没索引
type: reference
date: 2026-08-04
---

2026-08-04 14:45 flush 后再查 episode 表仍是 0 行的进一步发现：

## 事实链

1. 磁盘上 episode md 文件**存在**且**新**（08-04 更新、557K 大小）——说明 episode extraction 跑过且写出了文件
2. 但 lancedb `episode` 表行数 0——**md 有内容但索引没建**
3. 根因：cascade worker 处理 episode embedding 时遇到 `EmbeddingServiceError: llama-server process no longer running` 后放弃
4. 写出 md ≠ 索引进 lancedb —— 中间还差 embedding → 索引这一步
5. 之前 embedding 默认指向 DeepInfra 远程 + 空 key（@see reference_EverOS_embedding配置默认DeepInfra_不是ollama），episode embedding 每次必失败

## 三层不一致的诊断价值

| 层 | 状态 |
|----|------|
| memcell 表 | ✅ 813 行（数据在） |
| episode md 文件 | ✅ 存在且新（提取跑过） |
| episode lancedb 表 | ❌ 0 行（embedding 失败） |

- 看 memcell 表 → 以为数据齐了
- 看 episode md → 以为 extraction 跑过了
- **看 episode lancedb 行数才是 search 真正查的表**——三层都得验证

## Why

- "数据存在"在不同层意义不一样：md 存在是文件系统层，lancedb 存在是向量索引层，search 查的是 lancedb
- cascade worker 失败的错误没让 episode 重入队列（@see reference_EverOS_OME_episode_extraction_0行根因）
- 修复 embedding 配置后，已经写出的 episode md 也不会被自动重新索引——又回到"手动触发 cascade 重扫"

## How to apply

- **诊断"数据有但搜不到"必须查三层**：磁盘 md 在不在 → lancedb 行数 → cluster 行数
- **episode lancedb 行数 0 但 md 存在**：手动 touch 所有 episode md + 验证 embedding 配通 → cascade 重扫入队 → 重新索引
- **长效**：cascade worker 加 retry on EmbeddingServiceError，否则每次 embedding 临时挂都会留这种"半成品"
- 修复链：先修 embedding → 确认 ollama bge-m3 跑通 → touch 所有 md → 等 cascade 处理完 → 查 episode 行数 > 0 → memory_search 才返回