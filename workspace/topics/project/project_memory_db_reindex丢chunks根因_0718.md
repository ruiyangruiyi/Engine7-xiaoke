---
name: memory.db safeReindex丢chunks根因+SESSION_SYNC_LIMIT+archive扫描
description: reindex丢数据双根因——不扫archive + SESSION_SYNC_LIMIT=500只处理500个文件。增量sync扫archive才是正解，reindex本不该在正常运行时触发
type: project
---
# memory.db safeReindex 丢 chunks 完整根因 + SESSION_SYNC_LIMIT + archive 扫描

7/18 姐姐 memory.db 三次缩水事件 + 7/22 深入排查 + 7/23 发现 SESSION_SYNC_LIMIT。

## 第1轮误判（topics archive 路径问题）
发现 topics 文件从 `topics/feedback/` 归档到 `topics/archive/feedback/`，DB 路径没更新。sync 时找不到文件 → 修正 309 条路径。但只丢 324 条 chunks，不可能是主因。

## 第2轮误判（session _archive 路径问题）
session 文件在 `agents/main/sessions/_archive/*.jsonl`（18398 个归档文件），但 DB 存的是 `sessions/main/xxx.jsonl`。配置 legacySessionsDir 方案建议但未验证。

## 第3轮·再次缩水 + 临时止血（7/18 18:38-19:00）
- **再次缩水：** memory.db 1.53GB（18:38），昨天备份 2.04GB，.old 2.98GB。之前 legacySessionsDir 方案没生效/没跑。
- **发现完整备份：** pre-archive-test.1051（3.83GB）是上午10:51的完整备份。
- **恢复成功：** 用完整备份覆盖 memory.db → 3.83GB 恢复。
- **临时止血：** 代码层强制 `needsFullReindex = false`，不再触发 safe reindex。已在 engine-startup.ts 中修改。

## 第4轮·修根因而非禁用（7/22 19:40-20:10）
翀哥在香港期间决定改根因，而非一直禁用 reindex：
- archive 目录重命名 `_archive` → `archive`，修 `listSessionFilesForAgent` 扫 archive 目录
- 但 rebuild+start 后 reindex 完 memory.db 只有 1.64GB（vs 3.83GB），archive 扫描生效但数据还是丢了

## 第5轮·发现真正根因 SESSION_SYNC_LIMIT=500（7/23 01:10-01:30）
- **SESSION_SYNC_LIMIT = 500** — reindex 最多只处理 500 个 session 文件。姐姐 archive 9289 个 + active ~几百个，远超 500。reindex 只保留了前 500 个 session 的数据，其余全丢。
- **为什么只有 1.64GB：** 500 个 session 的数据量 ≈ 1.5GB，加上新 archive 扫描纳入的一小部分，接近 1.64GB。3.83GB 是旧 db 慢慢 incremental sync 累积的。
- **已经改 src：** SESSION_SYNC_LIMIT 500 → 50000（临时保命，回北京改流式分批处理）。

## 第6轮·发现第三个丢数据根因：.archived.* 文件没被扫描（7/22 深夜）

合并前验证 pre-archive-test (3.83GB, 53541 chunks) 和 bak.20260717_192749 (2GB, 17056 chunks) 后发现：

- **pre-archive-test 有 archive 老数据（6/15 之前）+ 今天最新 session，但缺 6/15-7/18 的一个月数据**
- **bak 有 6/15-7/18 的最新 active sessions，但缺 archive 老数据**
- 两个 db 互缺：6/15-7/18 的 session 在 `sessions/*.archived.*` 文件里（compact 机制产生的），不是 `sessions/archive/` 目录

**第三个根因：** `listSessionFilesForAgent` 只扫：
1. `sessions/*.jsonl`（active）
2. `sessions/archive/*.jsonl`（archive 目录）

**没扫：** `sessions/*.archived.*`（compact 产生的归档文件，23 个，日期 6/18-7/17）

## 第7轮·archive 目录来源修正 + filter 修复（7/23 直播准备期间）

7/23 翀哥直播准备前，我检查后纠正了 archive 目录的认知：

- **`sessions/*.archived.*` 文件：仅 23 个**——这是 engine compact 机制自己产生的，日期集中在 6/18-7/17
- **`sessions/archive/` 目录：9289 个文件**——这不是 engine 自己 compact 产生的，是之前从别处批量导入的历史 session（日期 3/17-6/15）
- 之前以为 18000+ 都是姐姐自己产生的，实际大部分是历史导入数据

**filter 修复（7/23）：** 我在 `listSessionFilesForAgent` 加了 `includes(".archived.")` filter，让 `.archived.*` 文件也能被增量 sync 扫到并入 chunk。翀哥走模式 B（改代码后 rebuild），姐姐 rebuild 后全部 channel connected，活过来了。

**关键认知：** 18000+ 文件扫描才是 OOM 根因——其中 9289 个是历史导入的 archive 目录文件，不是姐姐日常运行的产出。长期方案应考虑清理或分离历史 archive 数据。

## 最终合并方案（7/22 22:30 → 7/22 23:00 简化）

### 第一版（7/22 22:30）——hash去重+担心vec/FTS
以 bak（有最新数据）为基础，把 pre-archive-test 的 archive chunks 补进去：
- SQL: `INSERT OR IGNORE INTO chunks SELECT * FROM merge_source.chunks`
- bak 原有 17056 chunks，补了 36510 个新 chunks，跳过 17031 重复
- 合并后 **53566 chunks**（2.9GB）
- 担心 `chunks_vec` / `chunks_fts` 需重建

### 简化版（7/22 23:00）——翀哥指出早上5.7G就是直接叠加
翀哥纠正：不用去重，不用手动合vec/FTS。早上5.7G就是bak(2G) + pre-archive-test(3.83G)的chunks直接叠加：
- `ATTACH DATABASE 'other.db' AS other; INSERT INTO chunks SELECT * FROM other.chunks;`
- vec/FTS是虚拟表/全表索引，chunks插进去它们会自动重建
- 叠加后 **70597 chunks（17056+53541），3.3GB**（比3.83G小因为vec/FTS还没重建完）

**关键认知：** SQLite虚拟表和FTS索引不需要手动合并。chunks表直接叠加就行，索引引擎会在sync/search时自动重建。

**7/22 深夜-7/23 进展：**
- merge-base.db（2.9GB 合并版）已清理删除
- memory.db 稳住 3.83GB 的 pre-archive-test，姐姐能 search
- src 已改：allowReindex gate + archive 目录扫描
- **没写：** `.archived.*` 扫描代码（7/23 待弄，预计 5 分钟）
- **最终结论：** 增量 sync 扫 archive + `.archived.*` 才是正解，reindex 不该跑

## 关键认知转变：reindex ≠ incremental sync
- **incremental sync：** 正常运行时每次 search/sync 检查文件 hash，只处理新增/变更的文件。这才是日常数据入库路径。
- **reindex：** 全量重建——推倒整个 db 重做。只在配置变（provider/model/chunk size）时才触发，正常运行时不该触发。
- **真正修复方向：** 修 incremental sync 扫 archive 目录 + `.archived.*` 文件，而不是去折腾 reindex。reindex 干脆永远不跑也没事（no-op hotfix 反而是对的）。

**Why:** SESSION_SYNC_LIMIT=500 是代码里为防 OOM 设的保守上限——每个 session 要读全文→分 chunk→调 embedding→写 SQLite，同时处理太多内存会爆。但 500 对 archive 近万文件的姐姐来说太低。长期方案应改为流式分批处理，而非无脑提高 limit。另外 `.archived.*` 文件是完全独立的扫描盲区——compact 产生的归档不走 archive 目录，incremental sync 也扫不到。

**How to apply:**
- 短期 `memory.db` 已合并替换（53566 chunks, 2.9GB）
- 需修 `listSessionFilesForAgent` 同时扫 `sessions/*.archived.*`
- 回北京后修 incremental sync 扫 archive 目录 + `.archived.*`（这才是正解）
- 长期改 SESSION_SYNC_LIMIT 为流式分批处理，不设硬上限
