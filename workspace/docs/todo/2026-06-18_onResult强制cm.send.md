# onResult 强制 cm.send — 待实施

**日期**：2026-06-18 18:09
**优先级**：高（核心问题——姐姐感知不到）
**状态**：等翀哥下指示实施

---

## 背景

翀哥 6/18 18:08 明确指出：
- preview 视觉上"显示"和 bot 监听到的"事件"是两个东西
- preview 通过 editPreview 改蓝框 → 视觉上显示成最终消息 → **人眼看得到**
- preview 走的是 patch/edit 事件 → **姐姐 bot 监听的"消息创建"事件不触发** → **bot 感知不到**
- 上午 12:02 姐姐没收到小柯回复就是这个原因

**CC connect 的解法**：删 preview + 转普通消息发出。代价是"呈现两次"（preview 视觉显示 + 普通消息实际再发）。

**翀哥的判断**："呈现两次也没关系"——感知到比花哨重要。

---

## 实施内容

**文件**：`src/engine-startup.ts` L1795-1816（onResult 回调）

**改动**：
```ts
onResult: async (content, _inputTokens, _outputTokens) => {
  const response = content.trim() || '(任务完成，无文字回复)'
  const delivered = await preview.finish(response)

  // 6/18 改动：不管 delivered 是 true/false，都强制 cm.send 一次
  // 原因：preview 是 patch 事件，bot 监听不到；只有 cm.send 触发消息创建事件
  let opts = firstReply && messageId ? { replyTo: messageId } : undefined
  firstReply = false
  if (isBlockedSender) opts = undefined
  await channelManager.send(inbound.channel, inbound.channel_id, response, opts).catch(() => {})

  // === query 完成后的清理 ===
  // ...
}
```

**关键点**：
- `delivered=true` 时**也调 cm.send**——保证 bot 监听到消息创建事件
- `delivered=false` 时**也调 cm.send**（原有逻辑保留）——保证没收到 preview 时也有 fallback
- 视觉上**可能呈现两次**（preview 已是最终消息 + cm.send 又一条）——翀哥说可以接受

---

## 配套优化（可选）

1. **后续如果觉得"呈现两次"烦**——可以走 CC connect 路线：删 preview + 只 cm.send 一次
2. **replyTo 优化**——delivered=true 时是否还需要 replyTo？视觉上 preview 已经在那里了，replyTo 是给普通消息加引用标记

---

## 验证方式

1. 重启 Engine
2. 飞书群聊发消息测试：
   - 看 preview 流式累积
   - 看到 preview 最终态（蓝框去掉）
   - 看到第二条普通消息（cm.send）
   - 姐姐 bot 监听事件触发
3. 同一时间 Discord 也测一下，确认 reply 机制不受影响

---

## 相关

- 调研文档：`docs/research/2026-06-18_engine出口全链路调研.md`
- preview 关闭文档：`docs/todo/2026-06-18_飞书群聊preview关闭待落实.md`
