---
name: engine7 init 加 --force 重配参数
description: 2026-08-03 Amy 重跑 init 卡死→补 --force 跳过 .engine7 已存在检查直接重配，commit 014de0e2
type: project
date: 2026-08-03
---

# engine7 init --force 参数

**触发：** 8/3 深夜 Amy 要重新配飞书凭证，`engine7 init` 检测到 `.engine7` 目录已存在直接 return——没有任何重配选项

**改的代码：**
- `engine7 init` 加 `--force` 参数
- 命中 --force 时跳过 `.engine7` 目录已存在检查，直接重配
- return 语句同步更新（不再 return error）
- help 文本加 --force 说明

**commit：** `014de0e2`，已 push

**Why:** 非技术用户要重新配凭证（比如换 app_secret、加新 channel）时，必须手动 `rmdir /s /q` 清掉目录才能 init——太重也不安全（万一别的配置文件在里面）

**How to apply:**
- Amy 那边等 npm 版更新才能用——目前手动 `rmdir /s /q` 是 fallback
- 后续任务：#132（8/5）把 feishu-bot-bootstrap 集成进 init 流