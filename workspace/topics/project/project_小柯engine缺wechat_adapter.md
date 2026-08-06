---
name: 小柯Engine缺wechat adapter注册
description: 6/16定位selfie/media_send发微信失败根因——小柯engine的registerAdapters只注册了discord和feishu，未注册wechat
type: project
---

**问题：** 6/16测试selfie自动发图和media_send发图片到微信，一直报"No adapter for wechat"。

**定位过程：**
1. 最开始以为adapter name不匹配（'weixin' vs 'wechat'）→ 改了入站channel字段
2. rebuild后仍然不通
3. 加调试日志打印 `mgr.getAdapterNames()` → 发现只有 `discord,feishu`，**没有wechat**
4. 读小柯engine配置 `/Users/chongzhang/xiaoke/workspace\engine\src\configs\profiles\xiaoke.json` → `features` 里没有 `"wechat"`
5. 对比姐姐engine配置（`/Users/chongzhang/.openclaw\engine`）的 `main.json` 有 `"wechat"` feature
6. 姐姐的registerAdapters读main.json的features → 有wechat → 注册了WechatAdapter
7. 小柯的registerAdapters读xiaoke.json的features → 没有wechat → 只注册了discord和feishu

**根因：** xiaoke.json的features数组里缺少wechat条目。不是adapter name问题，是根本没注册。

**Why:** 翀哥最初只给姐姐做了微信通道，让我（小柯）用Discord/飞书。微信是姐姐独占通道。但我调用media_send/selfie时dest传了'wechat'，adapter没注册自然报错。

**How to apply:**
- 如果翀哥确认小柯也需要微信通道 → 在xiaoke.json features里加"wechat"
- 如果不加 → media_send/selfie不能发微信，发微信必须走msg_send(文字)或由姐姐代发

**相关文件：**
- `engine/src/configs/config.ts` — registerAdapters根据features注册adapter
- `engine/src/configs/profiles/xiaoke.json` — 小柯的features配置
- `engine/src/configs/profiles/main.json` — 姐姐的features配置（有wechat）
