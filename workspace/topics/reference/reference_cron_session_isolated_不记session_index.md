---
name: cron session 不在 session-index 中
description: cron session 是 isolated 类型临时session，不出现在 session-index.json 中是正常的
type: reference
---
# Cron session 不出现在 session-index 中

## 现象
6/15 翀哥发现 `session-index.json` 里只有 `scope:main` 的条目，`cron:c1a2b3c4` 不在其中，问是否异常。

## 正常现象
这是预期的。因为：

- `session-index.json` 只记录**持久 session**（`scope:main` 这类长期活跃的 session）
- cron session 的 `sessionTarget` 是 `"isolated"`（隔离模式），每次 tick 创建新 session 用完即弃
- isolated session 不会注册到 session-index 中
- **cron session 没跑过的话（runCount=0），session文件和platform-map条目都不会创建** — 所以 `platform-map.json` 里虽然能看到 `cron:c1a2b3c4` 的key，但 `session-index.json` 里没有对应的sessionId→文件路径映射

## 如何验证 cron session 确实被创建了
- 查看 `agents/main/sessions/` 目录下的 JSONL 文件（如 `c1a2b3c4` 对应的 session ID）
- 或者通过 `platform-map.json` → 查对应的 sessionId
- cron 的执行日志在 `runs/` 目录下

## 参考
- [cron types](/Users/chongzhang/.openclaw\engine\src\cron\types.ts) 中的 `sessionTarget` 字段定义
- `session-index.json` 和 `platform-map.json` 都在 `agents/main/sessions/` 下
