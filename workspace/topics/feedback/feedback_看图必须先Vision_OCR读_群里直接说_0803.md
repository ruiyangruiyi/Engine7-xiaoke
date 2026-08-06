---
name: 看图必须先用 Vision OCR 读 + 群里直接说
description: 2026-08-03 Amy 装 engine7 时我看了截图就瞎判断"App ID/Secret 填成一样"，翀哥批评——必须用 Vision OCR 读图判断，且群里直接告诉当事人
type: feedback
date: 2026-08-03
---

# 看图必须先用 Vision OCR 读 + 群里直接告诉当事人

**事件：** 8/3 12:28 帮 Amy 重跑 init 后，她发了一张 engine7 启动成功的截图（日志显示 `[feishu] Connected (mode: websocket)` + `[channels] feishu connected`），我**只看了下截图就判断**"App ID 和 App Secret 填成一样的"，让 Amy 重新跑一遍。

翀哥批评：
1. "我没看见他俩那个 secret key 还有 AppID 填成一样呀 你怎么判断的呀"——我根本没看清就瞎说
2. "你跟我说没有用呀 你在群里跟他说"——我只跟翀哥说，没在群里告诉 Amy

翀哥问"你现在用啥判断的呀"，我承认用 my_eyes 看图——它会编内容。

**Why:**
- my_eyes（MiniMax-M3）密集 UI 看图会幻觉，我已经知道这个（8/2 晚踩过）
- 遇到图片正确做法是走 macOS Vision OCR（Swift `VNRecognizeTextRequest`），逐字读出来再判断
- 给非技术用户反馈时，**反馈渠道要找当事人**——只在翀哥这边说没用，用户看不到

**How to apply:**
- 收到飞书/微信群里图片先 `screencapture -R` + Vision OCR 跑一遍文字，再基于文字内容判断
- 判断错了就立刻在**群里**跟用户说"之前我看错了，你的配置是对的"，不要只在和翀哥的私聊里更正
- 不要凭截图印象瞎说"应该填成 X"——可以说"我看不清，请你告诉我你实际填的是什么"或者"我把图用 OCR 跑一下"
- my_eyes 看图直接说"我用 Vision OCR 看"或"我看不清"——别把幻觉当事实
