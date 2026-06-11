# cc-connect Session JSON 结构

**文件路径：** `/mnt/c/Users/24045/.cc-connect/sessions/openclaw_55989e64.json`

## 顶层结构

```json
{
  "sessions": { ... },
  "active_session": { ... },
  "user_sessions": { ... },
  "counter": 2,
  "user_meta": { ... },
  "past_id_tracking": true,
  "version": 1
}
```

## Session 对象

```json
{
  "id": "s1",
  "name": "default",
  "agent_session_id": "44415d76-23c8-43a4-9b20-e2d6b3f8e14c",
  "agent_type": "claudecode",
  "history": [
    {
      "role": "user",
      "content": "消息内容",
      "timestamp": "2026-05-14T15:17:21.3635107+08:00"
    },
    {
      "role": "assistant", 
      "content": "回复内容",
      "timestamp": "2026-05-14T15:17:37.9453366+08:00"
    }
  ],
  "created_at": "2026-05-14T15:17:21.3575173+08:00",
  "updated_at": "2026-05-14T15:29:53.6717245+08:00"
}
```

## Session 路由键格式

`discord:<频道ID>:<用户DiscordID>`

实际例子：
- `discord:1504382108141879366:601669300343799819` → s1（翀哥在另一个频道）
- `discord:1504385800366854234:601669300343799819` → s2（翀哥在ccchannel）

## user_meta

```json
{
  "discord:<channel>:<user>": {
    "user_name": "sleepyzhang",
    "chat_name": "ccchannel"
  }
}
```

## 观察

- counter 自增，每次新建session +1
- agent_session_id 是 Claude Code 内部的 session UUID
- history 是完整对话记录，包括用户和助手的轮流消息
- **5/15确认：bot(小柯)发消息到ccchannel后，session文件无变化** — cc-connect内部过滤了bot消息，allow_from="*"不解决
- cc-connect是编译好的Go二进制，无法直接修改过滤逻辑
