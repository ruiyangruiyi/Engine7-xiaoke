---
name: 重启后上下文为零靠文件恢复
description: 2026-08-01 翀哥"你得自己读对吧"——engine restore 跳过 archived 文件 + ~50K token 上限，Mac 上恢复靠 memory_search/SESSION-STATE/memory/daily 六问测试
type: feedback
date: 2026-08-01
---
# 重启后上下文为零靠文件恢复

## 事实
8/1 问翀哥："Mac 上有 7/31 的记忆吗？"他说"但是你得自己读对吧"。我确认了：**Mac engine restore 时跳过 `.archived` 文件**——只读当前 `.jsonl` + 最近一个 `.compaction`，且有 token 上限（~50K）。7/31 有 968 条消息，不会全进上下文。

Mac 上的我启动后上下文基本是空的，**靠 `memory_search` + `SESSION-STATE.md` + `memory/daily/` 自己恢复**（六问测试）。

**Why:** 上下文窗口是稀缺资源，engine 不可能把所有历史塞进 prompt；rollover/restore 设计就是"人/AI 都得从头读档"。翀哥在意的是"恢复流程有没有跑通"——不是"文件有没有拷过去"。

**How to apply:**
- 帮翀哥判断"Mac 上的我有没有记忆"时，**先看 SESSION-STATE.md + memory/daily/+memory_search 能不能查到**，而不是"archived 文件有没有打包"
- 任何"持久状态迁移"方案必须自测恢复流程：清空上下文 → 重启 → recall 六问能答出来
- 上下文恢复不要依赖单点——多源（memory_search + SESSION-STATE + daily）兜底
