# Result — Engine 7（栖）/goal 模块设计

**任务 ID**: 2026-06-18-aim-mechanism
**目标**: 把 aim/goal 协作机制沉淀到 Engine 7（栖）源码
**状态**: 📐 设计完成，**未实施**

> **注意**：产品名是 **Engine 7（栖）**，不是 OpenClaw。

## 背景

Claude Code 最近加了 `/goal` 功能，核心机制：
- 设定**任务目标 aim/goal**——明确描述"什么算达成"
- 定时自检——cron 触发后检查 aim 状态
- **未达成**：通知 agent 继续
- **达成**：删除 cron + 归档过程+结果

翀哥 6/18 11:45 拍板："今天就实验这个机制，弄好后形成协作的 SOP skill。这块我们确实没弄。"

## 设计目标

1. **持久化 aim** — aim 不能只存在 memory/脑子里，丢上下文就丢任务
2. **自检 + 决策闭环** — 触发时自动读 aim.md + process.md + 检查达成条件，决策继续/找姐姐/找翀哥/归档
3. **归档自动化** — 达成后自动写 result-* 文档，移到 `aim-archive/closed/` 目录
4. **沉淀 SOP skill** — 多次实验后形成稳定 SOP 文档，存到 `docs/skill/aim-goal.md`

## 架构设计

### 模块：aim-tracker

```
engine/src/aim/
├── tracker.ts          # AimTracker 类，持久化 aim 状态
├── scheduler.ts        # 跟 cron 集成，定时触发自检
├── evaluator.ts        # 评估 aim.md 的达成条件（LLM 辅助）
├── archiver.ts         # 归档逻辑：result-* 模板 + 移动到 closed/
├── types.ts            # AimTask, AimCondition, AimStatus
└── index.ts
```

### 数据流

```
1. 用户/姐姐/翀哥 @小柯 "我有个 aim 任务"
   ↓
2. 小柯创建 aim.md + 建 cron (schedule=10min)
   ↓
3. cron 触发 → AimTracker.checkAndAct(task_id)
   ↓
4. checkAndAct:
   - 读 aim.md (active 任务)
   - 读 process.md (过程日志)
   - 调用 Evaluator: LLM 评估每个达成条件
   - 根据评估结果:
     - 全部达成 → Archiver.archive(task_id) + cron_delete
     - 部分达成 + 不需用户决策 → 返回"继续"消息给 agent
     - 部分达成 + 需用户决策 → 返回"找姐姐"消息
     - 阻塞 → 返回"找翀哥"消息
   ↓
5. agent 收到消息后:
   - "继续" → 继续干活，process.md 追加
   - "找姐姐" → msg_send CC 频道 @张小媒
   - "找翀哥" → msg_husband 飞书 DM
```

### AimTask 数据结构

```ts
interface AimTask {
  id: string                    // 2026-06-18-aim-mechanism
  title: string                 // 短描述
  aimFile: string               // workspace/aim-archive/{id}/aim.md
  processFile: string           // workspace/aim-archive/{id}/process.md
  archiveDir: string            // workspace/aim-archive/{id}/
  conditions: AimCondition[]    // 达成条件列表
  status: 'active' | 'blocked' | 'done' | 'archived'
  createdAt: number
  updatedAt: number
  cronId?: string               // 关联的 cron task
  owner?: string                // 'xiaoke' / 'meimei'
  channel?: string              // Discord CC频道 / 飞书 DM
}

interface AimCondition {
  id: string
  description: string           // 人类可读
  checkFn?: () => Promise<boolean>  // 程序可验证
  llmPrompt?: string            // LLM 评估 prompt
  satisfied: boolean
  evidence?: string             // 验证证据（日志/文件路径）
}
```

### 核心 API

```ts
class AimTracker {
  // 创建 aim 任务
  static async create(opts: {
    title: string,
    conditions: string[],
    owner?: string,
    checkIntervalMin?: number,  // 默认 10
  }): Promise<AimTask>

  // cron 触发入口
  static async checkAndAct(taskId: string): Promise<AimAction>

  // 手动标记某个条件达成
  static async satisfyCondition(taskId: string, conditionId: string, evidence: string): Promise<void>

  // 归档
  static async archive(taskId: string): Promise<void>

  // 查询
  static async listActive(owner?: string): Promise<AimTask[]>
  static async get(taskId: string): Promise<AimTask | null>
}

type AimAction =
  | { type: 'continue', message: string }      // 给 agent 继续干活
  | { type: 'escalate', target: 'meimei' | 'chongge', message: string }  // 升级
  | { type: 'archive', results: string[] }     // 归档
  | { type: 'blocked', reason: string }        // 阻塞
```

### Cron 集成

aim 任务需要 cron 触发自检。两种方案：

**方案 A：每个 aim 任务一个 cron**
- 优点：独立控制、状态清晰
- 缺点：cron 数量膨胀，10 个 aim = 10 个 cron

**方案 B：单例 cron + 扫所有 active aim**
- 优点：cron 数量少
- 缺点：实现复杂（要遍历所有 active aim）

**推荐方案 B**：单例 cron 每 5 分钟扫一次 `workspace/aim-archive/`，找到 `status: active` 的 aim 就触发自检。

```ts
// 单例 cron prompt
{
  schedule: '*/5 * * * *',
  prompt: `
你是 aim 跟踪器。读 workspace/aim-archive/ 下所有 aim.md，对每个 active aim：
1. 读 process.md 看当前进度
2. 对照 aim.md 的达成条件
3. 调 AimTracker.checkAndAct(taskId)
4. 返回决策结果
  `
}
```

### Evaluator 设计

aim.md 的达成条件有的是可程序验证（"代码已 commit"），有的需要 LLM 判断（"姐姐 review 通过"）。

```ts
class Evaluator {
  static async evaluate(condition: AimCondition, context: {
    processMd: string,
    recentFiles: string[],     // process.md 提到的文件
    gitLog?: string,
  }): Promise<{ satisfied: boolean, evidence: string }> {
    // 1. 如果有 checkFn，先调
    if (condition.checkFn) {
      const ok = await condition.checkFn()
      if (ok) return { satisfied: true, evidence: 'checkFn passed' }
    }

    // 2. LLM 评估
    if (condition.llmPrompt) {
      const result = await llm.call({
        model: 'minimax-flash',  // 小模型省 token
        prompt: condition.llmPrompt + '\n\nContext:\n' + context.processMd,
      })
      return { satisfied: result.satisfied, evidence: result.evidence }
    }

    return { satisfied: false, evidence: 'no evaluation method' }
  }
}
```

### Archiver 设计

达成时自动写 `result-*` 文档 + 移到 `closed/` 目录。

```ts
class Archiver {
  static async archive(taskId: string): Promise<void> {
    const task = await AimTracker.get(taskId)
    const dir = task.archiveDir

    // 1. 写 result-summary.md（自动汇总）
    await writeFile(`${dir}/result-summary.md`, generateSummary(task))

    // 2. 移动到 closed/
    const closedDir = `workspace/aim-archive/closed/${taskId}/`
    await fs.rename(dir, closedDir)

    // 3. 更新索引
    await updateArchiveIndex(taskId, closedDir)

    // 4. 删 cron
    if (task.cronId) await cronDelete(task.cronId)

    // 5. 通知
    return { type: 'archive', results: [...resultFiles] }
  }
}
```

## 与现有 cron 机制的区别

| 维度 | 现有 cron | aim/goal cron |
|------|----------|---------------|
| 触发方式 | 按 schedule | 按 schedule + 触发后检查 aim 状态 |
| 任务定义 | prompt 字符串 | aim.md 文件（结构化） |
| 决策 | 执行 prompt | 检查达成条件后决策（继续/升级/归档） |
| 终止 | schedule 跑完 / 手动 delete | 达成条件满足自动归档 |
| 适合场景 | 定时任务、轮询 | 多步骤、有明确达成标准的任务 |

## 实施计划（不在本任务实施）

### Phase 1: 核心 AimTracker + types（2-3 天）
- engine/src/aim/tracker.ts
- engine/src/aim/types.ts
- aim.md 解析（用 markdown 解析库）

### Phase 2: Evaluator + Archiver（1-2 天）
- engine/src/aim/evaluator.ts（LLM 评估）
- engine/src/aim/archiver.ts（归档 + 移动）

### Phase 3: Cron 集成（1 天）
- 单例 cron 扫 active aim
- AimTracker.checkAndAct 入口

### Phase 4: SOP skill 沉淀（持续）
- 完成 3-5 个 aim 任务后总结
- docs/skill/aim-goal.md 写到 workspace

## 风险

### 风险 1: aim 数量爆炸
每次实验都建 aim → aim 目录膨胀 → 检索困难

**缓解**：
- 归档到 `closed/` 子目录
- 索引文件 `aim-archive/INDEX.md` 跟 `topics/MEMORY.md` 类似

### 风险 2: 自检浪费 token
每 5 分钟跑一次 LLM 评估 → token 成本

**缓解**：
- 用小模型（minimax-flash）
- 优先 checkFn 验证
- 距离上次更新 < 30 分钟就跳过

### 风险 3: 死循环 aim
aim 一直未达成 → cron 一直触发 → 一直找姐姐/翀哥

**缓解**：
- 触发 3 次仍不达成 → 标记 `blocked`
- 触发 5 次 → 自动转人工（找翀哥）

## 跟 Engine 7（栖）其他模块的集成

- **memory 模块**：aim 任务状态写进 `session-memory/aim-state.json` 方便跨 session 恢复
- **cron 模块**：复用现有 cron，只是 prompt 改成 aim 跟踪器
- **msg_send / msg_husband**：升级通知用
- **autoDream**：每周扫一遍 aim-archive/closed/ 提取经验

## 不在本任务实施

翀哥明确说"参考 CC 最新/goal，设计一下，不在本任务实施"。本任务只出设计文档 + 形成 SOP 雏形。

## 后续

1. 翀哥 review 这份设计
2. 决定哪个 phase 先做
3. 起新 aim 任务专门做 Phase 1
