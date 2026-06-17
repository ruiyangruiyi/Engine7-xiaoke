---
name: Preview tool call时保留不删
description: 翀哥要求tool调用时不删preview卡片，内容"挺好"保留可见。discard改为freeze——保留preview但标记frozen停止更新。
type: feedback
keywords: [preview, freeze, tool call, discard, 保留, 可见, StreamPreview, isFinal, header]
created: 2026-06-11
updated: 2026-06-16
---

## 规则

Tool调用时，preview卡片**不删除**，改为freeze保留在频道里。LLM输出的文字是实时内容，应该可见而不是被discard清掉。

**Why:** 翀哥发现preview里的文字"还没看清就被你删了"，而且preview内容是LLM的实时思考过程，有价值。"那个preview卡片在tool call调用前能不删么？我觉得内容还是挺好的"

## 两个关键bug及修复

**Bug 1 — freeze header不消失（6/11下午，已修复）：** freeze()调用editPreview时没传isFinal → 黄色"处理中"header一直挂着。修复：freeze()传`isFinal=true`→立即去header。

**Bug 2 — freeze后preview被删（6/11下午，已修复）：** freeze()设了`degraded=true`→finish()看到degraded就删preview。修复：freeze()只设`frozen`不设`degraded`，finish()优先检查`frozen`→保留preview原内容+返回false让上层发最终回答。

## ⚠️ 6/16发现的问题（未修复）：freeze→finish双重发送（Discord消息层面）

**潜在问题：** freeze时 `editPreview(isFinal=true)` 将preview变成普通消息留在频道。finish()检查 `frozen===true` → 返回false → 上层又发完整回答。**如果livestream skill读Discord消息，preview和完整回答各发一次。**

**但是6/16直播翀哥听到的重复根因不是这个！** 详见`feedback_API超时重试导致消息重复_0616.md`：
- transcript证据显示重复是AutoDL服务器侧TTS/FlashHead/RTMP的帧重复（同一文字无缝播放2-4遍，0.00s gap）
- 最严重的重复时间点（约10:35）engine日志无1305无retry，排除了API限流
- 姐姐调livestream_send是exec主动调用的，不是preview自动送的

**freeze→finish双重发送是真实的潜在bug**，但跟6/16直播直播观众端听到的重复不是同一个问题。需分开对待。
