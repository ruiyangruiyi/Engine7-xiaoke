---
name: EverOS embedding 实际是 deepinfra Qwen3-Embedding-4B 不是 ollama bge-m3
description: 2026-08-03 翀哥发现 Mac 上 EverOS memory_search 实际走远程 API 而非本地 ollama，跟姐姐 Windows 配置不一样
type: reference
---

2026-08-03 翀哥问我 EverOS embedding 用的是什么模型，我之前一直以为 Mac 上是 ollama + bge-m3（跟姐姐一样），翀哥纠正——实际上：

**Mac 侧我用的：**
- 模型：`Qwen/Qwen3-Embedding-4B`（deepinfra 远程）
- API：deepinfra OpenAI 兼容接口
- 配置在 `.env`：`EVEROS_EMBEDDING__MODEL` / `_API_KEY` / `_BASE_URL=https://api.deepinfra.com/v1/openai`
- 链路：memory_search → EverOS agentic server → deepinfra API

**engine config 里那个 `"provider": "ollama", "model": "bge-m3"` 是 cognifold 旧配置，Mac 上 ollama 根本跑不起来（跟 lancedb 一样无 Intel Mac 预编译包），实际路径完全不走 ollama。**

**Why:** 翀哥让我以后别凭印象瞎猜（之前有过把"已启动"当"没启动"翻车的反馈），embedding 这种基础设施要查 `.env` 实际配置而不是看 config 注释/旧字段。

**How to apply:** Mac engine config 里看到的 ollama/bge-m3 是 cognifold 历史遗留，实际走 EverOS + deepinfra；跟姐姐（Windows + 本地 ollama bge-m3）不是一个路径。以后讨论 embedding 模型/性能/成本时按实际 deepinfra 路线算，别按 ollama 本地推算。

---

## ⚠️ 2026-08-04 更新：Mac 实际已切回本地 ollama bge-m3

8/4 下午全面排查后，embedding 已经从 DeepInfra 切回本地 ollama bge-m3（容器内 11434 + model=bge-m3）。因此：

- 链路：memory_search → EverOS agentic server → **本地 ollama bge-m3**（不再是 deepinfra）
- 性能预期改用 @see reference_cascade_CPU_embedding速度预期_0804（5-20s/块，大文件 2-4 小时）
- 客户端 timeout 必须 ≥ 120s（@see reference_EverOS_embedding_timeout30s边界死循环_0804）
