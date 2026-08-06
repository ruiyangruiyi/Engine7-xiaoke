---
name: EverOS 容器重启后什么丢什么留
description: 2026-08-04 凌晨 2 点容器重启后——lancedb volume 保留、/tmp checkpoint 丢、ollama 不自动起、import loop 丢
type: reference
date: 2026-08-04
---

2026-08-04 02:11 容器重启后实测数据保留情况：

**留（持久化）：**
- lancedb 在 Docker volume 里 → **所有 add 的数据都在**，search 仍可用
- topics 挂载的 `/root/.everos/topics` → Mac 改了容器立刻看到

**丢（容器内 /tmp）：**
- `/tmp/checkpoint` 导入断点 → import 脚本需要重新从 0/N 开始
- import loop 进程 → 不在 start.sh 里，重启不自动恢复
- **ollama serve** → 同样不在 start.sh 里，容器重启后 11434 端口无响应

**更新（8/4 06:30 第一轮 rebuild 后）：**
- ✅ ollama 已烤进 image → 容器启动自动跑（#136 闭环）
- ❌ import loop 还是没接 start.sh → 8/4 06:53 又一轮 rebuild 后又死了（50/497 卡住）
- 结论：**纯 docker restart 不丢 ollama 也不丢 import loop**（进程还在）；**rebuild image（= 新容器）会丢 import loop + /tmp checkpoint**；ollama 因在 image 里所以新容器自动起

**Why:** 容器内 /tmp 是临时文件系统，重启清空；只有显式挂载的 volume / 目录才持久化。

**How to apply:**
- 修 start.sh 把 ollama + import loop 一起加进去，避免每次重启手动恢复
- 后续设计：import checkpoint 应该写到 lancedb 同 volume（比如 `/root/.everos/checkpoint.json`）而不是 /tmp，这样容器重启能续传
- 重要数据（DB / 索引 / 断点）永远走挂载的 volume，不要依赖容器内 /tmp
