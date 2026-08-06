---
title: OpenClaw Memory Core DB 实测研究
author: 张小柯
date: 2026-05-28
---

# OpenClaw Memory Core DB 实测数据

> 测试库：`engine/test-data/main.sqlite`（496MB，从线上拷贝）
> 线上库（只读！）：`.openclaw-new/memory/main.sqlite`

## 核心数据

| 指标 | 值 |
|------|-----|
| chunks 总数 | 4,790 |
| 文件总数 | 761 |
| 向量维度 | 1024 (bge-m3) |
| 分块大小 | 400 tokens, 80 overlap |
| Embedding | Ollama bge-m3（本地） |
| FTS5 分词 | unicode61 |
| 数据库大小 | 496MB |

## 表结构

- `chunks` — 记忆分块（text + embedding JSON字符串）
- `chunks_vec` — sqlite-vec 向量索引（float32 BLOB）
- `chunks_fts` — FTS5 全文搜索
- `embedding_cache` — 向量缓存（避免重复embed）
- `files` — 文件索引
- `meta` — 全局配置

## 双写机制

- `chunks.embedding` = JSON "[-0.075, ...]"（~8KB/条，人类可读）
- `chunks_vec` = BLOB（float32 packed，高效搜索）
- 设计意图：调试/迁移用JSON，生产搜索用BLOB

## sqlite-vec

```bash
pip install sqlite-vec==0.1.9
```

KNN搜索示例：
```python
results = db.execute("""
    SELECT rowid, distance FROM chunks_vec
    WHERE embedding MATCH ?
    ORDER BY distance LIMIT 10
""", [struct.pack(f'{1024}f', *query_vec)])
```

## sync决策

共用同一个 main.sqlite → 无需sync。分库 → 需双向同步 chunks/fts/vec。
