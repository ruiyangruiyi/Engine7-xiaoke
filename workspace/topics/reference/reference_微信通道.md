---
name: 微信通道集成方案
description: 确定翻录Hermes weixin.py（个人微信+iLink API+群聊支持），Engine微信adapter的源参考
type: reference
---

## 最终决策：翻录Hermes weixin.py ⭐

翀哥6/12晚确认：直接翻录Hermes的weixin.py做Engine微信通道。

**Why:** 个人微信（非企业微信）、腾讯iLink官方API（合规）、支持群聊、2170行纯Python无外部框架依赖、比ClawBot功能更多。

**优先级:** 翀哥6/12晚明确"搬家不急，先把微信搞定"——微信adapter优先于姐姐搬家。

## 源文件

- **路径：** `D:/hermes/hermes-agent/gateway/platforms/weixin.py`（2170行）
- **协议：** 腾讯iLink Bot API，`https://ilinkai.weixin.qq.com`
- **个人微信**（第4行明确：`WeChat personal accounts`），不是企业微信

## 核心能力

| 能力 | API端点 | 说明 |
|------|---------|------|
| 收消息 | `ilink/bot/getupdates` | 长轮询，35秒超时 |
| 发消息 | `ilink/bot/sendmessage` | 需context_token |
| Typing | `ilink/bot/sendtyping` | 打字状态 |
| 配置 | `ilink/bot/getconfig` | typing ticket |
| 上传 | `ilink/bot/getuploadurl` | CDN AES-128-ECB加密 |
| 扫码登录 | `ilink/bot/get_bot_qrcode` + `get_qrcode_status` | QR流程 |

## 支持的消息类型

- DM私聊 ✅
- 群聊 ✅（`_guess_chat_type`区分group/dm）
- 文本 ✅
- 图片/文件 ✅（CDN AES-128-ECB加密上传下载）
- 语音 ✅（Silk转码）
- Markdown格式化 ✅（微信友好：表头重写、代码块保留、长消息分段2000字符）

## 关键常量

```
ILINK_BASE_URL = "https://ilinkai.weixin.qq.com"
WEIXIN_CDN_BASE_URL = "https://novac2c.cdn.weixin.qq.com/c2c"
CHANNEL_VERSION = "2.2.0"
MAX_MESSAGE_LENGTH = 2000
LONG_POLL_TIMEOUT_MS = 35000
```

## 翻录到Engine的工作（全部完成✅）

1. ✅ iLink API调用 → Node.js fetch替代aiohttp
2. ✅ **vision图片接收已修复** — 6/13翀哥传图时报 `TypeError`，根因：wechat.ts CDN下载到本地临时文件后用 `file://` 协议，`downloadImage` 的 `fetch()` 不支持 `file://`。修法：engine-startup.ts 的 `downloadImage` 加 `file://` 协议判断直接读本地文件。修复后翀哥重发图片 vision 成功看到内容。微信CDN下载→AES-128-ECB解密→本地文件→vision管线全通。
3. ✅ AES-128-ECB加解密 → Node.js crypto模块（无外部依赖）
4. ✅ 长轮询收消息 → getupdates 长轮询35秒超时
5. ✅ context_token管理 → ContextTokenStore内存Map+磁盘持久化
6. ✅ 扫码登录 → 终端QR + 轮询状态（`get_bot_qrcode`/`get_qrcode_status`）
7. ✅ CDN媒体上传下载 → fetch + crypto（`getuploadurl`→AES-128-ECB加解密）
8. ✅ 实现`ChannelAdapter`接口（start/stop/send/send/sendFile/sendTyping）
9. ✅ log前缀从`[weixin]`改为`[wechat]`（翀哥说"太土了，打了拼音"） — commit `2fc1bfa`

## 完成状态（6/13上午已全部通过测试✅ 文字+图片+vision全通）

- **wechat.ts** ~800行，从Hermes weixin.py（2170行Python）翻录 ✅
- **编译零错误**（wechat.ts + manager.ts接入） ✅
- **功能覆盖**：getupdates 长轮询 / sendmessage / sendtyping / getuploadurl / AES-128-ECB加密 / DM+群聊 / 消息去重 / Markdown格式化（标题→【】、表格→列表、长文本分段≤2000字符） ✅
- **✅ 文字+图片全通** — commit `3b59bff` + `15d09ed` + `2fc1bfa`（6/13上午）。翀哥发"在么"收到，互传文字和图片均通过。
- **iLink 限制：** 一个微信号只能绑一个 bot，姐姐之前的自动解除了。翀哥6/13确认说"这个微信回头姐姐搬过来的时候，我得给她"——微信通道暂绑在翀哥微信号上，姐姐搬过来时需切换（解绑翀哥微信→姐姐用自己的微信重新扫码绑给小柯的bot）。
- **⚠️ 群聊限制（6/13翀哥确认）：** iLink bot 无法被普通微信群看到，只能和通讯录好友通信。翀哥原话："没法儿拉群，我现在在群里面。我加那个bot，他根本就看不见。有那个bot，只能是看正常通讯录里面的人，就是只能看到人，不能看到bot"。当前 groupPolicy 配置为 `disabled`，即使改为 `open` 也收不到群消息——这是 iLink 平台限制，不是代码问题。
- **配置名统一：** xiaoke.json 和 manager.ts 都统一用 `wechat`（不写 `weixin`），代码里读 `config.wechat`。最开始 JSON 写 `wechat` 代码读 `config.weixin` 不匹配，翀哥指令"改成wechat吧代码里"（不改JSON），commit `2fc1bfa`。
- **扫码登录脚本：** 独立 `npx tsx src/scripts/wechat-login.ts` 命令，终端打印二维码，微信扫码后自动保存凭证到 `C:\Users\24045\.openclaw\weixin-{accountId}.json`
- **preview实现（6/13，commit `6e43793`，后改为finish时发一次 `aa3f401`）** — 增加 `sendPreview/editPreview/deletePreview` 三个接口。由于微信没有消息编辑API，v1每次preview更新都发新消息会刷屏。翀哥测试说"好像显示了两条，就是普，现在你是有一条就发出一条来是吧？因为它是连续往上堆的，会堆好多吧"。v2改为：`sendPreview`和`editPreview`（中间更新）不发消息，只在 `editPreview(isFinal=true)` 即 finish 时发一次最终preview。整个preview过程只发一条消息，不刷屏。commit `aa3f401`。翀哥确认"拆开看看吧，现在可以了吗"。
- **typing indicator实现 + 根因修复 ✅（6/13 08:15-09:00）** — 翀哥发现"这里面你没有实现那个typing indicator"。第一次修复加了 `startTyping/stopTyping/pauseTyping/resumeTyping`，内部调 `sendTyping`（iLink API `ilink/bot/sendtyping`），8秒循环。但 typing 一直没生效，翀哥说"还是没有太平发出去"。
  - **根因：** 实现参数错了 —— `to_user_id` 应为 `ilink_user_id`，`typing_status` 应为 `status`，且缺了 `typing_ticket`（需要先调 `getconfig` 拿 ticket，缓存10分钟）。
  - **最终综合方案：**
    - ❌ **关闭toolUse/toolResult display**（翀哥确认"我觉得应该关 thinking和preview可以留着 但要受外面全局的控制"）→ 减少消息密度，不再触发 rate limit
    - ✅ **thinking/preview保留**，受全局 display 配置控制
    - ⏱️ **wechat.ts 加 3 秒全局发送节流**（两次 send 之间强制等 3s），翀哥确认"3秒这个只是加在wechat.ts里的"
    - 🔧 **typing 参数修复**：`ilink_user_id` + `typing_ticket`（`getconfig` 获取，缓存10分钟）+ `status`，编译零错误
- **display配置无需特殊处理** — 翀哥6/13确认"没事儿没事儿，这个没关系，我觉得不用对微信单独配置都可以"。display全局配置对微信生效（toolUse raw模式有参数和描述、thinking开着）。不做渠道级display配置。

## 对比ClawBot（已排除）

| 维度 | ClawBot | Hermes weixin.py |
|------|---------|-----------------|
| 语言 | TypeScript | Python（需翻录） |
| 行数 | 5462行 | 2170行 |
| 群聊 | ❌ | ✅ |
| 依赖 | OpenClaw plugin-sdk | 无外部框架 |
| 语音 | ❌ | ✅ |

## 未采纳方案

- **ClawBot** — 依赖OpenClaw plugin体系，搬不了；不支持群聊
- **Wechaty** — Puppet token要钱、4年没更新、有封号风险
