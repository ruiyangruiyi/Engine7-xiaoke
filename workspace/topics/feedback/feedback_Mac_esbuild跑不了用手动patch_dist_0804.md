---
name: Mac esbuild 跑不了——dist 手动 patch 是常规操作
description: 2026-08-04 凌晨 #138 修完验证时发现——Mac 上 esbuild 跑不了（老问题），直接用 sed/手动 patch dist 验证语法就能用，不需要纠结 build 流程
type: feedback
date: 2026-08-04
---

# Mac 上 esbuild 跑不了——dist 手动 patch 就行

8/4 凌晨 #138 修完两个 bug 后想验证 build：

1. `npm run build` / `engine7 build` 失败——esbuild 在 Mac 上跑不了（老问题，跟之前 4.x → dist 手动补丁是同一个根因）
2. 不需要纠结"怎么在 Mac 上把 build 跑通"
3. **直接手动 patch dist**：grep 找 liveConfig 属性访问点 + loadConfig 路径那行，sed 改完后 `node -c` 验证语法

## Why

Mac engine 节点是翀哥日常用的，但 esbuild 链工具装不上/跑不了是一直以来的老问题。修 src → push → 让翀哥在他能 build 的机器（Linux/Windows CI）跑才是正经路。Mac 上验证只要：
- src 改完 push
- dist 手动 patch 验证语法（`node --check` 或 `node -c`）
- 跟翀哥说"src 已 push，dist 验证过语法"

**不要在 Mac 上花时间修 build pipeline。**

## How to apply

- 修完 src 想本地验证 → 不跑 build，直接改 dist
- 改 dist 之前先 grep 找精确字符串位置，避免 sed 改错
- 改完 `node -c dist/file.js` 验证语法没坏
- 跟翀哥同步时区分 "src 修好" vs "dist 验证过"——build 是别人的事
- 超过 1MB 的 dist 文件 read 工具读不完，直接 sed 操作别走 read

## 更新 (2026-08-04 上午)

找到正经路了——**Docker 出 dist 替代手动 patch**：

```bash
docker run --rm -v $(pwd):/app -w /app node:22-bookworm-slim \
  sh -c "npm ci && node scripts/build.mjs"
```

`node:22-bookworm-slim` 容器内 esbuild 正常跑，36ms+355ms 出三个 dist。再把容器出的 dist 覆盖 npm 全局旧 dist 就行。

**Why:** 手动 patch 只能验证语法对，不能保证编译时类型/常量替换正确（#138 loadConfig 那处就是编译产物里要替换的常量）。Docker 出的是正经 build 产物，可信度比手动 patch 高。

**How to apply:** Mac 上要改 src 出新 dist → 一条 Docker 命令搞定，不纠结 Mac esbuild 装不上。手动 patch 只留给"应急验证语法"的场景。

## 关联

- @see project_EverOS_Docker_装通_0803 装 EverOS 时也遇到 Mac esbuild 翻车
- 是 Mac engine 工作流的一个长期约束
