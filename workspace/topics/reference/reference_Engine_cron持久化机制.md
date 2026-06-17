---
name: Engine cron持久化机制
description: Engine的cron通过tasks.json（启动时loadTasks自动加载）实现持久化，不是临时cron_create
type: reference
keywords: [cron, tasks.json, loadTasks, cron-plugin, 持久化, Engine]
created: 2026-06-15
---

# Engine cron持久化机制

## 核心事实

Engine的cron已经有持久化机制，**不需要额外写代码**：

- 文件位置：`<stateDir>/cron/tasks.json`（跟OpenClaw的`cron/jobs.json`同位置、同格式）
- 启动加载：`cron-plugin.ts` 的 `start()` → `loadTasks()` 自动读取
- 加载逻辑：读tasks.json → 按 `name` 或 `id` 去重 → 新的建上，已有的不动
- 编辑方式：手动写tasks.json即可，重启自动恢复

## 跟OpenClaw的区别

| 维度 | OpenClaw | Engine |
|------|---------|--------|
| 配置文件 | `cron/jobs.json` | `cron/tasks.json`（不同名但同位置同格式） |
| 加载方式 | gateway启动时读jobs.json注册 | engine启动时loadTasks()加载 |
| 手动创建 | 无此功能 | 有 `cron_create` 工具（运行时建） |
| 持久化 | 依赖jobs.json文件 | 依赖tasks.json文件 |

## 实际应用：小忆内心独白

2026-06-15直接手写tasks.json配置小忆的cron，UUID保持跟OpenClaw原版一致 `f1e1cc55-...`，完整8步prompt原封不动照搬。不用改Engine代码。

## 注意事项

- cron_create创建的临时任务重启后可能丢失，正式任务统一放tasks.json
- tasks.json里任务跟cron_create可以共存，loadTasks去重只覆盖同名/同id的
