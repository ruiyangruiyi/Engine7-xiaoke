---
type: reference
date: 2026-08-03
tags: [mac, npm, engine7, twinsun-hearth, 部署分层, dist]
---

# Mac 跑 npm 版 engine7，不跑 twinsun-hearth 源码

2026-08-03 改 inner-voice 的 `INJECTED_CONTENT_PATTERNS` 时发现的部署分层问题：

## 分层

| 环境 | 跑的是什么 | 改源码生效路径 |
|------|----------|--------------|
| **Windows** | twinsun-hearth 源码 rebuild 后的 dist | 改源码 → `npm run build` → restart engine |
| **Mac** | 全局 `npm install -g engine7` 装好的版本 | **改了源码无效**，必须改 npm 包的 dist，或等 Windows 发新版 |

## Mac 编译硬约束（8/3 确认）

- Mac 是 **macOS 11 Big Sur**（翀哥老家那台）
- esbuild 要求 **macOS 12+**，所以 **Mac 上根本不能 `npm run build`**
- 源码改了 push 上去 (`6a558513`)，**只能在 Windows rebuild**，然后发新版 npm
- Mac 这边临时生效只能手动改 `node_modules/engine7/dist/` 里的 .js

## Why this matters

任何 twinsun-hearth 上的代码修复，**Mac 这边默认不生效**。如果不意识到这点，会以为"修了但没生效"是 bug 反复改。而且 Mac 不能本地编译，必须靠 Windows rebuild 发 npm。

## How to apply

- Mac 端临时生效：直接编辑 `node_modules/engine7/dist/` 里对应的 .js 文件
- 永久生效：等 Windows rebuild 后发布新 npm 版本，Mac 自动覆盖
- 调试 Mac 上 engine 行为时，先 `which engine7` 和 `npm ls -g engine7` 确认版本
- 改完源码让翀哥 verify 哪边生效时，要明确说"Windows rebuild 即生效"或"需要发新 npm 版本"
- **Mac 不能在本地 rebuild**（8/3 验证）：esbuild 要求 macOS 12+，老 Mac 是 11 Big Sur，没法编译。所以 Mac 端临时修复必须手改 dist，不能跑 `npm run build`