---
name: Docker Toolbox 3.3.3 hyperkit 是 Mac 11 Big Sur 终极备胎
description: 2026-08-03 Amy 装 Docker 时发现 Docker Toolbox 3.3.3 用 hyperkit 而非 Virtualization framework，绝对兼容 Mac 11
type: reference
date: 2026-08-03
---

# Docker Toolbox 3.3.3 — Mac 11 Big Sur 终极备胎

**场景：** 8/3 帮 Amy 装 Docker 时，4.27 因 Virtualization framework 跑不起来、官方 CDN 又封了 4.22/4.20 下载——

**翀哥 8/3 22:20 提出第三档方案：Docker Toolbox 3.3.3**

**关键差异：**
- Docker Desktop 4.x 用 **macOS Virtualization framework**（要 macOS 12+）
- Docker Toolbox 3.x 用 **hyperkit**（基于 xhyve/virtualbox，Mac 11 时代标准）
- Toolbox 时代命令是 `docker-machine`，跟现在的 `docker` CLI 命令大部分兼容但有差异

**Why:** Docker Toolbox 是 Apple 还没推 Virtualization framework 之前的官方方案，Apple 放弃 hyperkit 后 Toolbox 项目就被 Desktop 取代了，但在 Big Sur 上反而是**唯一能跑**的版本。

**How to apply:**
- Mac 11 Big Sur 上 Docker 装不上的最终 fallback：Docker Toolbox 3.3.3
- Toolbox 安装后会自动装 docker-machine、docker-compose、virtualbox，注意 VirtualBox 也要给辅助功能权限
- Amy 案例进度：翀哥在 Win 上用 Uptodown 下载中（先试 4.20/4.21，不行再上 Toolbox 3.3.3）