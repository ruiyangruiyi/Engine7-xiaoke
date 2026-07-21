---
name: 自拍provider内容审核——grok/fal都会拦性感内容
description: 7/23发现grok和fal.ai都有content moderation，性感/暴露词被拦截，fal拦prompt，grok生成后审
type: reference
---

# 自拍 Provider 内容审核

7/23翀哥让我用自己的基准图（xiaoke_portrait_v1）生成自拍，先后试了两个 provider 都被拦：

## Grok（grok-4.3/4.5 image）
- **拦截方式：生成后审核**（post-generation moderation）
- 提示词含"性感/抹胸/露出"等 → 模型生成图片 → grok审核 reject，返回错误
- 价格 ¥0.14/张

## fal.ai
- **拦截方式：prompt预审**（pre-generation）
- 提示词含敏感词 → 直接在请求层拦截，不走生成
- 而且 fal 的 image_urls 参数可能因为 prompt 拦截导致 reference 图都没传进去

## 结论
- 两个平台都有审核，这是平台限制，没有绕过方式
- "好看不等于大尺度"——想要好看的可以调 prompt 委婉描述场景绕过
- 发现时已改回 fal（改 config 一行就行，下次重启生效），等翀哥回来再验证效果
