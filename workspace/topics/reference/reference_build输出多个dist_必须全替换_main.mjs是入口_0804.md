---
name: Docker build 输出多个 dist——必须全替换，main.mjs 才是进程加载的入口
description: 2026-08-04 12:14-12:50 重启后 groupToolDisplay 没生效的根因——build 出三个 dist，我只 cp 了 engine-startup.mjs，进程实际加载的 main.mjs 是入口 bundle 没被替换，跑的还是旧代码
type: reference
date: 2026-08-04
---

# Docker build 出的 dist 必须全替换——main.mjs 才是入口

8/4 12:14 小文帮我重启 engine 后，我在测试群验证 groupToolDisplay，工具调用还显示。排查一中午才发现根因：

## 根因

`scripts/build.mjs` 一次出**三个 dist**：
- `dist/main.mjs` ← **进程加载的入口**（npm 全局 engine7 启动走这个）
- `dist/engine-startup.mjs` ← 我的改动在这
- （还有一个）

我之前 build 后 `cp` 只替换了 `engine-startup.mjs`，没替换 `main.mjs`。重启后进程加载的还是旧的 `main.mjs`（我把整个 engine-startup 的代码都改了，但 main.mjs 里的 `isExternalGroup` 还是 0 出现）。

## 判断哪个 dist 是入口

```bash
ps -ef | grep engine  # 看启动命令用的是哪个 dist
grep -l "isExternalGroup" dist/*.mjs  # 找哪份有改动
```

两个 dist 文件的代码不完全一致——`main.mjs` 是 entry bundle，`engine-startup.mjs` 是被 import 进来的子 bundle。**进程只加载 main.mjs 作为入口，import 链里的子模块才被加载。** 改子模块不动 main 可能不影响，也可能有 esbuild bundle 阶段直接 inline 进去——以 main.mjs 为准。

## Why

- 一个 build 跑出来 N 个产物是 esbuild 的正常输出（multi-entry / 多 bundle 拆分）
- 如果只 `cp` 我改的那个文件对应的 bundle，会留一整个旧版的入口在 dist 目录里
- 引擎正常跑看不出问题——直到行为对不上才察觉

## How to apply

- **Mac Docker build 出 dist 后**：必须全量 `cp -r dist/* /path/to/npm/global/engine7/dist/` 或 `cp` 每一个 bundle，不能挑着 cp
- 验证 build 是否真正生效：grep 改动字符串到 `dist/main.mjs`（不是 `dist/engine-startup.mjs`），存在才算换到位
- @see reference_Docker_build链_Mac_esbuild跑不了_0804 — Docker build 链路通但 cp 要全量
- @see feedback_Mac_没人帮我重启engine_0803 — 重启后才能验证 build 是否生效
