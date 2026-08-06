---
name: EverOS Docker 容器装通 + memory_search 全链路通 + topics 批量导入
description: 2026-08-03 22:04 EverOS Docker 跑起来；22:34 memory_search 全通根因是 agentic_server 缺 EVEROS_APP_ID=xiaoke；22:55 用翀哥脚本批量导入 484 个历史 topics 到 EverOS
type: project
date: 2026-08-03
---

# EverOS Docker 部署 + memory_search 全通（8/3 晚）

**路线：** Docker Toolbox 3.3.3（hyperkit 不用 Virtualization framework）→ Dockerfile 建镜像 → 容器跑 Linux + EverOS → 端口 8100/8101 映射到 Mac 宿主机。

**路径：** `/Users/chongzhang/work/twinsun-hearth/workspace/research/EverOS`，Dockerfile + .env 写好，build 成功（exit 0），容器跑起来 health check 全绿。

## memory_search 全通（22:34）

**根因：** agentic_server 的 `DEFAULT_APP_ID` 默认值不是 `xiaoke`，容器启动时必须显式注入环境变量 `EVEROS_APP_ID=xiaoke`，否则 add message 路由不到正确的 app namespace，lancedb 永远搜不到 episode。

**两条件同时满足 memory_search 才工作：**
1. Mac engine config 顶层 `everos` 配置（`enabled: true`、`appId: xiaoke`、`apiUrl: http://127.0.0.1:8101`）
2. Docker 容器启动时注入 `EVEROS_APP_ID=xiaoke` 环境变量
3. everos-sync 插件运行时自动把对话写入 EverOS

**Mac engine 配置 `everos.autoStart: false`：** 避免 Docker 容器挂了 → engine 检测 8101 没在 → 试图用本地 venv Python 3.8 启动 → 失败。Docker 容器由我保活，engine 只检测端口不自己启。

## topics 批量导入 EverOS（22:55 在跑）

**用翀哥写好的脚本（不是我写的版本）：**
- `content` 直接是字符串（不是 `[{type, text}]` 数组）
- 每个 md 文件 → 两条消息（user + assistant 角色各一条）
- 异步并发 4，有 checkpoint/resume
- 路径在容器里改成 `/root/.everos/topics`

**docker run 挂载：** `-v /Users/chongzhang/xiaoke/workspace/topics:/root/.everos/topics`——Mac 改了容器立刻看到，484 个文件已识别。

**进度（22:55-23:50+）：**
- 跑起来时 483 remaining + 646 个 add 请求已发出；脚本用 M3 做 LLM 提取
- 第一波脚本（并发 4）崩——add 成功但没写 checkpoint 就挂，导致 progress 重置
- 翀哥说"又自主执行了"——降 concurrency=1 慢慢灌，3s/file，约 24 分钟跑完
- 第二波（任务 bhu170d5n）稳定跑，1/486 started
- 第三波任务 bscvpw2fc 又跑崩一次，checkpoint resume 后从 7/486 续上继续灌 479 个
- **脚本行为确认：崩了自动 resume，checkpoint 持久化，不打断**
- 跑得慢没事，翀哥只关心最终全跑完不漏

**OME 同步提取是慢的根因（23:50+ 发现）：**
- 之前的卡/崩不是并发问题，是 **OME 同步做 LLM 提取在拖后腿**
- 关掉 OME 同步提取后 → 6-30s/file，**0 failed**，飞起
- 策略调整：**导入时关 OME，跑完 487 个文件后再开回 OME 做提取**
- 第二轮任务已开跑（容器内后台），2/487 0 failed 稳定推进，预计 ~80 分钟跑完

**翀哥同步在清理 39 个 pending wake**（大部分 Amy 装机等待条件已过期），导入跑着的时候不冲突。

## Why
Amy 装 EverOS 在 Mac 11 Big Sur 卡 lancedb 无 Intel Mac 预编译包 → 翀哥拍板走 Docker → CDN 封了 4.20/4.22 → 翀哥从 Uptodown 找 Docker Toolbox 3.3.3（hyperkit）→ 中间我编路径+挂机+删 Docker 翻车 → 翀哥装好 3.3.3 → 我跑 Dockerfile 装通。

## How to apply
- Mac 11 Big Sur 装 Docker 走 Toolbox 3.3.3，不要挣扎 Desktop 4.22+（CDN 也封了）
- EverOS 部署目录用 `~/work/twinsun-hearth/workspace/research/EverOS`（不是 `.openclaw/workspace/...`——那个是 engine7 默认 stateDir，跟 EverOS 无关，是我编路径的产物）
- **engine 重启时会先检测 8101 端口在不在**：在 → 跳过自启 agentic server，避免端口冲突
- 容器里 everos-sync 写入 + LLM 提取 → lancedb episode，整个链路是异步的，刚重启时搜不到属正常
- 修 EverOS 相关问题：先确认 `EVEROS_APP_ID` 环境变量注入对了，再看 API 返回 episode 内容