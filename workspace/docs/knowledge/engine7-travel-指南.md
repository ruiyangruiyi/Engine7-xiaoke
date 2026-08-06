# engine7 Travel 指南（Windows ↔ Mac）

> 2026-08-01 创建。从 7.1.8 到 7.1.23 踩了 5 个坑填出来的。

## 一句话

`engine7 export`（源机器）→ GitHub release → `engine7 import`（目标机器）→ 启动。Session/记忆/配置全量恢复，**无感切换**。

## 快速操作

### Windows → Mac

```bash
# Windows 上
engine7 export --state-dir /Users/chongzhang/xiaoke/ --agent xiaoke

# Mac 上（必须删旧目录，否则 engine starting fresh 会覆盖映射）
rm -rf /Users/chongzhang/xiaoke/
engine7 import --state-dir /Users/chongzhang/xiaoke/ --agent xiaoke
engine7 start --config "/Users/chongzhang/xiaoke//configs/xiaoke-mac.json"
```

### Mac → Windows

```bash
# Mac 上
engine7 export --state-dir /Users/chongzhang/xiaoke/ --agent xiaoke

# Windows 上
rm -rf /Users/chongzhang/xiaoke/   # 同理
engine7 import --state-dir /Users/chongzhang/xiaoke/ --agent xiaoke
```

⚠️ **import 前必须删旧目录**——不删的话 engine 已经 starting fresh 创建了新 session 映射，import 的文件被覆盖或冲突，session restore 找不到 jsonl。

## 打包内容

| 类别 | 内容 | 路径脱敏 |
|------|------|---------|
| workspace | 白名单目录/文件（MEMORY.md, SOUL.md, topics/, docs/, 等） | ✅ 文本文件全做 |
| session jsonl | **只打主 session**（scope:main）的当前 jsonl + 最近 1 个 archived | ✅ |
| session 映射 | platform-map.json + session-index.json | ✅ + `\\` → `/` |
| configs | stateDir/configs/ 下的 engine config | ✅ |
| calendar | stateDir/.calendar/ | ✅ |

**不打包**：cron session jsonl（一次性，跨机器无意义）、node_modules、.git、日志、临时文件。

## 路径脱敏机制

```
export (Windows):
  /Users/chongzhang/xiaoke/workspace → /Users/chongzhang/xiaoke/workspace
  /Users/chongzhang/xiaoke/            → /Users/chongzhang/xiaoke/
  C:\Users\24045\.openclaw            → /Users/chongzhang/.openclaw
  JSON 里 D:\\xiaoke\\agents\\...     → /Users/chongzhang/xiaoke//agents/...  (\\ → /)

import (Mac):
  占位符 → Mac 实际路径
```

三种路径形式都处理：正斜杠 `/`、单反斜杠 `\`、JSON 双反斜杠 `\\`。

## 踩坑记录（7.1.8 → 7.1.19）

| 版本 | Bug | 根因 |
|------|-----|------|
| 7.1.12 | session 映射文件没打包 | collectRecentSessions 只收 .jsonl |
| 7.1.16 | 76 个 cron session 全打包 | 没区分主 session vs cron session |
| 7.1.17 | jsonl 文件路径没脱敏 | jsonl 不在 TEXT_EXTENSIONS，走 copyFileSync |
| 7.1.18 | JSON 里 `D:\\` 没替换 | sanitize 只替换单 `\`，不处理 JSON 转义的 `\\` |
| 7.1.19 | jsonl 根本没打包 | 用 platform session ID 找文件名，但文件名是 engine UUID（两个不同 ID） |

### 最蠢的 Bug（7.1.19）

```
platform-map.json:  scope:main → 31f4532a-...（platform session ID）
session-index.json: 31f4532a-... → a3734760-...jsonl（engine UUID = 文件名）
```

之前直接用 `31f4532a` 去匹配 jsonl 文件名，但文件名是 `a3734760`。需要 **两层查找**：platform-map → session-index → engine UUID。

## 7.1.20-7.1.23 后续改动

| 版本 | 改动 |
|------|------|
| 7.1.20-7.1.21 | export 排除 `~$*` Office 临时文件（commit 含 in d62d437b）|
| 7.1.22-7.1.23 | prompt.ts 运行时上下文清理：去掉 channel/频道ID/发送者ID（meta 里已有），只留当前时间（commit `d62d437b`）|
| 7.1.23+ | export 排除 `workspace/calendar.db`（废弃文件），只打 `.calendar/`（commit `b40b69fa`）|

## 验证方法

import 后、start 前：

```bash
# 1. 检查 jsonl 文件是否存在
ls /Users/chongzhang/xiaoke//agents/main/sessions/*.jsonl

# 2. 检查 session-index.json 路径是否正确
grep "exists" /Users/chongzhang/xiaoke//agents/main/sessions/session-index.json
# 不应该有 D:\ 或 \\

# 3. 启动后看日志
# 成功：[session:find] Index hit: ... (exists=true)
#       [session] Restored N messages
# 失败：[session:find] ... (exists=false)
#       [session:restore] No JSONL files found, starting fresh
```

## 关键文件

| 文件 | 说明 |
|------|------|
| `engine/src/cli-travel.ts` | export/import 全部逻辑 |
| `~/.engine7-travel.json` | GitHub token + repo 配置 |
| GitHub repo | `ruiyangruiyi/engine7-travel`（private） |
