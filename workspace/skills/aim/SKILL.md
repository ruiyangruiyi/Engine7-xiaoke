---
name: aim
description: 团队协作目标追踪机制。派活→起cron盯→自检→达成→归档→block防循环。用法：/aim create、/aim status、/aim complete、/aim archive
allowed-tools: Bash(cron_create:*) Bash(cron_list:*) Bash(cron_delete:*) Bash(reply_blocklist:*) read write edit glob
---

# aim — 团队协作目标追踪

> 核心流程：写目标 → 催到完 → 归档 → block

## 命令

### `/aim create` — 创建 aim 任务

参数（从用户消息或 args 中提取）：
- `task`: 任务描述（必填）
- `goal`: 可验证的完成条件（必填，不能是模糊描述）
- `channel`: 协作频道（必填，如 discord#CC频道 或 feishu）
- `assignee`: 指派给谁（必填，agent 名字或 ID）
- `interval`: cron 检查间隔（默认 10min）
- `archive`: 归档路径（默认 workspace/aim-archive/<日期-任务名>/）

**执行步骤：**

1. 写入 aim 文件到 `workspace/aim-archive/<日期-任务名>/aim.md`：
```markdown
# aim: <task>

## 目标
<goal>

## 元信息
- 频道: <channel>
- 指派: <assignee>
- 创建时间: <now>
- 检查间隔: <interval>
- 状态: 🔄 进行中

## 进度记录
（cron 自检时追加）
```

2. 用 `cron_create` 创建定时检查任务：
   - `schedule_type`: "interval"
   - `schedule_value`: interval 值（如 "10" 表示 10 分钟）
   - `prompt`: 自检指令（见下方模板）
   - `description`: "aim-check: <task>"

3. 在 SESSION-STATE.md 加任务条目：
   `- [ ] 🎯 aim: <task> → <assignee> | cron=<cron_id>`

4. 通知协作者开始干活（通过 channel 发消息）

### cron 自检 prompt 模板

```
你是 aim 检查器。检查以下 aim 是否达成：

任务：<task>
目标：<goal>
频道：<channel>
指派：<assignee>
归档：<archive_path>
cron_id：<cron_id>

执行步骤：
1. 翻 <channel> 看 <assignee> 的最新进度
2. 检查 <goal> 是否达成（要具体验证，不能猜）
3. 如果没达成：
   - 在 <channel> 通知 <assignee> 继续做，说明还差什么
   - 在 <archive_path>/aim.md 追加进度记录
4. 如果达成了：
   - 回复 "aim 达成：<task>"
   - 后续由 agent 执行 /aim complete
```

### `/aim status` — 查看当前 aims

1. 扫描 `workspace/aim-archive/*/aim.md`
2. 列出所有状态为 "🔄 进行中" 的 aim
3. 显示：任务名 | 指派 | 频道 | 创建时间 | 最后检查时间

### `/aim complete <task-name>` — 标记 aim 达成

1. 更新 `workspace/aim-archive/<task-name>/aim.md`：
   - 状态改为 "✅ 已达成"
   - 追加达成时间和验收结果

2. 用 `cron_delete` 删除对应的 cron 任务

3. 用 `reply_blocklist` block 协作者（防循环）：
   - `action`: "add"
   - `user_ids`: 协作者的 ID

4. 更新 SESSION-STATE.md：
   - 把 `- [ ] 🎯 aim:` 改成 `- [x] 🎯 aim:`

5. 通知相关人：aim 已达成

### `/aim archive <task-name>` — 归档（complete 后自动执行）

1. 在 `workspace/aim-archive/<task-name>/` 下生成：
   - `COMPLETE.md` — 完成报告（目标、过程、结果、耗时）
   - 确保 `aim.md` 已更新为达成状态

2. 确认 cron 已删除、协作者已 block

### `/aim unblock <assignee-id>` — 解除 block（需要再协作时）

1. 用 `reply_blocklist` 解除：
   - `action`: "remove"
   - `user_ids`: 协作者 ID

2. 通知协作者：可以继续协作了

## 注意事项

- **goal 必须是可验证的**：不是"优化性能"，而是"响应时间 < 200ms"
- **cron 不停催**：翀哥说"歇会儿" ≠ 任务停，cron 继续催
- **主动翻频道**：不等 msg_send，主动去频道看进度
- **达成后立即 block**：防止心跳循环，这是铁律
- **归档要完整**：过程记录、验收结果、耗时统计都要有

## 示例

```
/aim create
  task: 小柯修复 session 回复路径敏感词
  goal: session 回复路径接上 getSensitiveWords，飞书测试群验证通过
  channel: discord#CC频道
  assignee: 小柯
  interval: 10min
```

```
/aim status
→ 🎯 修复敏感词 | 小柯 | discord#CC频道 | 10分钟前
```

```
/aim complete 修复敏感词
→ ✅ 已达成 | cron 已删 | 小柯已 block | 归档完成
```
