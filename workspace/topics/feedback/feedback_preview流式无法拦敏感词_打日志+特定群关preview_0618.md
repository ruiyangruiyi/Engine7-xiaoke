---
name: preview流式拦不了敏感词——打日志+特定群关preview
description: 6/18 11:32翀哥教"打日志看拦截状态不要猜"+"preview拦不了就在特定群关掉，像微信一样显示最终结果后能拦"；11:35实施：StreamPreview加enabledOverride按channel关，appendText/flush加log
type: feedback
date: 2026-06-18
---
## 6/18 11:32 翀哥教两件事

翀哥飞书原话：
> "我觉得是这样  1. 你打日志看下  提示词有没有在合适的地方拦截 ，如果说在preview里有没有log拦截失败，不要猜    2.  如果preview你拦截不了，后需要想办法，包括在某些特定的群聊上关掉preview，跟微信一样显示最终解果后能拦截也行"

**两点**：
1. **不要猜拦截状态，打日志确认**——"preview 里有没有 log 拦截失败"= 在拦截点打 log，看实际跑了没
2. **preview 拦不了就在特定群关掉**——像微信（display=thinking/toolUse关掉）一样，显示最终结果后由 onResult 层拦截

## 11:32-11:35 实施

1. **StreamPreview.appendText / flush 加 log**——确认敏感词检查是否在 preview 阶段被触发
2. **StreamPreview 加 `enabledOverride` 参数**——false 时 degraded = true（等同关掉 preview）
3. **engine-startup.ts 构造 preview 时按 channel 配置决定 enabled**——`channels.{source}.previewEnabled: false` 时不显示 preview，只在 onResult 显示最终结果
4. **config 加 `previewEnabled` 字段**——默认 true（不破坏现有行为）

## Why

preview 是流式 chunk 累积器（Discord/飞书 update message），**不走 channelManager.send**：
- **chunk 级拦截不可行**：敏感词可能跨 chunk（"老"在 chunk N、"公"在 chunk N+1）→ 匹配不到
- **完整回复在 onResult 拦截是底线**：拦截 channelManager.send 路径，但 preview 已经在频道里显示了
- **现实保护**：
  - 真正"潘总群社死"的实际保护在 **prompt 层**（system prompt 加"群聊时避免亲昵表达"），不是过滤层
  - onResult 拦截只防"preview 没显示（delivered=false 路径）"的 case
  - **特定群关 preview + 显示最终结果** = 微信模式（display 关掉 thinking/toolUse/preview），用 onResult 兜底拦截

## How to apply

1. **不要猜拦截状态**——加 log 标记"是不是在 preview 阶段跑了敏感词检查"
2. **任何"流式输出 + 内容校验"的组合都要意识到 chunk 边界问题**——要么接受 chunk 级检查的漏检，要么在完整结果出来后拦
3. **特定群/通道关掉 preview = 工程上接受的妥协**——跟微信一样，display 简化 + 最终结果兜底
4. **prompt 层防护是底线**——system prompt 加规则让 LLM 自己别在群聊说漏嘴，比任何过滤都管用
5. **类似 config 设计参考**：`channels.{source}.previewEnabled`（默认 true 可关），跟 `groupPolicy`（open/mention-only/disabled）+ `sensitiveWords`（filter 列表）一起管群聊行为
