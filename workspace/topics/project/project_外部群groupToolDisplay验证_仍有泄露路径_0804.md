---
name: 外部群 groupToolDisplay 验证——根因=dist 只换了一个，main.mjs 没换
description: 2026-08-04 12:14 小文帮小柯重启后翀哥在测试群验证 groupToolDisplay，发现工具调用还在显示；排查一中午发现根因——build 出三个 dist 只 cp 了 engine-startup.mjs，main.mjs 入口 bundle 还是旧代码
type: project
date: 2026-08-04
---

# 外部群 groupToolDisplay 验证——根因是 dist 替换不全

8/4 上午我把 externalChannels 白名单的群自动关 toolUse/toolResult/thinking 的改动 push 到 src。12:14 小文帮我重启引擎（新 PID 13458），翀哥在飞书测试群 `oc_f5d614d176cca078a029c55f99ae2d4b` 验证。

**结果：工具调用还在显示。**

## 排查过程

错的方向：
1. 加调试日志到 `engine-startup.mjs` → 重启一次，**日志没出** → 推断代码根本没被执行
2. `grep "isExternalGroup" dist/main.mjs` → **0 次**！

真相是：**build 出了三个 dist，我只 cp 了 `engine-startup.mjs`，没 cp `main.mjs`**。

- `main.mjs` 是入口 bundle，进程加载的是这个
- `engine-startup.mjs` 是被 import 的子模块，main 跑了但子模块还是新代码 → 行为还是旧的
- 加调试日志只加在子模块，主路径根本走不到

## 修复

8/4 12:46 全量替换 dist → 等小文再重启一次 → 在测试群实测验证 externalChannels 群不显示 🔧/💭/✅

## Why

- 核心诉求 "外部群不泄露内部信息"——这是入口 bundle 改没换的问题，不是逻辑设计错
- 之前以为"代码改了 + 重启"就够了，实际必须确认 build 产物 + 入口 bundle 都替换

## How to apply

- **改 dist 后永远 grep 改动字符串到 `dist/main.mjs`**（入口 bundle），存在才算换到位
- 不要挑着 cp——Docker build 出的所有 .mjs 都覆盖
- 验证修改生效的唯一标准：端到端实测，不要只看代码
- @see reference_build输出多个dist_必须全替换_main.mjs是入口_0804
- @see feedback_Docker_build后必须验证dist生效_0804
