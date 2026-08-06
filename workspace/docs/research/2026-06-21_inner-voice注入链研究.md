# Inner-voice（小忆）注入链研究

**日期：** 2026-06-21
**研究者：** 小柯
**状态：** 研究完成，待翀哥确认方案

## 一句话结论

inner-voice 注入链从 OpenClaw 时代的 `memory_whisper.py + gateway RPC` 迁移到了 Engine 架构。现在走的是 **scheduler.ts 的 postProcess + notify_session** 路径。`memory_whisper.py` 确实已废弃。

## 完整注入链路

```
cron 定时触发（每30分钟）
  ↓
scheduler.ts 执行 cron task
  ↓
Step 1: agent 执行 prompt（@workspace/prompts/my-inner-voice.md）
  → 小忆 prompt 第1步检查 session_history.py --active-within 30
  → 活跃 → 回复 "OK"
  → 不活跃 → 走8步生成念头
  ↓
Step 2: postProcess = hint_gen.py
  → 读 inner-voice/thought.txt
  → 按沉默时长决定 hint 概率
  → 可能追加 💡hint
  → 输出 finalResult
  ↓
Step 3: delivery（mode: local → 注入到 cron 自己的 session）
  ↓
Step 4: notify_session（scheduler.ts line 293）
  → isEssentiallyOK 判断
  → true → 跳过注入
  → false → 注入到 scope:main session
  → 注入格式：session_message = "[inner-voice] {result}"
```

## 关键文件

| 文件 | 作用 | 归属 |
|------|------|------|
| `C:/Users/24045/.openclaw/cron/tasks.json` | 姐姐的 cron task 配置 | OpenClaw |
| `/Users/chongzhang/xiaoke//cron/tasks.json` | 小柯的 cron task 配置 | Engine |
| `C:/Users/24045/.openclaw/engine/src/cron/scheduler.ts` | scheduler 执行逻辑 | Engine |
| `C:/Users/24045/.openclaw/workspace/scripts/hint_gen.py` | postProcess 脚本（替代 memory_whisper.py） | workspace |
| `C:/Users/24045/.openclaw/workspace/scripts/session_history.py` | 活跃检查脚本 | workspace |
| `C:/Users/24045/.openclaw/workspace/prompts/my-inner-voice.md` | 小忆 prompt | workspace |
| `C:/Users/24045/.openclaw/scripts/memory_whisper.py` | **已废弃** | OpenClaw 旧 |

## Bug 分析：`[inner-voice] OK 💡xxx` 泄漏

### 根因

`hint_gen.py` 不判断输入内容是不是 "OK"，给所有输入都可能追加 💡hint。

**时间线：**
1. 小忆 prompt 判断活跃 → 回复 "OK"
2. hint_gen.py 收到 "OK" → 按概率追加 💡hint → 输出 "OK\n💡不用酝酿完美的话..."
3. scheduler.ts 的 isEssentiallyOK 判断：
   - `firstLine === 'OK'` ✅
   - `restContent.length < 10` ❌（"💡不用酝酿完美的话..." 远超10字符）
   - 结果：isEssentiallyOK = false → **还是注入了**

### 两个问题

**问题1：OK 不该注入**
- 位置：scheduler.ts 的 isEssentiallyOK 判断
- 当前：`firstLine === 'OK' && restContent.length < 10`
- 应改为：只要 firstLine === 'OK' 就算 essentially OK（不管后面有没有 hint）

**问题2：hint_gen.py 给 OK 加了 hint**
- 位置：hint_gen.py 的 maybe_add_hint()
- 应改为：输入是 OK 时直接返回 OK，不加 hint

**问题3（翀哥提出）：正在聊天时不该注入**
- 当前：小忆 prompt 第1步检查 `--active-within 30`，但可能因为重启/compaction 导致 session_history 数据丢失
- scheduler.ts 第5步 notify_session 没有活跃判断
- 应改：scheduler.ts notify_session 时也检查 session 是否活跃

## 修复方案（待翀哥确认）

### 方案A：改 scheduler.ts（Engine 层）

```typescript
// scheduler.ts line 288-292
// 改为：只要 firstLine 是 OK 就跳过
const isEssentiallyOK = trimmedResult === 'OK' || trimmedResult === '' ||
  firstLine === 'OK'  // OK 开头就跳过，不管后面有没有 hint
```

优点：一处改动，所有 cron task 都生效
缺点：isEssentiallyOK 判断逻辑变粗（但 OK 开头的消息确实没注入价值）

### 方案B：改 hint_gen.py（postProcess 层）

```python
# hint_gen.py maybe_add_hint() 开头加：
if message.strip() == 'OK' or message.strip() == 'ok':
    return message  # OK 不加 hint，直接返回
```

优点：从源头解决，hint_gen 不给 OK 加 hint
缺点：scheduler 的 isEssentiallyOK 判断仍然是 restContent.length < 10

### 建议两个都改

- hint_gen.py：OK 不加 hint（从源头堵）
- scheduler.ts：OK 开头就跳过（兜底保护）

### 正在聊天时不注入

scheduler.ts notify_session 前加活跃检查——调用 session_history.py 或检查最近消息时间，15分钟内有活动就跳过。

## 废弃文件确认

- `memory_whisper.py` — **已废弃**，不再被任何 cron task 调用
- 旧的 `.openclaw/cron/jobs.json` — OpenClaw 时代格式，engine 不读
- 小忆 prompt 里仍然写着 `exec python ../scripts/memory_whisper.py` — **这是死代码**，因为 engine 的 cron task 用 prompt 文件 `@workspace/prompts/my-inner-voice.md`，不走 jobs.json 里的旧 prompt
