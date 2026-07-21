# #95 Stop hook notification

> 2026-07-17 翀哥需求

## 背景

agent 等"外部条件"（服务重启/SSH恢复/文件出现）时停了就不会再检查。凌晨实例：等 vLLM 重启，SSH 断了，直接停了，翀哥得手动叫起来。

## 翀哥设计

Stop hook 之前 → 检查有没有在等的东西/没干完的事 → 有的话注册 notification（带 description）→ 默认 5 分钟后唤起 → 也可指定时间。

复用 nudge/enqueueNotification 的唤起能力，触发源是 Stop hook 自动注册。

## 现有机制

- **Stop hook**：query.ts:400-423，executeStopHooks 已接线，能 preventContinuation + 注入 additionalContext
- **enqueueNotification**：task-manager.ts:124，已有 callback → dispatcher 注入主 session
- **NudgePlugin**：plugin.ts，5min tick，读 SESSION-STATE 解析活跃任务
- **CalendarReminderPlugin**：reminder-plugin.ts，5min tick，查 dueReminders → enqueueNotification

## 方案

在 Stop hook 处（query.ts:400）加一个 callback hook，逻辑：
1. agent 要停了 → 调 Stop hook
2. hook 内检查：有没有 pending notification 需要注册？
   - LLM 判断：从最近对话上下文看有没有"在等的东西"
   - 或 agent 自己在停止前主动声明"我在等 X"
3. 有 → 注册一个延迟 notification（默认 5 分钟）→ 用 enqueueNotification
4. notification 带 description："你在等 vLLM 重启，回去检查"
5. 5 分钟后唤起 → agent 检查条件 → 满足干活+不续期，不满足再注册一个

## Phase 拆分

- [ ] Phase 1: 设计 notification 注册/存储/到期触发机制
- [ ] Phase 2: 实现 Stop hook callback（检查+注册 notification）
- [ ] Phase 3: 实现 notification 到期唤起（复用 enqueueNotification）
- [ ] Phase 4: 验证（模拟等待场景）

## 验证标准

1. agent 等外部条件停了 → 5 分钟后自动被唤起
2. notification 带 description，agent 知道回去检查什么
3. 条件满足 → 干活 + 不再续期
4. 条件不满足 → 自动续期下一次 tick
