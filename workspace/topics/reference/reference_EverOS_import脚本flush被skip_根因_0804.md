---
name: EverOS 导入脚本 skip flush 是 episode 0 行的真根因
description: 2026-08-04 14:40 找到——翀哥的 import 脚本里 flush 被显式 pass 跳过（"add-only mode, flush separately later"），813 memcell 灌进去但 flush 从来没跑过；flush 才是触发 boundary detection → episode extraction 的关键
type: reference
date: 2026-08-04
---

2026-08-04 14:40 排查 memory_search 真正根因时找到——之前归因"OME 没自动处理 episode"只是表层，深层是 **导入脚本跳过了 flush**。

## 事实链

1. 翀哥的 EverOS 导入脚本走标准管线：`POST /api/v1/memory/add`（写 memcell）+ `POST /api/v1/memory/flush`（触发 episode extraction）
2. 脚本里 flush 这一段被显式 `pass` 跳过：
   ```python
   # Skip flush entirely — add-only mode, flush separately later
   # EverOS auto-detects boundaries on its own
   pass
   ```
3. 注释里说"EverOS auto-detects boundaries on its own"——**错的**，flush 是显式触发，不 flush 永远不提取 episode
4. 结果：813 条 memcell 全部在 unprocessed_buffer，但 episode 表 0 行
5. 即使手动调一次 flush（返 "extracted"），也只是触发少量 unprocessed 处理，不补历史——所以根本还是要"灌完手动 flush 全部"

## 为什么这是根因

- "auto-detects boundaries on its own" 是写脚本时的错误假设——可能 OME cascade worker 应该兜底，但实际它只处理"启动后看到的新文件"
- 跟之前的 @see reference_EverOS_OME_episode_extraction_0行根因 互补：那一层说的是"OME 设计没 recovery 路径"，这一层说的是"即使 OME 没 bug，flush 不跑也不会有 episode"
- 加起来才是完整真相：**flush 跳过 → memcell 进 buffer 不提取 + OME 不回头处理 → episode 0 行**

## Why

- "add-only mode"听起来合理（先灌数据后提取，分阶段），但脚本最后没有"later"步骤补 flush
- 注释里的"auto-detects"假设是错的——没有证据 EverOS 会自动 flush
- 调试时容易归因为"OME 没自动跑"，没去看脚本本身有没有跑完整流程

## How to apply

- **复现 / 重灌数据后必须手动 flush 一次**：调 `/api/v1/memory/flush` 把 buffer 里所有 memcell 推到 episode extraction
- **看别人的脚本不要只看注释**："add-only mode, flush separately later"——必须找到 "later" 在哪执行
- **断言边界检测**：灌完查 `episode` 表行数，必须 > 0 才算导入成功，不是看 memcell 行数
- **改脚本别破坏完整性**：省步骤省不了——flush + boundary detection + episode extraction 是串行依赖，省了哪步后面就废
- @see feedback_不用贪快要质量_OME最好不用_0804 — 翀哥拍板"flush 都没跑就别瞎折腾 OME 了"
- @see reference_EverOS_search端点_ollama崩重启_0804 — 完整搜索问题诊断链