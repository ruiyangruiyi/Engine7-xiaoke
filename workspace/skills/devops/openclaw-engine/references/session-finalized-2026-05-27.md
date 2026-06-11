# Session Restore + Review Finalization (2026-05-27晚)

## Session Restore最终方案

CC研究完CC和OpenClaw的session恢复机制后确定的方案：
- 核心原则：**一个session一个JSONL文件，续写不新建**
- 文件名：UUID（不用平台前缀如discord_xxx.jsonl）
- 映射：session-index.json做sessionId→UUID.jsonl映射
- header加engineSessionId字段精确关联
- 重启后续写同一文件（append模式）

CC之前的错误：每次重启都新建JSONL文件 → 改成续写
最初错误：用discord_xxx.jsonl做文件名 → 改成UUID + session-index.json

## 8条Code Review全部处理完毕

| # | 问题 | 状态 |
|---|------|------|
| P0-1 | reader.ts path import在末尾 | ✅ 移到顶部 |
| P0-2 | read.ts 5MB限制太大 | ✅ 改为1MB |
| P0-3 | readFileState存content浪费内存 | ✅ 去掉content只存mtime |
| P0-4 | ~~user消息重复~~ | ❌纠正，实际是assistant重复，已修(fullResponse→roundText) |
| P0-5 | sessionId格式(discord:xxx) | 设计层，后续做 |
| P1-6 | 截断砍30%太粗暴 | ✅ shift最旧1条 |
| P1-7 | text/toolCall互斥 | ✅ 去掉互斥 |
| P1-8 | flush条件 | ✅ if(roundText) |

## SendOptions回复功能三层断裂修复

1. manager.ts — send()加options?: SendOptions参数并透传
2. main.ts — firstReply标记，第一条回复带{replyTo: messageId}
3. discord.ts — 原有replyTo逻辑从死代码变活

## 工具显示格式对齐

对齐cc-connect i18n.go的MsgTool/MsgToolResult模板：
- Tool call: 🔧 **工具 #N: Name**\n---\ninput
- Tool result: 📤 **Name**\n---\nresult
- tool counter每turn从1开始计

## Phase进度总结 (2026-05-27晚)

| Phase | 状态 | 关键成果 |
|-------|------|---------|
| P1 基础循环 | ✅ | QueryEngine async generator |
| P2 工具系统 | ✅ | registry + executor + features |
| P3 通道层 | ✅ | DiscordAdapter + DM/Guild + typing + 工具可视化 |
| P4 Session | ✅ | JSONL持久化 + UUID + session-index + 恢复 |
| P5 Memory+Heartbeat | 待做 | 向量搜索 + cron |
| P6 剩余工具 | ✅ | 8个tool到位(read/write/edit/exec/glob/grep/web_search/web_fetch) |
| P7 Compact+Hook | 待做 | |
| P8 并行测试+切换 | 待做 | |
