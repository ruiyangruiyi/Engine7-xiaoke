---
name: EverOS embedding 配置默认指向 DeepInfra 而非本地 ollama
description: 2026-08-04 14:00 排查 memory_search 失败时发现——EverOS 默认 embedding 配置是 DeepInfra 远程 API（Qwen3-Embedding-4B），不是 ollama bge-m3；API key 字段空着，每次 search 都在尝试远程调用→超时
type: reference
date: 2026-08-04
---

2026-08-04 14:00 查 memory_search 为什么失败时发现的隐藏事实：

**默认配置：**
- EverOS embedding 服务端点指向 **DeepInfra 的 Qwen3-Embedding-4B**（远程 API）
- 不是翀哥装好、我在容器内验证过的本地 **ollama bge-m3**
- `api_key` 字段是空字符串 → 每次调用都因为没认证超时

**症状链（迷惑性）：**
1. search 接口超时
2. 看日志有 `EmbeddingServiceError: llama-server process no longer running`——以为是 ollama 崩了
3. 但根因是 **dense_recall 在调远程 DeepInfra（key 空）超时** + OME 的 episode extraction 也调 embedding 时遇到 EmbeddingServiceError
4. 实际 ollama 进程没崩，bge-m3 也在容器内跑得好好的

> ⚠️ 2026-08-04 下午补完：即使切回本地 ollama，llama-server 还是反复被杀——真正根因是 **Docker VM 内存 1.94GB 装不下 bge-m3**。
> 详细见 @see reference_EverOS_Docker_VM内存1.94G_bge-m3装不下_0804

**诊断方法：**
- 查 EverOS embedding 配置文件（ome.toml / everos.toml 之类）→ 找到 `embedding.provider = "deepinfra"` 或 endpoint URL
- 对比 endpoint URL 是 `https://api.deepinfra.com/...` 还是 `http://localhost:11434/...`
- 如果是远程但 key 空 → 改成本地 ollama（host: http://localhost:11434）+ model: bge-m3

**Why:** 翀哥/姐姐部署 EverOS 时默认配置可能用了远程 embedding（省钱/省事），跟 Mac 上的本地 bge-m3 路线不一致。我之前一直以为 EverOS = 本地 ollama（因为 ollama 容器跑起来了），没去查实际配置指向。

**How to apply:**
- 排 EverOS search/embedding 问题时**先查实际 embedding 配置**——不要假设是本地 ollama
- 看到 `EmbeddingServiceError: llama-server process no longer running` 不一定是 ollama 崩，可能是远程调用超时被误标
- 确认要本地：everos 配置里 `embedding.provider = "ollama"` 或 endpoint 改 `http://localhost:11434` + `model = "bge-m3"`
- 改完配置后**热加载不一定生效**——ome.toml 有些字段要重启 EverOS 才生效