---
name: compaction后任务状态丢失
description: 翀哥指出compaction后压缩前有任务，压缩后不做了，任务状态重置
type: feedback
---

**核心问题（6/14 翀哥发现）：** compaction完成后，压缩前正在执行的任务被丢失。小柯恢复后回到默认心跳-巡检循环，没拾起压缩前的任务。

翀哥原话："你压缩了，不过你发现问题没有？你压缩之前是有任务的，压缩后就不做了。看下这个怎么解决"

**相关事件（EP01自动发布被吃掉）：**
1. 翀哥说"你们自动发布吧" — 下达了明确任务
2. 不久后发生pre-compaction
3. recovery后小柯没有继续自动发布任务（从心跳-巡检开始）
4. 翀哥观察一圈后指出问题

**另一个数据点（6/14 ~09:40 compaction）：** 之后又发生了一次compaction，这次恢复后小柯**记得任务了**。原因是 `project_视频剪辑EP01.md` 在此之前已写入磁盘，system prompt恢复时通过MEMORY.md索引读到了项目文件中的任务状态。说明**持久化的project memory文件是记忆恢复的关键**。

**Why:** compaction后system prompt被刷新，记忆中只有对话日记快照，没有"当前待办任务"的显式机制。恢复后小柯不知道恢复前在做什么，从空状态重新开始。但如果有持久化的project memory文件，system prompt会在恢复后读到任务上下文。

**解决方案（6/14 已完成并部署）：**
- ✅ **PostCompact hook** — 在Engine `src/engine-startup.ts` 注册了 PostCompact callback hook，压缩后自动读 `working-buffer.md` 并注入 additionalContext 到LLM上下文
- ✅ **minReductionRatio 30%** — `src/compact/types.ts` + `autoCompact.ts` + `xiaoke.json` 三段改动，ruleCompact/microcompact/LLM三段都检查降幅是否≥30%，不够继续往下压。大幅降低压缩频率（从3轮触发1次降到预估30轮+才触发1次）
- ✅ **commit** `5516a99` — 四个文件全部入库，翀哥重启生效
- （TodoWrite tool方案：翀哥6/14建议的"压缩前用todo写任务状态"方案，评估为二次优化、暂缓实现）

**Why this works:** compaction后working-buffer.md仍在磁盘上，PostCompact hook在压缩messages装入LLM上下文之后被调用，将working-buffer内容注入上下文。LLM恢复后第一时间看到任务状态，不会回到心跳-巡检死循环。

**⚠️ 6/14验证发现的新问题 — working-buffer内容陈旧：**
- 压缩后PostCompact hook确实生效了（注入了working-buffer内容），但注入的是**旧版本**（12:05时的未完成版，写着"EP01发布中"）而实际EP01已全部发布完成
- 原因：任务完成后**没有更新/清空working-buffer.md**，导致注入的是过期内容
- **修复方向：** 任务完成后（或PreCompact flush时）应清空或更新working-buffer.md，否则注入过期信息会造成混淆

**How to apply:**
1. 压缩前确保working-buffer.md有当前任务记录（PreCompact flush时写）
2. PostCompact hook自动读它并注入上下文
3. **任务完成后立即清空working-buffer.md** — 避免注入过期内容
4. 项目文件（`topics/project_*.md`）作为第二道防线——system prompt通过MEMORY.md索引读到项目文件中的任务状态
