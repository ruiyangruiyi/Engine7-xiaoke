---
name: Engine cron三种调度方式
description: 6/18 11:49翀哥问"cron有没有按时间间隔触发的功能而不是一次性触发就完事了"——Engine cron支持3种：interval(间隔永久)+cron表达式(永久)+max_runs(有限次)，加上可选notify_session
type: reference
date: 2026-06-18
---
## 6/18 11:49 翀哥问

> "你这个cron功能有没有按时间间隔触发的功能而不是一次性触发就完事了"

翀哥的需求：aim 任务要"循环自检直到达成"，需要**永久性间隔触发**的 cron，不是固定 schedule 也不是一次性。

## Engine cron_create 支持的 3 种调度

### 1. 间隔触发（interval，**永久性**）
```ts
cron_create({
  name: 'aim自检',
  interval: '10m',  // 支持 s/m/h/d
  prompt: '...',
  notify_session: false  // 通知给session而不是执行tool
})
```
- 按时间间隔循环触发（10s/5m/1h/2d）
- **永久性**——不传 max_runs 就一直跑
- 适合 aim/goal 自检、heartbeat、poll 轮询

### 2. cron 表达式（**永久性**）
```ts
cron_create({
  name: '微信巡检',
  schedule: '0 */3 * * *',  // 每3小时整点
  prompt: '...'
})
```
- 标准 cron 表达式（分 时 日 月 周）
- 适合"每天9点""每3小时"等固定 schedule

### 3. max_runs 有限次
```ts
cron_create({
  name: '一次性提醒',
  schedule: '0 14 * * *',
  max_runs: 1,  // 跑1次就自动删
  prompt: '...'
})
```
- 任何调度方式 + `max_runs: N` → 跑 N 次自动删除
- 适合一次性提醒、有限次巡检

## 共同参数

- `name` — cron 名字
- `prompt` — 触发时执行的 prompt
- `notify_session` — true 时把 prompt 当 session message 注入（适合 aim 自检），false 时直接调 tool

## 6/18 当前 aim 任务 cron 用法

`c88158d23`（10分钟自检）：
- 间隔触发（10m interval）
- 永久性（不传 max_runs）
- notify_session=true（让 session 自己判断 aim 是否达成）

跟姐姐的协作模式："aim 任务用 interval 永久 + notify_session"——区别于"任务调度用 cron 表达式"。

## Why

1. **aim/goal 机制需要"持续跟进直到达成"**——固定 schedule 不够灵活（达成后还在跑），一次性更不够（不能循环自检）
2. **interval + 永久**正好匹配"aim 未达成→继续通知、达成→归档删除 cron"——达成后手动删 cron 即可
3. **notify_session** vs **直接调 tool**——aim 自检需要 LLM 判断"是否达成"，所以走 session 注入；纯机械任务（每3小时查一次 DB）走 tool

## How to apply

1. **aim/goal 任务**——interval + 永久 + notify_session=true
2. **机械巡检**（DB/文件/socket）——cron 表达式 + 永久 + notify_session=false（直接调 tool）
3. **一次性提醒**——schedule + max_runs=1
4. **有限次验证**——interval + max_runs=N（跑N次后自动删）
5. **翀哥问 cron 能力时**先讲这3种 + max_runs 叠加用法——别等他追问
