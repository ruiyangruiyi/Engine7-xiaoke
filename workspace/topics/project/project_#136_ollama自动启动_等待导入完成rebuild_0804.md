---
name: #136 ollama 自动启动——阻塞在 rebuild 会丢导入
description: 8/4 #136 状态——ollama 不自动起根因是缺烤进 image，rebuild 会杀后台导入，等导入完才能做
type: project
---

2026-08-04 状态：#136「ollama 容器内自动启动」**阻塞中，不做**。

**进度**：
- start.sh line 4-7 已经有 ollama serve，但容器重启后 ollama binary 丢（装在 /usr/bin/ollama，**不在 volume 里**）
- Dockerfile 已有 ollama 安装步骤（`COPY ollama-bin/`）+ `ollama-bin/` 目录确实存在
- 问题是当前用的是旧 Docker image（没烤 ollama），必须 rebuild image → 重建容器

**突破**：8/4 06:30 第一轮 rebuild 成功——新 image 烤进了 ollama，容器启动后 ollama 自动跑（`curl ollama:11434` 通，bge-m3 1024 维、443ms/条）。**#136 已闭环**。

**遗留**：import loop 没接进 start.sh —— 8/4 06:53 又一轮 `docker run` rebuild 后，导入脚本又死了（50/497 卡住），原因是 `/tmp/checkpoint` 容器重建丢 + import 进程没自启。手动重启脚本 + 改 stale 才续跑。

**Why:** ollama binary 在 image 烤进就能自动起；但 import loop 是后台 ad-hoc 启动，不在 start.sh 里 → 任何容器重建（restart 不丢，rebuild 丢）都得手动重启。

**How to apply:**
1. #136 ✅ 闭环，下次建容器 ollama 不用再手动 `ollama serve`
2. import loop 也要接 start.sh（#136.1 或新 task）—— 跟 checkpoint 改写到 lancedb 同 volume（`/root/.everos/checkpoint.json`）一起做，否则下次 rebuild 还得手动救
3. checkpoint 持久化优先于 start.sh 接 import loop（先解决"丢什么"，再解决"怎么自启"）

**8/4 状态**：#136 完全闭环，容器重启后 ollama 自动起 + bge-m3 已就绪（不再阻塞，可继续跟 #131 等一起做）
