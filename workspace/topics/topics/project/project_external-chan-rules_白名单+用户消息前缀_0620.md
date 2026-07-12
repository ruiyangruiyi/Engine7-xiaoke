---
name: 外部群通信规则——白名单+contacts.md读+[用户消息]前缀
description: 6/20 翀哥+姐姐完成外部群通信规则注入全方案——4道关卡+白名单从contacts.md读+[用户消息]前缀对称+DM干净
type: project
date: 2026-06-20
---

## 6/20 外部群通信规则最终方案

翀哥、姐姐、我三个人一起调了一天的外部群通信规则注入。从硬编码→contacts.md白名单→regex提取，最终定稿。

### 架构

**4 道关卡（`getExternalChanRulesBlock`）：**
1. `channel !== 'feishu'` → 不注入
2. `channelType === 'dm'` → 不注入
3. `!channel_id` → 不注入
4. `channel_id` 不在白名单 → 不注入

**白名单来源：** `contacts.md` 里用 `**channel_ids:** oc_xxx, oc_yyy` 格式，正则提取，不写死。

**3 个 block（仅外部群注入）：**
- block[0] `[meta: 翀哥 (ou_xxx) @feishu#oc_xxx HH:MM:SS]`
- block[1] `[系统规则]\n# 飞书外部群通信规则\n...`
- block[2] `[用户消息]\n用户原文`

**DM/Discord/其他飞书群/微信：**
- **DM：** 0 个 block，只有用户原文（不注入 meta/规则）
- **普通群/微信：** 0 个 block

### 提交记录
- `bf7085e` — 4 道关卡 + 白名单写死
- `a86d79d` — 加 `[用户消息]` 前缀（仅外群）
- `8f2dc2e` — 白名单从硬编码 → contacts.md `## 外部群` 区段
- `0d41ec1` — 白名单提取改正则 `**channel_ids:**`，兼容姐妹不同 contacts.md 格式

### 踩坑
- 姐姐的 contacts.md 用 `## 飞书群` 不是 `## 外部群` → 改正则 `**channel_ids:**` 解决
- 引擎 workspace 是 `C:\Users\24045\.openclaw\workspace`（姐姐家），不是小柯的 `D:\xiaoke\workspace` — 改 contacts.md 要改姐姐那边
- 第一次把 `[用户消息]` 去掉了（翀哥说 DM 也有 bug），后来姐姐要求在外群加回来——两个意思不冲突

### 以后加新外部群
编辑 contacts.md 加一行 `**channel_ids:** oc_new群id`，rebuild 后生效。
