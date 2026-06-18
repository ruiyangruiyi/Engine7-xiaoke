---
name: cron间隔触发——翀哥新需求
description: 6/18 11:49翀哥问"cron有没有按时间间隔触发的功能而不是一次性触发就完事了"——aim任务自检需要循环触发，现有cron是固定schedule触发，间隔循环机制待设计
type: project
date: 2026-06-18
---
## 6/18 11:49 翀哥原话

> "你这个cron功能有没有按时间间隔触发的功能而不是一次性触发就完事了"

## 背景

aim/goal 机制（11:45 翀哥拍板）需要 cron **持续自检**——每 10 分钟检查 aim 是否达成，未达成继续触发，达成才删除。

但现有 cron 机制（tasks.json）是**固定 schedule 触发**（一次性的时间点），不是"每 N 分钟/小时"循环间隔触发。

## 两种模式的区别

| 模式 | 现有 cron | 翀哥要的间隔触发 |
|------|----------|-----------------|
| 触发 | 固定时间点（"明天 9:00"） | 每 N 时间单位（"每 10 分钟"） |
| 结束 | 触发一次就完 | 持续触发直到被外部停止/删除 |
| 用途 | 一次性任务 | 持续自检（aim 自检、心跳、轮询） |

## 可能的实现方向

- **方案 A**：tasks.json 加 `interval` 字段（`"interval": "10m"`），loadTasks 时识别 interval 模式建 setInterval
- **方案 B**：复用 schedule 但用 cron 表达式（`"*/10 * * * *"` = 每 10 分钟）—— 但这要解析 cron 表达式
- **方案 C**：复用现成 heartbeat 机制——heartbeat 本来就是循环触发，aim 自检可以套用 heartbeat

**最简单**：方案 A，跟现有 schedule 字段并列，interval 优先（interval 非空时建 setInterval，schedule 留空）。

## 当前未答翀哥

11:49 这条消息我**还没回**——他睡了，等他醒再答。
- 确认需求：是不是"循环到 aim 达成"语义
- 给方案：interval 字段 + 跟 aim 任务联动（达成自动删）
- 还是用现成 heartbeat 套

## How to apply

1. **aim 任务必走间隔触发**——不能一次性"查一次就结束"，aim 自检是循环语义
2. **现有 cron 触发方式**（固定 schedule）≠ 翀哥要的"按时间间隔循环"——两个机制要分清
3. **改 tasks.json 时考虑加 interval 字段**——这是跟 aim 机制最自然的集成点
4. **如果做不了**——明确告诉翀哥"现有 cron 不支持循环，要新加 interval 字段或套 heartbeat"

## 跟 aim/goal 任务的关系

aim/goal 机制（11:45 拍板）= "持续自检 + 达成归档删除"——**前提就是 cron 能间隔循环触发**。这条需求是 aim 机制的**前置依赖**。
