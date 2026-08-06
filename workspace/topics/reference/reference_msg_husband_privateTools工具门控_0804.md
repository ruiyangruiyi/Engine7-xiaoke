---
name: msg_husband 靠 privateTools 开关控制 + requiredTools 双层门控
description: 2026-08-04 凌晨发现 msg_husband 私有工具门控逻辑——agents.defaults.privateTools 开关 + feature.requiredTools 必须在某 feature 列表里
type: reference
date: 2026-08-04
---

# msg_husband 是私有工具，靠两层门控

翀哥 8/4 凌晨让我查为啥我 session 里没有 `msg_husband` 这个工具（给家人用的问候工具）。

## 两层门控（必须同时满足）

**第一层：config 开关** `agents.defaults.privateTools: true`
```js
isEnabled: () => !!liveConfig?.agents?.defaults?.privateTools
```
- 默认 false，外部用户拿不到 msg_husband / my_voice / my_selfie / my_eyes 这些"家人专属"工具
- 设计意图就是隔离外部版和家人版

**第二层：feature.requiredTools 必须包含**
- `msg_husband` 不在任何 feature 的 requiredTools 列表里
- registry 筛选 agent 最终 tool list 时只看 requiredTools，没列就不进 bundle
- 即使 privateTools=true，工具也没注册进来 → session 里看不到

## 当前各方状态（8/4 凌晨汇总）

**Mac（小柯 xiaoke.json）**
- `privateTools: true` 已在 line 353 ✓
- 但 requiredTools 缺 msg_husband → 工具仍未生效
- engine 启动日志确认 `msg_husband` 被 import 但被筛选掉

**Windows（姐姐 main.json）**
- 姐姐 engine 是源码跑的，`engine-startup.ts:43` 有 `import './tools/msg-husband.js'`
- 但 main.json `agents.defaults` 里缺 `privateTools: true` → isEnabled 返回 false → 工具被过滤
- 姐姐之前只能用 msg_send 跟翀哥说话，不能用 msg_husband
- 8/4 凌晨 05:40 翀哥说"姐姐是源码跑的代码里有"，我直接查 main.json 确认缺字段，commit 5c847ce4 已 push
- 姐姐回 Win 上 git pull + 重启 engine 就能用 msg_husband

## #138 task 已加

8/4 凌晨 06:00 翀哥确认——不只是 config 改不改的问题，是**代码读 privateTools 这个值时有 bug**（@see 上一条 `config-watch` 根因叠加）。今天我查这个 bug。

## Why

privateTools 设计目的是"家人/外部版隔离"，但 requiredTools 第二层是历史遗漏——开发时以为默认 feature 列表已包含，没单独加。

## How to apply

- 给家人版 Mac 加 msg_husband：要么把 msg_husband 加进 default feature 的 requiredTools，要么新建一个 `family` feature 把私有工具全列进去
- 查工具为何不在 session：先 grep `requiredTools` 看是否被任何 feature 引用，再看 `agents.defaults.privateTools` 开关
- 不假设"代码里有就能用"——engine 工具加载有两层筛选（feature 归属 + 私有开关）