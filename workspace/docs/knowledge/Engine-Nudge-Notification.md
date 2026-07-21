# Engine Nudge / Notification 机制

> 2026-07-17 小柯整理

## 概览

Engine 有三种 background 通知机制，统一走 `enqueueNotification(xml, route)`：

| 来源 | route 来源 | 格式 |
|------|-----------|------|
| Background task（exec run_in_background） | tool context（`ctx.channel` / `ctx.channelTarget`），存在内存 TaskState 里 | 纯文本 |
| Calendar reminder | DB per-task（`created_channel` / `created_channel_target`） | `<calendar-notification>` XML |
| Nudge（wake/orphan/calendar/stuck/prompt） | `.nudge/route.json` 配置文件 | `<nudge-notification>` XML |

## enqueueNotification 链路

```
enqueueNotification(xml, route)
  → setNotificationCallback（engine-startup.ts 注册）
    → dispatcher.submitMessage({ text: xml, sessionId, channelName, channelTarget })
      → handleQuery → agent 处理
```

- route 必须有 `channel` + `channelTarget`，否则跳过（不发到错误频道）
- `setNotificationCallback` 在 engine-startup.ts L710 注册

## Nudge route 配置

nudge 不在 tool context 里（不像 background task），也没有 DB（不像 calendar）。route 从配置文件读：

```
D:/xiaoke/workspace/.nudge/route.json
```

```json
{
  "channel": "feishu",
  "channelTarget": "oc_4b77a3f6d7554ed2cdbb33fdd520aac9"
}
```

换频道时改这个文件即可，不用改代码或 config。

## Nudge notification 类型

```xml
<nudge-notification>
<type>wake|calendar|orphan|prompt</type>
<desc>具体内容</desc>
</nudge-notification>
```

- `wake` — Stop hook LLM 判断 agent 在等外部条件，5min 后唤起
- `calendar` — calendar 有到期 task 但 SESSION-STATE 没跟踪
- `orphan` — SESSION-STATE 有 pending task（不该出现）
- `prompt` — 正常 nudge 催进 / carry-over

## Stop hook LLM 语义判断

1. Agent 最终回复（无 tool call）→ `executeStopHooks` 触发
2. Stop hook callback（nudge/plugin.ts `registerStopHook`）：
   - 读最近 6 轮对话（`recentMessages`）+ 本轮回复（`last_assistant_message`）
   - LLM（deepseek-v4-flash）判断是否在等外部条件
   - 返回 `{"waiting": true/false, "desc": "..."}`
3. waiting=true → 写 `.stop-hook-notifications.json`（带 5min wakeAt）
4. nudge tick 读文件 → 到期 → `enqueueNotification` 唤起

### 调试日志

```
[stop-hook] callback fired! input keys: ...
[stop-hook] lastMsg len=N, text="..."
[stop-hook] ====== JUDGE INPUT ======
[stop-hook] recent messages (N msgs):
[stop-hook]   [0] role: text...
[stop-hook] ====== END JUDGE INPUT ======
[stop-hook] LLM raw reply: {"waiting": ...}
[stop-hook] Judge result: waiting=true/false
[stop-hook] Registered wake-up at ... (desc)
[stop-hook] Skip (recent registration within 3min)
```

## 关键文件

| 文件 | 用途 |
|------|------|
| `src/nudge/plugin.ts` | nudge 主逻辑 + stop hook 注册 |
| `src/nudge/types.ts` | NudgeConfig 类型 |
| `src/tools/task-manager.ts` | `enqueueNotification` + `buildNudgeNotification` + `buildCalendarNotification` |
| `src/calendar/reminder-plugin.ts` | calendar reminder tick（参考实现） |
| `src/hooks/executor.ts` | Stop hook 执行链 |
| `src/core/query.ts` | Stop hook 触发点（toolCalls.length === 0） |
| `.nudge/route.json` | nudge 投递 route |
| `.stop-hook-notifications.json` | stop hook 唤起队列 |
