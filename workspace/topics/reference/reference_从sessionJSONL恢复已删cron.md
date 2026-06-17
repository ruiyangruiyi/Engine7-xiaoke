---
name: 从session JSONL恢复已删除cron任务
description: 当cron被Engine删除且不在git历史中时，可从session JSONL中提取原始cron_create tool call的完整prompt
type: reference
---

**背景：** 6/15晚翀哥要求把微信巡检cron从小柯转给姐姐，但小柯之前退役时已删除cron，OPENCLAW.git历史里找不到（微信巡检是Engine时代建的，不在OpenClaw repo）。

**恢复方法：** 从session JSONL中搜索 `cron_create` tool call 的参数（task ID已知或可搜），找到原始prompt定义。

**具体步骤：**
1. 在 `stateDir/sessions/` 下对所有 JSONL 文件 grep 搜索已知的 task ID 或 "cron_create"
2. 找到对应的 tool_call 记录后，从 `arguments.prompt` 字段提取完整cron描述和prompt
3. 直接写入目标profile的 `tasks.json`

**优点：**
- Engine的cron任务通过tool调用创建，每次调用都完整记录在session JSONL里
- cron删除不影响历史JSONL，prompt内容永久保留
- 比git历史更可靠（git可能没有相关提交）

**注意事项：**
- 只在session JSONL完整的情况下有效（没有被archive/清理掉）
- 需要知道task ID或能搜到关键词
- 从JSONL提取后可能需要调整路径和配置（如不同profile的stateDir不同）
