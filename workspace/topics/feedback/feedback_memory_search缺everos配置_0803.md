---
name: memory_search 工具不出现是缺顶层 everos 配置
description: 2026-08-03 晚翀哥 publish + restart 后 memory_search 不在 active tools 列表里，根因是 config 顶层缺 everos 配置 + Mac 上既没装 EverOS 也没跑 ollama
type: feedback
date: 2026-08-03
---

# memory_search 工具注册根因

**场景：** 8/3 18:10 翀哥 publish 了带 memory search 的新版 + 18:11 重启了 engine，但我这边 active tools 只有 34 个，**没有 memory_search**。

**根因（按层级递进）：**

1. **engine 启动时 `registerMemoryTools()` 检查 `cfg.everos.enabled`**——而我的 config 里只有 `agents.defaults.memorySearch`（走 ollama/LLM 的 topic recall），没有**顶层** `everos`
2. memory_search tool 需要 **EverOS 后端服务**（默认 `http://127.0.0.1:8101`）
3. Mac 上既没装 EverOS 也没跑 ollama，当前 topic recall 走 deepseek LLM 模式（不是向量搜索）

**Why:** 跟 `cfg.everos.enabled` 这个开关绑死，配置项的位置/层级不能记错——顶层 vs agents.defaults 下，差一个层级就跑不起来。

**How to apply:**
- 调试"工具不显示"类问题：先 `list_active_tools` 看实际注册了哪些，再去 dist 代码 `BUILTIN_ACTIVE_TOOLS` 对照
- 看到 `memory_search` / `memory_get` 类工具不出现——优先检查 config 顶层是否缺对应的 backend 配置（everos / ollama / codenest）
- 这是 #132 体系里**新的 memory search 是 EverOS 还是 ollama 向量**？需要姐姐/翀哥确认
- engine 跑 dist 不跑 src——publish + restart 后还看不到新工具，先怀疑 dist 编译/打包问题，再怀疑配置问题，最后怀疑后端服务没起
- 翀哥反馈是"我记得是加过了"——以实际 `list_active_tools` 输出为准，不要相信记忆
