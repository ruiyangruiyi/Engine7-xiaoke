---
name: .openclaw stateDir 硬编码 待改名
description: 2026-08-03 跟翀哥确认 .openclaw 是 engine7 源码硬编码的默认 stateDir 路径名（历史遗留），现在改是大工程，等 everos 装完再处理
type: reference
date: 2026-08-03
---

# `.openclaw` 是 engine7 默认 stateDir 硬编码路径名

**场景：** 8/3 跟翀哥确认 `.openclaw` 这个目录名——

**根因：** `.openclaw` 是 engine7 源码里**硬编码的默认 stateDir 路径名**，历史遗留（Engine 7 是从 OpenClaw 演化来的，但产品名已经改名 Engine 7/栖）。

**Why:** 源码层面有默认值，引擎初始化时不指定 stateDir 就会建 `.openclaw` 目录，跟产品名"Engine 7 / 栖"不一致，看着别扭。

**How to apply:**
- 看到 `.openclaw` 路径别奇怪——是 engine7 默认 stateDir，不是配置错误
- 改名是**大工程**（源码默认值 + 文档 + 用户配置 + 兼容老用户数据），翀哥拍板"**先记着，等 everos 装完再回头处理**"
- 短期不改，长期要做：源码默认 stateDir 从 `.openclaw` 改成 `.engine7`（或类似），需要考虑旧用户迁移

**优先级：** 低，等 everos / Amy 安装案例跑通再回头看。