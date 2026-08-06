---
name: vision修了1ddc255 bug 但主模型多调exec浪费token
description: vision flow修了，但主LLM拿到vision描述后又调exec去验证，等于多此一举
type: feedback
---

## 事件
2026-06-19 修 vision bug 时（6/18 1ddc255 commit 改坏了 image block 注入路径）

## 关键错误
翀哥发了图后，vision 模型正常发了 221 chars 描述（feishu:send），但我（主 LLM）拿到这个描述后，又调 exec 去看那张图——等于绕了一圈。

翀哥 8:31 直接说："exec是你调的你搞了这么多分析"——话很短但意思是：你自己调的 exec 浪费 token，还以为 vision 不工作。

## 教训
1. **先看 log 再下结论**——vision 发了 221 chars，我应该马上知道 vision 是工作的
2. **别瞎验证**——vision 已经描述了，主模型不需要再去看图验证（除非 vision 描述模糊）
3. **保持简单**——翀哥 5/14 说过："保持简单别越挖越深"，我分析越来越复杂，自己都搞混了

## 修好的内容
1. handle-query.ts L265 改成 content blocks `[{type:'text', text: formattedText}, ...imageBlocks]`
   - 1ddc255 commit 之前是 `msg.user(text)`（含 image），1ddc255 改成了 `msg.user(formatWithMeta(textForApi))`（过滤 image）
   - 这次修回来了——image data 真的发给 API
2. engine-startup.ts 加过 toolOverride: []，后来翀哥说"别乱搞"回滚了

## 下次发图要做的事
- vision 发了 N chars 描述 → 直接用 vision 描述，不要再调 exec/my_eyes
- 只有 vision 描述模糊或空时才考虑 fallback