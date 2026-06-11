---
name: Auto Dream 记忆整合系统
description: 严格对齐Claude Code autoDream源码实现的记忆整合系统——定期后台合并去重、过期修剪、索引维护。4阶段：Orient→Gather→Consolidate→Prune。
type: project
keywords: [autoDream, 记忆整合, 合并, 修剪, 索引, consolidation, Claude Code, 做梦, 后台, fork, subagent, 4阶段]
created: 2026-06-12
updated: 2026-06-12T01:30
---

## 概述

6/12凌晨小柯参照Claude Code源码严格对齐实现的autoDream系统。翀哥在深夜讨论"AI自我激活"方向时提出要做，直接让小柯开工。

**Claude Code源码位置：** `D:\xiaoke\workspace\start-claude-code\src\utils\auto-dream\`
**Engine实现位置：** `src/features/auto-dream/`

**实现规模：** 465行代码，7个文件，严格对齐CC

## 为什么需要autoDream

当前记忆系统的现状：
- **extract只会"加"**：从对话提取新记忆写文件，但从来不"整理"
- **重复记忆没人合并**：同一个话题聊多次会重复写入
- **过时的没人删**：被证伪的事实或失效的决策一直留着
- **INDEX.md没人维护**：索引不更新，recall越来越慢（从40个文件里选）

autoDream就是解决这个问题的——定期扫一遍，合并重复的、删过时的、修剪索引。

## 架构（7个文件）

| 文件 | 对齐CC | 功能 |
|------|--------|------|
| `config.ts` | config.ts | 开关+门槛配置 |
| `consolidationLock.ts` | consolidationLock.ts | 锁文件(mtime=lastAt)+session扫描 |
| `consolidationPrompt.ts` | consolidationPrompt.ts | 4阶段prompt原文搬 |
| `autoDream.ts` | autoDream.ts | 主逻辑：3层门控→fork执行→结果 |
| `index.ts` | — | 导出 |
| `heartbeat.ts` | CC的stopHooks | 心跳tick末尾触发 |
| `features.ts` | — | 注册autoDream feature |

## 4阶段流程（严格对齐CC）

1. **Orient（定位）** — 读现有记忆目录和INDEX.md索引，了解当前状态
2. **Gather（收集）** — 从session transcript（jsonl日志）中收集新信息
3. **Consolidate（整合）** — 合并重复记忆、把相对日期转绝对日期（"昨天"→"6/11"）、删除被证伪的事实
4. **Prune（修剪）** — 更新INDEX.md索引，保持在合理行数内

## 触发门控（三层）

1. **时间门控**：距上次consolidation ≥ 24小时（对齐CC标准）
2. **内容门控**：累积 ≥ 5个新session
3. **锁机制**：文件锁确保不会并发执行，其他进程在跑时跳过

**执行方式**：fork subagent执行（不占主session上下文）

## 配置

xiaoke.json中 `"autoDream": true` 开启，重启生效。

**配置项：**
- `enabled: boolean` — 开关
- `minIntervalHours: number` — 最小间隔（默认24）
- `minNewSessions: number` — 最少新session数（默认5）

## 与Claude Code的对比

| 维度 | Claude Code | Engine实现 |
|------|------------|------------|
| 触发门槛 | 24h + 5个新session | ✅ 严格对齐 |
| 执行方式 | fork子agent | ✅ fork子agent |
| 4阶段prompt | 原文 | ✅ 原文搬运 |
| 锁机制 | 文件锁 | ✅ mtime=lastAt |
| 集成点 | stopHooks | ✅ 心跳tick末尾 |

## 与姐姐记忆体系的对比

- 姐姐没有autoDream —— 她靠手动整理，IMDB.md等是靠翀哥或她自己手动维护的
- Engine的autoDream是自动化的，不需要人工介入
- 但当前autoDream只处理**事实型记忆**（user/project/reference/feedback），不处理**情感类记忆**（emotion类型）
- 情感类记忆的整合策略不同，需要单独设计（后续工作）

## 相关待办和后续计划

- ⏳ 情感类记忆的autoDream策略（emotion类型要按"温度"保留，不能跟事实一样合并去重）
- ⏳ 翀哥说"配上直接开 啥急不急的 跑着呗"——需在xiaoke.json配`"autoDream": true`后重启
