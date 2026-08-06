---
name: 微信preview重复发送bug
description: 6/13修复：freeze()传isFinal=true导致微信每次tool调用都发preview，加previewSent标记解决
type: feedback
---

## 问题（6/13 12:00+）

翀哥发现：跟小柯在微信说话时，每次tool调用都会在微信端收到一条preview消息，导致刷屏。

## 根因分析

**`StreamPreview.freeze()` 内部调用 `editPreview(..., isFinal=true)`**

engine-startup.ts:1385 在每次 tool 调用时执行：
```typescript
onToolCall: async (name, args) => {
  await preview.freeze().catch(() => {})   // ← 问题在这里
}
```

而 `freeze()` 方法内部传了 `isFinal=true`：
```typescript
// freeze() 内部：
await this.cm.editPreview(this.channelName, this.previewHandle, text, undefined, true)
//                                                                             ^^^^ isFinal=true!
```

微信adapter的 `editPreview` 对 `isFinal` 的处理是：
```typescript
async editPreview(handle, content, agentName, isFinal) {
  if (!isFinal) return    // ← isFinal=false就跳过
  // ...发消息逻辑
}
```

所以每次freeze()都会发消息到微信。

## 修复方案

给 `WechatAdapter` 加一个实例变量 `previewSent = false`：
- `sendPreview()`（新turn开始）→ 重置 `previewSent = false`
- `editPreview(isFinal=true)` → 第一次发消息并标记 `previewSent = true`，后续freeze()再传 `isFinal=true` 也跳过
- 每个微信session只发一条preview消息

## 修复代码

```typescript
// WechatAdapter成员变量
private previewSent = false;

// sendPreview - 新turn开始时重置
async sendPreview(content: string, agentName?: string): Promise<PreviewHandle | undefined> {
  this.previewSent = false;
  // ...发消息...
  this.previewSent = true;
  return handle;
}

// editPreview - isFinal=true时检查
async editPreview(handle: PreviewHandle, content: string, agentName?: string, isFinal?: boolean): Promise<void> {
  if (isFinal && this.previewSent) return;  // 已发过就跳过
  if (isFinal) {
    await this.send(...);  // 发消息
    this.previewSent = true;
  }
}
```

## 验证（6/13 12:00）

✅ **重启后验证成功**：
- 微信不再刷屏，每个turn只收到一条preview（而不是每个tool调用都发一条）
- MiniMax extract触发时微信端正常，不再重复发preview
- 只影响WechatAdapter，飞书/Discord不受影响（它们有消息编辑能力）

**Why:** `freeze()` 是 Claude Code 的设计，freeze时不删除preview而标记为frozen停止更新，最终回复时去蓝框。但微信没有"编辑消息"API——只能发一次，不能反复编辑。所以 freeze() 传 isFinal=true 导致每次freeze都发一条消息到微信。解决方案是加标记让每个turn只发一次。

**How to apply:**
1. 这个修复只影响 WechatAdapter，Discord/LarkAdapter 不受影响（它们有编辑消息能力）
2. 如果其他平台也有类似问题，检查对应的 adapter 是否在 freeze() 时误传了 isFinal=true
3. 核心教训：没有编辑/删除API的平台，preview策略需要单独适配，不能直接照搬有编辑能力的平台
