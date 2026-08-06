# CC Session机制代码Review (2026-05-27 傍晚)

小柯对CC `e88ba75` commit的完整代码review。CC改了exec/read/write/session/main等多个文件。

## 🔴 P0 必须修的

### 1. reader.ts:153 — `path` import在文件末尾
```typescript
// 第153行（文件最后一行）
import * as path from 'node:path'
```
`listSessions()` 第144行用了 `path.join()`，但import在第153行。TS/ESM的hoisting能跑但不可靠，严格模式或某些bundler会报 ReferenceError。

**修复：** 移到文件顶部import区。

### 2. read.ts:91 — MAX_FILE_SIZE 5MB太大
Claude Code原始是 `256KB`。5MB大文件直接撑爆context window。大文件应offset+limit分段读。

**修复：** 改回 `256 * 1024`（或最多1MB）。

### 3. read.ts:70 — readFileState存完整content浪费内存
```typescript
export const readFileState = new Map<string, { timestamp: number; content: string }>()
```
write只用timestamp，不需要content。读5MB文件就存5MB在Map里，永不释放。

**修复：**
```typescript
export const readFileState = new Map<string, { timestamp: number }>()
```

### 4. main.ts:395 — user消息重复push（最严重！）
```typescript
// 第286行构造messages时已经包含了user消息
const messages: Message[] = [...history, msg.user(text)]

// 第395行又push了一次到history（引用）
history.push(msg.user(text))  // ← 重复！
history.push(...toolHistoryEntries)
history.push(msg.assistant(fullResponse))
```
`history` 是引用，第286行 `[...history, msg.user(text)]` 没有修改history。但第395行直接push到history——第一条user消息只出现一次。**等等，仔细看：**

- L286: `messages = [...history, msg.user(text)]` — 这里 `msg.user(text)` 被追加到messages（新数组），**不影响history**
- L395: `history.push(msg.user(text))` — 这里push到history
- 所以第286行和第395行并不重复。L286是构造给LLM的messages，L395是更新内存history。

**实际影响：** L395 push user → L396 push toolHistory → L397 push assistant。下次query时L280 `history = sessionHistories.get(sessionId)` 拿到的history已经包含上一轮的user+tool+assistant。L286 `[...history, msg.user(text)]` 把新一轮user追加上去。**这个逻辑是正确的**，user消息不重复。

### 5. main.ts:415 — sessionId格式 `discord:userId`
```typescript
const sessionId = `${inbound.channel}:${inbound.from}`
```
平台和用户ID绑在一起。文档已写在 `.openclaw/docs/session-mechanism.md`。

## 🟡 P1 建议修的

### 6. main.ts:236 — 截断逻辑太粗暴
```typescript
while (estimateTokens(messages) > RESTORE_MAX_CHARS / CHARS_PER_TOKEN && messages.length > 10) {
  messages = messages.slice(-Math.floor(messages.length * 0.7))
}
```
每次砍30%跳太猛。建议改成每次shift掉最旧1条：
```typescript
while (estimateTokens(messages) > limit && messages.length > 10) {
  messages.shift()
}
```

### 7. write.ts:207 — text和toolCall互斥不合理
```typescript
if (params.text && (!params.toolCalls || params.toolCalls.length === 0)) {
  content.push({ type: 'text', text: params.text })
}
```
Claude的assistant回复可以同时有text和tool_call——先说一段话再调工具。这个互斥条件会导致有tool_call时text被吞掉。

**修复：** 去掉tool_call判断，直接 `if (params.text)`。

### 8. main.ts:384 — 最后一轮flush条件可能漏掉tool_call
```typescript
if (roundText || roundToolCalls.length === 0) {
  flushRound('endTurn')
}
```
如果最后一轮只有tool_call没有text（roundText空且roundToolCalls.length > 0），条件为false——最后轮tool_call不会被flush。

**修复：**
```typescript
if (roundText || roundToolCalls.length > 0 || roundToolResults.length > 0) {
  flushRound('endTurn')
}
```

## ✅ CC做得好的
1. SessionWriter用 `crypto.randomUUID()` 生成ID ✅
2. JSONL格式跟OpenClaw v5兼容 ✅
3. session恢复有截断保护 ✅
4. 流式输出有缓冲（200字/换行flush）✅
5. mtime守护思路正确 ✅

## Review纠正（翀哥要求重新check）

### ❌ 第4条说错：user消息重复 — 撤回

展开运算符 `[...history, msg.user(text)]` 创建新数组不修改history引用。L286构造messages给LLM，L395 push到history，两者操作不同数组。**user消息不重复，CC逻辑正确。**

### ❌ 第8条说错：flush漏掉tool_call — 分析反了

`flushRound()` 里 `roundToolCalls.length = 0` 清空数组，循环结束后 `roundToolCalls.length === 0` 永远为true。条件退化成 `if (roundText || true)` = 永远true。**问题不是"漏flush"而是可能"重复flush空消息"**（如果最后一轮是tool_use，history chunk时已flush，循环后又会flush一个空assistant）。

### ❌ 第1条说太绝对：path import运行时报错

ESM import是静态hoisted的，运行时不存在ReferenceError。代码异味是有的但不会报错。优先级从P0降到P2。

### ✅ 仍然成立的

1. read.ts 5MB限制 — 还是太大
2. readFileState存content浪费内存 — write只用timestamp
3. sessionId格式 — 文档已写
4. writer.ts text/toolCall互斥 — 有toolCall时text被吞
5. main.ts截断逻辑 — 每次砍30%太粗暴

## session-mechanism.md文档
写好了放 `.openclaw/docs/session-mechanism.md`，commit `a10e3f9`：
- Session ID命名规范（别用`discord_xxx`，用UUID/时间戳）
- 记忆加载机制（双写、取多的、全量加载）
- 自动压缩（85%阈值、400条硬上限）
- 改进建议（原文不覆盖、分级取舍、token预算、跨平台合并）
- Hermes源码关键位置参考
