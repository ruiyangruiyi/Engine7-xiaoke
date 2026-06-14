---
name: Stream超时重试
description: glm-5.1 stream中途断开超时(60s)没有重试机制，直接报错。翀哥确认要加重试，但微信tool优先，先记待办。
type: feedback
---

## 规则

Stream异常（包括超时和截断）应该妥善处理重试，不能直接报错给用户。

### 类型1：Stream read timeout（60s）无新token

**现象：** glm-5.1连续两次stream中途卡住超时。第1次67秒无新token，第2次64秒无响应。fetchWithRetry的重试只覆盖HTTP错误（429/500），不覆盖stream中途断开。

**翀哥态度：** 确认"要"加重试，但优先级低于微信tool——"先做tool吧 这个记成待办"。切到DeepSeek v4-pro继续开发。

**临时措施：** 翀哥切到DeepSeek v4-pro（1M上下文），微信tool在DeepSeek下开发完成。

### 类型2：Anthropic API 400 — tool_use块无对应的tool_result（6/11夜间新增）

**现象：** [2026-06-11 22:41:27] `stream error after 3 retries: Anthropic API 400` — `messages.1:tool_use ids were found without tool_result blocks immediately after: call_10...call_18`

**根因确认（6/11夜间翀哥排除截断假设）：** flash模型一次返回多个tool_use（pro不会这样），而extract的mini agent loop中，消息历史里的tool_use没有全部配对对应的tool_result。具体表现为5轮×每轮多个tool_use=25个未配对的tool_use。

**与类型1的区别：** 类型1是"stream中途断开等不到数据"，类型2是"模型行为不同——flash为了快一次吐多个tool_use，消息历史出现缺口"。

**与模型的关系：** pro和flash都是DeepSeek的anthropic兼容接口，pro没事flash就炸——说明不是接口差异，是flash模型行为不同：pro每次调1-2个tool，flash一次吐5个，导致历史消息里tool_use数量多于tool_result。

**当前状态：**
- ✅ 根因已锁定：flash多tool_use + 消息历史tool_result不配对
- ✅ 修复已实施（6/11夜间→6/12凌晨优化）：第一版`patchOrphanedToolUse`补空tool_result，后改为**过滤删除**（直接删掉未配对的tool_use所在assistant消息），对齐reader.ts的`filterUnresolvedToolUses`策略
- ✅ 翀哥确认"对齐吧，没有result要信息也没啥用"——删除更干净，不浪费token
- ✅ 统一命名：两边都叫`filterUnresolvedToolUse(s)`，一个管OpenAI格式一个管Anthropic格式
- ✅ 提交 `0272f1d`

### 关键发现：filterUnresolvedToolUses已有但只覆盖OpenAI风格

**发现时间：** 6/11夜间调试中

**Context：** session reader（`reader.ts:560`）已有`filterUnresolvedToolUses`，但它处理的是**OpenAI风格**——`tool_calls`在message顶层。而Anthropic风格（`tool_use`/`tool_result`在content blocks里）不受影响。

**两套代码各管各的：**
- `reader.ts:filterUnresolvedToolUses` → OpenAI风格（tool_calls顶层）→ 过滤掉未配对的assistant消息
- `attachments.ts:patchOrphanedToolUse`（新增）→ Anthropic风格（tool_use在content blocks）→ 补空tool_result

**重启后自动恢复解释：** 重启后session干净，无残留未配对tool_use，所以400不再触发。但跑一段时间后可能复发，patchOrphanedToolUse作为防御性兜底仍然必要。

**How to apply:**
1. 类型1（timeout）：在query.ts的catch里判断timeout错误，重试1-2次。微信tool做完后再做。
2. 类型2（Anthropic 400 on tool_use）：在`normalizeMessagesForAPI`中加tool_use/tool_result配对校验——缺配对的tool_use补空tool_result。这个是flash模型特有行为，pro不会触发。重启无效（不是状态问题，是代码缺陷）。
