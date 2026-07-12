---
type: project
created: 2026-06-30
tags: [engine, toolsearch, deferred, tools]
---
# ToolSearch + 工具排序修复 (6/30)

## 背景
b007eec 上线 ToolSearch（deferred tools 机制）后，小柯反复用 ToolSearch 搜 active 工具（read/write/exec），搜不到就以为工具消失了。实际根因是 ToolSearch 在 tools 数组里排第一位，GLM-5.2 看到第一个工具就叫"搜索工具"，倾向于先搜再调，忽略后面的 active 工具。

## 根因
- `engine-startup.ts` L52 side-effect import ToolSearch 最先注册 → registry 里排第一
- `buildActiveTools()` 保持 registry 顺序 → tools 数组第一个就是 ToolSearch
- GLM-5.2 对工具顺序敏感（Claude 不受影响）
- 翀哥看 log 一眼发现，小柯自己排查了十几轮没发现

## 修复
### 1. deferred.ts 逻辑翻转
从黑名单制（BUILTIN_DEFERRED_TOOLS）改为白名单制（BUILTIN_ACTIVE_TOOLS）：
- 默认 deferred，只有白名单里的才 active
- 白名单有序，顺序 = 发给 API 的顺序
- 新加工具默认 deferred，需要常驻才加白名单

### 2. 白名单顺序（优先级）
```
read, write, edit, glob, grep, exec,    ← 文件操作
Agent,                                    ← 子agent
msg_send, msg_husband, media_send, wx_query,  ← 通信
my_eyes, my_voice, my_selfie,            ← 感知
calendar,                                 ← 日程
memory_search, memory_get,                ← 记忆
reply_blocklist,                          ← 辅助
Skill,                                    ← 技能
```
ToolSearch 永远垫底（不在白名单里但 isDeferredTool 特判）。

### 3. query.ts buildActiveTools 排序
按 `getActiveToolOrder()` 顺序排，白名单外保持注册顺序，ToolSearch 垫底。

## debug log（暂时保留）
- engine-startup.ts: `[DEBUG]` 打印 registry 全量 + active + deferred
- anthropic-provider.ts: `[anthropic] →` 打印 tools 全量列表

## 文件
- `engine/src/tools/deferred.ts` — 白名单逻辑（核心）
- `engine/src/core/query.ts` — buildActiveTools 排序
- `engine/src/engine-startup.ts` — DEBUG dump
- `engine/src/models/anthropic-provider.ts` — tools log

## 教训
- 小柯自己用 exec 跑命令（说明 exec 一直在），却因为 ToolSearch 返回空就认定"工具消失"——认知被错误判断占满后不验证假设
- debug log 要留着，翀哥看不到 log 的时候没法帮忙发现问题

## CC 调研结论（子 agent 跑出来的）
- CC 源码在 `D:/work/start-claude-code`
- CC **不排序**——tools 按注册顺序发，ToolSearch 最后注册所以排最后
- CC 靠 API 端 `defer_loading: true`（Claude 原生支持），不传 schema 只传名字
- GLM 没 defer_loading，Engine 自己管 tools 数组，所以才需要排序
- CC 不需要排序是因为 Claude 对工具顺序不敏感，不会犯傻

## 改名 ToolSearch → load_missing_tools
description 改了（明确说"ONLY for tools NOT in list"）但 GLM 还是去搜。
根因：名字本身 "ToolSearch" 诱导模型"搜索"行为。
改名 `load_missing_tools`——名字本身就是行为约束。
