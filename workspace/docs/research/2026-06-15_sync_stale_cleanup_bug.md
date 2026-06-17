# Sync Stale Cleanup 逻辑调研

> 2026-06-15 | Bug：文件归档后DB条目被删，搬回全重索引导致embedding rate limited

## DB Schema（4张表）

| 表 | 主键 | 内容 |
|---|---|---|
| **files** | path (TEXT) | source, hash(SHA256), mtime, size |
| **chunks** | id (TEXT) | path, source, start_line, end_line, hash, model, text, embedding, updated_at |
| **chunks_vec** | id (TEXT) | 向量虚拟表（vec0），id对应chunks表 |
| **chunks_fts** | FTS5虚拟表 | text, id, path, source, model, start_line, end_line |

另：**embedding_cache** 表以 (provider, model, provider_key, hash) 为主键——**stale cleanup不删这个表**，是唯一的救命稻草。

## Bug完整链路

```
1. session-abc.jsonl 存在 → files/chunks/vecs/fts 四张表都有数据
2. 归档操作把文件移走（移到archive目录）
3. 下一次sync → listSessionFilesForAgent() 扫描sessionsDir
4. session-abc.jsonl 不在扫描结果 → activePaths 不包含它
5. stale cleanup: activePaths.has(path) === false → 立即硬删：
   - DELETE FROM files
   - DELETE FROM chunks_vec
   - DELETE FROM chunks
   - DELETE FROM chunks_fts
   ⚠️ embedding_cache 不删（hash-based，独立于path）
6. 文件搬回sessionsDir
7. 下一次sync → 重新扫描到 → hash对比 → DB里没有了 → 全部重索引
8. 大量文件同时搬回 → 批量embedding调用 → rate limited
```

## 核心问题

**stale cleanup没有任何宽限期——文件消失一次就立即硬删。**

代码位置：`manager-sync-ops.ts` 行1068-1100

```typescript
for (const stale of staleRows) {
  if (activePaths.has(stale.path)) { continue; }  // 唯一保留条件
  // 立即删除：files + vectors + chunks + fts
}
```

## "已索引就跳过"逻辑（存在的，但不够）

`syncSessionFiles()` 行1013-1065：hash对比，相同就跳过：
```typescript
if (!params.needsFullReindex && existingHash === entry.hash) {
  this.resetSessionDelta(absPath, entry.size);
  return;  // hash相同 → 跳过重新索引
}
```

**问题：** stale cleanup先于hash对比执行。文件被删了DB条目，hash对比自然查不到existingHash → 一定全重索引。

## OpenClaw对比

**OpenClaw没有sync/stale cleanup逻辑。** 搜索整个 `D:/work/openclaw-src/` 无任何 syncSessionFiles/syncMemoryFiles/stale/cleanup 代码。schema完全一致（memory-schema.ts逐字相同），但sync策略是Engine独有的。

## 定向sync（targeted sync）不做stale cleanup

`manager-targeted-sync.ts`：调用syncSessionFiles时传 targetSessionFiles → activePaths=null → 行1068直接return跳过stale cleanup。**这是有意设计**。

## 修复方向

1. **stale cleanup加宽限期** — files表加 `last_seen` 列，连续N次sync仍消失才删
2. **或：文件消失时只标记不删** — 加一个 `stale_since` 列，真正删除在确认文件永久消失后
3. **或最简单：sync前先查DB** — 翀哥原话："应该先查DB看哪些已sync过，已索引的别重来"。即搬回来的文件如果hash跟embedding_cache里的匹配，直接复用不重新调API

方案3最轻量但只解决rate limited，不解决DB条目被删的问题。方案1/2从根上解决。
