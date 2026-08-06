---
name: Mac esbuild 跑不了——Docker node 容器 build 链路通
description: 2026-08-04 上午发现 Mac 本地 esbuild 跑不了（macOS 11 Big Sur），改用 Docker `node:22-bookworm-slim` 容器挂载源码跑 build.mjs，一次出三个 dist
type: reference
date: 2026-08-04
---

# Mac esbuild 跑不了——Docker node 容器 build 链路

2026-08-04 上午 #138 修复完后要 build 出新 dist 替换 npm 全局，发现 Mac 本地 esbuild 跑不了（旧老问题，Big Sur 不兼容）。这次找到**永久解法**。

## 根因
- Mac 11 Big Sur 上 npm install 装的 esbuild 二进制不兼容本机 libc
- 直接 `node scripts/build.mjs` 报错 → 没法 build dist

## 解法
用 Docker 跑 build（容器里 Linux + Node 22 + esbuild 都原生支持）：

```bash
docker run --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  node:22-bookworm-slim \
  node scripts/build.mjs
```

- 一次跑通 36ms + 355ms 出三个 dist
- `--rm` 完事自动清理容器，不污染本地

## Why
- 比手动 `sed` + `node -c` 验语法靠谱（自动出完整产物）
- 不需要 Mac 上折腾 node 版本/esbuild 原生包
- 容器是 Linux，跟 CI/Carpo/VoiceChat 等生产环境一致

## How to apply
- **Mac 上改 engine7 src 后要 build dist**：一条 docker run 命令搞定，不再手动 patch
- 跟 @see feedback_Mac_esbuild跑不了用手动patch_dist_0804 是"补丁 vs 链通"的差别——手动 patch 是临时救急，Docker build 是永久解法
- 如果 docker build 本身也卡（Docker Hub 被墙，@see reference_Mac_Docker_Hub被墙），让翀哥开梯子或换镜像源