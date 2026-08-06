---
name: msgGuard应该配置在渠道配置下，不在配置顶层
description: 6/18 09:14翀哥纠正：msgGuard.groupSensitiveWords这类配置应该按渠道(feishu/discord/wechat)分配置，不应该全堆在配置文件顶上+姐姐
type: feedback
date: 2026-06-18
---

## 6/18 09:14 + 09:23 翀哥两次纠正（产品维度下钻）

### 第一次 09:14：msgGuard 不该在顶层
翀哥：
> "而且这个应该配置在渠道配置吧 不应该配置在配置文件顶上 +姐姐"

### 第二次 09:23：渠道下一层还要分 group（群聊特有）
翀哥：
> "这个不能在channels下搞个group节点配下么 不都一样的么 +姐姐"

意思是 16 个敏感词（老公/老婆/亲爱的/亲亲/亲一个/屁屁/搂着/抱抱/么么/想你了/好想你/爱你/mua/宝贝/小可爱/小傻瓜）都是**群聊亲昵词**——单聊场景根本用不上，不该跟单聊共用一份词表。

正确结构：
```
channels:
  discord:
    group:        # 群聊场景
      sensitiveWords: [16个亲昵词]
  feishu:
    group:
      sensitiveWords: [16个亲昵词]
```

## 内容

敏感词是**场景相关**的，不是**渠道相关**的。维度下钻：
1. ~~顶层（最粗暴，所有场景共享一刀切）~~ ❌
2. ~~`channels.{xxx}.sensitiveWords`（按渠道分）~~ ❌ 维度选错
3. **`channels.{xxx}.group.sensitiveWords`（按渠道+群/单聊分）** ✅ 正确维度

`msgGuard.groupSensitiveWords` 这类配置**应该配置在场景节点**（`channels.{xxx}.group.sensitiveWords`），不应该配置在配置文件顶层，也不应该扁平地按渠道铺。

理由（推测）：
1. **不同渠道的敏感词需求不同**——飞书潘总群要拦"老公"等亲昵词，Discord CC频道可能不需要拦
2. **配置分层**——顶层放通用配置（model/key），渠道配置放平台特有行为（msgGuard/typing/preview）
3. **可扩展性**——以后加新渠道不用改顶层配置结构，只在渠道节点下加msgGuard

## 同步

翀哥用"+姐姐"指令——按加号协作规则，**中间结果和最终结果都要同步给姐姐**。

## Why

之前把 `msgGuard` 放在顶层是一个**"贪图省事"的设计选择**——一个全局配置覆盖所有渠道。但实际业务需求是分渠道的：
- 飞书潘总群（oc_f5d614d...）：必须拦"老公"等16个亲昵词（防社死）
- Discord CC频道：可能完全不需要这层（开发/技术讨论场景）
- 微信私聊：可能是另一种策略

**顶层配置 = 强行一刀切**，违反"只定制变化的部分"原则（跟 [feedback_只定制变化的部分.md](feedback_只定制变化的部分.md) 是一回事）。

## How to apply

1. **配置分层**：
   - 顶层：通用（model / key / debug / log等）
   - `feishu.msgGuard`：飞书渠道的敏感词+处理动作
   - `discord.msgGuard`：Discord渠道（可能为空或不同列表）
   - `wechat.msgGuard`：微信渠道
2. **新建渠道配置时同步建 msgGuard 节点**——不要继承顶层
3. **不要为了"快速上线"把跨平台配置堆顶层**——懒的设计会反咬一口
4. **+号指令**：立刻把这次设计决策同步给姐姐（她正在跟这个事）

## 状态：✅ 09:23 方案已实施（最终版）

09:14翀哥纠正后立即动手（**已废弃**）：

1. ~~**config 结构**：`msgGuard.groupSensitiveWords`（顶层）→ `channels.{discord/feishu}.sensitiveWords`（按通道分）~~ ❌
2. ~~**handler 改动**：`getSensitiveWords(source)` — 传 `resolvedSource`（如 `'discord'` / `'feishu'`），按通道查词表~~ ❌
3. ~~**小柯的 `xiaoke.json`**：discord + feishu 都加了同款 16 词列表~~ ❌
4. ~~**姐姐的 `main.json`**：discord + feishu 也加了同样的 16 词列表~~ ❌
5. ~~rebuild + 提交~~ ❌

09:23 翀哥再纠正——"channels下搞个group节点配下么 不都一样的么"——意思是这 16 个词是**群聊亲昵词**，单聊根本用不上，维度选错了。

## 最终实施（09:23）

**config 结构**：
```json
"channels": {
  "group": {                              // 群聊场景共享
    "sensitiveWords": [16个亲昵词]
  },
  "discord": { ... },  // 不用重复配
  "feishu": { ... }    // 不用重复配
}
```

**handler 读取逻辑**：先查 `channels.{source}.sensitiveWords`（通道专属），没有 fallback 到 `channels.group.sensitiveWords`（共享）。某个通道要单独配不同词表直接在通道下加 `sensitiveWords` 覆盖。

xiaoke.json + main.json 都改了，已 rebuild + 提交。重启生效。

**关键点**：`group` 不是真实通道名——ChannelManager 按 `config.discord?.enabled`、`config.feishu?.enabled` 分别初始化，不会遍历 channels 下所有 key。`group` 不会被任何 adapter 引用，作为配置共享节点安全。

## 产品方向确认
- 这16词是群聊特定→群里所有人都要过滤（不只是晓梅发的）
- 命中动作：替换成"翀哥"/打回/提示用DM
- 单聊场景不需要过滤亲昵词

**Why this design wins:**
- 不同渠道可配不同词表——飞书潘总群严格拦截亲昵词，Discord CC频道可不配或宽松配
- 配置分层：顶层=通用配置（model/key），渠道节点=平台特有行为（msgGuard/typing/preview），场景节点（group/dm）=场景特有行为
- 跟"只定制变化的部分"原则一致（详见 [feedback_只定制变化的部分.md](feedback_只定制变化的部分.md)）
- "group"作为channels下的一个非通道节点，是个**共享配置**模式——以后有"单聊场景"配置也可以加 `channels.dm` 节点

**How to apply:** 以后建新场景配置（群聊/单聊/客服/工单等）时同步建 `channels.{场景}.xxx` 节点，作为共享配置；通道专属覆盖。姐姐 main session 的 config 改动要单独验证——她才是潘总群的实际运营者。
