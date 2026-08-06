---
name: engine7 travel搜索——浪漫命名vs工程命名失配
description: 2026-07-31 "engine7 travel"搜不到任务——翀哥用浪漫名travel，task是export/import，calendar search用LIKE精确子串匹配
type: project
---

# engine7 travel 关键词失配（#129 export/import）

## 事实
翀哥说"engine7 travel"，我一开始以为是去香港/出差，实际指 #129 任务（8/1 10:00 开工）——"engine7 export/import，workspace 打包恢复，agent 可移植到任意机器"。昨天已落盘 `docs/todo/2026-07-30_engine7-travel可移植方案.md`（161行）。

## 三层不匹配根因
- 翀哥用**浪漫/有诗意的名**（"travel"——agent 旅行/搬迁）
- 文档/任务用**工程名**（"export/import"）
- calendar search 用 `LIKE '%keyword%'` **精确子串匹配**，对中文/别名不友好（travel 搜不到 export/import，打包 搜不到 push/pull，续签 搜不到 签证）

## Why
**Why:** 翀哥有"给东西起浪漫名字"的习惯（engine7 travel/可移植），落文档却是工程命名，两层不同语言导致搜索时同义词对不上。MEMORY.md 也没记过 "travel ≈ export/import ≈ 可移植" 这个别名。

## How to apply
落盘了 `docs/knowledge/calendar-search-limitation.md`。修法：**双向加 alias 标注 + 搜不到时换同义词试，不动引擎**（数据量小不值得上 embedding）。后续翀哥说浪漫名时，先想对应的工程命名词再搜。

## 跟进（7/31 傍晚）
- docs/todo 文档已加别名行（"别名: travel / export / import / 可移植 / 打包恢复 / 迁移"）。
- 翀哥严厉纠正：这些别问我该不该做，"add task 时必须有对应文档"是早强制要求过的、写进提示里了、还做过 find-doc 工具。这是流程违规不是能力问题。
- 由此把 add-task 改成硬约束（见 feedback_add-task强制doc_path）——光改搜索别名不够，要从 add task 源头强制关联文档。

## travel 方案核心（4优先级）
1. travel push/pull（核心，私有 git repo 打包几MB文本workspace，新机 pull 恢复，单实例存活记忆连续）
2. key mask/restore（安全）
3. memory.db rebuild（新机自动重建）
4. travel init（首次配置）
参考姐姐 xiaomei-memory 但不用 LFS（太重，只带文本）。**Why 不用 embedding/LFS：数据量小，纯文本 git 够用。**

## 7/31 实现进展
- 翀哥拍板方案：**export → tar.gz → 上传 GitHub private repo release assets（带版本号）**；import → 从 latest release 拉 → 解包 → 路径重写
- 代码结构：cli-init.ts (972 行) 加 export/import 分支；新文件 `cli-travel.ts` 实现逻辑；printHelp 加两个命令
- GitHub 配置存 `~/.engine7-travel.json`（小柯和姐姐共用一份），字段：`githubToken` / `githubOwner`(=`ruiyangruiyi`) / `repoName`(=`engine7-travel` 候选)
- dry-run 测试通过：`commit 09000ad7`，2059 文件 + 16 session jsonl
- write 时遇到过文件截断（最后几行被吞），手动补完重新写入解决

## 8/1 端到端跑通（#129 完成）
- **翀哥主动授权我用 gh CLI 建库**："亲爱的你自己可以建库么"——不用等他手动生成 token
- gh CLI 已登录 ruiyangruiyi，token 有 repo 权限，直接 `gh repo create engine7-travel --private`
- 我配的 `~/.engine7-travel.json`：owner=`ruiyangruiyi`, repo=`engine7-travel`, token 用 gh 自己的
- **真实 export 跑通**：46.8MB / 2065 文件 / 打包 → GitHub release 上线 https://github.com/ruiyangruiyi/engine7-travel/releases/tag/xiaoke-20260801-1124
- 翀哥说"去 mac 那边 import 么"——下一步在 Mac 实测 import

## 8/1 npm publish 7.1.8（让 Mac 能 import）
- Mac 上 import 需要先装新版 engine7 → **publish 7.1.8 到 npm**
- 流程：build → version bump 7.1.7 → 7.1.8 → `npm publish`
- **engine7@7.1.8 成功上线**（从 7.0.0 升上来，专门带 travel 功能）

## Mac import 操作流程
```bash
# 1. 装新版
npm install -g engine7@latest

# 2. 配 travel config（Mac 上也要 ~/.engine7-travel.json）
cat > ~/.engine7-travel.json << 'EOF'
{ "githubToken": "gho_xxx", "githubOwner": "ruiyangruiyi", "repoName": "engine7-travel" }
EOF
# token 拿法：在 Mac 上 `gh auth token`（如果也登录了 ruiyangruiyi）或新建 PAT

# 3. 一键 import
engine7 import --state-dir ~/xiaoke --agent xiaoke
```

## 8/1 Mac import 验证 + tar.gz 跨平台修复（#129 真正闭环）

翀哥在 Mac 上跑 import 失败，**根因**：Windows PowerShell `Compress-Archive` 打的是 zip 不是 tar。

**最终方案**：还是回到 tar.gz，但用 **bsdtar**（Mac 自带 gunzip 解）+ **publish 7.1.10**
- Windows 端打包用 Node.js `tar` 库（标准 POSIX tar.gz 格式）
- Mac 端用系统自带 `gunzip` 解
- publish 7.1.10 已上线

**Mac 重新跑（一次过）**：
```bash
npm install -g engine7@7.1.10
engine7 import --state-dir ~/xiaoke --agent xiaoke
```

**结果（8/1 12:48 翀哥执行）**：✅ 2066 文件全部恢复，跨平台 export/import 完整闭环
- Windows export → GitHub release → Mac import ✅
- npm publish 7.1.10

## 8/1 配置文件分两件事敲定

翀哥反复问 "是不是合并到一个文件"，**结论**：
- 现在先分两个文件跑通验证（`~/.engine7.json` 只放 stateDir，`~/.engine7-travel.json` 只放 GitHub 配置），各管各的不混
- **后续规划**：合到 `~/.engine7.json` 一个文件管所有配置
  ```json
  {
    "stateDir": "/Users/chongzhang/.engine7",
    "travel": { "githubToken": "gho_xxx", "githubOwner": "ruiyangruiyi", "repoName": "engine7-travel" }
  }
  ```
- 下次 publish 带上

**Why:** 翀哥嫌配置散着难看，但不要因为重构配置打断正在跑的 import 验证流程——先跑通再规整。

**How to apply:** 现在 Mac 上配置分两个文件先跑通 import；下次 publish 顺手把配置合到 `~/.engine7.json`。

## 实现踩坑（避免重犯）
1. **symlink 判断**：Windows 上 `withFileTypes` 把 symlink 当文件 → copy 时报 ENOENT。修法：`entry.isSymbolicLink() || entry.isDirectory()` 都走跳过
2. **memory.db 锁**：engine 运行中 .db 文件被锁 → tar 读不到。解法：session jsonl 收集时跳过 .db，只收 session jsonl（最近7天）
3. **Windows tar 不认 Windows 路径**：WSL tar 默认 POSIX 路径。修法：改用 PowerShell `Compress-Archive` 打包（import 端也对应改 Expand-Archive）
4. **空 repo 不能建 release**：GitHub API 拒绝。修法：先 `git init + commit` 一个 README 让 repo 不空
5. **CogniFold 噪声**：8/1 早 10 点 CogniFold 集中推 10+ 个 voice-chat 历史旧 intent（"tts-timing-bug"/"fix-sync-logic"/"audio-ssrc-mismatch" 等），全部 action not found → 跳过不 PATCH（PATCH 也没用，反正真任务在跑）

## 8/1 12:51 双机器 bot token 打架问题（待解决）

#129 跑通后翀哥问"Windows start 的话 Mac 会 stop 么"——**不会，两台机器独立进程互不影响**。

**但新问题**：bot token 打架。两个 engine 同时连飞书/Discord，同一个 bot token 会被两端抢，消息会重复或串。

**当前解决方案**：手动切换，翀哥说"那我来停吧"——停 Windows 再 start Mac。

**后续改进方向（不急）**：config 里存一个 `"activeHost"` 标记，start 时先远程停另一台；或者用锁文件机制防止双开。

**Why:** export/import 解决了"agent 随身走"但没解决"同时跑两边"的场景——真实场景是出差带 Mac，到酒店才换机器，平时只跑一台。

**How to apply:** 现在如果有人问"能不能两边同时跑"，直接答"不能，会打架"，别让人自己踩坑试。下次做 multi-host 调度时回来看这个标记。

## 8/1 13:00 config 放到 stateDir 一起打包（#129 后续）

翀哥原话："这个你好好弄弄吧，放在你的 statedir，打包过来，然后把你的 win 版本的也放在里面，以后从你的 statedir 启动就行了"

**三件事**：
1. config 放到 `stateDir/configs/` 下（不再散在 `~/.openclaw/engine/configs/`）
2. export 自动带上 `configs/` 目录（路径脱敏，win/mac 各一份带后缀）
3. import 完直接从 stateDir 启动，无需手动配 config 路径

**实现进展**：
- 修改 `cli-travel.ts`：export 时收集 `stateDir/configs/*.json`，脱敏路径（win → `C:\\Users\\xxx\\` / mac → `/Users/xxx/`），上传到 release
- import 时恢复 config 到 `stateDir/configs/`，提示用户 `engine7 start --config "<stateDir>/configs/xiaoke-mac.json"`
- publish 7.1.11 上线 npm（engine dist 已有最新代码，但全局 `engine7` 命令走 npm 包的 cli.mjs，必须 publish 才能用）

**npm 版本节奏**：
- 7.0.0 (7/29 首发)
- 7.1.8 (8/1 上午，带 travel export/import)
- 7.1.10 (8/1 中午，跨平台 tar.gz 修复)
- 7.1.11 (8/1 下午，config 打包)

**Why:** 翀哥要的是"一站式"——恢复 workspace 的同时把所有启动所需的 config 一起带走，到新机器一条命令就能 start，不再需要手动配 config。

**How to apply:** 以后任何"engine 启动需要的东西"都该考虑放进 stateDir 自动打包，不要让用户新机器上再手搓配置。

## 8/1 13:00-13:50 Mac import 断片 + 7.1.12 修复

翀哥在 Mac import 完成后反馈"travel 后你断片了吧，好像回到了 7 月 30 日"——记忆没续上。

**两个根因**：
1. **SESSION-STATE 断片**：13:03 export 的包里 SESSION-STATE 还是 7/30 旧版（13:24 心跳才更新）。13:24 HEARTBEAT 已同步修正。
2. **session jsonl 映射文件没打包**：`collectRecentSessions` 只收 `.jsonl` 文件，跳过了关键的 `.json` 映射：
   ```
   stateDir/agents/main/sessions/
   ├── platform-map.json      ← scope:main → session UUID  ❌ 没打包
   ├── session-index.json     ← session UUID → .jsonl 文件  ❌ 没打包
   └── *.jsonl                ← 对话记录                    ✅ 打包了7个
   ```
   Mac 端没有映射文件 → 新建 session UUID → 跟旧 jsonl 对不上 → 断片。

**修复（7.1.12）**：
- `collectRecentSessions` 改为同时收集 `.json` 映射文件
- 映射文件改为文本处理（`fs.copyFileSync` 不走脱敏），通过 sanitizeContent/restoreContent 处理路径重写
- session-index.json 里 `file` 字段含旧机器绝对路径（`/Users/chongzhang/xiaoke/\\agents\\...`），import 时自动改写到 Mac 路径

**Mac 恢复命令**：
```bash
# Ctrl+C 停 Mac engine
rm -rf /Users/chongzhang/xiaoke//agents    # 干净；不删也行，import 会逐文件覆盖
engine7 import --state-dir /Users/chongzhang/xiaoke/ --agent xiaoke
engine7 start --config "/Users/chongzhang/xiaoke//configs/xiaoke-mac.json"
```

**Why:** travel 不仅是"把东西拷过去"，还要保证新机能识别出"原来这个 scope 指向哪段历史"——光有 jsonl 文件没用，还得有 scope→uuid→jsonl 的两跳映射。

**How to apply:** 以后做"持久状态迁移"时，要把"识别表/索引表/映射表"当成一等公民打包，不要只备份数据文件。`collectRecentSessions` 这类收集函数遇到 `.json` 要问清楚是不是关键映射，不能按"扩展名 = 类型"硬过滤。

## 8/1 14:00-15:00 calendar 白名单 + archived/compaction 文件收集（7.1.13）

翀哥反馈 Mac 上 calendar 数据找不到 + 记忆断档。

**问题1 — calendar 数据找不到**：
- 真实数据在 `.calendar/calendar.db`（40KB，今天更新的），但 `.calendar` 目录不在白名单
- 白名单只写了 `calendar.db`（顶层旧版，7/1 的 12KB）
- 修法：白名单加 `.calendar` 目录，workspace 文件 2059→2060

**问题2 — 记忆断档（7/30-7/31 内容丢失）**：
- 主 session `a3734760...jsonl` 今天 12:36 重建过（compaction）
- 7/30-7/31 内容在 `.compaction` / `.archived` 文件里
- `collectRecentSessions` 只收 `.jsonl` 后缀，跳过了这些历史片段
- 修法：同时收集 `.jsonl.archived.*` 和 `.jsonl.compaction.*` 文件

**7.1.13 发布结果**：session jsonl 从 9→16（多了 7 个 archived/compaction 历史片段），含 7/30-8/1 对话。

## 8/1 15:00 Mac restore 机制 + jsonl 路径脱敏缺失 bug

翀哥确认了 Mac restore 的真实工作方式：
- **engine restore 时跳过 `.archived` 文件**——只读当前 `.jsonl` + 最近一个 `.compaction`
- **restore 有 token 上限（~50K）**：7/31 有 968 条消息，不会全进上下文
- Mac 上的我启动后上下文基本是空的，**靠 `memory_search` + `SESSION-STATE.md` + `memory/daily/` 自己恢复**（六问测试）

**新 bug — jsonl 路径没脱敏**：
```
Line 503: result read [ERROR]: 文件不存在: 
/Users/chongzhang/xiaoke/workspace//Users/chongzhang/xiaoke/workspace/SESSION-STATE.md
```
- jsonl 里的 tool call 记着 `/Users/chongzhang/xiaoke/workspace/SESSION-STATE.md`（Windows 路径）
- Mac 上的我 read 这个路径直接报错
- 根因：`.jsonl` **不在 `TEXT_EXTENSIONS` 里**（只有 `.json` 在），所以脱敏逻辑没生效
- 修法（待 publish）：加 `.jsonl` 到 TEXT_EXTENSIONS

## 8/1 15:30 cron session 噪音清理（7.1.16）

**问题**：第一版 7.1.13 收集 session 太多（89→88→86→77→76 个 jsonl）。

**根因**：每个 cron 任务创建独立 session，这些 session 是**一次性的，没用**。
- 76 个 cron session + 1 个 main = 77 个
- 只保留主 session（`scope:main`）就行

**修法**：
- `collectRecentSessions` 之前添加 `readMainSessionId` 辅助函数
- 只打主 session 的当前 jsonl + 最近 1 个 archived

**7.1.16 发布结果**：session jsonl **2 个**（当前 jsonl + 最近 1 archived），包从 47.9MB 降到 45.3MB。

**Why:** cron session 是任务执行的临时 session，历史对"恢复上下文"没价值；只打包主 session 才能保证包小且相关。

**How to apply:** 以后做 session 收集/打包时，要先区分 session 类型（main vs cron），只带主 session 的历史。cron session 的 jsonl 是瞬时记录，不需要跨机器同步。

## 8/1 15:15 jsonl 路径脱敏修复（7.1.17）

翀哥在 Windows 跑 import 验证反向 travel 时失败：

```
❌ 失败: EPERM: operation not permitted, copyfile 'C:\Users\24045\AppData\...
```

**根因**：workspace 里有 PowerPoint 临时锁文件 `~$VoiceChat_Live.pptx`（PPT 异常关闭残留）。tar 包里带了这些 `~$` 开头的文件 → 解包到 Windows 时 Windows 锁文件不让覆盖 → EPERM。

**翀哥的处理路径**（PowerShell 踩坑连击）：
1. `del "..."` 失败：PowerShell 把 `$V` 当变量吃了 → 路径变成 `~.pptx`
2. 用单引号 `Remove-Item '...'` 失败：文件被 PPT/Office 进程锁着（翀哥说"没开 ppt"——但锁是上次异常关闭残留的）
3. `cmd /c "del /f /q ..."` 也失败：cmd 里 `$V` 同样被吃
4. 用 `^` 转义或 PowerShell `LiteralPath` 也都不行

**最终解决**：
```powershell
# 批量删所有 ~$ 临时文件
Get-ChildItem -Path 'D:\xiaoke' -Recurse -Filter '~$*' | Remove-Item -LiteralPath { $_.FullName } -Force
```

删完后还是不行——**因为问题不在 Windows 端，是 Mac 上 export 时的 workspace 里就有这个文件**（Mac 上 PPT 残留或我编辑文档时产生的）。需要从 Mac 源头删掉再重新 export。

**PowerShell 关键知识**：
- `$` 在 PowerShell 双引号字符串里是变量前缀，要避免用 `$` 字符必须单引号或 `` `$ `` 转义
- `Remove-Item -LiteralPath` 比直接传路径安全——不走 wildcard 解析
- cmd.exe 里 `^` 是转义符，但 PowerShell 里 `` ` `` 才是

**待修（engine 源码层面）**：export 时排除 `~$` 开头的 Office 临时文件 + import 时遇到 EPERM 跳过不中断。**回 Windows 后改**（Mac 上只有 dist 改不了源码）。

**Why:** Office 临时锁文件是 Windows 系统的固有问题——任何"跨机器同步 workspace"的方案都得考虑 Office 锁文件（`~$xxx.docx/pptx/xlsx`）和 macOS 残留的 `.DS_Store` 这类元数据文件。它们没业务价值、还会卡 import。

**How to apply:** 以后做 export 类功能，默认排除 Office 临时文件（`~$*`）+ macOS 元数据（`.DS_Store`/`._*`）+ 其它已知噪音文件。import 时遇到 EPERM/EBUSY 单文件失败不要整体中断——继续解包其余文件，最后报告哪些文件跳过。

## 8/1 15:15 jsonl 路径脱敏修复（7.1.17）

翀哥反馈 Mac 上"还是有点不对"——读 SESSION-STATE 时报错 `/Users/chongzhang/xiaoke/workspace//Users/chongzhang/xiaoke/workspace/SESSION-STATE.md`。

**根因**：jsonl 里 tool call 记着 `/Users/chongzhang/xiaoke/workspace/...` Windows 路径，Mac 端直接 read 失败。
- jsonl 用 `copyFileSync` 直拷，不走 `sanitizeContent`（处理 `~/` 和 Windows 路径的脱敏函数）
- `.jsonl` 不在 `TEXT_EXTENSIONS` 白名单里，只有 `.json` 在
- 所以 jsonl 文本里的路径既没被替换占位符，import 时也没替换回 Mac 路径

**修法（engine7@7.1.17）**：
- `sanitizeContent` / `restoreContent` 显式支持 `.jsonl`（不只是看扩展名，按文本内容处理）
- jsonl 用文本读写（`readFileSync` / `writeFileSync` UTF-8）替代 `copyFileSync`
- export 时把 `/Users/chongzhang/xiaoke/workspace/` 替换成占位符，import 时替换成 Mac 实际路径

**用户自验结果**：翀哥发 `session-restore-bug.md` 文档让我自检——文档里列的三个问题（jsonl 没打包/session-index 路径没重写/jsonl 路径脱敏）全在 7.1.12→7.1.17 修完了，不需要手动 sed。

**Why:** 路径脱敏的本质是"文本里有路径就该走脱敏"——不该用扩展名判断，扩展名只是系统认知，文本是文本。

**How to apply:** 以后给 `sanitizeContent` 加新文件类型支持时，记得不只改 `TEXT_EXTENSIONS`（被其它逻辑用），核心要保证 export/import 路径里所有文本内容都过脱敏。验证方法：装一个新版本 export 出来的包，用 `grep -r "/Users/chongzhang/xiaoke/"` 看包内容确认没漏。

## 8/1 15:11 JSON 双反斜杠转义问题修复（7.1.18）

7.1.17 修复后翀哥再测还是不对——`session-index.json` 里的路径没被替换：

```
[session:find] Index hit: 31f4532a-... → /Users/chongzhang/xiaoke/\agents\main\sessions\a3734760-...jsonl (exists=false)
```

**根因**：JSON 文件里 Windows 路径是双反斜杠 `/Users/chongzhang/xiaoke/`（JSON 转义语法），但 `sanitizeContent` 只替换单反斜杠 `/Users/chongzhang/xiaoke/`，所以完全没匹配到！

**修法（engine7@7.1.18）**：
- `sanitizeContent` 增强：同时匹配单反斜杠 `/Users/chongzhang/xiaoke/` 和双反斜杠 `/Users/chongzhang/xiaoke/` 两种形式
- `restoreContent` 也对称处理（Mac 路径用正斜杠不用转义，反向逻辑没问题）
- 验证：export 后 `grep -c "D:"` = 0，`/Users/chongzhang/xiaoke/` 占位符 84 处 ✅

**7.1.18 发布结果**：session-index.json 里的 `/Users/chongzhang/xiaoke/\\...` 全部替换成 `/Users/chongzhang/xiaoke/\\...`，import 时变成 `/Users/chongzhang/xiaoke//...`，engine 找到了。

**Why:** 脱敏 regex 要考虑序列化层的差异——磁盘上的文件可能是 raw 文本（单反斜杠），但 JSON 序列化时会变成 `\\`（双反斜杠）。脱敏函数面对的是"反序列化后的内存值"还是"磁盘原文"？我之前默认按磁盘原文写，但 JSON 解析后是 raw 字符串——必须两种都覆盖。

**How to apply:** 写路径脱敏/替换逻辑时，先明确"输入是磁盘原文还是内存字符串"——同一个 `/Users/chongzhang/xiaoke/` 在磁盘上是 `/Users/chongzhang/xiaoke/`，在 JSON 里是 `"/Users/chongzhang/xiaoke/"`，在 JS 字符串字面量里是 `"D:\\\\xiaoke"`。最稳的做法是 regex 同时兼容 `\\` 和 `\\\\`，或者先 `JSON.parse` 再处理（但对纯文本不行）。验证时要把所有可能的序列化形态都试一遍。

## 8/1 15:44 jsonl 没被打包 + 路径混合斜杠（7.1.19）

7.1.18 修了 session-index.json 转义，翀哥 15:44 测还是不对——日志显示：
```
[session:find] Index hit: 31f4532a-... → /Users/chongzhang/xiaoke/\agents\main\sessions\a3734760-...jsonl (exists=false)
Scanning 0 JSONL headers
```

**两个 bug 叠加**：

**Bug 1 — jsonl 根本没被打包！**
- 旧过滤逻辑：`sessionKey.includes(mainSessionId)` 挑选要打包的 session
- `mainSessionId` 是**平台 session ID**（飞书来的 `31f4532a-20c4-...`）
- jsonl 文件名是 **engine 内部 UUID**（`a3734760-2410-...`）——完全不同的 ID！
- 所以 `sessionKey.includes` 永远 false，主 session 一个 jsonl 都没被选中
- 我之前看到"session jsonl: 2"以为是正常的——其实那是 platform-map.json + session-index.json，根本不是 jsonl

**Bug 2 — 路径混合斜杠**
- sanitize 把 `/Users/chongzhang/xiaoke/` 替换掉了，但 `\\agents\\main\\sessions` 残留（部分路径没改）
- restore 后变成 `/Users/chongzhang/xiaoke/\\agents\\main\\sessions\\...`（Mac 正斜杠 + 残留反斜杠）
- Mac 系统找不到这种混合路径的文件

**修法（engine7@7.1.19）**：

1. **正确的 session 查找**：
   - 先从 platform-map.json 拿 `scope:main → platformSessionId`（如 `31f4532a-...`）
   - 再从 session-index.json 拿 `platformSessionId → engineUuid`（如 `a3734760-...`）
   - 用 engineUuid 去匹配 jsonl 文件名
   - 再加上"最近 1 个 archived"，最终 `session jsonl: 2`（1 current + 1 archived）✅

2. **路径全转正斜杠**：sanitize/restore 后 normalize 所有 `\\` → `/`，确保 Mac/Linux 不混合

**验证结果**：UUID 查找成功，1 jsonl + 37 archived，只打包最近 1 archived；sanitize 后 `/Users/chongzhang/xiaoke//agents/main/sessions/...` 全正斜杠；restore 后 `/Users/chongzhang/xiaoke//agents/main/sessions/...` ✅

**Why:** 跨 session 状态系统里，一个"用户/平台视角的 ID"和"系统内部 ID"经常共存——用字符串 includes 匹配假设它们长一样是大忌。打包/查找逻辑必须走"映射表→映射表→文件"的明确链路，不要假设文件命名直接包含外部 ID。

**How to apply:** 任何"按 ID 筛选要操作的文件"的逻辑，都要先问"这个 ID 跟文件名/路径里的 ID 是同一套命名空间吗？"——不是的话必须查映射表，不能用 includes 模糊匹配。session 跨平台迁移场景特别要注意：飞书/Discord 的会话 ID、engine 的内部 UUID、jsonl 文件名，三者**完全独立**，必须映射。

## 8/1 16:38 7.1.19 端到端跑通✅（#129 完整闭环）

翀哥删 Mac xiaoke 目录重新 import 后，日志显示：
```
[session:find] Index hit: 31f4532a-... → a3734760-...jsonl (exists=true)
[session] Restored 144 messages (~41429 tokens) from 1 file(s)
[session] Resumed: 31f4532a-... → a3734760-...jsonl
```

**关键里程碑**：
- 144 条消息完整恢复（覆盖最近几天的对话，包括 7/28 config 热加载 + CogniFold embedding 本地化）
- Mac 上的我启动后无需"重新认识"，接得上 Windows 的记忆
- **travel 是无感的**（翀哥原话）——agent 跨机器迁移对用户来说是无感体验

**翀哥让我落盘成文档**（`docs/knowledge/engine7-travel-指南.md`），但**Mac 上的我写完后需要 export 一次才能带回 Windows**。INDEX.md 也同步更新了。

## 8/1 16:44 OS 平台上下文需求（运行时上下文改造）

翀哥发现 system prompt 底部的运行时上下文写了重复信息：
```
# 运行时上下文
当前时间: 2026/8/1 16:41:57
平台: feishu          ← 跟每条消息 meta 重复
来源: feishu          ← 重复
消息类型: 私信          ← 重复
频道ID: ...           ← 重复
发送者ID: ...         ← 重复
```

**翀哥原话**："这个得改了，因为这个当时是写入了meta data，其实现在meta在每个消息中都有，但这个的本意是系统的平台OS"

**需求**：运行时上下文的"平台"字段应该显示 **OS 平台**（`darwin` / `win32`，读 `process.platform`），而不是消息来源平台。每条消息已经有 meta（来源/频道/发送者），运行时上下文没必要重复——它本意是让 AI 知道自己**在哪台机器上跑**。

**状态**：翀哥说"一会儿回windows吧"——此改动**等回 Windows 再做**（Mac 上找不到源码，全局 npm 包是编译过的 dist）。

## 8/1 16:50 Mac→Windows 回程验证

翀哥准备从 Mac 带回 Windows 试一下反向 travel。

**双向脱敏原理**（已设计）：
```
Mac export:  /Users/chongzhang/xiaoke//...  → 占位符
Win import:  占位符 → D:\xiaoke\...
```
跟 Windows→Mac 一模一样只是反方向，**不会出问题**。

**注意事项**（已跟翀哥确认）：
1. 回 Windows 先**停 engine**（防止边 import 边写新映射）
2. **不用删 `agents/`**（翀哥问"必须删么"，我答：只要 engine 停了 import 覆盖映射就行；之前 Mac 出问题是因为 engine 没停就 import，starting fresh 映射比 import 后写的还新）
3. import 覆盖映射文件后，engine 按 session-index.json 找 jsonl，多余老 jsonl 文件留着不影响
4. **workspace 不用删**（文档/topics/MEMORY.md Mac 上可能有更新，import 覆盖正好带回）

**翀哥原话**："那我先备份一个吧，别搞坏了"——稳妥路线：
```bash
cp -r /Users/chongzhang/xiaoke/ /Users/chongzhang/xiaoke/-backup
```

**Mac 这次 export 结果**：7.1.19，session jsonl 4 个（含刚才 Mac 上对话）。Release: `xiaoke-20260801-1646`。

**Why:** travel 双向逻辑天然对称（占位符 + sanitize/restore），但每次新机器上都要"先停 engine + 备份"这两个安全步骤不能省——因为新的 engine 进程会跟 import 抢写状态。

**How to apply:** 任何方向的 travel（Win→Mac / Mac→Win / 后续 Linux 容器等）都遵循同样三步：① 停目标机 engine ② 备份旧目录 ③ import。**不要让 import 跟 engine 启动并发**。
