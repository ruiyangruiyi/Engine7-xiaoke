---
title: Memory Core DB + sqlite-vec 实测研究
date: 2026-05-28
author: 张小柯
data_source: .openclaw-new/memory/main.sqlite (拷贝到 engine/test-data/)
---

# OpenClaw Memory Core 数据库结构 + sqlite-vec

## 数据库表结构 (main.sqlite, 496MB)

| 表 | 行数 | 用途 |
|---|---|---|
| chunks | 4,790 | 记忆分块(text + embedding JSON + 元数据) |
| chunks_fts | — | FTS5全文搜索虚拟表 |
| chunks_vec | — | sqlite-vec向量搜索虚拟表 |
| embedding_cache | — | 向量缓存(避免重复embed) |
| files | 761 | 文件索引(memory/ + sessions/) |
| meta | 1 | 全局配置(model/dims/chunk参数等) |

## chunks 表关键设计

```sql
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,       -- SHA256(path+start_line+end_line)
    path TEXT,                 -- 'memory/2026-03-10.md'
    source TEXT,               -- 'memory' | 'sessions'
    start_line INTEGER,
    end_line INTEGER,
    hash TEXT,                 -- 文本内容hash
    model TEXT,                -- 'bge-m3'
    text TEXT,                 -- 分块原文
    embedding TEXT,            -- 向量JSON数组！"[-0.075, -0.026, ...]"
    updated_at INTEGER         -- 毫秒时间戳
);
```

**双写机制：**
- `chunks.embedding` = JSON字符串（~8KB/条，1024维，人类可读）
- `chunks_vec` = BLOB（struct.pack float32，高效向量搜索）

## meta 配置

```json
{
  "model": "bge-m3",
  "provider": "ollama",
  "sources": ["memory", "sessions"],
  "chunkTokens": 400,
  "chunkOverlap": 80,
  "ftsTokenizer": "unicode61",
  "vectorDims": 1024
}
```

## sqlite-vec 用法

```python
import sqlite3, sqlite_vec, struct, json

db = sqlite3.connect("main.sqlite")
db.enable_load_extension(True)
sqlite_vec.load(db)

# 读取已有向量做KNN搜索
row = db.execute("SELECT embedding FROM chunks LIMIT 1").fetchone()
vec = json.loads(row[0])
packed = struct.pack(f'{len(vec)}f', *vec)

results = db.execute("""
    SELECT rowid, distance
    FROM chunks_vec
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT 10
""", [packed]).fetchall()
```

- sqlite-vec版本: 0.1.9 (`pip install sqlite-vec`)
- 向量存为BLOB (struct.pack float32数组)
- KNN搜索通过 `WHERE embedding MATCH ? ORDER BY distance`
- 结果通过rowid关联回chunks表获取原文

## 关键数据

| 指标 | 值 |
|---|---|
| chunks总数 | 4,790 |
| 文件总数 | 761 |
| 向量维度 | 1024 |
| Embedding模型 | bge-m3 (Ollama本地) |
| 分块大小 | 400 tokens |
| 分块重叠 | 80 tokens |

## 测试数据库

- 位置: `C:\Users\24045\.openclaw\engine\test-data\main.sqlite`
- 从 `.openclaw-new/memory/main.sqlite` 拷贝，可随意操作
- **⚠️ 绝对不要动线上的数据库**

## sync建议

如果Engine和姐姐共用同一个main.sqlite，sync问题不存在。
分库才需要双向同步 chunks/fts/vec 数据。
