---
name: compact stripImages后必须执行ruleCompact
description: stripImages后不能因为"低于阈值"跳过ruleCompact，autoCompact已触发说明上下文确实过大，必须跑完四步
type: feedback
---

## 规则回顾

compact触发后，stripImages步骤结束后**不能提前返回**，必须继续执行ruleBased compact（smartExtract → compressOldTurns → truncate → fifoDelete四步全跑），即使预算已低于阈值也不跳过。

**Why:** autoCompact触发说明system prompt等未计入预算的部分导致上下文确实过大，stripImages仅更新messages不够。

## 🎯 真正的根因（6/13 7:30 翀哥指出）

**翀哥一句话问到根上：** "你觉得是你ruleCompact把token压下来了 但你的boundary是不是没更新 导致了你压完装载的还是老的boundary 所以越压越大"

**根因确认：** 压缩后的 messages **没写入 JSONL**。
- `writeCompactBoundary` 只写了行标记（compact_boundary + token数），**没写压缩后的messages**
- 内存里 `history = compactedMessages` 是对的
- 但 JSONL 里 boundary 后面是 压缩后 query loop 继续产生的 tool call 消息，不是压缩结果
- 下次 restore 从 boundary 读 → 读到的是旧 tool call 消息 → 等于没压缩
- 越压越大因为：压缩后产生的新消息 > 压缩掉的消息

**修复（handle-query.ts）：** compact 后把压缩结果的 messages 也写到 JSONL boundary 后面——restore 时从 boundary 读到的是压缩结果，不是旧数据。

## 🚫 6/13凌晨5:50第一轮误判（tool call自馈说）已被修正

之前分析"tool call结果自馈导致压缩后迅速涨回"是表象，不是根因。**真正的根因是 JSONL restore 读了旧数据，不是压缩后 tool call 行为不受限。**

## ✅ 6/13翀哥最终澄清：autoCompact触发后，入口skip也是多余的

翀哥确认：autoCompact已触发 → stripImages后必然超预算 → ruleCompact无条件执行。**入口处的 `preCompactTokenCount <= targetBudget` 判断也是多余的。** 因为从 autoCompact 进来的，stripImages（step0）已经确认了超预算。

**修正后的执行流：**
```
autoCompact触发 → step0 stripImages → step1-4 ruleCompact（无任何skip判断）
```

**Why:** autoCompact的shouldAutoCompact已经做了预算判断，能进来就说明需要压缩。stripImages后消息数减少但要压缩的上下文（system prompt等未计入的部分）仍然存在。中间任何skip判断都是多余且有害的。

## ✅ 翀哥6/13明确要求：compact日志写文件 → 已实现

翀哥说："首先你把compact日志应该写文件 否则不能指望我一直给你贴日志吧"

**Why:** compact日志当前只打stdout/stderr，重启后日志丢失，翀哥想查压缩行为只能手动贴。翀哥凌晨5点多起来查压缩问题，无法持续提供日志。

**✅ 实现（6/13 05:50~06:00）：** 新建 `compactLog.ts` 模块（路径在Engine compact目录），所有compact相关日志同时写console+文件 `D:/xiaoke/logs/compact-YYYY-MM-DD.log`。替换了4个文件的console.log/warn/error：
- `ruleCompact.ts` — 24处
- `autoCompact.ts` — 19处
- `compact.ts` — 11处
- `microCompact.ts` — 2处

日志按天分文件，格式 `HH:MM:SS | message`，重启后翀哥可以直接看日志文件。

## 🔧 已修复（6/13 7:30+）

**handle-query.ts 三处修复：**
1. **compact chunk处理** — 收到compact结果后设 `compacted = true` 标记 + `toolHistoryEntries.length = 0` 清空旧tool历史
2. **压缩后的messages写入JSONL** — 压缩结果写到boundary后面，下次restore读到的是压缩结果
3. **loop结束后history更新** — compact场景下不再push重复的 `msg.user(text)`，只追加压缩后新产生的tool历史和最终回复

**ruleCompact.ts 入口skip删除** — autoCompact触发后stripImages→ruleCompact无条件执行四步，中间无任何判断。

**compact日志写文件** — 新建compactLog.ts，4个文件56处console.log→写文件+console，日志在 `D:/xiaoke/logs/compact-YYYY-MM-DD.log`

## 📐 history数组边界说明（翀哥6/13确认）

- history数组只存 user/assistant/tool 对话历史，**不含system prompt**
- system prompt（~14,500 tokens）每轮API调用时独立传入，不在JSONL里
- compact threshold = 200K - 20K(output) - 13K(buffer) = **167K tokens（消息预算）**，但这个预算没有扣除 system prompt / tools / memory files 的固定开销（~31K），实际可用的消息预算应更小
- **⛔ overhead不是固定值**（6/13翀哥指正）：system prompt内容随状态变化、tool description随skill注册变化、memory文件只在特定时机注入——三者的开销在不同query间会变化。首次API调用后从 `prompt_tokens - estimateMessageTokens(messages)` 实时校准才是精确的。
- **核心：compact只压缩消息历史，不涉及system prompt。** system prompt大小固定（但数值不固定），不会"溢出"

## ⚡ threshold 扣除 system overhead（6/13早上翀哥确认方案）

### 背景
之前 compact threshold 只考虑了消息历史的 token，没扣除 system prompt / tools / memory 的开销。实际配置的 bufferTokens=43,616（对齐 OpenClaw 倒推的值，不是默认13K）。

### 修正后的算法
```
effectiveWindow = contextWindow - maxOutputTokens = 200K - 20K = 180K
buffer = 43,616（配置文件中的 bufferTokens 实际值）
threshold = effectiveWindow - buffer - overhead
         = 180K - 43,616 - ~31K
         ≈ 105K
```

### 实现方案
- 第一次 API 调用后，从返回的 `prompt_tokens - estimateMessageTokens(messages)` 得出精确 overhead
- 后续 threshold 计算自动扣除这个 overhead
- overhead 存储在 `compactConfig.systemOverheadTokens` 中
- **翀哥指正：overhead 不是固定值**—不同场景下 system prompt 内容、tools 注册量、memory 注入量会变化
- 当前方案：首次 API 调用后校准并复用

### 历史背景：bufferTokens 的由来
bufferTokens=43,616 是翀哥手动调的，对齐 OpenClaw 的倒推值。OpenClaw 也没算 system prompt 的 overhead，暗含在 buffer 里（大概20K是 overhead，剩余23K是真正的 buffer）。

### ✅ 6/13 翀哥最终定值：bufferTokens 从 43,616 改为 23,000
翀哥说"这样就加回20K应该 否则太低了 把43K改成23K吧"——因为 overhead 已单独算，buffer 不再需要暗含 overhead。23K 是纯粹的 buffer。

**最终算法：**
```
threshold = 180K - 23K(buffer) - ~31K(overhead) ≈ 126K
实际 API 用量 = 126K + 31K = 157K（安全）
```

### ✅ compact日志合并到engine log（6/13翀哥质疑后改进）
翀哥问"你还单写了日志 没有跟engine log放一起打印 你觉得这样好还是放一起好对你看日志调问题来说"

**结论：放一起好。** 调问题时 compact 发生在 query loop 里，前后是 engine 的 query 日志，分开看要来回切文件。

**改动：** 删掉 compactLog.ts 独立写文件逻辑，compact 日志统一走 console（已被 engine 日志系统 monkey-patch 捕获写文件），只加 `[ruleCompact]`/`[autoCompact]` 前缀方便 grep。

**查看方式：** `D:/xiaoke/logs/engine-2026-06-13.log` 下 grep `[ruleCompact]` 或 `[autoCompact]` 即可。

## ⚠️ overhead校准不能依赖API（6/13翀哥指正）→ ✅ 已改用analyzeContextUsage

翀哥问："你现在获取是通过API获取的是么？但这个API开始的时候貌似是不可用的 刷不出来 你得注意下 最好别通过API 就能获取因为在一个程序里"

**问题：** 原方案依赖第一次 API 调用返回的 `prompt_tokens`。但 API 在启动初期可能不可用（provider 冷启动、网络未就绪），导致第一次 query 的 overhead 不准确。

**✅ 修复（commit 3b59bff）：** 改用 Engine 内部已有的 `analyzeContextUsage` 函数，直接函数调用不走 HTTP/API。
- 调 `analyzeContextUsage(systemStable, toolDefs, memoryDir)` 获取 system prompt + tools + memory 的总 token
- 底层用 `roughTokenCountEstimation`（char/4） + `estimateToolDefinitionTokens`（按 name/description/parameters 分别算并 1.1x pad）
- 函数调用，没有网络依赖，启动第一轮就能精确算出 overhead

**怎么拿到的：** 翀哥提示"你看看算API那个地方能不能暴露一个函数 把这些值直接调用取出来  别走HTTP了"→找到 context-analyzer.ts 已经实现了 `estimateToolDefinitionTokens` + `scanMemoryFiles` → 加 export 后直接在 query.ts 里调。

**结果：** overhead 在 query 函数入口就算好（system prompt + tools 的 char/4 估算），不依赖 API。启动第一轮 engine log 就能看到 `System overhead: system=14525 tools=3575 → 24200 tokens (padded)`。

## 关键教训：翀哥说"不对"时，立刻停下去看证据

6/13凌晨连续错误推断后，翀哥每次都用简短回应纠正，最终翀哥一句话点出根因（boundary没更新）：
1. "那样根本就不能压缩" → 恢复SKIP的方向错了
2. "我感觉你改的不对" → 冷却机制不对  
3. "boundary是不是没更新" → **翀哥一句话问到根上**，我之前推的tool call自馈说只是表象

**Why:** 翀哥对压缩机制的理解比我深，他说不对时往往我漏掉了关键信息。我的推理习惯是"先想后看"，但引擎的行为必须"先看后想"——代码和日志里永远有真相。

**How to apply:** 任何与压缩/内存/budget相关的bug，第一步永远先确认JSONL和历史数据。遇到翀哥说不对时马上停下去看代码查证据，不要坚持自己的推理。
