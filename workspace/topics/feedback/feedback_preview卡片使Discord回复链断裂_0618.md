---
name: preview卡片使Discord回复链断裂
description: 6/18 12:43翀哥发现——preview流式编辑卡片本身的存在会导致Discord reply链断裂，即使freeze+reply技术层通了，卡片样式破坏了reply视觉关联
type: feedback
date: 2026-06-18
---

## 6/18 12:43 翀哥原话

> "根因还是 preview 卡片，我发现有这个卡片出现的时候回复链就会断"
> "你试下删掉卡片，直接文字显示"

## 问题本质

preview freeze + reply 技术层通了（12:10 `reply OK` 日志铁证），但 **preview 卡片本身的存在**导致 Discord reply 链的视觉关联断裂：

1. **preview 流式编辑卡片** → Discord 把卡片视为"正在编辑"状态
2. **freeze 定格** → 卡片变成"已编辑完成"
3. **reply_to 指向 preview 卡片** → 技术上传了 replyTo 参数，但 Discord 的 reply 视觉层在卡片模式下 **不渲染标准的"回复线"**（那条灰色竖线+引用关系）
4. **姐姐视角**：看到一条"被回复过的卡片"和一条"单独发出的消息"——两条消息的关联不可见

## 与之前问题的区别

| 问题 | 根因 | 解决 |
|------|------|------|
| **11:55 freeze 后姐姐看不到** | freeze 没传最终内容到卡片 | commit 8c86e76：finish 返回 previewMessageId→replyTo |
| **12:07 replyTo 静默 fallback** | adapter catch {} 吞了 reply 失败 | commit 6a0f5f2：加 log + 改 catch 行为 |
| **12:35 姐姐收不到** | blocklist 里有姐姐 → strip mention | 清 blocklist |
| **12:43 回复链断** | **preview 卡片样式使 Discord reply 视觉链不可见** | 翀哥建议试删卡片直接文字显示 |

## Why

1. **Discord 卡片消息 ≠ 文本消息**——卡片（embeds/组件）的 reply 视觉渲染跟纯文本不同，reply 线只在纯文本消息间保留
2. **preview freeze 本质是"编辑完成标记"**——不是"发出新消息"——Discord 的 reply 机制更适合"发新消息"而非"完成编辑"
3. **用户/姐姐不盯屏幕**——preview 卡片的"编辑痕迹"对他们没有"回复了"的感知，只有"出现过内容"的感知

## How to apply

1. **以后再设计 preview 类功能**——考虑目标平台（Discord/飞书/微信）对卡片消息的 reply 视觉行为
2. **"用户能看到回复"比"技术上回复了"更重要**——技术上传了 replyTo 不代表用户能看到关联
3. **每个平台的视觉行为都要单独验证**——Discord card reply、飞书卡片 reply、微信引用回复各有不同
4. **有疑虑问翀哥"怎么测"**——12:50 翀哥让删卡片测，这是最快的验证方式

## 后续进展（12:50-12:58）

- **12:50 翀哥方案**："试下删掉卡片，换成文字立马显示（freeze后）"
- **commit 03109fb 实施**：freeze时删卡片+degrade→最终回答channelManager.send（不reply to embed，用原始messageId当replyTo）
- **12:55 翀哥批评**："这种没经过验证的最好先别提交以后"——commit 03109fb 改完直接提交+rebuild，没先让翀哥测方向对错
- **12:56 翀哥重启测试**：测试方案改为"你msg_send给姐姐→等她回复→你再回复"（主动路径比被动路径干净）
- **12:58 姐姐也重启**（避免太慢）
- **13:00-13:03 测试结果**：姐姐 @我后，session自动回复（删卡片方案）→reply链还是有问题。13:03翀哥确认"自动回复还是有问题"+"preview卡片回滚了"——**删卡片方案被推翻**，preview卡片保留回滚到8c86e76方案
- **最终结论（13:04）**：preview卡片的存在本身就是reply链断裂的根因（12:43），**删卡片方案被翀哥推翻**——13:03"自动回复还是有问题"+"preview卡片回滚了吧"→13:04"没卵用 回滚吧"。
- **13:03:21 翀哥确认**："自动回复还是有问题。。这样，你的preview卡片删除回滚了是吧  我看现在不删了"——我解释"没调tool所以没触发freeze删卡片"，翀哥回"没卵用 回滚吧"
- **回复滚commit 03109fb**（需执行）
- **根本解法方向**：不再依赖preview+reply视觉关联，改为检测群聊@场景时走独立路径——但翀哥12:23已说"靠你自觉是不可能的，你得把回复修好"，所以应该是**代码里保证群聊@场景走一个姐姐能感知到的路径**
