---
name: 翀哥质疑scheduler cache设计——直接读json文件
description: 6/16翀哥指出Engine cron的cache/merge设计过度复杂，直接读JSON文件就行。我认了——cache带来的麻烦远大于收益
type: feedback
date: 2026-06-16
---

# 翀哥：为啥要cache？直接读json文件不行么

**时间：** 2026-06-16 18:17+（调试内心独白postProcess时）

**背景：** 内心独白postProcess测试了一下午，每次手动改tasks.json都被persistTasks用cache覆盖。我跟翀哥说"persistTasks用cache覆盖了磁盘文件，得停Engine再启动"。翀哥问：

> "我有点不明白哈  我为你下  为啥你要弄个cache呢  你直接读json文件不行么"

**我的回答：** "你说得对，这cache就是多此一举。10秒tick读一个小JSON文件，性能完全不是问题。"

**反思：** 当初加cache的出发点可能是"减少磁盘IO"，但10秒一次读小JSON文件完全没有性能压力。cache带来的麻烦：
1. merge逻辑复杂（磁盘↔cache双向同步）
2. 手动改disk文件无效（persistTasks用cache覆盖）
3. deletedIds防复活需要额外维护
4. 运行时改配置必须走API，不能直接改文件
5. 调试时增加了心智负担（"现在cache里是什么？"）

**6/16 18:29 结局：** 最终靠"停Engine→改tasks.json→loadTasks"绕过了cache问题。翀哥说"直接读json不行么"——如果没有cache，这一下午所有cache问题根本不会出现。

**结局（6/16 18:30-19:00）：** 翀哥问完40分钟内，我直接把cache去掉了——所有CRUD操作直接read-modify-write磁盘。scheduler.ts/tasks.ts/tools.ts全改完+rebuild。翀哥追问"那你还改么？会不会下次再加个字段又得折腾"——我说不根治下次还得出事，当场就改了。

**How to apply:**
- **10秒tick频率直接读JSON就够了**，任何cache在这频率下都是多余的
- 没有cache就没有cache一致性问题——删了不会复活、手动改文件不会被覆盖、加字段不用考虑"cache里有没有"
- **质疑就改彻底，不留下次：** 翀哥指出问题后，不要只打补丁（加deletedIds），直接去掉问题根源（去掉cache本身）
- **翀哥的追问方式值得学：** 遇到问题不要只在框架内绕，先退一步问"这个框架本身是不是多余的"
- 重建task后翀哥说"那刚写的文档也没啥用了"——去cache后设计文档里三分之一是cache bug的踩坑，删掉了
