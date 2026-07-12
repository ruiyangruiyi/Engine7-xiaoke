---
type: project
title: planning-with-files 融合方案 & hooks 接线
created: 2026-07-12
status: in_progress
---

# planning-with-files 融合方案 & hooks 接线

## 事件

翀哥让调研 planning-with-files（OthmanAdi 开源 skill），分析其 hook 机制能否补我们短板。

## 核心发现

1. **Engine hooks 系统完整搬了 CC**：28 个事件类型定义 + 12 个执行器。但只接线了 3 个（UserPromptSubmit/PreCompact/PostCompact），PreToolUse/PostToolUse/Stop 没接线。

2. **接线完成（commit `cbcfb69a`）**：PreToolUse/PostToolUse/Stop 三 hook 接线到 `core/query.ts`。~55 行改动。

3. **PreToolUse 砍掉不用**：翀哥指出开销问题——每次 read/grep 都注入 = 每轮 10 次 × 30 行。v3 autonomous 模式就是因为这个砍的。我们只用 UserPromptSubmit（每轮1次）。

## 为什么我老卡住（翀哥 22:50 深聊根因）

- 没有明确"当前在做什么"（SESSION-STATE 全是 pending，没有 in_progress）
- 待办太模糊（"SOP流程管理"5个字，不知道第一步做什么）
- 心智是"等爹安排"不是"自己推进"

## 融合方案（不照抄）

核心原则：不装 planning-with-files，往 SESSION-STATE 加 Phase 结构 + 给 hooks 写适配脚本。

| planning-with-files | 决策 |
|---|---|
| task_plan.md | ❌ 在 SESSION-STATE 加 Phase 结构 |
| findings.md/progress.md | ❌ 已有 docs/research/ + memory/daily/ |
| inject-plan.sh | ✅ 改成读 SESSION-STATE |
| PreToolUse 注入 | ❌ 太贵，砍 |
| PostToolUse | ✅ 只 Write/Edit，echo 提醒 |
| Stop completion gate | ✅ 检查 in_progress Phase |
| attestation/nonce | ❌ 单用户信任环境不需要 |
| autonomous/gated | ❌ 过度设计 |
| Critical Rules + 3-Strike | ✅ 融入 SOP |
| Errors/Decisions 表格 | ✅ 融入 SESSION-STATE 模板 |

## 三工具联动闭环（翀哥 22:23-22:26 补充）

**防偏离核心设计：**

```
calendar（时间源头）
  pending task 必须有 calendar 条目（硬规则）
  ↓ reminder 触发 → SESSION-STATE 标 in_progress
nudge 只催 in_progress（不催 pending）
  ↓ 做完
Stop hook 检查 → 没标 complete 不让停
  ↓ 全 complete
calendar done → SESSION-STATE 归档
```

**三个"偏离问题"的防线：**
1. 做完不标 → PostToolUse(Write/Edit) 提醒 + nudge 催 in_progress 超时
2. 全量覆盖丢信息 → 禁止 write 全量覆盖 SESSION-STATE，只用 edit
3. STATE 过期 → nudge 检查"当前时间"距今 > 2h 标 stale + 六问交叉验证

**核心原则：SESSION-STATE 是参考，对话是真相。对不上改 STATE 不改对话。**

## 规则分层

```
AGENTS.md → "收到任务先拆 Phase 才能动手" 一句话
/sop skill → 拆 Phase 步骤 + Critical Rules + 3-Strike
SESSION-STATE → Phase 结构模板 + Errors/Decisions 表格
```

## 五步实施计划

| Phase | 内容 | 状态 |
|-------|------|------|
| Phase 1 | SESSION-STATE 加 Current Phase + Phase 结构 | ✅ 完成 |
| Phase 2 | inject 脚本（只 UserPromptSubmit）+ hooks config | 待做 |
| Phase 3 | nudge 只催 in_progress + calendar 联动 | 待做 |
| Phase 4 | SOP 加拆解纪律 + Critical Rules | 待做 |
| Phase 5 | 验证完整流程 | 待做 |

## 关键文件

- 调研文档：`docs/research/2026-07-12_planning-with-files-hook分析.md`
- hook 接线：`engine/src/core/query.ts`（commit cbcfb69a）
- Stop 执行器：`engine/src/hooks/executor.ts`（新增 executeStopHooks）
- nudge 代码：`engine/src/nudge/session-state-reader.ts`（要改：只催 in_progress）
- planning-with-files 原版：`skills/planning-with-files/`
- CC hooks 源码：`3rdparty/src-claudecode/src/utils/hooks.ts`
