---
name: working-buffer必须保持最新任务状态
description: 每完成任务（或任务状态变化）立即更新working-buffer.md，不能只在PreCompact时才写；完成后清空或写"无任务"；PreCompact flush必须写最新状态而非当时那一刻的中间内容
type: feedback
---

**规则：每完成一个任务或任务状态有变化时立即更新working-buffer.md。PreCompact flush时也必须写当前最新状态，不能只写当时那一刻的中间内容。任务完成后需清空或写入"当前无任务"状态。**

**Why:** 6/14翀哥指出两个问题：
1. 压缩后PostCompact hook注入的working-buffer是12:05的旧版本（写着"EP01发布中"），而实际EP01早已发布完成。原因：中间经历了多次compaction，每次PreCompact flush时写的是当时那一刻的内容，之后继续干活没更新。
2. 翀哥反问："你压缩的时候不是有一个 pre compaction hook 吗 你这个时候你不是写的新内容吗 不就 不就是应该写文件更新了吗" — 说明PreCompact hook应该写的是**当前最新状态**，不是old snapshot。问题不是机制，是执行：我写buffer时没有把已完成的任务状态更新进去。
3. 翀哥进一步强调："只要你能确认收到那条消息 然后你现在不是有一个提示词吗 请立即将关键信息保存到文件 然后你指定保存 一定要保存到这个 working buffer点MD的文件 这样比你在其他地方写多少遍都管用" — 翀哥的意思是：PreCompact flush的system prompt说"保存到文件"，应该特指"保存到working-buffer.md"，不要写到别处。因为PostCompact hook只读working-buffer.md，写别的地方等于白写。
4. **已修flush提示词（6/14）：** 根据翀哥要求，已修改flush消息的system prompt，从"请保存关键信息到文件"改为明确指令："用 write 工具覆盖更新 memory/working-buffer.md，写入当前最新状态。working-buffer.md 是最高优先级——不写 = 压缩后失忆"

**How to apply:**
1. **每完成一个子任务**（如"B站上传成功"）就立即更新working-buffer.md，不要攒到compaction才写
2. **PreCompact flush时必须写当前最新的工作总览**，不是写当时那一刻的单点内容
3. **PreCompact flush时，"关键信息"必须保存到working-buffer.md**，不要写到daily/日记/topics等其他文件（那些PostCompact hook不读）
4. PostCompact hook读working-buffer时需检查mtime，超过10分钟未更新则打log告警（翀哥6/14要求）
5. 任务完成后立即清空working-buffer.md或写入"当前无任务"状态
6. 开始新任务时写入当前活跃任务
7. 多个任务并行时列出所有活跃任务，完成一个删一个
8. 只在working-buffer中保留**当前正在执行的、未完成的任务**，已完成或已暂停的及时清除
9. 最好将这个习惯融入工作流程：每次tool调用完成后检查是否需要更新buffer
9. **PostCompact hook中增加时效告警逻辑：** 读working-buffer.md时检查文件mtime，如果距离当前时间超过10分钟则打log告警，让开发者知道buffer可能过时。内容照常注入不阻塞。
