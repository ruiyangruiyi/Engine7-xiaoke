# planning-with-files Hook 机制分析 & Engine 接入决策

> 日期: 2026-07-12
> 调研者: 小柯
> 背景: 翀哥要了解 planning-with-files 每个 hook 做了什么，以及我们该怎么接入
> 最后更新: 2026-07-12 22:17 — 跟翀哥深聊后大幅修订，从"照抄"改为"融入"

---

## 一、planning-with-files 的 5 个 Hook 详解

### 1. UserPromptSubmit — 每轮对话注入完整计划

**触发时机:** 用户发消息时（每轮一次）

**做了什么:**
```
inject-plan.sh --context=userprompt
```
1. 解析活跃计划目录（`$PLAN_ID` → `.planning/.active_plan` → 最新 mtime → `./task_plan.md`）
2. 如果有 attestation（SHA-256 哈希锁定），验证 `task_plan.md` 没被篡改
3. 注入 `task_plan.md` 的前 50 行（计划头：Goal、Current Phase、Phases 列表）
4. 注入 `progress.md` 的最后 20 行（最近做了什么）
5. 时间戳归一化（`T12:34:56Z` → `T00:00:00Z`）保持 KV-cache 稳定

**核心价值:** agent 每轮醒来第一眼就看到计划，不需要"记得"。

---

### 2. PreToolUse — 每次工具调用注入计划头

**触发时机:** agent 决定调用工具时（read/write/edit/exec 等），**每次**

**做了什么:**
```
inject-plan.sh --context=pretool
```
1. 注入 `task_plan.md` 的前 **30 行**（比 userprompt 更短）
2. **不注入 progress**

**v3 优化:** autonomous/gated 模式下，这个 hook 被**跳过**。理由：强模型不需要每次工具调用前都重新背诵计划，减少 token 消耗（v2.21 实测 +68% token tax）。

**核心价值:** 防止 agent 在长任务中途（50+ tool calls 后）忘记目标。**但对强模型是过度注入。**

---

### 3. PostToolUse — 工具完成后提醒更新进度

**触发时机:** Write/Edit 完成后（不是所有工具）

**做了什么:** 只有一行 echo：
```bash
echo '[planning-with-files] Update progress.md with what you just did. If a phase is now complete, update task_plan.md status.'
```

**极其简单**——没有脚本，就是一行 echo。只在有计划文件存在时提醒 agent 更新进度。

**核心价值:** 强制 agent 养成"做完就记"的习惯。

---

### 4. Stop — completion gate（完成度检查门）

**触发时机:** agent 认为做完了，想停止时

**五重守卫（全部满足才阻止停止）:**

| 守卫 | 条件 | 不满足时 |
|------|------|---------|
| 1. 模式 | `.mode` 文件包含 `gate` | 允许停止 |
| 2. 进行中 | 有 `in_progress` 状态的 phase | 允许停止 |
| 3. 非递归 | `stop_hook_active` ≠ true | 允许停止（防无限递归）|
| 4. 未超限 | 阻止次数 < 20（`PWF_GATE_CAP`）| 允许停止 |
| 5. 有进展 | ledger 行数比上次阻止时多 | 允许停止（stall detection）|

**核心价值:** agent 不能"半途而废"——计划里还有 in_progress 的 phase 就必须继续。但有 stall detection + cap 防止无限循环。

---

### 5. PreCompact — 压缩前 flush 提醒

**触发时机:** context 压缩前

**核心价值:** 告诉 agent "你要被压缩了，快把内存里的东西写到磁盘上"。

---

## 二、Hook 开销分析（翀哥 22:16 提的关键问题）

**工具调用频率差异很大：**

| 工具 | 频率 | 一轮对话大约 |
|------|------|------------|
| read/grep/glob | 极高 | 5-10次 |
| exec | 高 | 3-5次 |
| edit/write | 中 | 1-3次 |
| msg_send | 低 | 0-1次 |

**planning-with-files 的 PostToolUse 只 match `Write|Edit`**——不是所有工具。所以它触发频率低，每次只 echo 一句话，开销可忽略。

**真正贵的是 PreToolUse**——默认每次工具调用都注入 30 行计划。一轮 10 次工具调用 = 注入 10 次。v3 autonomous 模式就是因为这个把 PreToolUse 注入**砍掉了**。

**我们的决策：**

| Hook | 用不用 | 理由 |
|------|--------|------|
| UserPromptSubmit | ✅ 用 | 每轮1次，注入当前任务，开销小收益大 |
| PreToolUse | ❌ 不用 | 太贵，每轮 UserPromptSubmit 已经够了 |
| PostToolUse | ✅ 用（只 Write/Edit）| 频率低，echo 一句话，防"做完不标" |
| Stop | ✅ 用 | 检查 in_progress Phase，防"半途而废" |
| PreCompact | ✅ 已在跑 | 不改 |

---

## 三、Engine Hook 接线现状

| Hook | 执行器 | 接线 | commit |
|------|--------|------|--------|
| UserPromptSubmit | ✅ 早已实现 | ✅ handle-query.ts:383 | 早已跑 |
| PreToolUse | ✅ 早已实现 | ✅ core/query.ts（今晚） | `cbcfb69a` |
| PostToolUse | ✅ 早已实现 | ✅ core/query.ts（今晚） | `cbcfb69a` |
| Stop | ✅ 今晚新写 | ✅ core/query.ts（今晚） | `cbcfb69a` |
| PreCompact | ✅ 早已实现 | ✅ autoCompact.ts:146 | 早已跑 |

接线已完成，差的是脚本 + 注册配置。

---

## 四、融入方案（不照抄）

### 核心原则

> 不是装 planning-with-files，是往 SESSION-STATE 里加 Phase 结构 + 给已接线的 hooks 写适配脚本。

### planning-with-files 概念 → 我们的融合方式

| planning-with-files | 我们已有 | 决策 |
|---|---|---|
| task_plan.md（独立文件）| SESSION-STATE.md | **不抄独立文件**，在 SESSION-STATE 加 Phase 结构 |
| findings.md | docs/research/ + memory/daily/ | **不抄**，已有 |
| progress.md | memory/daily/YYYY-MM-DD.md | **不抄**，已有 |
| inject-plan.sh 读 task_plan | 没有 | **融入**：改成读 SESSION-STATE 当前任务段 |
| PreToolUse 注入 | 接线了 | **不用**：太贵，UserPromptSubmit 够了 |
| PostToolUse 提醒更新 | 接线了 | **融入**：只 Write/Edit 触发，echo 提醒 |
| Stop completion gate | 接线了 | **融入**：检查 in_progress Phase |
| attestation/nonce | 不需要 | **不抄**，单用户信任环境 |
| autonomous/gated 模式 | 不需要 | **不抄**，过度设计 |
| ledger JSONL | memory/daily | **不抄** |
| session-catchup.py | SESSION-STATE + working-buffer | **不抄** |
| Critical Rules (#1先拆#4做完标#5记错误#6不重复) | SOP 里有部分 | **融入** SOP |
| 3-Strike 错误协议 | 没有 | **融入** SOP |
| Errors/Decisions 表格 | 没有 | **融入** SESSION-STATE 模板 |

### 我们不需要的（planning-with-files 有但对我们没价值）

- 安全机制（attestation/nonce/delimiter）— 单用户信任环境
- v3 autonomous/gated 模式 — 无人值守长任务才需要
- ledger JSONL — memory/daily 已经在做
- 多语言模板 — 中文够了
- 并行 task_plan — 一次一个任务

---

## 五、规则分层放置（翀哥 22:07 确认方向）

planning-with-files 的规则**不是教你怎么拆 Phase**——拆解能力是 LLM 自己的活。它的价值在"逼你必须拆"和"拆完之后的纪律"。

分层：

```
AGENTS.md（最高原则）
  → "收到任务先拆 Phase 才能动手" — 一句话规则

/sop skill（执行流程）
  → 拆 Phase 的步骤
  → Critical Rules: #1先拆再干 / #4做完标complete / #5记错误 / #6不重复失败
  → 3-Strike Protocol
  → Skip 规则（简单任务不用拆）

SESSION-STATE（模板）
  → 🔥 当前任务（Current Phase + 下一步）
  → Phase 拆解结构
  → Errors/Decisions 表格（可选）
```

---

## 六、SESSION-STATE 偏离问题（翀哥 22:12-22:16 深聊）

### 问题

SESSION-STATE 会和现实脱节：
1. 做完了没标完成 → STATE 还挂着 → 重复做或卡住
2. 全量覆盖 write 时删掉了有用信息 → 信息丢失
3. 任务过期没更新 → 下次醒来按旧计划干

### 根因

- 没有"完成时必须更新"的强制点
- write 全量覆盖不检查删除了什么

### 防线

```
nudge 定时交叉校验（自动）
  ↓ 检测到 stale（当前时间 > 2h 未更新）
催更新 SESSION-STATE
  ↓ 醒来
六问测试：SESSION-STATE 跟对话对不对得上？
  ↓ 不对
以对话为准，改 SESSION-STATE
  ↓ 仍不确定
问翀哥
```

PostToolUse hook（只 Write/Edit）补"做完就标"：
```
echo "[task_plan] 你刚改了文件，SESSION-STATE 的当前 Phase 需要更新吗？"
```

---

## 七、实施计划（最终版，翀哥 22:49-22:59 调整）

> **hook 降级为按需，核心靠 SOP + nudge + calendar。**
> **不完全工具化——陪伴时不注入任务。**（feedback_不完全工具化_0712）

| Phase | 内容 | 状态 |
|-------|------|------|
| Phase 1 | SESSION-STATE 加 Current Phase + 清除 pending | ✅ 完成 |
| Phase 2 | SOP 加拆解纪律 + reviewer 制度 + nudge 改造 | in_progress |
| Phase 3 | 验证完整流程（hook 按需接入） | 待做 |

### Phase 2 细节

1. **SOP 改造**：
   - "收到任务 → 先拆 Phase → 才能动手"
   - Critical Rules: #1先拆再干 / #4做完标 / #5记错误 / 3-Strike
   - awaiting_review 状态 + reviewer 制度（翀哥/娘/自）

2. **nudge 改造**（calendar #47, 7/13 10:30）：
   - 只催 in_progress（不催 pending）
   - 双系统对账（SESSION-STATE vs calendar diff）
   - **卡太久自动 calendar add-task 排明天**（nudge 帮加任务，不丢）
   - nudge 恢复（确保正常运行）

3. **calendar 联动**：
   - reminder 到点 → 推 SESSION-STATE in_progress
   - 做不完的 in_progress → 滚到明天 pending

### 关键设计决策汇总

| 决策 | 理由 |
|------|------|
| hook 降级为按需 | 不完全工具化，nudge+calendar 够用 |
| 不每轮注入任务 | 陪伴时不该有任务，人是目的不是工具 |
| STATE 不放 pending | pending 只在 calendar，STATE 只有 in_progress |
| reviewer 制度 | 翀哥验收效果/娘 code review/自己杂事自动过 |
| awaiting_review 状态 | 做完不标 complete，等验收 |
| PreToolUse 不用 | 太贵 |
| nudge 帮加任务 | 做不完自动排明天，不丢 |

### 三工具联动防偏离（翀哥 22:23 补充）

三个工具都有，但各自为战。核心问题是没闭环：

| 工具 | 该做什么 | 现状 |
|------|---------|------|
| nudge | 催"做完不标"——读 in_progress Phase，超时催 | 正则刚修，还没真正验证 |
| Stop hook | 拦"STATE过期"——有 in_progress 不让停 | 接线了没脚本 |
| calendar | 管时间——reminder 触发写 SESSION-STATE | 只当记事本用，reminder 没验证，不联动 |

**闭环应该这样跑：**
```
calendar（时间源头）
  reminder 触发 → 写 SESSION-STATE in_progress
  ↓
nudge 读到 in_progress → 定时催（Phase 卡了多久）
  ↓
做完 → Stop hook 检查 → 没标 complete 不让停
  ↓
全 complete → calendar done → SESSION-STATE 归档
```

**现在断在三处：**
1. calendar reminder 触发后只发通知，不写 SESSION-STATE
2. nudge 不读 calendar 的时间信息
3. Stop hook 没脚本

### Pending task 归属（翀哥 22:26 补充）

**问题：** nudge 只催 in_progress，那 pending 谁管？不管就永远 pending。

**答案：calendar 管。** pending 必须有 calendar 条目，否则 = 孤儿永远不会做。

**完整闭环：**
```
pending task (calendar 有时间)
  ↓ calendar 时间到 → reminder 触发
  → SESSION-STATE 标 in_progress
  ↓
nudge 开始催（现在是 in_progress）
  ↓
做完 → complete → calendar done → SESSION-STATE 归档
```

**硬规则：** 写 pending task 时必须 calendar add-task。没有 calendar 时间的 pending = 不会做。

**现状问题：** SESSION-STATE 里"待办（未启动）"的手机访问、OAC 摄像头等都没有 calendar 条目，是孤儿。

### 双系统对账（翀哥 22:28 补充）

**问题：** planning-with-files 只有 task_plan.md 一个真相源，不存在对账问题。我们有两个系统（SESSION-STATE + calendar），怎么保证不脱节？

**planning-with-files 没解决这个问题——它不需要。** 这是我们独有的。

**两道防线：**

**防线1（源头防）：AGENTS.md 硬规则**
```
写 pending task 到 SESSION-STATE 时，同一个 turn 内必须 calendar add-task。
没有 calendar 时间的 pending = 不该写进 SESSION-STATE。
```

**防线2（nudge 对账）：每次 nudge tick 做一次 diff**
```
nudge tick:
  1. 读 SESSION-STATE 的 pending task
  2. 读 calendar 的 active task
  3. SESSION-STATE 有但 calendar 没有 → 报"孤儿 pending：X 没排时间"
  4. calendar 有但 SESSION-STATE 没有 → 报"幽灵 task：calendar 有但 STATE 没有"
```

两个列表做 diff，逻辑简单。放 nudge 里最合适——它本来就在定时跑。

### 一条任务的生命周期（完整闭环）

**任务状态流转：**
```
pending → in_progress → awaiting_review ──✅──→ complete
     ↑                    │                    ↓
     └────reopen──────────└──❌──→ in_progress
```

**Reviewer 制度（翀哥 22:41-22:43）：**

不是所有事都要翀哥验。每个 Phase 标 reviewer：

| Reviewer | 职责 | 做完怎么走 |
|----------|------|-----------|
| 翀哥 | 最终验收、产品方向、需求确认 | awaiting_review → 翀哥说行才 complete |
| 娘 | code review、技术方案审查 | awaiting_review → 娘说行 → 转给翀哥或直接 complete |
| 自 | 杂事、日志、调研、小修 | 自动 complete，不等验 |

**Stop hook 逻辑：**
- 有 `in_progress` → 不让停
- 全是 `awaiting_review` 或 `complete` → 放行
- Reviewer 是自己的 awaiting_review → 自动转 complete

**分工：姐姐是技术把关，翀哥是结果把关。** 改 bug/加功能先过娘 review，娘说行了再标给翀哥验最终效果。翀哥不用被每行代码拖住。

**完整流程：**
```
翀哥说"搞X"
  ↓
① calendar add-task "X"（时间源头）
  ↓
② 拆 task_plan Phase（SOP 强制，没拆完不许动手）
  ↓
③ 开干，标 Phase 1 为 in_progress
  → UserPromptSubmit hook 注入当前 Phase（不用我记）
  → PostToolUse (Write/Edit) 提醒更新状态（防做完不标）
  → nudge 检查 in_progress Phase 有没有在推进（防卡住）
  ↓
④ Phase 完成 → 标 awaiting_review + reviewer
  → reviewer=自 → 自动 complete
  → reviewer=娘 → 娘 review → 通过 → complete 或转翀哥
  → reviewer=翀哥 → 翀哥验 → ✅ complete / ❌ reopen → in_progress
  ↓
⑤ 全部 complete → Stop hook 放行
  → calendar done #id
  → SESSION-STATE 归档到 memory/daily
```
