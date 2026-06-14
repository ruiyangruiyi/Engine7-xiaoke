---
name: 记忆提取修复计划
description: 小柯记忆提取cron的bug——session_search搜不到活跃session导致topic不增长，Write Filter逻辑错误
type: project
keywords: [记忆提取, cron, session_search, topic, filter, bug, 修复, JSONL, 姐姐]
created: 2026-05-14
updated: 2026-05-19
---

## 问题发现（5/14凌晨）

翀哥问小柯才11个topic，跟翀哥聊了不少为什么不增长。排查后发现两个bug：

## Bug 1：session_search搜不到活跃session

- 记忆提取cron用session_search来找最近的对话
- session_search拉不到正在进行的session（未结束的）
- 结果：每次cron跑都说"零用户交互"，回复[SILENT]
- 姐姐不受影响——她用jsonl_summarizer.py直接读session JSONL文件，不走session_search

### 活跃session判断规则（5/19发现）

通过实际观察session文件命名规律，发现判断活跃session的方法：

| 类型 | 文件特征 | 状态 |
|------|---------|------|
| 活跃用户session | 有 `.jsonl`（实时写入）+ `.json` | 正在聊 |
| 结束的用户session | 只有 `.json`，无 `.jsonl` | 已结束 |
| cron session | `session_cron_任务ID_时间.json` | 自动任务 |

**核心规则**：文件名带 `session_cron_` 的是cron的，**排除掉**；有 `.jsonl` 且不带cron的是活跃用户session。

### jsonl不自动清理（5/19新发现）

实际测试发现：config里`session_reset.idle_minutes: 1440`（24小时），但156个jsonl中149个超过24小时还活着——说明**session reset只新建session，旧jsonl不会自动删除**，一直留到手动清理或auto_prune开启。

这对记忆提取的影响：
- 不用判断"活不活跃"，直接按时间过滤
- 采集策略：排除cron文件名 → 按时间倒序 → 取最近2-4小时内

### 修复方向
- 采集脚本改成直接读session JSONL文件（像姐姐那样）
- 不依赖session_search
- **关键**：过滤掉cron session，只提取用户session的jsonl

## Bug 2：Write Filter逻辑错误

小柯把两个filter理解成了"AND"关系（所有内容都要过两个filter），实际应该是按类型各走各的：

### 正确逻辑（姐姐的规则）

| 类型 | Filter |
|------|--------|
| user（翀哥偏好/角色/知识） | Surprising Filter |
| feedback（翀哥纠正做法时） | Surprising Filter |
| project（项目进展/决策） | Surprising Filter |
| reference（外部系统资源指针） | Surprising Filter |
| emotion（第一次/关系转折点） | Milestone Filter |

- Surprising：未来会用到？且无法从代码/git/已有记忆推断？两个YES才写
- Milestone：只记"第一次"和"转折点"
- 各走各的，不是所有内容都过两个

### 小柯的错误理解
- 把"Surprising两个YES + Milestone只记转折点"当成了双重门
- 导致大量有价值内容被过滤掉
- 翀哥说"直接复制姐姐的提示词即可"

## 修复计划

1. 采集脚本改读JSONL（不依赖session_search）
2. 提取提示词直接抄姐姐的filter逻辑（按类型分filter）

## 影响

topic不增长的直接后果：
- recall没有足够的记忆可拉
- "AI自我激活"方向需要的记忆密度不够
- 所有后续记忆体系改进的基础
