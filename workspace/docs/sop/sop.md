# SOP — 工作流程标准

## 任务四状态

所有任务统一用四状态标记，**每次状态变迁必须记时间**：

| 标记 | 状态 | 含义 | 变迁格式 |
|------|------|------|---------|
| `- [ ]` | pending | 排队，还没开始 | `- [ ] 任务名` |
| `- [~]` | in_progress | 正在做 | `- [~] 任务名 — started M/D HH:MM` |
| `- [!]` | block | 卡住，等外部条件 | `- [!] 任务名 — blocked: 原因, unlock: 条件 (M/D HH:MM)` |
| `- [x]` | completed | 做完了 | `- [x] 任务名 — M/D HH:MM→HH:MM (Nmin)` |

**规则**：
- 同时 `- [~]` 最多 1-2 个
- 状态变迁时立刻改标记 + 记时间，不要事后补
- `- [!]` block 必须带"原因 + 解锁条件"——单纯"卡了"等于没标
- block 解除后改回 `- [~]`，完成后改 `- [x]`，**不直接从 block 跳 completed**

**禁止用 emoji 标记状态**（~~✅~~ ~~🔄~~ ~~⏳~~ ~~🚧~~ ~~🔴~~ 全部废弃）。

---

## 状态三处同步

状态改了必须**三处一起改**，不能只改一处：

| 位置 | 角色 | 谁看 |
|------|------|------|
| **docs/todo/ 文档** | 永久真相源——任务清单全状态 | 人 / 协作者 / 跨 session |
| **TodoWrite**（engine tool） | 当前 session 工作台——高亮在跑的 | 当前 session 自己 |
| **SESSION-STATE.md** | 跨 session 接力棒——心跳/恢复时读 | 跨 session / 心跳 / 协作者 |

**分工**：
- docs/todo/ = 计划在哪、做到哪一步（永久）
- TodoWrite = 当前正在做哪个（session 内临时高亮）
- SESSION-STATE = 跨 session 留痕（恢复上下文读这里）

---

## 新建TODO流程

当翀哥说"记成todo"/"先记着"/"后面再做"等，**不止记SESSION-STATE**：

```
Step 1: SESSION-STATE.md → 当前任务区加 - [ ] 条目
Step 2: docs/todo/YYYY-MM-DD_主题.md → 写详细文档（背景+方案+任务清单+验证标准）
Step 3: 如果翀哥没说不写文档 → 默认执行 Step 2
```

**Why:** SESSION-STATE 是工作台，压缩/重启后可能丢上下文。docs/todo/ 是持久化的。

**写文档时加双链：** 如果 todo 涉及已有的调研/知识/决策文档：
```
相关调研：[docs/research/2026-06-15_xxx.md](../research/2026-06-15_xxx.md)
```

---

## 执行TODO流程

开始做一个 TODO 时，**先读文档再动手**：

```
Step 1: 三处同步标记 in_progress：
        - SESSION-STATE → - [~] 任务名 — started M/D HH:MM
        - docs/todo/ 文档 → 对应 task 标 - [~]
        - TodoWrite → 标 in_progress
Step 2: read docs/todo/ 对应文档
Step 3: 顺着双链引用，read 相关的 research/knowledge/decisions
Step 4: 确认当前代码状态跟文档描述一致（文档可能过时）
Step 5: 有把握了再动手改代码
```

**卡住了怎么办：**
```
→ 三处同步标 block：
  - SESSION-STATE → - [!] 任务名 — blocked: 原因, unlock: 条件 (M/D HH:MM)
  - docs/todo/ 文档 → 对应 task 标 - [!]
  - TodoWrite → 标 blocked
→ 告诉翀哥/姐姐卡在哪
→ 等条件满足后改回 - [~] 继续
```

**开发任务（写代码/改代码/加功能）同时遵守**：`docs/sop/superpowers-summary.md`（脑暴→写计划→执行→收尾 + Direction Gate）。

---

## 完成任务后

```
1. 三处同步标 completed：
   - SESSION-STATE → - [x] 任务名 — M/D HH:MM→HH:MM (Nmin)
   - docs/todo/ 文档 → 所有 - [ ] 和 - [~] 改成 - [x]
   - TodoWrite → 标 completed
2. memory/daily/YYYY-MM-DD.md → 追加操作记录
3. 如果是调研/分析 → 确认已写到 docs/research/ 或 docs/knowledge/
4. 如果涉及新知识 → topics/ 写记忆文件
```

---

## 文档分类速查

| 场景 | 写到哪 |
|------|--------|
| 要做/正在做的事 | SESSION-STATE.md（四状态标记 + 时间） |
| 新 todo 的详细方案+任务清单 | docs/todo/YYYY-MM-DD_主题.md |
| 调研/技术研究 | docs/research/YYYY-MM-DD_主题.md |
| 方案设计/架构决策 | docs/decisions/主题.md |
| 知识文档（持续更新） | docs/knowledge/主题.md |
| 今天发生的事 | memory/daily/YYYY-MM-DD.md |
| 操作流程（给下次照着做） | docs/sop/主题.md |
| 开发任务规范（脑暴/TDD/Gate） | docs/sop/superpowers-summary.md |
| 翀哥偏好/核心原则 | MEMORY.md |
| 项目知识/经验教训 | topics/下对应分类 |

---

## 恢复上下文后第一件事

```
1. read SESSION-STATE.md
2. read memory/working-buffer.md
3. memory_search 搜索当前任务关键词
4. read memory/daily/今天.md + memory/daily/昨天.md
5. 瞄一眼 docs/todo/ — 有没有 - [ ] 或 - [~] 或 - [!] 的
6. 全部答得上六问 → 开始工作
```

**六问里的"做到哪了"** → 看 SESSION-STATE 四状态：
- `- [ ]` 还没开始
- `- [~]` 正在做（看 started 时间知道做了多久）
- `- [!]` 卡住了（看 blocked 原因 + unlock 条件）
- `- [x]` 已完成
