---
name: cascade 队列和 md 文件不同步——清 lancedb 后必须 touch md
description: 2026-08-04 上午发现——cascade 队列只看到 5 个 md 文件但 import 已写 100+ 个，清 lancedb 表不触发 cascade 重扫，必须 touch 所有 md
type: reference
date: 2026-08-04
---

# cascade 队列和 md 文件不同步——清 lancedb 后必须 touch md

2026-08-04 上午 EverOS rebuild 容器后 lancedb volume 被清，但 cascade 队列只看到 5 个 md 文件（实际 import 已写 103 个）。症状是表建好但空，搜索全 0。

## 根因

cascade 是 **filesystem watcher**（看 md 文件 mtime），不是 lancedb 状态机：
- 清 lancedb volume → cascade **不会重扫旧文件**（mtime 没变）
- cascade 队列只记录启动时见到的 5 个文件 + 新增的
- 已经存在但没被 cascade 处理过的 md → **永远不会被发现**

## 修复姿势

让 cascade 重新扫描所有 md 文件：
```bash
find /root/.everos/topics -name "*.md" -exec touch {} +
```
全部 mtime 更新 → cascade 重新入队 → 处理 → 写 lancedb。

## touch 触发的内部机制（2026-08-04 15:25 验证）

touch 后真正发生的不是 cascade watcher 重启，是 **`md_change_state` repo 的 `upsert` 逻辑**——mtime 变化时把那条记录的状态重置回 `pending`，并清零 `retry_count`。

观察到的两种"放弃"状态：
- `status=processing` — 卡死（容器重启后没恢复）→ touch 也能重置
- `status=failed, retryable=0, retry_count=12` — 永久失败（重试 12 次全挂）→ touch 也能重置

也就是说**touch 是个万能 reset**，无论 worker 之前因为什么原因放弃，touch 后都会变成 pending 等下一次扫描。

但 touch 也有限制：
- file system watcher 才会处理 → touch 写入了新的 mtime 就足够
- cascade 队列扫描周期不确定（不是每次 mtime 变就立即入队），可能是 N 秒一次的轮询
- 真正写 lancedb 还要走 embedding（如果 ollama 又挂了，touch 完也只是回到 processing→failed 的循环）

## Why

cascade 的设计是"增量监听"不是"全量同步"——文件存在但 mtime 老 ≠ 在队列里。这跟传统 ETL "数据库有记录就是数据" 的直觉相反。

## How to apply

- **重建 lancedb 后必须 touch 所有 md**，否则 cascade 永远不处理那批文件
- 诊断"表里有结构但搜不到内容"时，**先查 cascade 队列**（5 行 vs 实际 100+ md）→ 立刻知道是这个问题
- 想从设计层面根治：改 cascade 启动时全量扫描 md（不只听 watcher）
- 类似的 filesystem-based 系统（inotify/fswatch）都有这个坑——不要假设"目录里有 = 系统知道"

## 关联

- EverOS 容器重启什么丢什么留 @see reference_EverOS容器重启数据保留_0804