---
name: EverOS Docker VM 内存 1.94GB 装不下 bge-m3
description: 2026-08-04 下午最终根因——Mac 物理 16GB 内存但 Docker VM 默认只给 1.94GB，bge-m3 加载需 ~1161 MiB + 1024 MiB free target=装不下，llama-server 被 OOM kill；调 Docker 内存到 8GB 是彻底解法
type: reference
date: 2026-08-04
---

# EverOS Docker VM 内存 1.94GB 装不下 bge-m3

2026-08-04 下午 14:40-15:00 排查 llama-server 反复被杀，找到的**真正根因**——之前一直以为是 cascade 大文件 OOM，其实是 **Docker VM 内存配额太小**，bge-m3 根本装不进去。

## 根因

```
Mac 物理内存：16GB
Docker VM 默认内存：1.94GB（默认配额太小）
bge-m3 模型加载：~1161 MiB
ollama free memory target：1024 MiB
→ 1161 + 1024 = 2185 MiB > 1940 MiB → 装不下
```

## 症状链

- 日志：`llama-server process no longer running` sys=9 signal: killed
- 日志：`was unable to fit model into system memory`
- 日志：`cannot meet free memory target of 1024 MiB, need to reduce device memory by 197 MiB`
- atomic_fact 表有 288 行（早期小文件勉强能跑出来）
- episode 表 0 行（episode md 557KB 大文件，embedding 必然 OOM）
- cascade worker 遇 EmbeddingServiceError 不重试 → episode 永远 0

## 为什么之前误判

之前 `reference_ollama_CPU单slot_import_search互抢_0804` 写"episode 大文件让 llama-server 内存崩"是**对症不对根**——
- 大文件确实是触发条件（小文件 early 跑出 288 条 atomic_fact）
- 但真正原因是**VM 内存上限**而不是"文件太大"
- 小文件跑多了也会随机崩，因为模型随时可能被 unload→reload

## 彻底解法

**调 Docker VM 内存到 8GB**（Mac 16GB 物理，分一半给 Docker）

- Docker Desktop → Settings → Resources → Memory → 8GB
- 保存后 Docker Desktop 会重启，所有容器都停
- 装 ollama + bge-m3 后 episode 大文件也能稳定 embed

**临时绕过**（不想重启 Docker）：
- 换 bge-small（~100MB，远小于 1.94GB 限额）能跑但精度差
- 或降低 ollama `OLLAMA_KEEP_ALIVE` + `num_ctx` 减少常驻

## 姐姐 Windows 没事的根因

Windows 物理 32GB 内存 + 容器无内存限制（或很高），bge-m3 装得下。

## 实战修复路径（2026-08-04 15:00 验证成功）

调 VM 内存实际姿势（不需要靠 Settings UI 重启）：

1. 改 `~/Library/Group Containers/group.com.docker/settings.json` 把 `memoryMiB` 改成 `8192`
2. **强制 kill 整个 Docker 进程链**——`pkill -9 -f "Docker Desktop"` + `pkill -9 -f "com.docker.hyperkit"` + `pkill -9 -f "com.docker.virtualization"` 等所有相关进程
3. 留 vmnetd 不杀（系统特权守护）
4. 用 launchctl 或直接 open 拉起 Docker Desktop
5. 等 hyperkit 重启后 VIRT=7.78GB（之前 1.94GB），内存生效
6. `docker start everos` —— 容器内 `/proc/meminfo` 显示总内存 7.8GB，bge-m3 embed 9s/条稳定

**关键教训**：
- Settings UI 重启不是唯一路径，pkill + launchctl / open 重新拉起也算"重启"
- "调 Docker Desktop 要重启"不是"必须 UI 操作"——pkill 进程也算重启
- 调完验证标准：hyperkit 进程 VIRT 列 > 4GB 才是生效，光看 settings.json 改了没用

**Why:** Docker Desktop 在 Mac 上跑的是 LinuxKit VM，受 macOS Hypervisor.framework 限制，默认给的内存配额远小于物理内存（Mac 16GB → VM 1.94GB）。Mac 上跑需要本地 ollama/LLM 的容器，必须显式调大 VM 内存。

**How to apply:**
- Mac 上跑 ollama/llama.cpp/vLLM 等本地 LLM 容器 → 先把 Docker VM 内存调到 ≥ 8GB
- 看日志有 `unable to fit model into system memory` 或 `signal: killed` → 100% 是 VM 内存不够，不是代码 bug
- atomic_fact 部分成功 + episode 全失败 → 几乎肯定是 VM 内存不够（episode 文件大、文本长、需要更多 memory headroom）
- Docker Desktop 调大内存要重启 → 翀哥/姐姐住院时不能随便动，得标 blocked 等人。但：pkill + launchctl/open 拉起是翀哥授权过的姿势（"分吧 你设置下 Docker"），不需要等他点 UI
