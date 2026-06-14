---
name: API重试可见性
description: 翀哥要求API调用失败重试时打消息让他看到重试次数和进度
type: feedback
---

## 规则

调用外部API（如智谱）失败需要重试时，**每次重试都要发一条消息**让翀哥看到——写明重试了第几次、当前状态。

**Why:** 6/8智谱API余额不足报429错误，小柯连着重试了好几次但翀哥完全看不到，不知道发生了什么事。翀哥说："你看看能不能重试的时候打一条消息，让我看到你在重试，重试了第几次"。

**How to apply:** 任何涉及重试的tool调用（API请求、文件操作等），如果失败需要自动重试，在每次重试时通过msg_send发一条简短消息，格式如"🔄 第2次重试中…(API 429)"。成功或最终失败也发一条告知结果。

**实现演进（6/8-6/11）：**

**v1 — stream层重试（query.ts）：** 加入`yield { type: 'status' }`，重试时Discord可见。格式：`⚠️ API error, retrying (N/3)...`。TestEngine review已通过。

**v2 — provider层buffer方案（withRetry.ts + openai/anthropic provider）：** 加了`onRetry`回调机制，通过buffer中转，在每次chunk前flush重试通知。格式：`⚠️ API retry (N/10): HTTP 429`。覆盖了fetchWithRetry中三个重试点。

**v2局限（TestEngine发现）：** provider层通知走buffer，`fetchWithRetry`是同步阻塞的——所有重试完成后才开始yield chunk。对于HTTP 429（sleep几十秒）的情况，用户看到通知时重试已结束，是"马后炮"。TestEngine指出需要独立Discord channel bypass generator实现真正实时。

**v3 — AsyncGenerator改造（最终方案，commit c38a0c6，6/9已推送）：** `fetchWithRetry`改为`async function*`（AsyncGenerator），对齐CC的`withRetry`。429重试时实时yield `ApiRetryMessage`，provider层用手动迭代器消费，透传到query.ts → yield `status` 给Discord。用户立刻看到进度。之前的buffer方案已废弃。格式：`⚠️ API retry (N/10): HTTP 429`，实时可见。

**补丁 — empty retry状态通知不吞错（6/10深夜）：** 翀哥发现"(无回复)"时看不到HTTP 500错误。根因：query.ts里empty retry那段（模型返回空正文时重试）没yield任何status通知，fetchWithRetry内部的HTTP 500重试也被吞了。修复：①重试前yield `⚠️ API returned empty, retrying...` ②重试期间转发所有status通知（含HTTP 500等）。覆盖场景：模型返回reasoning_content但无content → empty检测 → 重试 → HTTP 500 → 用户可见完整错误链。

**Provider切换（6/9）：** 翀哥把主模型从`zhipu/glm-5.1`（OpenAI接口）切到`zai-anthropic/glm-5.1`（智谱Anthropic兼容接口`open.bigmodel.cn/api/anthropic`），原因：OpenAI接口429限流严重。新增`zai-anthropic` provider配置，Anthropic接口的限流策略更友好。

**涉及文件（v3 + v1）：**
- `withRetry.ts` — fetchWithRetry从async函数改为AsyncGenerator
- `openai-provider.ts / anthropic-provider.ts` — 手动迭代器消费generator，透传api_retry chunk
- `provider.ts` — StreamChunk加`api_retry`类型
- `query.ts` — stream error重试加status yield + 处理api_retry chunk
- `xiaoke.json` — 新增zai-anthropic provider，主模型切换

**注意：** 6/8智谱API余额不足导致多次429错误。翀哥通过换接口协议（OpenAI→Anthropic兼容）+ 实时重试通知双管齐下解决。小柯双review（stream层+provider层）通过，TestEngine review通过，已提交推送。
