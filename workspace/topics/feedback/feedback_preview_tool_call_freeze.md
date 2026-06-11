---
name: Preview tool call时保留不删
description: 翀哥要求tool调用时不删preview卡片，内容"挺好"保留可见。discard改为freeze——保留preview但标记frozen停止更新，finish时正常去蓝框变成最终回答。tool结果作为新消息出现在下方。freeze时传isFinal=true立即去header。
type: feedback
keywords: [preview, freeze, tool call, discard, 保留, 可见, StreamPreview, isFinal, header]
created: 2026-06-11
updated: 2026-06-11T20:00
---

## 规则

Tool调用时，preview卡片**不删除**，改为freeze保留在频道里。LLM输出的文字是实时内容，应该可见而不是被discard清掉。

**Why:** 翀哥发现preview里的文字"还没看清就被你删了"，而且preview内容是LLM的实时思考过程，有价值。"那个preview卡片在tool call调用前能不删么？我觉得内容还是挺好的"

之前discard的设计是为了避免preview文字（半截）和tool结果（新消息）混在一起视觉混乱。但翀哥认为内容本身有价值，视觉上的"混乱"可以接受。

**两个关键bug及修复：**

**Bug 1 — freeze header不消失（6/11下午，已修复）：** freeze()调用editPreview时没传isFinal → 黄色"处理中"header一直挂着。修复：freeze()传`isFinal=true`→立即去header。

**Bug 2 — freeze后preview被删（6/11下午，已修复）：** freeze()设了`degraded=true`→finish()看到degraded就删preview。根因：freeze的本意是"冻结保留"，degraded的意思是"降级→别再用了"，语义冲突。修复：①freeze()只设`frozen`不设`degraded` ②finish()优先检查`frozen`→保留preview原内容+返回false让上层发最终回答。修改文件：`stream-preview.ts`的freeze()和finish()方法。

**How to apply:**
1. Tool调用前调用 `preview.freeze()` 而非 `preview.discard()`
2. freeze后标记 `frozen=true`（不设degraded！degraded会让finish删preview），`appendText()`检查frozen→跳过不发新preview
3. **freeze()必须传`isFinal=true`**：立即去掉黄色"处理中"header，冻结卡片直接变成普通消息卡片
4. `finish()`优先检查`frozen`→保留preview原内容，返回false让上层发最终回答为新消息。只有非frozen、非degraded时走正常路径（更新preview为finalText）
5. Tool结果和后续文字**新发消息**，preview作为"历史文字"保留在原位
6. 效果：频道里preview → tool结果（新消息）→ 最终回答（新消息），preview始终可见

**注意：** 只有纯文字对话（不调tool）才能享受"打字机→去蓝框→原地变最终回答"的体验。中间有tool时，最终回答是新消息，preview是冻结的历史文字。两者分开但都不丢。
