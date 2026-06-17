---
name: sync stale cleanup 移除
description: 6/15移除sync文件消失即删DB逻辑，文件归档不再丢失embedding索引
type: project
---
# Sync stale cleanup 移除 — 2026-06-15 18:00

## 问题
`manager-sync-ops.ts` 的 `syncSessionFiles`(line 1068-1100) 和 `syncMemoryFiles`(line 931-947) 在 sync 完成后遍历 DB files 表，任何不在当前磁盘目录的文件就**硬删** DB 四张表关联数据（files/chunks/vectors/fts_entries）。

**后果：** 归档旧 session 文件 → stale cleanup 将其从 DB 全删 → 搬回来时 hash 查不到 → 重索引（可能 rate limited）。

## 根因
OpenClaw 源码 `extensions/memory-core/manager-sync-ops.ts` 就有同样的 stale cleanup 逻辑（不是 CC/TestEngine 乱加的，是 OpenClaw 原版设计）。DB 的 `files` 表存文件**元数据**（路径/hash/状态），`chunks` 表存文件内容切片（`text` 字段）+ **embedding** + **FTS**。

原设计理念：DB 是文件索引缓存，文件不在磁盘了 DB 条目没意义。这对普通文件删除合理，但 **session 归档不是删除**，一刀切全删不合理。

## 修复（2026-06-15 实际动手移除 ✅）
两处 stale cleanup 循环直接去掉（session 和 memory 各一处），commit `33eb425`：

- `syncSessionFiles`（line 1068-1100）：删掉 stales 遍历删除
- `syncMemoryFiles`（line 931-947）：同上

**注意：DB 不存文件内容。** `chunks.text` 存的是文件内容**切片**（按行分段），memory_search 搜的是这些切片+向量，不读原文件。文件只要 sync 过一次，之后移走归档都能搜到。

## 效果

### 原逻辑
```
文件归档 → DB 遍历发现不存在 → 硬删 files/chunks/vectors/fts
→ 搬回来 → hash 查不到（files 表条目已删）
→ 走 indexFile → 可能调 embedding API
→ rate limited
```

### 新逻辑
```
文件归档 → DB 保留不动（files/chunks/vectors/fts 都在）
→ 搬回来 → hash 命中（files 表 existingHash 保留）
→ 直接跳过，零开销 ✅
```

### 为什么 embedding_cache 不够？
embedding_cache 是以内容 hash 为主键，跟文件路径无关。但原流程中 files 表被删后，hash 对比那步查 `existingHash` 返回 undefined → 模型认为"新文件" → 走 indexFile。indexFile 里虽然会查 embedding_cache，但要看 cache 是否启用、provider/model 是否一致，条件多不一定命中。

**新流程根本不用进 indexFile**，因为 files 表保留让 hash 对比直接命中。

## 副作用
真正删除的文件会在 DB 留孤儿数据（多占磁盘空间），不影响功能。要真删文件走显式 `forgetFile` 命令。

## 关联文档
- `docs/knowledge/2026-06-15_sync_stale_cleanup.md` — 含 DB 结构图 + 流程对比图
- [memory_search OOM crash](project_memory_search_OOM_crash.md) — 同一个 sync 系统

## 进度
- ✅ 6/15 已完成并生效：两处stale cleanup循环已删除 + 文档落地 + commit `33eb425`（1文件，-47行+3行）+ `docs/knowledge/2026-06-15_sync_stale_cleanup.md`（含DB结构图+流程对比图）
- ✅ 翀哥确认：OpenClaw源码 `extensions/memory-core/manager-sync-ops.ts` 就有同样的stale cleanup逻辑（非CC/TestEngine乱加）——这是OpenClaw原版设计问题
- DB只存文件元数据（path/hash/mtime/size），不存文件内容。但chunks表有text字段存内容切片，所以文件移走memory_search依然能搜到内容
- **效果验证：** 文件归档 → DB保留 → 搬回 → hash命中跳过 → 零开销，不会再rate limited了
