# OpenClaw memory-core 深度分析 + 集成结果 (2026-05-28)

## 源码分析

CC完整阅读了OpenClaw memory-core源码后的分析。

### SQLite 表结构

| 表 | 字段 | 用途 |
|---|------|------|
| `files` | path, source, hash, mtime, size | 文件索引（变更检测） |
| `chunks` | id, path, source, start_line, end_line, text | 分块内容 |
| `chunks_fts` | — | FTS5 全文索引 |
| `chunks_vec` | — | sqlite-vec 向量索引 |
| `embedding_cache` | — | 向量缓存（避免重复计算） |

### 索引过程

1. 监控 `memory/*.md` 和 `MEMORY.md`
2. **分块策略**：400 token 一块，80 token 重叠（保证跨块上下文连续性）
3. 每块生成 embedding 向量
4. 写入 `chunks` + `chunks_fts` + `chunks_vec` 三表

### 搜索流程

#### 双路召回
- **向量搜索**：query → embedding → cosine similarity → top candidates
- **关键词搜索**：SQLite FTS5 + BM25 排名

#### 混合合并
- 默认权重：**70% 向量 + 30% 关键词**
- 可选 MMR 去重（结果多样性）
- 可选时间衰减（新记忆权重高）

#### 兜底机制
```
hybrid → 纯向量 → 纯 FTS5 关键词
```

### 关键 SQL

```sql
-- FTS5 关键词搜索
SELECT id, path, source, start_line, end_line, text,
       bm25(chunks_fts) AS rank
FROM chunks_fts
WHERE chunks_fts MATCH ?
ORDER BY rank ASC
LIMIT ?

-- 向量搜索
SELECT c.*, vec_distance_cosine(v.embedding, ?) AS dist
FROM chunks_vec v
JOIN chunks c ON c.id = v.id
WHERE v.embedding MATCH ?
ORDER BY dist ASC
LIMIT ?
```

### memory_get 实现

- 按路径精确读取 memory 文件
- 默认 120 行 / 12000 字符
- 超出给 `nextFrom` 续读参数
- `corpus` 参数切换：memory / wiki / all

## 集成结果 (2026-05-28 完成)

### 实现策略

**直接 import openclaw memory-core**（工具层）+ **memory-host-sdk**（搜索引擎），不重复造轮子。

- 从 openclaw v2026.5.18 源码扒了 ~80 个 TS 文件
- 创建 20+ shim 模块替代 `openclaw/plugin-sdk` 和 `@openclaw/fs-safe` 依赖
- 编译产出 JS（241 个类型错误待修，不影响运行）

### 集成踩坑

1. **shim 函数签名必须匹配位置参数** — OpenClaw 调 resolveAgentDir/resolveAgentWorkspaceDir 用位置参数不用命名参数，shim 必须对应
2. **enforceEmbeddingMaxInputTokens 需要 3 个参数** — 少传会 undefined 报错
3. **sync 索引流程空 chunk 问题** — DB 表结构正确但全空，根因是 shim 函数签名不匹配导致文件发现后跳过索引
4. **sqlite-vec 未安装** — 向量搜索受限，但 FTS5 文本搜索不受影响

### 验证结果

- ✅ **memory_get** — 成功读取 workspace 记忆文件，支持分页截断
- ✅ **memory_search** — 端到端跑通
  - 877 个 workspace 文件成功索引
  - Ollama bge-m3 embedding 实际工作
  - 搜索 "翀哥" 返回结果，综合得分 0.68（向量 0.63 + 文本 0.81）
  - 配置与 openclaw.json 完全一致

### Embedding 配置

```json
{
  "provider": "ollama",
  "model": "bge-m3",
  "baseUrl": "http://127.0.0.1:11434"
}
```

### 搜索范围配置

```json
{
  "sources": ["memory", "sessions"],
  "extraPaths": ["topics", "docs"]
}
```

### 待办

- 清理 debug 代码
- 安装 sqlite-vec 扩展解锁完整向量搜索
- 修 241 个类型错误
