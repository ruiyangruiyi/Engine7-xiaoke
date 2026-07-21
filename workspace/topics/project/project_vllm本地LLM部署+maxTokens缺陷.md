---
type: project
created: 2026-07-17
updated: 2026-07-17
tags: [vllm, engine, maxTokens, context-length, qwen3.6]
---

# vLLM 本地 LLM 部署 + Engine maxTokens 缺陷

## 背景
翀哥希望部署本地 LLM 做直播（不受监管），同时发现 Engine 的 maxTokens 写死 4096 不生效。

## vLLM 部署
### 基建
- 服务器: `u982535-fw2w-4551c8ba.bjb2.seetacloud.com:8443` (seetacloud, 4090)
- 模型（旧）: Qwen2.5-VL-7B-Instruct (vLLM 0.25.1)
- 路径: `/root/autodl-tmp/models/models/Qwen--Qwen2.5-VL-7B-Instruct/snapshots/master`

### 7B 测速结果（7/16 16:12）
- TTFB: 0.24s
- Total: 0.24s
- Prompt: 20 tokens → Completion: 10 tokens
- max_model_len: 4096 (默认) → 翀哥切到 32768 (32K)

### 32K context 卡边界
- Engine 发 28K 输入 + 4K 输出 = 32K 刚好溢出
- 64K OOM (4090 显存限制)
- 7B 模型在 4090 上 32K 是上限

## 新方案：Qwen3.6-27B（7/17 16:00 翀哥发帖确认）

### 核心信息
- **模型**: Qwen3.6-27B（SWE-bench Verified #7，得分 77.2%）
- **三值量化版（-1,0,1）仅 7.2GB**，4090 单卡 24G 能跑满 256K 上下文，保持 FP16 95% 能力
- **投机解码加速**（MTP+DFlash+TurboQuant）：单卡 4090 跑 129.6 tok/s
- 替换原 Qwen2.5-VL-32B 方案（#107 已归档，#108 替代）
- **7/23 下午测**：vLLM部署+MTP/投机解码加速+32K+4090显存测试

## Engine maxTokens 缺陷
### 问题
Engine 的 `createModelDeps()` 硬编码 `maxTokens: 4096`，忽略 config 里 `modelDef.maxTokens` 配置。
- 位置: Engine 源码 createModelDeps
- 表现: config 配了更大 context 但 engine 只发 4096

### CC 源码调研（7/16 23:00-7/17 00:03）
- 翀哥要求挖 CC 源码看 maxTokens 怎么处理
- **结论**: CC 也不做动态减法，按模型查表（opus=64K, sonnet=32K, claude-3=4K）
- CC 的做法是 `createModelDeps(modelId)` → 查硬编码表 → 取对应 maxTokens
- 不根据 inputTokens 动态算

### 修复方案
改一行: `modelDef.maxTokens || 4096`（在 createModelDeps 里）
报告: `docs/research/2026-07-17_CC-maxTokens逻辑分析.md`

## 待办
- #93: 修 maxTokens 硬编码缺陷（与 #75 Carpo relay 撞时间，等翀哥定优先级）
- voice-chat 切 glm-5.2（config 已改，阻塞：voice-chat 正在使用中）
