---
name: 微信typing indicator缺失与实现
description: 翀哥6/13发现微信通道没有显示"对方正在输入..."，我后来加上了startTyping/stopTyping实现
type: feedback
---

## 反馈内容

翀哥6/13微信测试后说："我发现这里面你没有实现那个typing indicator, 就是比如我跟你说话，它从来不显示你正在输入"

我之前翻录微信adapter时只翻了收/发消息、媒体上下传的基础功能，startTyping/stopTyping/pauseTyping/resumeTyping四个公开方法没有实现（虽然sendTyping是有的）。跟Discord的对比——Discord有sendTyping + 8秒循环，微信没有。

修复：在wechat.ts加了四个公开方法，内部调sendTyping（iLink API `ilink/bot/sendtyping`），8秒间隔循环发，跟Discord一致的逻辑。

**⚠️ 实际效果（6/13翀哥测试后）：** typing 请求被 iLink rate limit 了（`ret=-2`），微信上没有看到"对方正在输入..."。而且在测试过程中连接不稳定，翀哥反馈"发着这个就断了，然后你总是报那个微信的有一个好像是，Connection error"。typing indicator 功能代码已实现但 iLink API 侧限流 + 连接不稳定，实际体验未达到预期。

**Why:** iLink API 有 sendtyping 端点（`ilink/bot/sendtyping`），Hermes weixin.py 也实现了，但翻录时漏掉了。翀哥在实际使用时发现没有"对方正在输入..."的体验，直接指出来。加完后测试发现 iLink 对 typing 请求有频率限制且长轮询连接不稳定。

**后续（6/13 08:15-09:00）—— 最终解决方案 ✅**
- **2s节流不够** — 对 send 加了 2s 全局节流（两次 send 之间至少间隔 2 秒），但 iLink rate limit（`ret=-2`）仍然持续。翀哥问"这个是hermes的逻辑么"——参考Hermes的退避策略（默认retry_delay=1.5s，退避系数3倍=4.5s）。
- **display精简思维转变** — 翀哥认为"我觉得应该关  thinking和preview可以留着  但要受外面全局的控制"。最终决策：❌关toolUse/toolResult display，✅thinking/preview保留受全局控制。
- **3s节流仅wechat.ts** — 翀哥确认"3秒这个只是加在wechat.ts里的吧"，各平台独立。
- **typing不生效根因查明并修复** — 之前以为只是iLink rate limit导致typing没显示，实际上typing实现有bug：
  1. 参数名错了：`to_user_id` → `ilink_user_id`，`typing_status` → `status`
  2. 缺 `typing_ticket`：需要先调 `getconfig` 拿 ticket（缓存10分钟），再调 `sendtyping` 时带上
  3. 修复后编译零错误，等待翀哥重启验证
- **✅ typing已生效（6/13 09:00验证）** — 翀哥重启后测试"看看北京的天气"，确认"这回有太平indicator了"。但发现"但是没有结束"——stopTyping没有正确停止。
- **✅ stopTyping已修好（6/13 09:XX最终验证）** — 翀哥再次重启后测试，说"也有结束"。根因：stopTyping只清了本地timer但没发 `status=2` 给iLink API。修复：stopTyping发 `ilink/bot/sendtyping?ilink_user_id=xxx&typing_ticket=xxx&status=2`。编译零错误。
- **⚠️ 仍有工具调用发出 → 已修复 ✅** — 翀哥反馈"但是还是有工具调用"。根因：engine-startup的onToolUse/onToolResult回调未检查adapter能力，直接通过channelManager.send发消息。修法：给ChannelAdapter加`suppressToolDisplay`属性，wechat.ts返回true，engine-startup在发送前检查。已实现并最终验证通过（翀哥重启后说"看看 ok 了么"，日志确认toolUse不再发到微信）。
- **总结最终方案：** 全部验证通过 ✅：①关toolUse/toolResult display ②wechat.ts 3秒全局发送节流 ③rate limit退避5秒 ④typing参数修复（`ilink_user_id` + `typing_ticket` + `status`） ⑤stopTyping发status=2 ⑥suppressToolDisplay方案（微信不显示工具消息）
