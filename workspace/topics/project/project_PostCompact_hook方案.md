---
name: PostCompact hook方案
description: Engine压缩后任务断档问题的完整解决方案——minReductionRatio 30%阈值+PostCompact hook自动注入working-buffer（已完成并部署，6/14重启生效）
type: project
---

## PostCompact hook + minReductionRatio 30% — ✅ 已完成并部署（6/14重启生效）

**问题：** compaction后压缩前正在执行的任务丢失，重启后回到默认心跳-巡检循环。

**解决方案（已实现）：**

### 1. minReductionRatio 30% 降幅阈值 ✅
- ruleCompact/microcompact完成后检查降幅是否≥minReductionRatio（默认0.30）
- 降幅不够不满足，继续往下压缩（microcompact → LLM compact）
- 配置项：`configs/xiaoke.json` compaction节点
- **Why:** 之前降幅9%就停了，3-4轮后再次触发，形成频繁压缩死循环
- **文件改动：**
  - `src/compact/types.ts` — CompactConfig加 `minReductionRatio?: number`（默认0.30）
  - `src/compact/autoCompact.ts` — ruleCompact/microcompact/LLM三段都加了降幅检查
  - `configs/xiaoke.json` — compaction节点加 `"minReductionRatio": 0.30`

### 2. PostCompact hook 时序调整 ✅
- **原位置（❌）：** 在压缩完messages数组后立即调用，但压缩结果还没装入LLM上下文
- **新位置（✅）：** 压缩后messages装入LLM上下文之后调用 — 这样working-buffer的内容回到上下文中，LLM恢复时第一时间看到
- **文件改动：**
  - `src/compact/autoCompact.ts` — 将hook调用移到context装入之后
  - `src/engine-startup.ts` — 注册PostCompact callback hook，读working-buffer.md并注入additionalContext

### 3. 新增配置
```json
"compaction": {
  "enabled": true,
  "bufferTokens": 23000,
  "maxOutputTokens": 16384,
  "minReductionRatio": 0.30,
  "ruleBased": {
    "enabled": true,
    "essentialFields": []
  },
  "memoryFlush": {
    "enabled": true,
    "forceFlushTranscriptBytes": "1.0mb"
  }
}
```

### 4. 后台任务通知机制（exec run_in_background）
翀哥6/14问：执行耗时任务（如transcript转写）时能不能"泡着不用sleep，跑完通知我"？

**答案：** Engine的 `exec` tool 已支持 `run_in_background: true`，任务异步后台执行，完成时系统自动 `TaskOutput` 通知给LLM。不需要sleep轮询。

**如何用：**
```typescript
// tool call 传 run_in_background: true
{
  command: "whisper large-v3 input.mp4",
  run_in_background: true
}
// 完成后系统自动推送 TaskOutput 到上下文
```

### ⏸️ TodoWrite tool任务持久化（翀哥6/14建议，已规划暂缓实现）

翀哥在改完30%阈值+PostCompact hook后提出一个新思路：压缩前用TodoWrite类tool把正在做的任务写入，压缩后LLM恢复时读到todo自动继续执行。

**这个方案的优点：**
- todo是tool调用结果，通过PostCompact hook注入上下文
- todo有明确状态（pending/done/completed）
- 不需要单独维护working-buffer.md文件
- LLM天然会关注tool调用结果中的pending任务

**和working-buffer的对比（翀哥决策）：**
- 6/14翀哥问"todo还做么" → 当前方案（PostCompact hook + working-buffer注入）已经够用
- 30%降幅阈值已大幅减少压缩频率（从3轮触发1次降到预估30轮+才触发1次）
- TodoWrite作为后续优化方案，先规划到文档里，不急实现
- **翀哥最后确认：** "好的 先commit吧 然后把todo这个规划放到我们之前对压缩改进的文档里" — 已执行

**如果需要实现时的设计要点（翀哥6/14讨论中确认）：**
1. 压缩前由PreCompact flush触发→调用TodoWrite tool写当前任务
2. Todo保存在stateDir中，不依赖外部文件
3. PostCompact hook读取todo状态并注入到上下文
4. todo状态可配置（过期时间/完成自动清理）

**Why 暂缓实现：** 当前方案已解决任务丢失问题，TodoWrite是二次优化而非必须。翀哥确认"先不急做"（6/14）。

### ✅ 6/14部署验证结果

**压缩触发时的实况日志：**
```
Rule compact SUFFICIENT: 133068 → 87506 tokens (34.2% >= 30% min)
PostCompact: injecting working-buffer (460 chars)
```

三项全部生效：
1. ✅ **30%降幅阈值** — 34.2%降幅超过30%门槛才停止，不再9%就停
2. ✅ **PostCompact hook注入** — working-buffer.md成功读入并注入460字符到压缩后的上下文
3. ✅ **任务恢复** — LLM恢复后第一条消息准确报出当前状态（"EP01已全部发布完..."），无任务丢失

**翀哥6/14验证反馈（压缩触发后）：** "很好。还有就是对比下你现在的config和main的，看看你那有啥东西需要给她配过去，别漏掉" — 压缩后任务没丢，翀哥确认效果后进入下一个任务（姐姐配置补缺）。

**⚠️ 发现新问题 — working-buffer内容过时：**
- 注入的是12:05的旧版本（写着"EP01发布中"），而实际EP01已全部发布完成
- 原因：任务完成后没有更新/清空working-buffer.md
- 修复方向：任务完成后立即清空working-buffer.md（已在 `feedback_working-buffer完成后清空.md` 记录）

**🔔 翀哥新要求 — PostCompact hook增加working-buffer时效检查（6/14 讨论中）：**
翀哥在对话最后提出："然后再post hook里读working-buffer.md的时候，确认下这个文件的修改时间是不是太长了，比如超过10分钟，超过则打log告警"

这意味着PostCompact hook需要：
1. 读working-buffer.md内容注入上下文
2. 同时检查文件的mtime（最后修改时间）
3. 如果mtime距离当前时间超过10分钟 → 打log告警"working-buffer.md stale (>10min)"
4. 逻辑：告警但不阻塞注入，内容照常注入，让LLM知道buffer可能过时

**Why:** 翀哥发现压缩后working-buffer还是12:05的旧内容，说明buffer更新不够及时。加了时效检查后，10分钟内没更新会告警触发反思——是"确实没任务"（buffer为空）还是"忘了更新"（buffer内容过时）。

### 关联知识：后台任务通知机制
exec tool的 `run_in_background: true` 让任务后台异步执行，完成时系统自动发送 `TaskOutput` 通知给小柯。不需要sleep轮询。

#### Commit记录
- `5516a99` — 6/14四个文件全部改动入库（types.ts + autoCompact.ts + engine-startup.ts + xiaoke.json）
- `e9d87f6` — 6/14 SKILL.md恢复姐姐删多的发布章节（youtube_upload.py + sau多平台发布工具）

## 发现过程（6/13-6/14）
1. 第一次compaction（~22:45渲染中）：项目文件尚未写，恢复靠日记存档
2. 第二次compaction（~23:30）：同上
3. 第三次compaction（6/14 ~09:30 "自动发布"指令后）：恢复后完全丢失任务，进入心跳-巡检循环
4. 第四次compaction（6/14 ~09:40）：恢复后自动拾起了任务——因为project memory文件已存在
