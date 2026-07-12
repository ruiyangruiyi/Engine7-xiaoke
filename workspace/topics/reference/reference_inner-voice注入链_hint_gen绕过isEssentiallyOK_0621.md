---
name: inner-voice注入链 — hint_gen.py给OK加hint绕过isEssentiallyOK
description: 6/21 研究inner-voice注入链：memory_whisper.py已废弃，实际路径是cron→agent→postProcess(hint_gen.py)→notify_session，hint_gen给OK加hint绕过了isEssentiallyOK
type: reference
date: 2026-06-21
---

6/21 12:40 inner-voice 泄露触发完整注入链研究。

## 注入链（当前 Engine 时代）

```
cron 触发（tasks.json）
  → agent 执行 prompt（@workspace/prompts/my-inner-voice.md）
    → 产出念头（可能"OK"）
  → postProcess: hint_gen.py（给念头加💡hint后缀）
  → finalResult（含hint的完整文本）
  → 第4步 delivery（mode: local/local-chat）
  → 第5步 notify_session（isEssentiallyOK 判断 → 注入 scope:main）
```

## memory_whisper.py 已废弃

翀哥确认 memory_whisper.py 是 OpenClaw 时代的旧路径。当前不需要它做任何修改。

## 泄露根因

**hint_gen.py 给 "OK" 也加 hint：**
- 小忆 cron task 第1步检查 ACTIVE/INACTIVE，如果活跃就回复 OK
- hint_gen.py 不判断输入内容，给 "OK" 也追加 💡hint → `OK\n💡不用酝酿完美的话...`
- scheduler 的 `restContent.length < 10` 判断收到 `OK\n💡不用酝酿完美的话...`，长度超过10，不认为是 OK 就注入了

## 关键文件

- `D:/xiaoke/cron/tasks.json` — 小柯的 inner-voice cron 配置（postProcess + notify_session）
- `workspace/scripts/hint_gen.py` — hint 追加脚本
- `engine/src/engine/scheduler.ts` — scheduler 的 delivery + notify_session 逻辑（含 isEssentiallyOK）

## 实际修复（已实施）

1. **hint_gen.py**：输入 trim 后 `startsWith('OK')` → 直接返回原文，不加 hint。不用 `===` 精确匹配，`startsWith` 能覆盖 "OK"、"OK\n💡xxx"、"OK收到" 等变体。
2. **scheduler.ts isEssentiallyOK**：hint_gen 层已堵住，scheduler 层无需改。
3. **活跃判断**：hint_gen.py 里调 session_history.py，15 分钟内有活动直接输出空字符串 → scheduler 自然跳过注入（postProcess 输出空 → finalResult 空 → notify_session 不执行）。commit: `c6f4ffc`。

**关键原则：`startsWith('OK')` 优于 `=== 'OK'`**，因为 OK 可能有换行/后缀变体。
