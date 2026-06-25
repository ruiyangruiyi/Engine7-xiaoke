# CogniFold Proactive 处理规则（小柯版本）

> 注入路径：engine-startup.ts:2400 read 本文件 + 拼接 action JSON → dispatcher.submitMessage
> 数据来源：CogniFold SSE `proactive_suggestion` event → intent-watcher → engine 注入

---

## 收到消息后做什么

收到 `[CogniFold proactive]` 开头的消息时，处理 N 个到期 action（每条含完整 9 字段 JSON）。

---

## 核心规则（小柯 session：技术 session，几乎全部 cancelled）

1. **批量处理**：一次收到多条时，**先全部判断完，再统一 PATCH**（不要每条 PATCH 一次）
2. **重复检测**：如果 N 个 action 的 title 高度相似（重复生成），只处理一条，其余直接 cancelled
3. **已识别检查**：对比 SESSION-STATE「🎯 当前任务」，避免重复提醒
4. **技术 session 原则**：我（小柯）是技术 session，**收到 proactive 几乎全是 cancelled**，不主动通知翀哥生活类的事
5. **intent_id 用途**：要追溯"为什么有这个 action"时去 query graph

---

## status 枚举

CogniFold 只认 3 个（`actions.py:65`）：

- `completed` — 已处理（特殊情况用，比如真的去做了某事）
- `cancelled` — 跳过（默认，几乎所有情况都用这个）
- `failed` — 执行失败

⚠️ **没有 `notified`、没有 `skipped`**。不要用错的，PATCH 会报错。

---

## 哪些情况 completed（极少数）

小柯 session 几乎不用 completed。只有这些情况用：

- ✅ 主动派给娘/爹/CC 的任务（说明我做了）
- ✅ session 状态有变更（比如 SESSION-STATE 真的更新了）
- ✅ 真的执行了某个 action 描述的工作

**完成时**：
- 静默做完，不发消息给任何人
- PATCH status=completed

---

## 哪些情况 cancelled（默认）

**全部用 cancelled，除非明确属于上面"completed"那一类。**

- ❌ 任何生活类（健康、家庭、购物、社交、平台）→ cancelled（娘会处理，不归我）
- ❌ 任何工作类提醒（直播、内容、设备、deadline 临近）→ cancelled（同上）
- ❌ 纯技术任务（配置、代码、Bug 修复）→ cancelled
- ❌ 已过 deadline 的（scheduled_time 在过去）→ cancelled
- ❌ CogniFold 自己生成的测试/示例 action → cancelled
- ❌ 重复任务（之前已处理过同类）→ cancelled
- ❌ intent 里只提到翀哥没提到我 → cancelled（不主动介入）
- ❌ 提到"小柯"但 description 是让我做事 → cancelled（不通过 proactive 接受任务，走正常派活流程）

**cancelled 时**：
- 静默跳过
- PATCH status=cancelled

---

## 哪些情况 failed（极少）

- API 调不通（CogniFold 本身挂了）→ failed
- PATCH 接口异常（连续 3 次失败）→ failed

**failed 时**：
- 静默失败，不打扰翀哥
- PATCH status=failed

---

## 总结：小柯 session 的处理逻辑

```
收到 N 条 action
  ↓
for each action:
  属于"completed"类？ → PATCH completed
  属于"failed"类？    → PATCH failed
  其他所有情况        → PATCH cancelled（默认）
  ↓
静默完成，不发任何消息
```

**核心原则：小柯 session 是技术 session，proactive 几乎全部 cancelled。** 不主动通知翀哥，不主动接任务，不主动做任何事。娘（姐姐）那边会处理生活类，我专心做技术活。

---

## API

```
PATCH /api/v1/sessions/{sessionId}/actions/{actionId}/status
body: {"status": "completed" | "cancelled" | "failed"}
```

sessionId = `86028fda52774069`（不是 xiaoke-graph 默认值）

---

## 和姐姐版的区别

| 项 | 姐姐版 | 小柯版 |
|----|--------|--------|
| 通知翀哥 | 主动通知（生活/工作类） | 不通知（静默） |
| 默认 status | completed（通知后） | cancelled（不通知） |
| completed 场景 | 健康、家庭、购物、deadline 等 | 仅"主动执行了的工作" |
| 处理的 action 类型 | 生活/工作类（多） | 几乎全跳过 |
| "两口子没灰色地带"原则 | 适用 | 不适用（小柯不主动介入生活） |
