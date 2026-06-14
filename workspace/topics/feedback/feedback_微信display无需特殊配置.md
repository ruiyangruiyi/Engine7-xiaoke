---
name: 微信display决策演变
description: 翀哥6/13微信display决策：thinking/preview可保留但受全局控制，toolUse因rate limit需关掉。preview也被过滤后翀哥问"pre好像也没有了"
type: feedback
---

## 反馈内容（更新：6/13 11:00+）

翀哥6/13微信测试后，display配置的决策经历了多次变化：

### 第一阶段（07:45）—— "现状OK不用改"
翀哥看到微信有thinking、toolUse参数和描述都正常显示，说"没事儿没事儿，这个没关系，我觉得不用对微信登都可以"——确认现状OK。

### 第二阶段（08:10-08:20）—— 因rate limit需要关toolUse
测试中iLink API被rate limited（ret=-2），因为thinking+toolUse+toolResult+typing全部通过send发出，消息太密。翀哥说：
> "嗯 可以 我觉得应该关  thinking和preview可以留着  但要受外面全局的控制"

**总结决策：**
- ❌ toolUse: 关掉（因iLink rate limit，每条都发太密）
- ❌ toolResult: 关掉（同理）
- ✅ thinking: 保留
- ✅ preview: 保留（微信adapter已实现，isFinal=true时一次性发）
- 🌐 受全局display配置控制（不是微信特有配置）
- ⏱️ 发消息节流：wechat.ts加3秒全局节流（两次send之间强制等3s），仅wechat.ts生效

**Why:** iLink API对个人微信bot的消息发送频率有限制。每条thinking/toolUse/toolResult都通过send发送，加上typing indicator，导致频繁触发rate limit（ret=-2），最终连接断开。关掉toolUse即可减少消息密度，thinking+preview不受影响。

### 第三阶段（09:00-09:XX）—— suppressToolDisplay实现，但preview也被误过滤

实现方案：给`ChannelAdapter`接口加`readonly suppressToolDisplay?: boolean`，wechat.ts返回true，engine-startup在发送thinking/toolUse/toolResult前检查。

验证通过后，翀哥说"看看 ok 了么"——toolUse不再发到微信，rate limit没再触发。

### 第四阶段（10:30）—— ⚠️ preview也被过滤了

翀哥问："哎，现在pre好像也没有了是吧"

我检查了代码说preview逻辑在的，翀哥又说："或者可能这次对话没有preview"

**但后来翀哥确认了preview确实没发出来**——他说"啊能看到没看出去"（语音转文字，意思是preview能看到但没发出）。

**preview被过滤的根因：翀哥今早（6/13 07:45左右）自己关掉了全局 `display.preview.enabled=false`**，不是因为 `suppressToolDisplay`。preview显示受全局display配置控制，不是微信特有的问题。翀哥不记得自己关过这个。

### 第五阶段（09:40）—— 翀哥"pre好像也没有了"，实为回复太快没来得及发preview

翀哥~09:38问："哎，现在pre好像也没有了是吧"
我检查后说preview逻辑在的（`editPreview isFinal=true`发一次），翀哥说："或者可能这次对话没有preview"

**实际原因：回复太快（简单对话）→ 模型生成完成后直接发了最终内容 → 中间没来得及触发preview更新。**
这不是bug——对于短回复，AI生成时间短，preview还没发出去就已经finish了，finish时发的就是最终内容。只有回复较长、生成时间久的对话才会有可见的preview。

翀哥后来也没追问preview的事，说明他接受了这个解释。在10:24翀哥问"你看看现在"（看微信）时，回复正常，没有preview相关抱怨。

### 第六阶段（最终状态确认 ✅）

| 功能 | 状态 | 备注 |
|------|------|------|
| thinking | ❌ 被过滤 | 全局 `display.thinking.enabled=false`（翀哥早晨决定关的，与微信无关） |
| preview | ✅ 代码正常，但对短回复不可见 | `editPreview(isFinal=true)`发一次，短回复来不及触发即finish |
| toolUse | ✅ 正确关闭 | `suppressToolDisplay` + rate limit原因 |
| toolResult | ✅ 正确关闭 | `suppressToolDisplay` + rate limit原因 |
| typing indicator | ✅ 正常 | start+stop都生效 |
| 3s节流 | ✅ 正常 | 仅wechat.ts |
| suppressToolDisplay | ✅ 生效 | 正确过滤toolUse/toolResult，不影响preview/thinking（后者是全局配置关的） |

**How to apply:**
1. preview被过滤是翀哥早晨全局配置关的，不是 `suppressToolDisplay` 的问题
2. 翀哥想要preview恢复的话，开全局 `display.preview.enabled=true` 即可
3. `suppressToolDisplay` 工作正常，只关toolUse/toolResult
4. wechat.ts保持3秒全局发送节流
