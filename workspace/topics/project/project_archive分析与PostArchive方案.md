---
name: JSONL archive分析与PostArchive方案
description: JSONL archive不丢内存history，任务"中断"是Discord ECONNRESET+心跳安静导致的。PostArchive方案已回退。6/15翀哥要求文档化完整链路。
type: project
---

## 发现（6/14晚-6/15凌晨）

### 问题现象
6/14 21:09 翀哥说任务"断了"——让我整理topics目录，回复"继续啊 怎么停了"。初步怀疑archive触发导致内存history被trim。

### 根因分析

**Archive机制（session-manager.ts → checkAndArchive）：**
- archive在query loop的`finally`块执行——**query跑完后才触发**，不中断tool调用
- `archiveFileOnDisk`内部通过`readPostBoundaryFromArchived`查找最后一个compact_boundary
- **有compact_boundary：** 新JSONL保留boundary后全部消息
- **无compact_boundary：** 新JSONL为空（只有header）

6/14 21:09的archive日志：
```
Archive complete: ...(2.0MB) → new JSONL created (853514 bytes)
```
853KB ≠ 空——说明有compact_boundary，新JSONL不是空的。

**真正原因（不是archive）：**
1. **首次中断（20:32）：Discord ECONNRESET导致回复丢失** — 20:32:38我完成分析后回复翀哥（"看完了，确实乱..."），但Discord发送时`read ECONNRESET`连接重置，消息没发出去。query已完成但用户看不到响应。翀哥等了39分钟无输出。
2. **后续（21:09）：** 心跳Turn 3回复HEARTBEAT_OK后，LLM只输出简短文本（78字符），用户看不到任何响应
3. archive + extractMemories跑了约1分钟（21:09:54→21:10:13）
4. 用户以为"停了"，实际心跳刚完成，LLM在等待用户下一条指令
5. **是两个独立事件叠加：20:32 ECONNRESET（发送失败）+ 21:09 心跳安静（LLM无输出）**，都不是archive bug

### PostArchive方案（已实现但多余）

**方案（commit `312d3b7` + `7ed2495`）：**
- `checkAndArchive`成功后读working-buffer.md
- 通过`writer.writeUserMessage()`写进新JSONL
- 重启后restore读到，LLM知道任务状态

**为什么多余（翀哥6/15确认）：**
- 不重启：内存history没丢，不需要注入
- 重启：新JSONL通过`readPostBoundaryFromArchived`已有853KB内容（含完整compact_boundary后对话）
- working-buffer写进新JSONL只增加了几百字节，但实际已有足够历史
- "如果逻辑都是正确的，我们没必要写"——翀哥

**已回退：** commit `75ce013`，全部代码恢复原状。

### Log口径修复（commit `5150fe9`）

**背景：** 翀哥看到日志 `Restored 213/342 messages (~45083 tokens)` 觉得"丢了100多条"。

**根因：** 342是`allMessages.length`（过滤后未截断的消息数），213是token安全阀截断后的消息数。两者是**不同口径**——不是丢消息。

**修复：** 改日志显示 `Restored 213 messages (~45083 tokens) (token-truncated: 129 older msgs dropped, max 50000 tok) from 1 file(s)`。

### 结论
archive本身不影响任务连续性。真正需要解决的问题是"LLM在心跳后安静，用户感知中断"——这不是archive能解决的。

## 完整链路：Compact → Archive → Restore（6/15翀哥要求文档化）

### Compact流程
1. **触发：** auto-compact检测token超阈值（memoryHistoryTokens + overhead > maxContextTokens）
2. **PreCompact flush：** 注入system消息，要求LLM立即更新working-buffer.md（内容为当前任务状态）
3. **压缩：** LLM总结旧消息为compact_boundary（human + assistant各一条）
4. **PostCompact hook：** 读working-buffer.md，作为user消息注入压缩后上下文
5. **关键：** compact_boundary写入JSONL，但boundary之前的旧消息**不删除**，仍留在同一个JSONL文件中

### Archive流程
1. **触发：** maxFileEntries或maxFileSize超限 → 创建新JSONL
2. **readPostBoundaryFromArchived：** 找最后一个compact_boundary，只拷贝boundary之后的内容到新JSONL
3. **旧JSONL改名：** `xxx.archived.2026-06-14.jsonl` 归档不再读取
4. **关键：** archive不丢内存history，因为query跑完才触发，且新JSONL有post-boundary完整内容

### Restore流程（重启时）
1. 读JSONL所有entries → 过滤出`message`类型 → 找最后一个compact_boundary → 恢复boundary后消息
2. 过滤未配对tool_call和空assistant消息
3. token安全阀截断（max ~50000 tokens）

### 易混淆点（翀哥指出）
- **JSONL行数（entries）≠ 消息数（messages）：** 342 entries含header/model_change/custom_message/attachment等非消息行，过滤后约250 messages
- **compact不删旧消息：** compact_boundary是物理行标记，旧消息仍留在文件同一JSONL中。archive时才通过readPostBoundary切割
- **archive写working-buffer是无用功：** 新JSONL已有post-boundary完整对话历史，LLM不需要额外注入任务状态
- **Restore日志口径已修复：** 显示 "messages (token-truncated: N older msgs dropped, max M tok) from X file(s)" 双口径

### 关联
- 跟`project_PostCompact_hook方案.md`不同——那是压缩导致任务丢失（memory文件未写），这个是archive但不丢历史
- working-buffer保持最新仍是好习惯（参见`feedback_working-buffer完成后清空.md`）

## 6/15更新：文档化完成 ✅
- 翀哥6/15要求把compact→archive→restore完整链路+易混淆点文档化
- 上方"完整链路"章节已写完（6/15 commit包含）
- PostArchive方案（写working-buffer进新JSONL）已确认无用，**已回退**（commit 75ce013）
- restore日志口径已修复（`5150fe9`），显示token-truncated双口径
