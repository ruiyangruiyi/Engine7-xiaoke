# Sync Stale Cleanup 修复

> 2026-06-15 | 去掉文件消失时的DB硬删逻辑，改为保留DB条目

## 背景

Engine的memory sync每次扫描磁盘文件，跟DB对比。如果DB里有但磁盘上找不到的文件（被归档/移走），原逻辑会立即硬删DB四张表的全部关联数据。文件搬回后hash对比查不到existingHash，走全量重索引 → embedding API rate limited。

**代码来源：** OpenClaw原版 `extensions/memory-core/src/memory/manager-sync-ops.ts` 自带的设计，Engine搬过来的。不是CC/TestEngine加的。

## DB结构（4+1张表）

```
┌─────────────────────────────────────────────────────┐
│                    memory.db                         │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│  files   │  chunks  │ chunks_vec│ chunks_fts│ emb_cache│
│ (path PK)│ (id PK)  │ (vec虚拟表)│ (FTS5虚拟)│(hash PK)│
├──────────┼──────────┼──────────┼──────────┼─────────┤
│ path     │ id       │ id       │ text     │ provider │
│ source   │ path     │ embedding│ id       │ model    │
│ hash     │ source   │          │ path     │ hash     │
│ mtime    │ hash     │          │ source   │ embedding│
│ size     │ text     │          │ model    │          │
│          │ embedding│          │          │          │
└──────────┴──────────┴──────────┴──────────┴─────────┘
     ↑              ↑           ↑          ↑        ↑
     │     stale cleanup 删这四张表     │   不删（hash-based）
     └──────────────┴───────────┘      │
              文件路径关联删除          独立于path
```

## 原来的逻辑（已删除）

```
sync触发（interval/watch/search/session-start）
  │
  ▼
listSessionFilesForAgent() / listMemoryFiles()
  │ 扫描磁盘目录
  ▼
构建 activePaths = Set(磁盘上所有文件路径)
  │
  ▼
遍历 DB files 表中的 existingRows
  │
  ▼
┌──────────────────────────────────────┐
│ for each row in existingRows:        │
│                                      │
│   if activePaths.has(row.path):      │
│     ✅ 保留（文件还在磁盘上）          │
│     continue                         │
│                                      │
│   else:                              │
│     ❌ 文件不在磁盘 → 立即硬删：       │
│     1. DELETE FROM files             │
│     2. DELETE FROM chunks_vec        │
│     3. DELETE FROM chunks            │
│     4. DELETE FROM chunks_fts        │
│     (embedding_cache 不删)           │
│                                      │
└──────────────────────────────────────┘
```

### Bug完整链路

```
场景：session-abc.jsonl 被 archive 操作移走

Step 1: 正常状态
  磁盘: sessions/session-abc.jsonl ✅
  files:  { path: ".../session-abc.jsonl", hash: "H1" } ✅
  chunks: [chunk1, chunk2, ...] ✅
  vectors: [vec1, vec2, ...] ✅
  fts: [row1, row2, ...] ✅

Step 2: 归档（文件移到archive目录）
  磁盘: sessions/session-abc.jsonl ❌ 不在了
  DB:   全部数据还在（还没sync）

Step 3: 下一次sync触发
  扫描sessions目录 → session-abc.jsonl 不在结果中
  activePaths 不包含它
  → stale cleanup 触发 → 硬删 files + chunks + vecs + fts
  💥 embedding_cache 保留（但没啥用了，因为hash对比环节断了）

Step 4: 文件搬回sessions目录
  磁盘: sessions/session-abc.jsonl ✅
  files: 空了（被Step3删了）

Step 5: 下一次sync
  扫描到 session-abc.jsonl
  hash对比: existingHash = undefined（files表没这条了）
  existingHash !== entry.hash → 走 indexFile()
  → 调 embedding API
  💥 大量文件同时搬回 → 批量API调用 → rate limited
```

## 现在的逻辑（修复后）

```
sync触发
  │
  ▼
扫描磁盘 → 构建 activePaths
  │
  ▼
遍历 DB existingRows
  │
  ▼
┌──────────────────────────────────────┐
│ for each row in existingRows:        │
│                                      │
│   (stale cleanup 已删除)             │
│   → 不做任何删除操作                  │
│   → DB条目原样保留                    │
│                                      │
└──────────────────────────────────────┘
```

### 修复后的归档→搬回流程

```
场景：session-abc.jsonl 被 archive 操作移走，再搬回

Step 1: 正常状态
  磁盘: sessions/session-abc.jsonl ✅
  files:  { path: ".../session-abc.jsonl", hash: "H1" } ✅

Step 2: 归档（文件移走）
  磁盘: sessions/session-abc.jsonl ❌
  files: { path: ".../session-abc.jsonl", hash: "H1" } ✅ 保留！

Step 3: sync触发
  activePaths 不包含 session-abc.jsonl
  → stale cleanup 不执行（已删除）
  → DB条目原样保留 ✅

Step 4: 文件搬回
  磁盘: sessions/session-abc.jsonl ✅
  files: { path: ".../session-abc.jsonl", hash: "H1" } ✅

Step 5: sync触发
  扫描到 session-abc.jsonl
  hash对比: existingHash = "H1"（files表还在！）
  entry.hash = "H1"（内容没变）
  existingHash === entry.hash → ✅ 直接跳过
  → 不走 indexFile
  → 不调 embedding API
  → 零开销恢复
```

## 修改的代码

文件：`engine/src/memory/tools/memory/manager-sync-ops.ts`

| 位置 | 原代码 | 改后 |
|------|--------|------|
| syncMemoryFiles 行931-947 | stale遍历删除 files+chunks+vecs+fts | 删除整段循环 |
| syncSessionFiles 行1068-1100 | 同上 | 删除整段循环 |

## hash对比逻辑（未改，保持原样）

```
sync扫描到文件后：
  │
  ▼
buildSessionEntry(absPath) → 计算 hash
  │
  ▼
查 files 表 existingHash
  │
  ├── existingHash === entry.hash → ✅ 跳过（hash没变）
  │
  ├── existingHash !== entry.hash → 重新索引（内容变了）
  │
  └── existingHash = undefined → 走 indexFile（新文件）
```

**修复的关键：** files表不再被stale cleanup删除，所以搬回来的文件existingHash一直都在，hash对比直接命中跳过。

## 副作用

| 方面 | 影响 |
|------|------|
| 磁盘空间 | 真正删除的文件会在DB留孤儿数据，多占几MB~几十MB |
| 搜索结果 | 孤儿数据可能被搜到（但内容是旧session，问题不大） |
| 功能 | 不影响任何功能。memory_search正常工作 |
| 性能 | 反而更好——不再批量删+重索引 |

如果以后需要清理孤儿数据，可以手动跑 `DELETE FROM files WHERE path NOT IN (磁盘上的文件列表)`。
