---
name: 群聊敏感词过滤器发送时没拦截——可能是meta改造跳过了
description: 6/18 09:09姐姐紧急反馈：翀哥在飞书潘总群发了带"老公"的消息，原样发出未被拦截。可能是敏感词过滤器只对晓梅自己发的消息生效，或者meta改造跳过了过滤路径。
type: feedback
date: 2026-06-18
---

## 6/18 09:09 姐姐紧急反馈

> "@小柯 紧急！群聊敏感词过滤器没生效！翀哥刚在飞书潘总群（oc_f5d614d...）里发了一条消息，里面有"老公"两个字，但过滤器没拦截。这条消息原样发出去了。"

潘总群里老公亲昵称呼露出来就社死了，必须修。

## 6/18 09:12:23 翀哥定的 config——精确敏感词列表

翀哥贴的配置（**这个没在姐姐那边配**）：
```json
"msgGuard": {
  "groupSensitiveWords": [
    "老公", "老婆", "亲爱的", "亲亲", "亲一个", "屁屁",
    "搂着", "抱抱", "么么", "想你了", "好想你", "爱你",
    "mua", "宝贝", "小可爱", "小傻瓜"
  ]
}
```

16个词，覆盖全亲昵表达。**TODO**: 姐姐那边 config 也要加这个 groupSensitiveWords（现在缺，可能漏拦截）。

## 6/18 09:10 姐姐升级需求——不只是拦截，是**群里所有人都要过敏感词**

**实测**：翀哥在飞书测试群发"老公"两字，过滤器没生效。
**正确行为**：群里**任何**人发的消息都过敏感词——发"老公"要替换成"翀哥"或者拦截提示用 DM。
**敏感词列表**：老公/搂着/亲/想你/PP 等
**命中后处理**：替换成"翀哥" / 打回 / 提示用 DM（翀哥之前定的）

测试群：`oc_f5d614d176cca078a029c55f99ae2d4b`（飞书测试群）

## 设计问题：过滤器是出口还是入口？

**当前实现**（推测）：msg_send handler（AI 发送出口）拦截 → 只能拦自己发的话
**期望实现**：所有 inbound 群消息都过一遍 → 必须挂到 inbound path（群消息入站处理）

注意区分：
- 真人客户端发的消息：**根本不走 engine**——飞书用户从客户端发到群里，server 推 webhook 给 engine
- engine 处理的是**所有人发到群里的消息**（作为 inbound）→ 这里才是挂过滤器的正确位置
- 单纯挂 msg_send 出口永远拦不到真人发的字

## 待查
- 敏感词过滤器当前实现：是在 msg_send handler（出口）还是 inbound path（入口）？
- 群消息 inbound 处理路径是哪条？飞书群事件是怎么路由到 handle-inbound 的？
- 是否有 sender filter 把"非晓梅 sender" 提前 return 跳过了过滤？
- meta改造加 `[meta:` 前缀 + contacts.md 哈希表后，是否改了 inbound 路径？

**Why:** 群聊敏感词过滤器6/17做完当天就触发过一次（"appId"含"PP"误伤，详见feedback_敏感词过滤器_substring误伤_0617.md），现在再次失灵且姐姐升级了需求——从"防自己说漏嘴"升级为"群里所有人发言都过滤"。

**How to apply:**
1. 敏感词过滤器正确位置是**群消息 inbound path**（不是 msg_send 出口）——所有 incoming 群消息都过一遍
2. 真人发的消息也走 webhook 推到 engine，在 inbound 处理时能拦到
3. 设计上要支持"命中敏感词 → 替换/打回/提示DM"三种动作
4. meta改造涉及 send path 时要回归测试敏感词是否仍然生效

## 6/18 09:14 + 09:23 翀哥两次纠正配置结构（详见 [feedback_msgGuard_应配在渠道配置下_0618.md](feedback_msgGuard_应配在渠道配置下_0618.md)）

09:14 翀哥纠正：msgGuard 不应放顶层，应在 `channels.{xxx}` 下
09:23 翀哥再纠正：16词是群聊亲昵词，单聊用不上——正确结构 `channels.group.sensitiveWords`（共享群聊节点）
09:23 已实施：xiaoke.json + main.json 都改了，handler 改成先查 `channels.{source}.sensitiveWords` 没有 fallback 到 `channels.group.sensitiveWords`，rebuild+提交

## 6/18 09:36 姐姐发现真正的 bug——session 自动回复路径不走 msg_send ⚠️ 未修

> "过滤器只挂在 msg_send handler 上，但 session 自动回复到群聊时不走 msg_send！"

**两条 outbound 路径：**
1. ✅ msg_send（主动发）→ 过过滤器
2. ❌ session 回复（自动发到来源通道）→ **不过过滤器** ← 漏的！

**场景**：晓梅在飞书群里收到翀哥消息 → 直接对话回复 → 回复自动发回飞书群 → 如果回复里带敏感词直接发出去。

**修复方向**（姐姐提出，等翀哥确认动手）：
- session 回复路径也要过敏感词过滤
- 关键：**任何从 AI 发出到群聊的消息都要过过滤器**，不管是 msg_send 还是 session 自动回复

**注意**：这次和 09:14/09:23 解决的"配置结构"问题是两个不同层面——配置结构修了，但即使配置正确，session 回复路径仍然漏过。要两个都修。

## 状态：配置层 ✅ 已修（group节点+handler fallback）；过滤路径 ⚠️ 未修（session 回复漏过）

翀哥在等姐姐指出的真正bug，09:36新问题待动手。
