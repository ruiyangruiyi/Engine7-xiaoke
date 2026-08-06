---
name: engine history 内存缓存 + JSONL 必须重启
description: 2026-08-04 晚救小文时确认——engine 的 getHistory() 从内存读，只在空时从 JSONL 恢复一次，CLI 改文件不重启不生效
type: reference
date: 2026-08-04
---

engine history 缓存机制（救小文时确认）

**核心事实：**
- `getHistory()` 从内存数组返回历史
- 只有内存空时才从 session JSONL 恢复一次（启动时）
- 进程不重启，CLI 改磁盘 JSONL 文件 = 浪费，in-memory session 不会重新读

**Why:** 这是设计——JSONL 是持久化层，in-memory 是运行时层，session 创建后两者解耦。要让磁盘改动生效必须 restart。

**How to apply:**
- 救 agent / reset session 的 CLI 设计原则：①改完提示重启 ②提供 `--restart` 一把梭 ③给"外人用"模式（友好提示），给"自己用"模式（一把梭）
- 救小文能成功是因为 engine 重启后空 history → 自动从 JSONL 恢复 → 上下文接着走
- 跟 JSONL 图片重注入机制配合：restart 后 engine 重建 history 时按图片路径从磁盘重新注入图片（@see reference_JSONL图片重注入机制_0804）
- compaction 文件是另一个坑——存在时会覆盖 JSONL，救 agent 前先 ls 看有没有 compaction

**设计哲学（8/4 晚翀哥拍板）——救援通道必须在被救系统之外：**
> "救护车不能是病人自己开" ——翀哥 2026-08-04 住院时

两条派生好处：
1. **外部进程能安全重启目标 engine** ——自己重启自己是自杀，engine 进程内无法优雅 self-restart
2. **engine 坏了也能救** ——slash 命令依赖 engine 活着，CLI 不依赖；今天小文 500 报错时，session 内任何命令都够不着她，只有外部 CLI 能碰她

@see project_#139_session_reset_CLI_0804