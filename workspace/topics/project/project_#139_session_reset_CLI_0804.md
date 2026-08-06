---
name: #139 engine7 session reset CLI
description: 2026-08-04 晚翀哥住院时拍板——给 engine7 加 session reset CLI（archive/drop-last/strip-images/--restart），CLI 改磁盘文件不重启不生效是核心约束
type: project
date: 2026-08-04
---

#139 task：engine7 session reset CLI

**起因：** 8/4 傍晚救完小文（Kobun）后，翀哥提问 "engine 改 JSONL 后会不会自动 reload 不用重启"——我答"不会且必须重启"，因为 engine `getHistory()` 从内存读，只在空时从 JSONL 恢复一次。CLI 改文件不重启 = 浪费。

**设计核心原则（翀哥拍板，2026-08-04 晚）——救援通道必须在被救系统之外：**
> "救护车不能是病人自己开"

两条具体好处：
1. **外部进程能安全重启目标 engine** ——自己重启自己是自杀，做不到（engine 进程内不能优雅 self-restart）
2. **engine 坏了也能救** ——slash 命令依赖 engine 活着，CLI 不依赖；今天小文 500 时每轮都报错，session 内任何命令都够不着她，只有外部 CLI 能碰她

**Why:** Session 数据出问题时（agent 卡死/上下文污染/历史丢图太大/需要 drop-last 回到前一轮），纯手改 JSONL 改完引擎不读；要么 CLI 改完提示用户 `engine7 restart`，要么 `--restart` 一把梭。

**How to apply:**
- 8/6 完成，提前 60 分钟提醒
- Phase 拆了 5 个：①CLI 骨架 ②archive（旧 session 归档）③drop-last（弹掉最后 N 轮）④strip-images（历史图清掉省 token）⑤--restart+验证
- 文档先写再 add task，session JSONL 编辑 SOP 落 docs/
- ⚠️ 改 session JSONL 时记得 compaction 文件这个坑（小文没踩到，但其他 agent 可能）