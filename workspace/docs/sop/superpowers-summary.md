---
name: superpowers-summary-软件工程SOP
description: 0621翀哥让我从 Superpowers 4 个核心 skill 提炼的"软件工程 SOP"——给小柯做开发任务时遵守的精简流程。脑暴→写计划→执行→收尾。
type: sop
---

# 软件工程 SOP（小柯用版）

> 来源：obra/superpowers（150k stars）+ 4 个核心 skill 提炼
> 适用：小柯做开发任务、改 bug、加功能
> 核心：**先想清楚，再写代码，最后验证**

---

## 0. 入口检查（每次开工前）

**问自己：** 这个任务符合下面哪个？
- 写新功能 / 改老逻辑 / 修 bug / 改配置
- 只要沾"创造"或"修改"，**必须走完整 4 步**

**Red flag（这些想法 = 停）：**
- "这个太简单不用设计" → 简单项目最浪费返工时间
- "我先写代码再设计" → 写完才发现方向错
- "用户已经说要什么了" → "要什么" ≠ "怎么做"，还要脑暴

---

## 0.5 Direction Gate（每步一道——防白干）

**核心：方向错了 = 全白干。代码写得多漂亮都没用。**

**何时触发：**
- 写完 spec → **Direction Gate #1**
- 写完 plan → **Direction Gate #2**
- execute 中途改了方向 → **Direction Gate #3**（任何时刻觉得"这不对"立刻停）

**谁来确认（必须有一人，不能"自己 review 自己"）：**

| 阶段 | 守门人 | 时长 |
|------|--------|------|
| **Phase 1 日常 gate** | 我（晓梅） | 0621 起 2 天 |
| **Phase 2 终审** | 老公（翀哥） | 之后所有 gate |

**确认什么（4 件事）：**
- ✅ 这是不是老公真正要的？
- ✅ 现在做这件事方向对吗？
- ✅ 有没有更简单的方案？
- ❌ 方向错了 → 立刻停，回到上一步
- ❌ 不知道对不对 → 停下来问，不硬撑

**为什么重要：** 小柯 0621 反馈："今天改 SSE 那轮就是反面教材——没写 spec 直接上手，改着改着顺手重构了整个 stream 块。按 SOP 应该先写 spec，翀哥批准了再动手。"

**派活时附这句：** "按 docs/sop/superpowers-summary.md 走——每步走完停一下，等晓梅/老公确认方向再继续。"

---

## 1. 脑暴（Brainstorming）—— 不写代码，先想清楚

**目的：** 把"模糊想法"变成"清晰 spec"

**做这 5 件事：**
1. **看项目现状**（read files、check git log、找相关文档）——别凭印象动手
2. **一次问一个澄清问题**——multiple choice 优先
3. **给 2-3 个方案 + 各自权衡** + 我的推荐
4. **分段讲设计**——讲完一段问"这块对吗"
5. **写到 `docs/decisions/YYYY-MM-DD-<topic>.md`** + git commit

**铁律：**
- ❌ **HARD-GATE：没 spec + 用户没批准，不准写代码**（不管看起来多简单）
- ❌ 不写 "TBD"、"适当处理"、"类似前面"
- ✅ 写完 spec 自查 4 件事：占位符 / 内部矛盾 / 范围聚焦 / 歧义
- ✅ 完了让用户审 spec，再进下一步

**快速通道：** 真简单任务（改个 config）spec 可以就 3 句话，但**必须**写下来 + 用户批准

**Karpathy 防过度设计红线（脑暴时必过）：**
- ❌ **假想用户没提的"灵活性"** → 不做
- ❌ **"如果以后要 X"** → 不做
- ❌ **200 行能搞定不写 500 行** → 写之前问自己
- ❌ **多种解释就列出来** → 不要 silent pick
- ❌ **不确定就问** → 不要假装懂老公意思

> 来源：Karpathy 4 条原则（Think Before Coding / Simplicity First）。跟 Superpowers 互补——SOP 管流程，Karpathy 管"流程里别过度设计"。

---

## 2. 写计划（Writing-Plans）—— spec 批了再拆任务

**目的：** 把 spec 拆成"2-5 分钟一步"的执行清单

**做这 4 件事：**
1. **文件结构**——先列要建/改哪些文件，每个文件一个职责
2. **拆任务**——每个 task = 一个可独立测试的交付物
3. **每个 task 写明**：
   - Files（精确路径）
   - 写失败的测试 → 跑确认 fail → 写代码 → 跑确认 pass → commit
   - 完整代码（不写"类似 Task N"）
4. **写到 `docs/todo/YYYY-MM-DD-<feature>.md`**

**铁律：**
- ❌ 不写 placeholder（"TBD"、"implement later"、"add validation"）
- ❌ 不写"类似前面"——engineer 可能倒着读
- ✅ 每步带精确文件路径 + 完整代码 + 期望输出
- ✅ DRY + YAGNI + TDD + 频繁 commit
- ✅ 写完自查 3 件事：spec 覆盖、占位符、类型一致

**关键：每 task 2-5 分钟。** 30 分钟的活 = 拆 6-10 个 task

---

## 3. 执行（Executing-Plans）—— 一步步来

**目的：** 按 plan 一步步执行，每步验证

**做这 3 步：**
1. **先 review 整个 plan**——有疑问先问，不要开始后才卡住
2. **每个 task 走这个循环：**
   - 标 in_progress
   - 严格按 plan 步骤
   - 跑 plan 写的验证（测试/命令）
   - 标 completed
3. **全做完** → 喊："我正用 finishing-a-development-branch skill 收尾"

**状态标在哪（3 处同步）：**

| 位置 | 状态怎么写 | 持久化？ | 谁看 |
|------|------------|---------|------|
| **docs/todo/ 文档** checkbox | `- [ ]` → `- [~]` → `- [!]` → `- [x]`（写在 `docs/todo/YYYY-MM-DD_主题.md` 每个 task 标题下） | 永久留 | 人 / 协作者 / 跨 session |
| **TodoWrite**（engine 的 tool） | `pending` → `in_progress` → `block` → `completed`（4 态） | session 内 | 当前 session 自己 |
| **SESSION-STATE.md** | `- [ ]` → `- [~]` → `- [!]` → `- [x]` + 时间 | 永久留 | 跨 session 同步 / 心跳 / 协作者 |

**3 处的分工（不是平级）：**

- **docs/todo/ checkbox** = **永久真相源**——计划在哪、做到哪一步
- **TodoWrite** = **当前 session 的工作台**——engine 持久化但**只在当前 session_id 范围有效**；换 session_id 看不到
- **SESSION-STATE** = **跨 session 接力棒**——心跳/换 session/恢复时读这里

**关键认知：** TodoWrite **不是纯内存**，engine 写到了 `stateDir/todos/<sessionId>.json`。重启 session 还在，但换 session_id 就没了。所以**真正跨 session 同步靠 SESSION-STATE，不是 TodoWrite**。

**4 个状态：**

```
- [ ]   pending       # 没开始
- [~]   in_progress   # 在做 — started M/D HH:MM
- [!]   block         # 卡住——必须带原因+解锁条件
- [x]   completed     # 完成 — M/D HH:MM→HH:MM (Nmin)
```

**block 状态必须带"原因 + 解锁条件"**——单纯"卡了"等于没标。

例：
```
# TodoWrite
- status: block
  task: "Task 3: 接 OAuth"
  blocked_by: "等老公确认用哪个 provider（zhipu / deepseek）"
  unlock: "老公回复 provider 选择后立即继续"
  blocked_at: "14:35"
```

```
# SESSION-STATE.md「🎯 当前任务」
- [!] **OAuth 接入** — blocked: 等老公确认 provider, unlock: 老公回复后继续 (6/24 14:35)
```

**最小组合（小柯用）：**
- docs/todo/ checkbox = 任务清单真实状态
- TodoWrite = 当前正在做的那一个（高亮在跑的）
- SESSION-STATE = **跨 session 留痕**——心跳时从这里读"现在在哪"

**例：做完 Task 2 → 3 处一起改：**
```markdown
# docs/todo/ 文档
- [x] **Task 2: 实现 xxx** — 6/24 14:25→14:32 (7min)
  - [x] Step 1: 写失败测试
  - [x] Step 2: 跑确认 fail
  - [x] Step 3: 写代码
  - [x] Step 4: 跑确认 pass
  - [x] Step 5: commit
```

```
# TodoWrite
- [x] Task 2: 实现 xxx
- [ ] Task 3: 接 OAuth
```

```
# SESSION-STATE.md「🎯 当前任务」
- [x] **xxx 功能开发** — Task 2/5 done (6/24 14:32)
- [ ] **接 OAuth** — 待开始
```

**铁律：**
- ❌ **不准跳验证**——plan 写的命令必须跑
- ❌ 不准在 main/master 直接动手（必须用 worktree）
- ❌ 卡住不要瞎猜——立刻问老公
- ❌ 状态只在一处改 = 信息不一致，**三处必须同步**
- ❌ block 状态不带原因 = 等于没标
- ✅ 停的条件：依赖缺失 / 测试反复失败 / 不懂 plan 在说啥
- ✅ 计划需要改 → 回到 Step 1 review，不硬撑

---

## 4. 收尾（Finishing-a-Development-Branch）—— 别忘了最后一步

**做这 4 件事：**
1. **跑全套测试**——确认没破坏其他东西
2. **给老公 4 个选项**：merge / 开 PR / 留着 / 丢弃
3. **老公选了再执行**——不要自己决定
4. **清理 worktree**

---

## 5. 出问题怎么办（Debug 速查）

| 现象 | 第一步 | 第二步 |
|------|--------|--------|
| 测试 fail | 看错误信息 | 找到对应 task 重做 |
| plan 有 gap | 回到 Step 1 | 让老公改 spec |
| 不知道下一步 | 停下来问 | 不要猜 |
| 越改越乱 | git diff 看变化 | revert 重新来 |

---

## 关键约束（再说一遍）

1. **没 spec 不写代码**（HARD-GATE）
2. **每步 2-5 分钟**——别想一气呵成
3. **TDD 必走**——先写失败测试
4. **频繁 commit**——每 task 完都 commit
5. **卡住就问**——别瞎猜

---

## 这个 SOP 的来源

- **obra/superpowers**（GitHub 150k stars）— https://github.com/obra/superpowers
- 4 个核心 skill：using-superpowers / brainstorming / writing-plans / executing-plans
- License: MIT

## 相关文档

- `aim协作机制_团队协作基础模式.md` — 我用版 SOP（怎么派活、怎么盯任务、怎么归档）
- `workflow-sop.md` — 工作流
- `automemory-config-sop.md` — auto memory 配置
