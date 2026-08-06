---
name: Engine 已有 /reload 热加载 features 机制
description: 6/18发现Engine已有完整/reload命令热加载机制（L1077-L1119），`deps.features = newConfig.profile.features` 可直接热更新features
type: reference
date: 2026-06-18
---
6/18 16:00 做 topic-recall 命令开关时发现 Engine 已经存在完整的 `/reload` 热加载机制。

## 位置
- handle-query.ts L1077-L1119（`/reload` 命令处理）
- `/reload` 流程：读 config 文件 → `loadConfig()` → `deps.features = newConfig.profile.features`
- **features 热加载已经原生支持**，不依赖 watcher 或 API

## 为什么没直接用
翀哥要的 `/topic-recall on/off` 是命令行直接切（不让姐姐手动改 JSON），所以还是做了 slash command。但 `/reload` 是底层基础——如果不做命令，手动改 xiaoke.json + `/reload` 也能热加载 features。

## How to apply
- 要热加载任何 config 改动（features/profile 等）：改 xiaoke.json → `/reload`
- slash command 可以直接调 `deps.features['xxx'] = true/false` runtime 生效（不需要走 /reload 重读文件）
- 但 slash command 改动默认不持久化——要持久化必须同步写 xiaoke.json 磁盘
