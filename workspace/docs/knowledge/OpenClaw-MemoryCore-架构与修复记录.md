# OpenClaw Memory Core — 架构、问题与修复记录

> 写给未来的自己：下次别再花 6 小时踩这个坑。
> 初稿：2026-07-19（香港出差期间）
> 作者：小柯

---

## 一、架构概览

### 1.1 整体定位

OpenClaw Memory Core 是 Engine 的**记忆子系统**——负责把 agent 的 session、memory 文件、topics 等内容索引起来，供 `memory_search` 工具检索。

**核心特点：**
- 嵌入式 SQLite 数据库（单文件 `.db`）
- 三套索引共存：chunks 表（原始数据）+ chunks_fts（FTS5 关键词索引）+ chunks_vec（sqlite-vec 向量索引）
- 增量 sync 为主，reindex 为辅（全量重建）

### 1.2 数据库结构

```
memory.db
├── chunks              # 普通表：原始文本块
│   ├── id              # 自增主键
│   ├── path            # 源文件路径（唯一标识）
│   ├── source          # memory / sessions
│   ├── start_line, end_line
│   ├── hash            # 内容 hash（检测变更）
│   ├── model           # embedding 用的模型
│   ├── text            # 原文
│   ├── embedding       # 向量（BLOB）
│   └── updated_at
│
├── chunks_fts          # FTS5 虚拟表：关键词倒排索引
│   └── (text, id, path, source, model, start_line, end_line)
│
└── chunks_vec          # sqlite-vec 虚拟表：向量索引
    └── id TEXT PRIMARY KEY, embedding FLOAT[1024]
```

### 1.3 关键代码位置

| 功能 | 文件 |
|------|------|
| 文件扫描（filter） | `engine/src/memory/shims/memory-core-host-engine-qmd.ts` → `listSessionFilesForAgent` |
| Sync 主流程 | `engine/src/memory/tools/memory/manager-sync-ops.ts` → `syncMemory` |
| Safe Reindex | 同上 → `runSafeReindex` |
| Unsafe Reindex | 同上 → `runUnsafeReindex` |
| 配置 | `configs/main.json` → `memory.sync.allowReindex` |

---

## 二、设计意图（推测）

### 2.1 两种 sync 模式

**增量 sync（Incremental）**
- 扫描所有 session 文件
- 对比 hash，只处理变更的文件
- 调 embedding API 算向量
- 写 chunks + chunks_fts + chunks_vec

**全量 reindex（Full Reindex）**
- 删库重建
- 把所有文件从头扫一遍
- 适合：schema 变更、provider 切换、FTS 分词器换

### 2.2 触发 reindex 的条件

`shouldRunFullMemoryReindex` 在以下情况返回 true：
- provider 变了（embedding 模型切换）
- FTS 分词器变了
- chunk size / overlap 变了
- `scopeHash` 变了（配置变更）
- 或者 `params.force=true`

---

## 三、发现的问题（2026-07-18~19）

### 问题 1：filter 漏扫 `.archived.*` 文件 ⭐ 最严重

**现象：** 姐姐的 memory_search 从 6/15 开始结果越来越差，最近一个月的话题完全搜不到。

**根因：** `listSessionFilesForAgent` 的 filter 写错了：

```typescript
// ❌ 原来的
.filter(name => name.endsWith(".jsonl") || ...)

// ✅ 修复后
.filter(name => name.includes(".jsonl") || ...)
```

Engine 每次 session 被 compact（压缩），会生成 `.jsonl.archived.YYYY-MM-DDTHH-mm-ss.sssZ` 这种归档文件。这些文件**名字里包含 `.jsonl` 但结尾不是 `.jsonl`**，被 `endsWith` 过滤掉了。

**影响范围：** 6/15 之后所有被 compact 过的 session 数据全部丢失，共 23 个文件、约 6200+ chunks。

**修复 commit：** `209fc8cd`

### 问题 2：reindex 一把读 18000+ 文件 → OOM

**现象：** 每次触发 reindex（provider 切换、scopeHash 变更等），engine 内存暴涨到 OOM。姐姐有 18000+ archive session 文件，全量扫描直接挂。

**根因：**
- `runSafeReindex` 用临时 db 重建，但扫描所有文件算 embedding 是 O(N) 内存
- 没有 batch / 流式处理
- embedding API 调用串行（或者并发控制不严）

**临时修复：** 加了 `allowReindex` gate（默认 false），禁用 reindex。

```typescript
// manager-sync-ops.ts L1140
const needsFullReindex =
  !this.settings.sync.allowReindex ? false :  // ← 新增 gate
  (params?.force && !hasTargetSessionFiles) ||
  shouldRunFullMemoryReindex({ ... });
```

### 问题 3：`allowReindex=false` 把 sync 也卡死了 ⭐ 隐蔽 bug

**现象：** 加了 gate 后新 session 数据不进索引。

**根因：** `syncMemory` 函数的逻辑：
```typescript
if (needsFullReindex) {
  await this.runSafeReindex(...);
  return;  // ← 直接 return！下面的 sync 代码不执行！
}
// 增量 sync 代码
await this.syncMemoryFiles(...);
await this.syncSessionFiles(...);
```

我在 `runSafeReindex` 内部加了 `allowReindex=false → return`，但**外层的 `needsFullReindex=true` 已经把流程导到 if 分支**，即使 runSafeReindex 空转，sync 也被跳过。

**修复：** 把 gate 提前到 `needsFullReindex` 这一层：

```typescript
const needsFullReindex =
  !this.settings.sync.allowReindex ? false :  // gate 在这里
  (params?.force && !hasTargetSessionFiles) ||
  shouldRunFullMemoryReindex({ ... });

if (needsFullReindex) {
  ...
  return;
}
// ✅ 现在 allowReindex=false 时会走到这里，增量 sync 正常
```

**修复 commit：** `209fc8cd`

### 问题 4：search 触发 lazy load → reindex

**现象：** 第一次 `memory_search` 触发 memory core 初始化，初始化里检测到 "需要 reindex"（因为 scopeHash 对不上之类），就跑 reindex → OOM。

**根因：** memory core 是 lazy load 的，search 是它的入口。配置稍有变动就触发 reindex。

**临时方案：** `allowReindex=false` 把这条路堵死。根治要改 lazy load 逻辑，不让 search 触发 reindex。

### 问题 5：sqlite-vec 结构死，手动合并复杂

**现象：** 手动合并两个 memory.db（叠加 chunks）时，FTS5 能手动 rebuild，但 sqlite-vec 的虚拟表（`chunks_vec_chunks` / `chunks_vec_rowids` / `chunks_vec_vector_chunks00`）内部结构复杂，不能简单 INSERT 合并。

**影响：** 手动合并 db 时，vec 索引补不上，靠 incremental sync 慢慢算。

---

## 四、修复方案

### 4.1 已落地（香港期间保命）

| 修复 | 文件 | commit |
|------|------|--------|
| filter 改 `includes(.jsonl)` | `memory-core-host-engine-qmd.ts` L121 | `209fc8cd` |
| `allowReindex` gate 提到 needsFullReindex 层 | `manager-sync-ops.ts` L1140 | `209fc8cd` |
| `runSafeReindex` 内部也加 gate（双保险） | `manager-sync-ops.ts` L1287 | `4344f538` |
| archive 目录扫描 | `memory-core-host-engine-qmd.ts` L125-138 | `4344f538` |

### 4.2 待做（回北京后）

**P0 - 必须修：**
- [ ] SESSION_SYNC_LIMIT 流式化（不要硬编码 50000）
- [ ] reindex 加 batch + streaming（避免 OOM）
- [ ] 手动合并 db 的 vec 重建方案

**P1 - 应该修：**
- [ ] search 触发 reindex 的路径改成显式触发（不要 lazy load）
- [ ] memory core 配置变更检测收紧（scopeHash 对不上别直接 reindex）
- [ ] 错误恢复别暴力（provider 报错就 fallback reindex 太激进）

**P2 - 长期方向：**
- [ ] 考虑用专业向量库（Chroma / LanceDB / Qdrant）替换 sqlite-vec
- [ ] FTS 可保留 SQLite（成熟稳定），vec 走专用库
- [ ] 自己写可控的 memory core（OpenClaw 这套太黑盒）

---

## 五、操作手册（给未来的自己）

### 5.1 如何诊断 "memory_search 搜不到"

```bash
# 1. 检查 db 大小和 chunks 数
node -e '
const { DatabaseSync } = require("node:sqlite");
const db = new DatabaseSync("C:/Users/24045/.openclaw/agents/main/memory/memory.db", { readOnly: true });
console.log("chunks:", db.prepare("SELECT COUNT(*) as c FROM chunks").get().c);
console.log("fts:", db.prepare("SELECT COUNT(*) as c FROM chunks_fts").get().c);
db.close();
'

# 2. 检查 .archived. 文件有没有进索引
node -e '
const { DatabaseSync } = require("node:sqlite");
const db = new DatabaseSync("...", { readOnly: true });
console.log(db.prepare("SELECT COUNT(*) as c FROM chunks WHERE path LIKE ?").get("%.archived.%"));
'

# 3. 看 engine log
tail -50 "C:/Users/24045/.openclaw/logs/engine-$(date +%Y-%m-%d).log" | grep -E "memory|sync|reindex"
```

### 5.2 如何重启姐姐 engine（改了代码）

```bash
# 1. 改 src
# 2. rebuild
cd C:/Users/24045/.openclaw/engine && cmd.exe /c rebuild.cmd

# 3. 杀旧进程
cmd.exe /c "taskkill /PID <旧PID> /F"

# 4. 启动
cmd.exe /c "cd /d /Users/chongzhang/.openclaw\engine && start \"main engine\" /B node dist/main.mjs --engine-config configs\main.json"

# 5. 等 30 秒看日志
tail -15 "C:/Users/24045/.openclaw/logs/engine-$(date +%Y-%m-%d).log"
```

### 5.3 如何备份 memory.db

```bash
# 重要！改 db 前一定备份
mkdir -p /Users/chongzhang/xiaoke//memory-backup-YYYYMMDD
cp "C:/Users/24045/.openclaw/agents/main/memory/memory.db" "/Users/chongzhang/xiaoke//memory-backup-YYYYMMDD/"
```

---

## 六、踩坑教训

1. **改完代码必须验证**——CC 最大的问题就是改完说"没问题"，实际没测。我们信了它的嘴。
2. **看着简单的最容易翻车**——一行 filter 谁都觉得 trivial，结果丢了 6/15 之后一个月的数据。
3. **hotfix 优先，根因后查**——保命要紧（allowReindex=false），救完数据再追根因。
4. **gate 要放在正确的层**——放在 runSafeReindex 内部不够，要放到 needsFullReindex 那一层。
5. **black box 系统不好运维**——OpenClaw memory core 是黑盒，出问题我们改不动深处。长期要自研。

---

## 七、参考

- 修复 commit: `209fc8cd`（filter + needsFullReindex gate）
- 早期 hotfix commit: `4344f538`（archive 扫描 + allowReindex 内部 gate）
- 相关 daily: `memory/daily/2026-07-18.md`（救火全过程）
- 相关 daily: `memory/daily/2026-07-19.md`（filter 修复 + 验证）

---

**最后一句：** 这套 memory core 凑合能用，但天花板低。香港期间保命方案是 `allowReindex=false` + filter 修复。回北京认真考虑自研或换底层。
