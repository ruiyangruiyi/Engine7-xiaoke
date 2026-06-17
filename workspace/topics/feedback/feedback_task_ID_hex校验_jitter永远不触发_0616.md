---
name: cron task ID必须是合法hex，否则jitter永远不触发
description: 6/16调试发现task ID含非hex字符时parseInt返回NaN，jitter计算全失效，cron永远不会触发执行
type: feedback
---

**时间：** 2026-06-16 下午

**问题：** 测试cron task ID设为`ctestr001`，scheduler的`shouldFireWithJitter`一直返回false，cron永远不触发。

**根因：** scheduler用`parseInt(task.id.slice(1), 16)`取ID的hex部分计算数值偏移。`ctestr001`中`testr`含字母r/t/s等hex不合法字符 → `parseInt`返回`NaN` → `NaN % jitterMs`也是`NaN` → 比较永远为false → 永远不触发。
- `NaN < anything` → false
- `NaN >= anything` → false

**修复：** task ID改成纯hex格式（如`ca11b22c`），`parseInt`正常解析，jitter计算正确。

**后续：** 建议scheduler对`parseInt`结果做isNaN防御，避免类似问题静默吞掉cron执行。

**Why:**
- JS的`parseInt`对非hex字符不报错，返回NaN，NaN参与比较永远false
- NaN的比较行为跟C/C++不同——不会触发assert或error，静默失败

**How to apply:**
- cron task ID必须用合法hex字符（0-9, a-f），不能有其他字母
- 推荐格式：`c` + 8位随机hex（如`ca11b22c`）
- 如果未来要改ID生成逻辑，记得对parseInt结果加isNaN防御
