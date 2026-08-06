---
title: Memory Core DB Hands-On Research
author: 张小柯
date: 2026-05-28
source: /mnt/c/Users/24045/.openclaw/engine/test-data/main.sqlite
---

# Memory Core DB 实测数据 (2026-05-28)

测试数据库从 `.openclaw-new/memory/main.sqlite` 拷贝到 `engine/test-data/main.sqlite`（496MB）。

## 实测数据量

| 表 | 行数 |
|----|------|
| chunks | 4,790 |
| files | 761 |
| embedding_cache | ~数条 |
| meta | 1 |

## 完整表结构（SQLite PRAGMA 实测）

### chunks（核心记忆分块）
- `id` TEXT PK — SHA256 hash (path+start_line+end_line)
- `path` TEXT — 如 'memory/2026-03-10.md'
- `source` TEXT — 'memory' | 'sessions'
- `start_line` / `end_line` INTEGER — 行范围
- `hash` TEXT — 文本内容hash
- `model` TEXT — 'bge-m3'
- `text` TEXT — 分块原文
- `embedding` TEXT — **JSON字符串**！如 "[-0.075, -0.026, ...]"，1024维
- `dims` INTEGER — 1024
- `updated_at` INTEGER — 毫秒时间戳

### chunks_vec（sqlite-vec虚拟表，通过rowid关联chunks）
- `chunks_vec_vector_chunks00` — 实际float32 BLOB向量
- `chunks_vec_rowids` — rowid映射（sqlite_sequence seq=221081）
- `chunks_vec_chunks` — 分段元数据（sqlite_sequence seq=145）

### chunks_fts（FTS5虚拟表）
- `chunks_fts_content/data/docsize/idx` — FTS5标准辅助表
- 分词器：unicode61（meta表确认）

### embedding_cache（向量缓存）
- `provider` TEXT — 'ollama'
- `model` TEXT — 'bge-m3'
- `provider_key` TEXT — provider标识hash
- `hash` TEXT — 输入文本hash
- `embedding` TEXT — 向量JSON（同chunks格式）
- `dims` INTEGER — 1024
- `updated_at` INTEGER

### files（文件索引）
- `path` TEXT — 'memory/2026-03-10.md'
- `source` TEXT — 'memory' | 'sessions'
- `hash` TEXT — 文件内容hash
- `mtime` REAL — 文件修改时间
- `size` INTEGER — 文件大小

### meta（全局配置）
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

## 关键发现：双写机制

- `chunks.embedding` = JSON字符串（~8KB/条，人类可读）
- `chunks_vec` = BLOB（float32 pack，高效向量搜索）
- 两边都存了向量，是冗余双写设计

## sqlite-vec 安装与验证

```bash
pip install sqlite-vec==0.1.9  # 最新稳定版
```

Python验证代码：
```python
import sqlite3, sqlite_vec, struct, json

db = sqlite3.connect("engine/test-data/main.sqlite")
db.enable_load_extension(True)
sqlite_vec.load(db)

# 读取已有向量做测试
row = db.execute("SELECT embedding FROM chunks LIMIT 1").fetchone()
vec = json.loads(row[0])
packed = struct.pack(f'{len(vec)}f', *vec)

# KNN 搜索
results = db.execute("""
    SELECT rowid, distance
    FROM chunks_vec
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT 5
""", [packed]).fetchall()
```

## sync建议

如果Engine和姐姐共用同一个main.sqlite，sync问题不存在（直接读写同一库）。
分库才需要双向同步 chunks/fts/vec 数据。

## ⚠️ 线上数据库位置（绝对只读！）
- 新版（v2026.5.3）：`/mnt/c/Users/24045/.openclaw-new/memory/main.sqlite`
- 旧版（v4.11）：`/mnt/c/Users/24045/.openclaw/` 下（不要碰）
