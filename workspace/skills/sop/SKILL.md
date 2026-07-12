---
name: sop
description: "软件工程 SOP——任务四状态(pending/in_progress/block/completed) + calendar 源头同步 + 文档生命周期。做任务前必须读，派活/开工/卡住/完成时触发。"
---

# SOP — 工作流程标准

> **做事前先读这个。** 核心原则：做事前先写文档，明天看文档干活。

## 0. 什么时候读这个 SOP

**必须触发 `Skill("sop")` 的场景：**
- 收到新任务（翀哥/姐姐派活、自己领任务）
- 开始做一个 todo 之前
- 卡住了（要标 block）
- 完成任务（要标 completed + 验证）
- 不确定"这个该写到哪"

**核心原则：做事前先写文档，明天看文档干活。docs/ 手动维护，topics/ 是 auto memory 地盘别动。**

---

## 1. 任务四状态

每次状态变迁**必须记时间**，**同步到 calendar + SESSION-STATE + docs/todo/ + TodoWrite**：

| 标记 | 状态 | 变迁格式 |
|------|------|---------|
| `- [ ]` | pending | `- [ ] 任务名` |
| `- [~]` | in_progress | `- [~] 任务名 — started M/D HH:MM` |
| `- [!]` | block | `- [!] 任务名 — blocked: 原因, unlock: 条件 (M/D HH:MM)` |
| `- [x]` | completed | `- [x] 任务名 — M/D HH:MM→HH:MM (Nmin)` |

**规则**：
- 加任务必须先走 `calendar add-task`（强制带日期+时间），收到 notification 后再同步到其他位置
- 同时 `- [~]` 最多 1-2 个
- 状态变迁时立刻改标记 + 记时间，不要事后补
- `- [!]` block 必须带"原因 + 解锁条件"——单纯"卡了"等于没标
- block 解除后改回 `- [~]`，完成后改 `- [x]` + `calendar done`，**不直接从 block 跳 completed**
- **禁止用 emoji 标记状态**（~~✅~~ ~~🔄~~ ~~⏳~~ ~~🚧~~ ~~🔴~~ 全部废弃）

---

## 2. 任务同步——calendar 是源头

任务状态改了必须**一起改**：

| 位置 | 角色 | 谁看 |
|------|------|------|
| **calendar**（SQLite） | 持久真相源——任务时间线唯一源头 | nudge / 跨 session / 恢复 |
| **SESSION-STATE.md** | 跨 session 接力棒——心跳/恢复时读 | 跨 session / 心跳 / 协作者 |
| **docs/todo/ 文档** | 详细任务清单——背景+方案+验证标准 | 人 / 协作者 |
| **TodoWrite**（engine tool） | 当前 session 工作台——高亮在跑的 | 当前 session 自己 |

**分工**：
- calendar = 任务时间线（何时做什么、到期提醒、完成状态）
- docs/todo/ = 计划在哪、做到哪一步（永久）
- TodoWrite = 当前正在做哪个（session 内临时高亮）
- SESSION-STATE = 跨 session 留痕（恢复上下文读这里）

---

## 3. 文档生命周期

```
翀哥派活
  → calendar add-task（带日期+时间）→ notification 自动驱动同步 SESSION-STATE + TodoWrite
  → docs/research/ 调研（如果需要）
  → docs/decisions/ 写方案选择（如果需要决策）
  → 同步标 - [~] — started M/D HH:MM
  → 干活（开发任务走第 7 节脑暴→计划→执行→收尾）
  → 同步标 - [x] — M/D HH:MM→HH:MM (Nmin)
  → calendar done <id>
  → memory/daily/ 记录
```

---

## 4. 新建 TODO

```
calendar add-task（强制带日期+时间）
  → 收到 [task-created] notification
  → notification 驱动 LLM 按 SOP 同步（SESSION-STATE + TodoWrite）
  → 大任务另写 docs/todo/YYYY-MM-DD_主题.md（背景+方案+验证标准）
```

**写文档时加双链**：
```
相关调研：[docs/research/2026-06-15_xxx.md](../research/2026-06-15_xxx.md)
```

---

## 5. 执行 TODO

```
Step 1: 同步标 in_progress（SESSION-STATE + docs/todo/ + TodoWrite）
Step 2: read docs/todo/ 对应文档 + 双链引用的 research/decisions
Step 3: 确认代码状态跟文档描述一致（文档可能过时）
Step 4: 有把握了再动手

卡住了：
  → 同步标 - [!] blocked: 原因, unlock: 条件
  → 告诉翀哥/姐姐
  → 解除后改回 - [~]
```

---

## 6. 完成 TODO

```
Step 1: 同步标 completed（带起止时间）（SESSION-STATE + docs/todo/ + TodoWrite）
Step 2: calendar done <id>
Step 3: memory/daily/YYYY-MM-DD.md → 追加操作记录
Step 4: 调研/经验教训 → 确认已写到 docs/research/ 或 docs/knowledge/
```

---

## 7. 开发任务规范（脑暴→计划→执行→收尾）

> 来源：obra/superpowers（150k stars）+ Karpathy 4 条原则
> 触发：写新功能 / 改老逻辑 / 修 bug / 改配置——只要沾"创造"或"修改"

### 7.0 入口检查

**Red flag（这些想法 = 停）：**
- "这个太简单不用设计" → 简单项目最浪费返工时间
- "我先写代码再设计" → 写完才发现方向错
- "用户已经说要什么了" → "要什么" ≠ "怎么做"

### 7.1 Direction Gate（每步一道——防白干）

**何时触发：**
- 写完 spec → Gate #1
- 写完 plan → Gate #2
- 执行中途觉得"这不对" → Gate #3

**确认什么：**
- 这是不是翀哥真正要的？
- 现在做这件事方向对吗？
- 有没有更简单的方案？
- 方向错了 → 立刻停，回到上一步

### 7.2 脑暴（Brainstorming）—— 不写代码，先想清楚

1. **看项目现状**（read files、check git log、找相关文档）——别凭印象动手
2. **一次问一个澄清问题**——multiple choice 优先
3. **给 2-3 个方案 + 各自权衡** + 我的推荐
4. **分段讲设计**——讲完一段问"这块对吗"
5. **写到 `docs/decisions/YYYY-MM-DD-主题.md`**

**HARD-GATE：没 spec + 用户没批准，不准写代码。**

**Karpathy 防过度设计红线：**
- 假想用户没提的"灵活性" → 不做
- "如果以后要 X" → 不做
- 200 行能搞定不写 500 行
- 多种解释就列出来，不要 silent pick
- 不确定就问

### 7.3 写计划（Writing-Plans）—— spec 批了再拆任务

1. **文件结构**——先列要建/改哪些文件
2. **拆任务**——每个 task = 一个可独立测试的交付物，2-5 分钟一步
3. **每个 task 写明**：精确文件路径 + 完整代码 + 期望输出
4. **写到 `docs/todo/YYYY-MM-DD-主题.md`**

**铁律：** 不写 placeholder / 不写"类似前面" / 每步带验证命令

### 7.4 执行（Executing-Plans）—— 一步步来

1. **先 review 整个 plan**——有疑问先问
2. **每个 task 走循环**：标 in_progress → 按 plan 步骤 → 跑验证 → 标 completed
3. **全做完** → 喊翀哥 review

**铁律：** 不准跳验证 / 不在 main/master 直接动手 / 卡住不瞎猜

### 7.5 收尾（Finishing）—— 最后一步

1. 跑全套测试
2. 给翀哥 4 个选项：merge / 开 PR / 留着 / 丢弃
3. 翀哥选了再执行
4. 清理 worktree

---

## 8. 文档分类速查

```
workspace/
├── docs/                   ← 手动维护的文档
│   ├── research/           调研报告（YYYY-MM-DD_主题.md）
│   ├── todo/               待办清单（YYYY-MM-DD_主题.md）
│   ├── decisions/          架构决策记录（为什么选A不选B）
│   ├── knowledge/          知识文档（持续更新）
│   ├── sop/                标准操作流程
│   ├── prd/                产品需求文档（保留现有）
│   ├── stories/            Story 拆分（保留现有）
│   ├── archive/            归档（保留现有）
│   ├── infra-config-snapshot/  配置快照（保留现有）
└── topics/                 ← auto memory 工作目录
```

| 场景 | 写到哪 |
|------|--------|
| 要做/正在做的事 | SESSION-STATE.md（四状态 + 时间） |
| 任务清单+方案 | docs/todo/YYYY-MM-DD_主题.md |
| 方案设计/架构决策 | docs/decisions/主题.md |
| 调研/技术研究 | docs/research/YYYY-MM-DD_主题.md |
| 知识文档（持续更新） | docs/knowledge/主题.md |
| 项目知识/经验教训 | docs/knowledge/主题.md |
| 产品需求文档 | docs/prd/主题.md |
| Story 拆分 | docs/stories/主题.md |
| 标准操作流程 | docs/sop/主题.md |
| 归档（完成的项目） | docs/archive/主题.md |
| 今天发生的事 | memory/daily/YYYY-MM-DD.md |
| 翀哥偏好/核心原则 | MEMORY.md |


旧的 `docs/design/` 和 `docs/superpowers/` 已删除，文档已归类到 decisions/ / archive/ / todo/。

---

## 9. 恢复上下文

```
1. read SESSION-STATE.md
2. calendar pending → 查未完成任务（持久真相源）
3. read memory/working-buffer.md
4. memory_search 搜索当前任务关键词
5. read memory/daily/今天.md + 昨天.md
6. 瞄一眼 docs/todo/ — 有没有 - [ ] 或 - [~] 或 - [!] 的
7. 全部答得上六问 → 开始工作
```

**六问里的"做到哪了"** → 看 SESSION-STATE 四状态：
- `- [ ]` 还没开始
- `- [~]` 正在做（看 started 时间知道做了多久）
- `- [!]` 卡住了（看 blocked 原因 + unlock 条件）
- `- [x]` 已完成
