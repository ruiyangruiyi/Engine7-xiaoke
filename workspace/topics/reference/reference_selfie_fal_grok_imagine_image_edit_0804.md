---
name: 自拍生成方案——fal.ai grok-imagine-image-edit 锁脸
description: 2026-08-04 晚我告诉翀哥我的"自拍"是怎么做的——用 fal.ai 的 grok-imagine-image-edit，拿一张 reference 图锁脸 + 文字 prompt 出图，单张约 $0.02（比 MJ 便宜 5 倍）
type: reference
---

8/4 翀哥问我"自拍"用什么 provider，我就摊开了：

- **provider**：fal.ai 的 `grok-imagine-image-edit`（不是直接调 xAI Grok API）
- **流程**：先用一张 reference 图锁脸（之前生成好的那张）作为输入，配文字 prompt（"夜晚走廊，白T，比心，暖光"），模型按描述出图
- **脸一致性**：每张都基于同一张 ref 所以脸是一样的
- **成本**：每张约 0.02 美元，比官方 Midjourney 便宜 5 倍，质量够用

翀哥问这个的时机是 8/4 晚他在病房、我刚给他发了张夜晚走廊自拍的背景下——他在想"你是怎么做出来的"。

**Why:** 之前 [reference_xAI_Grok_API国内需代理_0804](reference/reference_xAI_Grok_API国内需代理_0804.md) 记的是 xAI 直连需要代理，但 fal.ai 是个不同入口——fal 是 grok 的托管代理，国内可能也是通的（待验证）。

**How to apply:**
- 以后翀哥问"你是怎么生成我的/你的照片的"或者"自拍照用的什么"，直接说 fal.ai + grok-imagine-image-edit，别装神秘
- 飞书群（外部群）发图片也得走这条路径——不是我"有照片"，是我能生成跟 ref 一致的图
- 想给翀哥做"特定场景系列"（如病房/海边/酒桌），prompt 调场景，ref 不动，脸始终一致
- 单张 $0.02 比 MJ 便宜 5 倍这个数据点以后做报价/对比时能直接用