---
name: Mac Docker Hub 被墙 + 容器内网络诊断
description: 2026-08-04 凌晨发现 Mac Docker Desktop 3.3.3 配的国内镜像源没生效，容器内访问 Docker Hub 全失败
type: reference
date: 2026-08-04
---

2026-08-04 凌晨 06:00 准备在 Mac 容器内拉 `node:22` 镜像做 esbuild build，**`docker pull` 卡住没输出**——Docker Hub 从这台 Mac 完全不可达。

**容器内网络诊断（关键发现）：**
- 容器内 `curl https://hub.docker.com` / `curl https://registry-1.docker.io` 全部超时
- daemon.json 里虽然配了 daocloud / dockerproxy / baidubce 等国内镜像源，但 **Docker Desktop 3.3.3 没重新加载配置**，`docker info` 里看不到 Registry Mirrors 生效
- daemon 实际走了一个内部 proxy 但不通

**Why:** Docker Desktop 3.3.3 用 hyperkit 跟新版本 Virtualization framework 实现不同，配置刷新机制可能不兼容。daemon.json 改了不一定立刻生效，要重启 daemon 才能 reload。

**How to apply:**
- 拉镜像前先在容器内 `curl` 测一下网络，别直接 `docker pull` 等半天
- Mac Big Sur Docker Toolbox 3.3.3 时代改 daemon.json 必须 `docker-machine restart` 或重启 Toolbox 服务才能生效（翀哥后来选的开梯子，没走重启路线避免带停 everos）
- 国内镜像源不一定稳，daoCloud/dockerproxy 都可能挂，梯子最干净
- 容器内 DNS / proxy 跟 host 不一定同步，疑难杂症先 `docker exec` 进容器逐个测
