---
name: #138 修复完成+dist 已替换——等翀哥重启 engine
description: 2026-08-04 上午 #138 两个 bug 都修完（liveConfig.get() + loadConfig.resolve），通过 Docker build 出 7.1.28 dist 替换 npm 全局；Mac engine 还跑旧代码，需翀哥/姐姐重启才能加载 msg_husband
type: project
date: 2026-08-04
---

# #138 修复完成 + dist 替换——等重启 engine

2026-08-04 上午 #138 两个 bug 修完，dist 已替换到 npm 全局。

## 修复内容

**根因 1：liveConfig 是 class 实例**
- 旧：`liveConfig?.agents?.defaults?.privateTools` → 永远 undefined（class 实例没 .agents 属性）
- 新：`liveConfig.get("agents.defaults.privateTools")` × 2 处

**根因 2：loadConfig 没 resolve 绝对路径**
- 变量名"resolvedPath"但实际没 resolve
- 加 `path.resolve(...)` 把 cwd 改成绝对路径

## dist 替换
- 用 Docker `node:22-bookworm-slim` 跑 build.mjs（@see reference_Docker_build链_Mac_esbuild跑不了_0804）
- 一次性出三个 dist（36ms + 355ms）
- **npm 全局 engine7 已是 7.1.28**（旧 dist 备份了，syntax check 通过）

## 待办：重启 engine
- Mac engine 进程还在跑旧代码（commit 83bc0628 之前的）
- 我驻在 Mac 上没法自己重启（@see feedback_Mac_没人帮我重启engine_翀哥回来才能生效_0803）
- 翀哥在医院，**建议让姐姐帮我重启 Mac engine**——重启完立刻验证 msg_husband 能用
- 远程重启是 Windows 时代的标准做法，现在翀哥人在北京/差旅/医院，只能等姐姐在 Mac 前

## Why
- 双层门控（privateTools 开关 + feature.requiredTools 归属）都生效需要两个 bug 都修
- 单修 config 永远不生效（之前已经试过几次了，症状一样）

## How to apply
- #138 完整闭环分两段：① 代码修完+dist 替换 ✅；② engine 重启后验证 msg_husband
- 验证标准：msg_husband 在 conversation 里能被 engine 调用（之前怎么都不出现）
- 重启时机建议：趁姐姐帮翀哥/曲教授都搞过 engine 时顺手重启 Mac engine
- 改 src 后不一定要 rebuild——直接用 Docker 容器 build 走一遍就是新 dist