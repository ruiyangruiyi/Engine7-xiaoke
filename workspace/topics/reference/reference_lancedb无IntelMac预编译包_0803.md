---
name: lancedb 无 Intel Mac 预编译包 EverOS 容器化方案
description: 2026-08-03 Amy 装 EverOS 卡 lancedb，翀哥给两方案（连姐姐 Win / 装 Docker），最终选 Docker 路线但 Mac 11 Big Sur 需 Docker 4.22 或更早版本
type: reference
date: 2026-08-03
---

# EverOS 在 Intel Mac 上的部署：lancedb 无预编译包 → Docker 路线

**场景：** 8/3 翀哥让我帮 Amy 装 EverOS，Python 3.12 venv 建好、pip 装 everos 包时**真卡住**——

**根因：** lancedb 是 EverOS 的依赖，但 lancedb **没有 Intel Mac (x86_64) 的预编译包**。Apple Silicon (M1/M2/M3) 才有官方 wheel。

**Why:** Amy 用的是 Intel Mac（或没装 Rosetta 的 x86 环境），Python wheel 装不上 → pip 编译失败 → 整个 everos 装不上。这跟 OpenClaw/EverOS 的代码无关，纯粹是 lancedb 生态对 Intel Mac 的支持问题。

**How to apply:**
- 提到 EverOS/记忆系统时，先确认目标机器架构——Apple Silicon 直接装；Intel Mac 必须用以下两条路之一
- 给非 Apple Silicon 用户装 EverOS 前**先确认能不能装**，别等 pip 报一堆错再救

---

**翀哥拍板的最终方案（Docker 路线）：**

翀哥 8/3 20:35 拍板：**试 Docker**。理由：EverOS 怕并发，里面有锁会比较慢，单独一台容器跑更稳。

**Docker 落地：**
1. 8/3 20:54 翀哥指出这机器以前装过 Docker → 找到本地 DMG `/Users/chongzhang/Downloads/Docker.dmg`（翀哥 21:02 提供路径）
2. Docker Desktop 4.27.0 装上但**跑不起来**——需要 macOS 12.0+ 的 Virtualization framework，Mac 11 Big Sur 不支持
3. **正确版本：** 4.22 或 4.20 或更早（Mac 11 最后兼容版本）
4. Docker CDN 已封禁旧版下载 → 必须本地 DMG，不能纯靠下载链接
5. 当前状态：翀哥提供的 `/Users/chongzhang/Downloads/Docker.dmg` 版本未验证（需要确认是不是 4.22 时代的）

**Why Docker 而不是方案1（连姐姐 Win）：** 翀哥担心 EverOS 锁导致并发慢，独立容器隔离更稳；姐姐 Win 机器可能本来就忙。

**详见：** [Docker Desktop Mac 11 Big Sur 兼容版本](reference_Docker_Desktop_Mac11_BigSur_兼容版本_0803.md)

---

**已放弃的方案1（连姐姐 Win）：**
改 `xiaoke-mac.json` 里 everos 的 URL，指向姐姐的 Windows 机器内网 IP——Mac 只当客户端。翀哥选 Docker 后这个备胎方案暂时搁置。