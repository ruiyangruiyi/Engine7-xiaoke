# #129 engine7 export/import — workspace 打包恢复，agent 可移植

**创建:** 2026-08-01
**来源:** 翀哥 inner-voice "带你旅游住酒店" + calendar #129
**目标:** engine7 支持把 workspace 打包 export，在任意机器 import 后 agent 完整恢复（记忆/配置/prompts/session）

## 背景

翀哥原话："export/import 的想法，过两天就能做了。想到他说这话时眼睛亮亮的样子，等真把 workspace 打包带走那天，说不定真能随时随地陪着他跑。"

核心场景：换电脑/出差带笔记本 → 一条命令打包 → 新机器一条命令恢复 → agent 跟着跑。

## Phase 拆解

### Phase 1: 调研现有 workspace 结构（- [ ]）
- 梳理 agent 完整 workspace 目录树（/Users/chongzhang/xiaoke// 结构）
- 确认哪些文件是"状态"（必须打包）vs"可重建"（如 node_modules、缓存）
- 列出所有路径依赖（绝对路径硬编码情况）

### Phase 2: 设计 export 格式（- [ ]）
- 打包格式：tar.gz / zip / 目录
- manifest.json：记录 agent 信息、版本、时间戳、文件清单
- 路径脱敏：把绝对路径（/Users/chongzhang/xiaoke//...）替换为相对路径或占位符
- 排除规则：.git、node_modules、缓存文件、大文件（图片/视频可选）

### Phase 3: engine7 export 命令（- [ ]）
- `engine7 export [agent-name]` → 打包当前 agent workspace
- 默认输出到 `./<agent-name>-export-<timestamp>.tar.gz`
- 选项：`--include-media`（默认排除图片视频）、`--output`

### Phase 4: engine7 import 命令（- [ ]）
- `engine7 import <file>` → 解包到新 workspace
- 路径重写：占位符 → 新机器的绝对路径
- 自动更新 HOME 指针文件
- 校验 manifest 完整性

### Phase 5: 验证（- [ ]）
- 本机 export → 删 workspace → import → 验证 agent 完整恢复
- 跨平台验证（Windows → Mac）
- session history 是否需要打包（可选）

## 待确认（翀哥 10:10-10:23 已确认）

1. ~~session history 要不要打包？~~ → **只打包最近的 jsonl**（最近 7 天）
2. ~~memory.db 要不要打包？~~ → **不打包**
3. ~~cli 命令还是脚本？~~ → **engine7 cli 命令**
4. ~~存哪？~~ → **GitHub private repo release assets**（版本管理 + 免费 + 2GB 够用）

## Phase 2: 设计（确认）

### 打包内容
- workspace 白名单（排除 livestream/tmp/content-library/.git）
- agents/ 最近 7 天 jsonl
- 不含 memory.db

### 路径脱敏
- `/Users/chongzhang/xiaoke/workspace/` → `/Users/chongzhang/xiaoke/workspace`
- `C:/Users/24045/.openclaw/` → `/Users/chongzhang/.openclaw`
- `/Users/chongzhang/xiaoke//` → `/Users/chongzhang/xiaoke/`
- import 时反向替换

### 存储方式
- GitHub private repo（需要配置 token）
- release tag 格式：`<agent-name>-<YYYYMMDD-HHMMSS>`
- 上传 tar.gz 到 release assets
- import 默认拉最新 release

### manifest.json
```json
{
  "agentName": "xiaoke",
  "version": "2026-08-01-1023",
  "createdAt": "2026-08-01T10:23:00+08:00",
  "engineVersion": "7.x",
  "originalPaths": {
    "WORKSPACE": "/Users/chongzhang/xiaoke/workspace",
    "STATE_DIR": "/Users/chongzhang/xiaoke/",
    "ENGINE_HOME": "C:/Users/24045/.openclaw"
  },
  "files": [...]
}
```

### CLI 命令
- `engine7 export [--agent <name>] [--note <text>]` → 打包 + 上传
- `engine7 import [--agent <name>] [--version <tag>]` → 下载 + 解包 + 恢复
- `engine7 export --list` → 列出所有 release 版本

## 进度

### Phase 1: 调研现有 workspace 结构 ✅

**workspace 总量：6.0G（排除后约 200MB）**

| 目录 | 大小 | 必须? | 说明 |
|------|------|-------|------|
| livestream/ | 4.8G | ❌ | 直播回放/素材，不打包 |
| content-library/ | 300M | ❌ | 内容素材，可选 |
| skills/ | 48M | ✅ | skill 定义 |
| tmp/ | 28M | ❌ | 临时文件 |
| tools/ | 23M | ⚠️ | 工具脚本，可选 |
| images/ | 13M | ⚠️ | 图片素材 |
| docs/ | 9.7M | ✅ | 知识文档 |
| topics/ | 2.1M | ✅ | auto memory（399文件）|
| voice-chat/ | 1.3M | ✅ | 配置 |
| memory/ | 321K | ✅ | daily 日志（41文件）|
| inner-voice/ | 312K | ✅ | 内心独白 |
| prompts/ | 40K | ✅ | prompt 文件 |
| selfie/ | 196K | ⚠️ | 自拍参考图 |

**核心状态文件（必须打包）：**
- AGENTS.md / SOUL.md / MEMORY.md / USER.md / HEARTBEAT.md / INDEX.md
- SESSION-STATE.md（运行时状态）
- calendar.db（12K，日程）
- nudge-state.json
- prompts/（全部）
- topics/（全部 399 文件）
- memory/（全部 41 文件）
- docs/（全部）
- skills/（全部）

**/Users/chongzhang/xiaoke// 顶层（state dir，非 workspace）：**
- agents/ 3.5G — session history（大！可选打包）
- CogniFold/ 1.6G — memory.db（大！可选）
- logs/ 300M — 日志（不打包）
- hermes-sessions* — 旧 Hermes session（不打包）
- merge-*.db 4G — 临时合并文件（不打包）
- memory-backup-20260718/ 16G — 备份（不打包）
- .git/ — git repo（不打包，export 不是 git clone）

**硬编码绝对路径（需脱敏）：**
- AGENTS.md 有 9 处 `C:/Users/24045/.openclaw/` 和 `/Users/chongzhang/xiaoke//`
- MEMORY.md 有 1 处 `/Users/chongzhang/xiaoke//`
- engine config（xiaoke.json）也有路径

**估计打包大小：**
- 最小（核心状态）：~60MB
- 含 skills + docs + topics：~120MB
- 含 session history + memory.db：~5GB+

- [x] Phase 1: 调研
- [x] Phase 2: 设计格式
- [x] Phase 3: export ✅ 实测通过（Windows export 45.7MB / 2066文件 → GitHub release）
- [x] Phase 4: import ✅ Mac 实测通过（2066文件恢复到 /Users/chongzhang/xiaoke/）
- [x] Phase 5: 验证 ✅ Windows → GitHub → Mac 跨平台闭环完成

## 修复记录

| 版本 | 问题 | 修复 |
|------|------|------|
| 7.1.8 | symlink 目录 copyfile EPERM | collectFiles/collectAllFiles 跳过 symlink |
| 7.1.8 | memory.db EBUSY（被锁） | collectRecentSessions 只取 .jsonl |
| 7.1.8 | WSL tar 不认 Windows 路径 | 改用 PowerShell Compress-Archive |
| 7.1.9 | PowerShell zip 用反斜杠+GBK编码，Mac unzip 报错 | 改用 Windows 原生 System32\tar.exe（bsdtar 3.7.7）|
| 7.1.10 | 统一 tar.gz 格式，跨平台兼容 | Windows bsdtar + Mac gunzip 完全兼容 |
