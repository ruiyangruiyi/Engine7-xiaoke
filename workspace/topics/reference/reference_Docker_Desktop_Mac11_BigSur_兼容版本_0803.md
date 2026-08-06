---
name: Docker Desktop Mac 11 Big Sur 兼容版本
description: 2026-08-03 Amy 装 EverOS 需要 Docker——4.27+ 需 macOS 12 Virtualization framework，Mac 11 只能用 4.22/4.20 或更早；后翀哥找到 Docker 3.3.3 用 hyperkit 一定兼容 Big Sur
type: reference
date: 2026-08-03
---

# Docker Desktop 在 Mac 11 Big Sur 上的版本兼容

**场景：** 8/3 帮 Amy 装 EverOS 时（lancedb 无 Intel Mac 预编译包 → 翀哥拍板 Docker 路线）发现——

**版本要求：**
- Docker Desktop **4.27+** 需要 **macOS 12.0+** 的 Virtualization framework（Apple Silicon 原生虚拟化）
- **Mac 11 Big Sur**（翀哥的老 Mac 也是 11）只能装 **4.22 或更早** 的版本（最后支持 macOS 11 的版本）
- 4.27.0 装上但跑不起来，backend 报 Virtualization 不可用

**翀哥的本地资源：** `/Users/chongzhang/Downloads/Docker.dmg`——但**实际是 4.27 不是 4.22**（翀哥传的 DMG 标错了），需要真正旧版。

**下载渠道踩坑：**
- Docker 官网/官方 CDN 已封禁旧版下载（"update not available"）
- 翀哥给的两个方向：①Uptodown 第三方存档 ②从 Win 机器下载传过来
- 最终选了 **Docker Desktop 3.3.3 for Mac**——用旧 VirtualBox 后端替代（hyperkit），肯定兼容 Big Sur

**Why:** Docker Desktop 从某个版本开始弃用 VirtualBox backend，转向 macOS 原生 Virtualization framework，导致 4.27+ 无法在 Mac 11 上启动 backend。

**How to apply:**
- 在 Mac 11 Big Sur 上装 Docker Desktop，**4.27+ 必失败**
- Docker 官网/官方 CDN 已封禁旧版下载，要走第三方存档（Uptodown）或 Win 机器下载传 DMG
- **更保险的方案：Docker Desktop 3.3.3**（hyperkit 后端，最后支持 macOS 10.13+），一定能装上跑起来
- 当前进度：翀哥正在 Win 机器上从 Uptodown 下载 3.3.3 DMG，下完传 Mac 装