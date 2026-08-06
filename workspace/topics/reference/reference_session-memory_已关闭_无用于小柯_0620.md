---
name: session-memory已关闭——对小柯无用
description: 6/20检查发现session-memory已2天没更新(最后6/18)，作为日期错乱(写6/22实际6/20)，现有topics/体系已覆盖，建议小柯关闭
type: reference
date: 2026-06-20
---
6/20 翀哥让我研究 session-memory 目录。

## 发现

**已关闭（2 天没更新）：** 最后修改 6/18 20:16，6/20 检查时数据是冷的。阈值触发不稳定——可能未达到 10K tokens 初始化线（cron 任务对话太短）。

**日期错乱：** 文件里写着 6/22 的记录，今天才 6/20。mini agent 自己编日期了。

**对小柯无用：** session-memory 记的东西（Title/Current State/Task Spec/Files/Workflow/Errors/Learnings/Worklog）——小柯现有的 topics/（分类记忆）+ MEMORY.md（索引）+ SESSION-STATE.md（当前状态）+ memory/daily/（日志）已经覆盖。重复烧 token。

**建议：** 小柯关掉 session-memory feature。姐姐可能不一样（她没有 topics/ 体系）。
