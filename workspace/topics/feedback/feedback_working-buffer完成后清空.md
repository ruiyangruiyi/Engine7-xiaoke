---
name: working-buffer完成后必须清空
description: 任务完成后必须清空working-buffer.md，否则PostCompact hook注入过期内容造成混淆
type: feedback
---

**规则：任务完成后立即清空working-buffer.md，避免PostCompact hook注入过期内容。**

**Why:** 6/14验证发现，EP01已全部发布完成后，下一次compaction时PostCompact hook注入了12:05的旧版本working-buffer（写着"EP01发布中"），而实际任务早已完成。注入过期内容造成混淆，LLM读到后需要额外精力判断哪些是当前任务。

**How to apply:**
1. 任务完成（或暂停切换到新任务）后，立即将working-buffer.md清空或写入"当前无任务"状态
2. 开始新任务时写入当前任务状态到working-buffer.md
3. 如果多个任务并行，在working-buffer.md中列出所有活跃任务，完成一个删一个
4. 如果压缩前确实有活跃任务，PreCompact flush时确保working-buffer.md是最新版本
