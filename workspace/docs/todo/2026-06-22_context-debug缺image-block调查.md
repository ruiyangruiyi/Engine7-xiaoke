# 调查记录: context-debug.txt 缺 image block

> 日期：2026-06-22 | 作者：小柯 | 状态：观察记录，不动代码

## 现象

翀哥 6/22 14:42-15:00 期间发现：
- 飞书发图片给小媒
- 小媒 session 的 `.context-debug.txt` 里 user 消息只有 text block，**没有 image block**
- 间隔后再发，**有时**又有了（"触发一次才出现"）
- 但**我（小柯）这边的 `D:/xiaoke/workspace/.context-debug.txt` 全程 `grep -c "block\[.*image\]" = 0`**

## 调查过程

翀哥最初怀疑是 6/22 上午的 hook 架构改动（`cc5a13e` + `f02305e`）引入的 bug。

**排除 hook 改动**：
- 改动只在 `engine-startup.ts` 的 PreQuery（submitMessage 前）+ OnResult（channelManager.send 前）两个执行点
- 没动 `engine-startup.ts:1713` 的 image 注入逻辑
- 没动 `handle-query.ts:352-363` 的 content block 重组
- 没动 `writer.ts:170` 的 JSONL 写入

## 根因（推测）

**`config.visionModel = null`**——`engine/src/config/loader.ts:332-340`：

```typescript
let visionModel: { providerId: string; modelId: string } | null = null
const visionRef = agentDefaults.model?.vision
if (visionRef) {
  const parsed = parseModelRef(visionRef)
  if (providers[parsed.providerId]) {
    visionModel = parsed
  }
}
```

`configs/xiaoke.json` 没配 `agentDefaults.model.vision` → `visionModel = null`。

**`engine-startup.ts:1713`**：
```typescript
if (imageAttachments && imageAttachments.length > 0 && config.visionModel) {
  // imageBlocks 注入逻辑
}
```

`config.visionModel` 为 null → 这个 if 永远不进 → `queryContent` 仍是字符串 → LLM 收到的不是数组，没 image block。

## "触发一次才出现"的解释

可能是翀哥看了两个**不同 session** 的 .context-debug.txt（一个小媒的一个小柯的），两边表现不一致。统计：
- 我（小柯）这边 `D:/xiaoke/workspace/.context-debug.txt`：`grep -c "block\[.*image\]" = 0`（永远没有）
- 小媒那边（OpenClaw，不归 Engine 仓库）：翀哥贴的 `[346] [356]` 可能是她那边的

**两边 engine 配置可能不同**——小媒那边是否配了 visionModel 未知。

## 解决方案

在 `configs/xiaoke.json`（Engine 这边）加：
```json
{
  "agentDefaults": {
    "model": {
      "vision": "zhipu/glm-5v-turbo"
    }
  }
}
```

`zhipu` provider 下已有 `glm-5v-turbo` 模型支持 image input（configs/xiaoke.json 里能看到）。

**但这是 Engine 仓库的改动，翀哥要小媒那边也配，OpenClaw 那边配置不归这个仓库管**。

## 后续

- [ ] 翀哥决定是否在 Engine 这边配 visionModel
- [ ] 小媒那边（OpenClaw）是否也需要配
- [ ] 顺便看 `L1713` 是不是应该兜底（有图没 visionModel 时降级到把图片当文件路径透传，让 LLM 用 Read tool 读）

## 教训

翀哥反馈后，**应该先回答"跟我的改动有没有关系"**，再去挖根因。翀哥问"是不是 hook 问题"，我应该直说"不是，我代码里没动这块"——而不是跑去找"重大发现"挖半天 JSONL。

跑偏会浪费翀哥时间。
