---
name: persistTasks全量覆盖改merge
description: 6/15修复persistTasks全量覆盖磁盘tasks.json的bug，改为merge写入（保留磁盘上cache没有的seed任务）
type: feedback
---
# persistTasks 全量覆盖 → merge 写入

**时间：** 2026-06-15 晚上

**问题：** `persistTasks()` 直接用内存cache全量写入磁盘tasks.json。姐姐用 `cron_create` 新建cron后，内存里没加载的seed任务（如生成每日hint）被覆盖丢失。

**修复：** `persistTasks` 写入前先读磁盘上已有的tasks.json，把内存cache里没有的任务merge进来再写。
- 不再覆盖手动编辑的seed任务
- 姐姐 `cron_create` 不再影响磁盘上已存在的其他cron

**⚠️ 6/16发现merge的对称性bug：删掉的task复活**
- merge是单向的——磁盘有但cache没有就加回来。但`cron_delete`是从cache删的，persist时磁盘上的旧task又被merge回来。
- **修复：** 维护`deletedIds`集合，merge时跳过已删除的task ID
- **教训：** merge逻辑要同时考虑"cache有磁盘没有"和"cache没有磁盘有"两个方向，delete操作必须清理两侧

**⚠️ 6/16 17:00+ 额外发现：运行时改tasks.json无效**
- Engine在运行时，cache是权威源。persistTasks会用cache覆盖磁盘文件。
- 改tasks.json的唯一可靠方式：停Engine → 改文件 → 启动Engine（loadTasks读到）
- 通过API（cron_create/cron_delete/updateTask）操作cache才是运行时正确的变更方式

**How to apply:**
- tasks.json的seed任务现在受merge保护，不会被cron_create覆盖
- 修改seed任务还是直接编辑tasks.json
- 删cron时，merge逻辑会检查deletedIds防止从磁盘复活
- 运行时改tasks.json无效——persistTasks用cache覆盖磁盘。改disk不如改cache或重启loadTasks
