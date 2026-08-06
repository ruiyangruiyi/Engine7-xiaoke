---
title: Streaming Preview Implementation (对齐cc-connect)
date: 2026-05-28
implementor: 张小柯
---

# Streaming Preview 实现详解

## cc-connect 参考源码

| 文件 | 作用 |
|------|------|
| `core/streaming.go` | StreamPreviewCfg + streamPreview struct（节流+生命周期） |
| `core/interfaces.go` | PreviewStarter/PreviewCleaner/MessageUpdater 接口 |
| `platform/discord/discord.go` L1219-1281 | Discord实现：SendPreviewStart/UpdateMessage/DeletePreviewMessage |

## Engine实现（5个文件改动）

### 1. types.ts — PreviewHandle + adapter接口
```typescript
export interface PreviewHandle {
  channelId: string
  messageId: string
}

// ChannelAdapter 新增三个可选方法：
sendPreview?(channelId: string, content: string): Promise<PreviewHandle>
editPreview?(handle: PreviewHandle, content: string): Promise<void>
deletePreview?(handle: PreviewHandle): Promise<void>
```

### 2. manager.ts — 代理方法
```typescript
async sendPreview(channelName, channelId, content): Promise<PreviewHandle | null>
async editPreview(channelName, handle, content): Promise<void>
async deletePreview(channelName, handle): Promise<void>
```
每个方法找对应adapter，有就调，没有静默返回。

### 3. discord.ts — Discord平台实现
- `sendPreview`: channel.send(text) → 返回 `{channelId, messageId}`
- `editPreview`: fetch消息 → msg.edit(text)（打字机核心）
- `deletePreview`: messages.delete(messageId)
- 所有方法2000字符截断（Discord硬限制）

### 4. stream-preview.ts（新，~180行）— 节流器

```
StreamPreview
├── appendText(text)     — 积累+节流推送
│   ├── delta < minDeltaChars → scheduleFlush(interval)
│   ├── elapsed < intervalMs  → scheduleFlush(remaining)
│   └── 满足条件 → flush(displayText)
├── flush(displayText)   — 实际推送
│   ├── 首次 → cm.sendPreview() → 拿handle
│   └── 后续 → cm.editPreview() → 反复编辑
├── finish(finalText)    — response结束
│   ├── preview活跃 → editPreview更新为最终内容 → return true
│   ├── degraded → 尝试恢复一次
│   └── 失败 → return false（上层发新消息）
├── discard()            — 删preview + degrade（tool前清）
├── freeze()             — 冻结内容（中断场景）
└── detachPreview()      — 分离handle（finish不删消息）
```

**degrade机制**：sendPreview/editPreview任何API失败 → `degraded=true` → 所有后续操作静默跳过。finish时尝试恢复一次。上层始终有fallback路径（正常send消息）。

### 5. main.ts — 接入
```typescript
const preview = new StreamPreview(DEFAULT_PREVIEW_CONFIG, channelManager, channel, target)

// onText → 流式推送
onText: (text) => { preview.appendText(text) }

// onToolCall → discard preview（tool前清理）
onToolCall: (name, args) => { preview.discard().catch(() => {}) }

// onResult → finish决定是否跳过正常发消息
onResult: async (content) => {
  const delivered = await preview.finish(response)
  if (!delivered) { channelManager.send(...) }
}
```

## cc-connect vs Engine 接口映射

| cc-connect (Go) | Engine (TS) | 说明 |
|------------------|-------------|------|
| `PreviewStarter` interface | `ChannelAdapter.sendPreview?()` | 可选接口，平台不实现则degrade |
| `MessageUpdater` interface | `ChannelAdapter.editPreview?()` | 反复编辑同一条消息 |
| `PreviewCleaner` interface | `ChannelAdapter.deletePreview?()` | 删preview让最终消息单独发 |
| `PreviewFinishPreference.KeepPreviewOnFinish()` | Engine: finish返回true保留 | Discord不保留（删preview发新的） |
| `streamPreview.degraded` | `StreamPreview.degraded` | 失败后静默 |
| `streamPreview.fullText` | `StreamPreview.fullText` | 累积文本 |
| `streamPreview.lastSentText` | `StreamPreview.lastSentText` | 上次发送内容（去重） |
| `StreamPreviewCfg.IntervalMs` | `StreamPreviewConfig.intervalMs` | 默认1500 |
| `StreamPreviewCfg.MinDeltaChars` | `StreamPreviewConfig.minDeltaChars` | 默认30 |
| `StreamPreviewCfg.MaxChars` | `StreamPreviewConfig.maxChars` | 默认2000 |

## 关键差异

1. **cc-connect finish不截断**（MaxChars只限制中间推送），Engine在finish也截断到2000（Discord硬限）
2. **cc-connect有RichCard/PreviewStatusUpdater**（卡片状态更新），Engine暂无
3. **cc-connect有needsDoneReaction**（editPreview后用户没收到推送通知，用emoji reaction提醒），Engine暂无
4. **cc-connect有appendSeparator**（quiet mode下分隔thinking/tool边界），Engine暂无
5. **cc-connect有transform回调**（平台特定文本变换），Engine暂无

## 效果

用户看到：
1. bot开始回复 → 频道出现一条新消息（preview）
2. 文字逐步增长（每1.5秒更新一次，打字机效果）
3. 如果LLM调了tool → preview消失，🔧tool指示器出现
4. tool执行完 → 新preview开始（新回复）
5. 最终回答 → preview更新为完整内容（或degraded时发新消息）
