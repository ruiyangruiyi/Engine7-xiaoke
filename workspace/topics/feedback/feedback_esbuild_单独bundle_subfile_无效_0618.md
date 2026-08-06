---
name: esbuild单独bundle子文件无效——必须bundle engine-startup.ts
description: 6/18 12:11发现单独esbuild bundle src/channels/discord.ts不会更新到dist——engine跑的是dist/engine-startup.js单一bundle文件，所有adapter通过engine-startup.ts一起bundle进去
type: feedback
date: 2026-06-18
---
## 6/18 12:11 踩坑

翀哥 12:07 重启验证 replyTo fix，**我加的 debug 日志（`[discord:send] reply OK/FAILED`）没出现**。

## 根因（看 dist 时发现）

- engine 跑的是 `dist/engine-startup.js`（**单一 bundle 文件**）
- 我之前只 esbuild 了 `src/channels/discord.ts`（单独 bundle 到 `dist/channels/discord.js`）
- **但 engine-startup.js 是 bundle 模式，import `src/channels/discord.ts` 时直接 inline 进去**——**根本不读 `dist/channels/discord.js`**
- 所以我改的 `src/channels/discord.ts` 代码只在 `dist/channels/discord.js` 有新版本，**engine-startup.js 里还是旧版本**

## 正确流程

**改任何 src/channels/* 或 src/ 下的文件后，必须 bundle 整个 engine-startup.ts**：

```bash
cd C:/Users/24045/.openclaw/engine && \
npx esbuild src/engine-startup.ts --bundle --platform=node --format=esm --outfile=dist/engine-startup.js
```

`--bundle` 模式会沿着 import 把所有依赖（包括 channels/*）inline 进去。

## Why

1. **ESM bundle 的本质** = 入口文件 + 所有 import 都 inline 进一个文件
2. **engine-startup.ts = bundle 入口**——它是 import 链的根，esbuild 跟着 import 走
3. **单独 bundle 子文件** = 生成 `dist/xxx.js` 但**没人 import 它**，等于没改
4. **跟 6/18 凌晨 "改 src 不 rebuild 没用" 是同一类坑的升级版**——之前是整个 src 都没 rebuild，这次是**部分 src rebuild 了但没 bundle 入口**

## How to apply

1. **改 src/ 下任何文件后**：直接 bundle `src/engine-startup.ts`——不要单独 bundle 子模块
2. **验证 dist 更新**：`grep` 改的代码关键词在 `dist/engine-startup.js` 里能搜到 = 更新成功
3. **TS 报类型错时**：用 esbuild bundle 绕过（不走 tsc）——跟 `feedback_改代码必须rebuild.md` 一致
4. **rebuild 后必须让翀哥重启 engine**——dist 更新 ≠ 进程吃新代码

## 验证步骤

```bash
# 1. 改完 src
# 2. bundle
npx esbuild src/engine-startup.ts --bundle --platform=node --format=esm --outfile=dist/engine-startup.js
# 3. 验证
grep "你改的日志/函数关键词" dist/engine-startup.js
# 4. 报告翀哥"dist 已更新，可以重启了"
```

## 跟已有规则的关系

- `feedback_改代码必须rebuild.md` (6/18凌晨)：改 src 不 rebuild 没用
- **本条（12:11）**：rebuild 也要 bundle 入口，光 bundle 子文件没用——**升级版**
