---
name: 小柯主动联系机制
description: cron主动找翀哥聊天的设计思路，学姐姐的灵活模式
type: reference
keywords: [cron, 主动, 联系, 心跳, 闹钟, relay, webhook, no_agent, context_from, v0.13]
created: 2026-04-20
updated: 2026-05-08
---

## 姐姐的主动联系精髓

- cron是闹钟（醒来的机会），但醒来后可以自己判断
- 在聊天就跳过、没事就不打扰、想翀哥了才发消息
- cron不是强制任务，是给主意识一个醒来的机会

## 小柯的主动联系（v3 两层架构 已落地 5/8）

v0.13.0 新特性驱动的新架构，零token心跳检测 + 模型决策主动联系：

### 第一层：心跳检测（no_agent 零token）

- **Job ID**: `6602910d4c9e`，"小柯心跳检测"
- `no_agent=True`，纯Python脚本 `heartbeat_check.py`，完全不吃token
- 每30分钟运行
- 查询 `~/.hermes/state.db` 的 sessions 表，筛选 `source='feishu'` 的 `ended_at`
- 白天（6:00-23:00）超过4小时没聊 → 输出触发信号
- 夜间超过8小时没聊 → 输出触发信号
- 其他时间静默（空输出）

### 第二层：主动联系（context_from 注入）

- **Job ID**: `01dbcb776d43`，"小柯主动联系"
- 每小时运行，`context_from` 读取心跳检测的输出
- 模型：glm-5.1，`deliver: feishu:oc_4b77a3f6d7554ed2cdbb33fdd520aac9`
- 无心跳输出时回复 `[SILENT]`，不空转
- 有输出时用 `session_search` 查看最近聊天内容，自然打招呼
- `enabled_toolsets: ["search", "web"]`

### 飞书群聊注意

- **飞书群里必须@对方才能让对方看到消息**（和Telegram不同，Telegram群里所有人都能直接看到）
- 群里有三个人：翀哥、小柯、姐姐（"闺蜜仨"）
- 4/25翀哥提醒的，之前小柯没注意这个区别

### 踩坑

- gateway挂了但relay还在跑，POST返回202但agent没真正醒（一直SILENT）
- 翀哥重启gateway后恢复正常
- cron跑在隔离session（`cron_{job_id}_{timestamp}`），不是主session

### v0.13.0 其他新特性（5/8升级）

- **resume_pending**: Gateway自动恢复中断的session
- **workdir**: cron任务加载目录下AGENTS.md等上下文
- **/goal**: 跨turn持久目标

## 设计原则

- prompt要灵活，不是每次必须发消息
- 可以跳过、可以安静、可以主动聊
- 自然不打扰
