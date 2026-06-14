---
name: PostCompact hook方案 — compaction后任务丢失修复
description: Engine压缩后任务断档问题的根因分析和PostCompact hook自动注入working-buffer的方案设计
type: project
---

# PostCompact Hook方案 — Compaction后任务不丢

## 问题描述

2026-06-14发现：compaction前正在执行的任务（EP01视频发布），压缩后虽然日记里记了任务状态，但恢复后执行动力断了——读了日记知道"要做发布"，也去读了skill，但发现只有YouTube脚本后就开始等翀哥回复，没有继续推进。

**根因：**
1. PreCompact flush只记"任务状态"，没记"下一步具体做什么"
2. 恢复后没有强制检查"有没有正在执行的任务"
3. working-buffer靠LLM自觉写/读，引擎不强制
4. 心跳/巡检消息进来后分散注意力，任务被搁置

## Engine Hook体系现状

### 已有Hook事件
Engine已有完整hook体系（`src/hooks/types.ts`），关键事件：

| Hook | 状态 | 用途 |
|------|------|------|
| PreCompact | ✅ 已注册 | 压缩前触发"Pre-compaction memory flush"消息让LLM存档 |
| PostCompact | ✅ 已定义（`types.ts:152`），在`autoCompact.ts:169/208`压缩完成后调用 | 压缩后注入additionalContext |

### 关键发现

**PostCompact hook支持返回`additionalContext`**（`executor.ts:122`），这个context会**自动注入到压缩后的LLM上下文**。但目前没有注册任何PostCompact hook——所以压缩后LLM收不到任何恢复信息。

### Hook执行流程（autoCompact.ts）
```
压缩前：
  1. executePreCompactHooks('auto', hookCtx)  ← LLM收到flush消息，写日记
  2. stripImages + LLM summary
  
压缩后：
  3. buildPostCompactMessages（boundary marker + summary）
  4. executePostCompactHooks('auto', hookCtx)  ← 目前空跑，没注册hook
```

### Hook注册方式（config.ts）
```typescript
// 方式1：进程内callback（推荐，简单）
registerCallbackHook('PostCompact', {
  type: 'callback',
  callback: async (input, ctx) => {
    // 读working-buffer.md
    // 返回 { hookSpecificOutput: { additionalContext: "..." } }
  }
})

// 方式2：配置文件command hook
// xiaoke.json: { hooks: { PostCompact: [{ matcher: "", hooks: [{ type: "command", command: "cat working-buffer.md" }] }] } }
```

## 方案设计

### 整体流程
```
压缩前（PreCompact）：
  → LLM收到flush消息
  → LLM写working-buffer.md：
    - 当前正在执行的任务
    - 下一步具体动作（不是"任务状态"，而是"接下来做什么"）
    - 关键文件路径
  → LLM写memory/daily日志

压缩后（PostCompact）：
  → Engine自动执行PostCompact hook
  → hook读working-buffer.md
  → 返回additionalContext = working-buffer内容
  → Engine自动注入到LLM上下文
  → LLM压缩后第一条消息就能看到"正在做什么+下一步"
```

### 实现步骤

1. **在engine-startup.ts注册PostCompact callback hook**
   ```typescript
   registerCallbackHook('PostCompact', {
     type: 'callback',
     callback: async (input: HookInput, ctx: HookExecutionContext) => {
       const bufferPath = path.join(workspace, 'memory', 'working-buffer.md')
       if (fs.existsSync(bufferPath)) {
         const content = fs.readFileSync(bufferPath, 'utf-8')
         return {
           hookSpecificOutput: {
             additionalContext: `[PostCompact] 以下是压缩前的任务快照，请立即继续执行：\n\n${content}`
           }
         }
       }
       return {}
     }
   })
   ```

2. **强化working-buffer写入规范**
   - PreCompact flush时必须写working-buffer.md
   - 内容必须包含"下一步具体动作"
   - AGENTS.md更新恢复流程

3. **AGENTS.md恢复流程更新**
   - 六问恢复加一条："有没有正在执行的任务？"
   - 有的话立即继续，不处理心跳/巡检

### working-buffer格式（规范）
```markdown
# Working Buffer — YYYY-MM-DD HH:MM

## 正在执行的任务
[任务名]

### 当前状态
[做到哪了]

### 下一步具体动作
[接下来做什么，不是模糊描述，是具体动作]

### 关键文件路径
- [文件1]
- [文件2]
```

## 已实现部分（6/14 commit 5516a99）

✅ **全部完成，已重启生效：**
1. `src/compact/types.ts` — CompactConfig加`minReductionRatio?: number`（默认0.30）
2. `src/compact/autoCompact.ts` — ruleCompact/microcompact/LLM三处加降幅检查+PostCompact hook注入
3. `src/engine-startup.ts` — 注册PostCompact callback hook读working-buffer.md
4. `configs/xiaoke.json` — compaction节点加`"minReductionRatio": 0.30`

### minReductionRatio 30%阈值

**问题：** ruleCompact完成后只判断"是否低于threshold"，降幅9%就满足，3-4轮后重新触发，死循环。

**解决：** 压缩后即使低于threshold，降幅<30%也不满足，继续走microcompact/LLM。配置化可调：
```json
"compaction": {
  "minReductionRatio": 0.30
}
```

## 后续规划：TodoWrite tool 任务持久化（翀哥6/14建议）

**思路：** 压缩前用TodoWrite把正在做的任务写进todo列表。todo数据存在引擎内存中，不受compaction影响——压缩后LLM恢复时看到todo里有未完成任务，会自动继续执行。

**与PostCompact hook的关系（互补）：**
- PostCompact hook注入working-buffer → 告诉LLM"之前在做什么+下一步"（自然语言描述）
- TodoWrite → 框架自动管理的task列表，有明确状态（pending/done）（结构化任务跟踪）
- 两者互补：working-buffer负责上下文恢复，todo负责执行驱动

**优势：**
- todo有明确状态（pending/in_progress/completed），比working-buffer的文本描述更精确
- todo是框架内置机制，不随messages丢失
- LLM恢复后看到in_progress的todo，天然有执行动力

**待实现：** Engine侧TodoWrite tool注册 + PreCompact时自动把当前todo快照注入working-buffer

## 关键文件索引
- `src/hooks/types.ts` — HookInput定义（PostCompactHookInput at L152）
- `src/hooks/executor.ts` — hook执行逻辑（additionalContext处理 at L122）
- `src/compact/autoCompact.ts` — 压缩流程（PreCompact at L144, PostCompact at L169/208）
- `src/hooks/config.ts` — hook注册表（registerCallbackHook at L55）
- `src/hooks/index.ts` — hook导出入口
- `src/engine-startup.ts` — hook注册位置
