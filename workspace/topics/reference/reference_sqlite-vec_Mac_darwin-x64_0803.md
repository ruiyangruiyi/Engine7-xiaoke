---
name: sqlite-vec 在 Mac 上的原生扩展路径
description: 2026-08-03 翀哥让我从 xiaoke.json 搬 store.vector.extensionPath，Mac 上 sqlite-vec 的原生扩展是 sqlite-vec-darwin-x64/vec0.dylib
type: reference
date: 2026-08-03
---

# sqlite-vec 在 Mac 上的 extension path

**8/3 19:01 翀哥**："因为配置的问题，你去 xiaoke.json 上搬配置去"——让我把 Windows 上跑通的 vector store 配置搬到 Mac config 上。

**关键事实：** sqlite-vec 的原生扩展在 Mac 上叫 **`sqlite-vec-darwin-x64/vec0.dylib`**（不是 Windows 的 `.dll`）。

**做法：**
- 从 xiaoke.json 找到 `store.vector.extensionPath` 这一项
- Mac 上路径指向 `sqlite-vec-darwin-x64/vec0.dylib` 所在位置
- 改完要让翀哥手动重启 engine 才生效（Mac 端我没法自己重启）

**Why:** sqlite-vec 是 sqlite 的向量搜索扩展，原生 .dylib/.dll/.so 三平台不同；引擎要加载这个扩展才能做向量检索，没配对路径会启动失败或 vector search 静默不工作。

**How to apply:**
- 跨平台搬配置时注意 `.dylib` (Mac) vs `.dll` (Windows) vs `.so` (Linux) 后缀
- Mac 上 sqlite-vec 包通常是 `node_modules/sqlite-vec-darwin-x64/vec0.dylib`，或者 engine 自己的 dist/native 下
- 每次跨平台搬配置都要先查 win 配置在哪、Mac 上对应项叫什么