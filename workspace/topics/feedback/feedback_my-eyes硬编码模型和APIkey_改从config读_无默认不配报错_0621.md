---
name: my_eyes硬编码改从tools配置读，走provider不自己fetch
description: 6/21翀哥发现my_eyes.ts写死qwen3.5-flash+API_KEY，最终方案：tools.my_eyes.model配provider引用→ctx.provider.streamChat调，不自己fetch/拼URL
type: feedback
---

## 事件
2026-06-21 13:13 翀哥发现 my-eyes-handler.ts 写死了 qwen3.5-flash 模型 ID 和 API KEY。

## 最终方案（3轮迭代后）
1. config `tools.my_eyes.model: "dashscope/qwen3.5-flash"` — 指向 provider 引用
2. dashscope provider 的 models 里声明 qwen3.5-flash（让 provider 知道有这个模型）
3. my-eyes 用 `ctx.provider.streamChat()` 调，不自己 fetch/拼 URL
4. 删掉死配置 `tools.vision: true`
5. toolContext 缺 config，需加进 HandleQueryDeps

**Why:** 
- 自己 fetch 拼 endpoint 换 provider（如 M3）就挂，走 provider 换模型只改一行
- endpoint 不该代码里拼，provider 内部统一拼 `/chat/completions`
- config 顶层 vision 字段语义混（engine visionModel/tools vision/capabilities vision）

**How to apply:**
1. 工具需要 LLM 调用时，先看 ctx.provider 能不能直接用
2. 工具自己的配置放 `tools.{toolName}.xxx` 命名空间下
3. model 值用 `providerId/modelId` 格式，指向 provider 配置

## 踩坑记录
- ❌ 第一版在 config 顶层加 visionApiKey/visionEndpoint — 翀哥："vision意思太多了"
- ❌ 想搞 myEyes provider 独立 — 翀哥："这样多乱"
- ❌ endpoint 代码拼 baseUrl + /chat/completions — 翀哥："这些应该是配置"
- ❌ dashscope provider models 里没配 qwen3.5-flash — 翀哥："你这provider里都没配啊"
- ❌ toolContext 缺 config 字段 — deps 没传 config，tool 拿不到 tools 配置
  - 修法：HandleQueryDeps 加 `config?: any`，engine-startup deps/visionDeps 填上
- ✅ 最终：tools.{name}.model → provider 引用 → ctx.provider.streamChat

## 翀哥金句
"你这个superpower不要确认环节么？听我说，跟我确认了你再干。"
