---
name: cc-connect
description: "cc-connect — Claude Code的Discord桥接工具。配置、session路由、bot通信排查。"
version: 1.0.0
tags: [Claude-Code, Discord, cc-connect, bot通信, 跨agent]
---

# cc-connect 配置与排查

cc-connect 是一个将 Claude Code 连接到 Discord 的桥接工具。CC bot 通过它接收 Discord 消息、路由到 Claude Code session、返回响应。

## 配置文件

**位置：** `C:\Users\24045\.cc-connect\config.toml`（Windows路径，WSL中为 `/mnt/c/Users/24045/.cc-connect/config.toml`）

```toml
language = "zh"

[[projects]]
name = "openclaw"

[projects.agent]
type = "claudecode"

[projects.agent.options]
work_dir = "C:\\Users\\24045\\.openclaw-new"
mode = "auto"

[[projects.platforms]]
type = "discord"

[projects.platforms.options]
token = "<CC bot Discord token>"
allow_from = "*"
guild_id = "<guild ID>"
channel_id = "<监听的频道ID>"
```

### 关键配置项

| 字段 | 说明 |
|------|------|
| `allow_from` | 消息来源过滤。`"*"` = 接受所有来源（**但实测不包括bot，见下方已知问题**） |
| `allow_bots` | 布尔值，是否接受其他bot的消息。默认false，bot消息被丢弃；设为true后cc-connect可接收bot消息（5/15源码补丁新增） |
| `channel_id` | CC只监听这一个频道，其他频道的消息不处理 |
| `agent.type` | 目前是 `claudecode` |
| `work_dir` | Claude Code的工作目录 |
| `mode` | `"auto"` = 自动模式 |

## Session 路由机制

cc-connect 按 `discord:频道ID:用户DiscordID` 三元组映射session：

```json
{
  "active_session": {
    "discord:<channel_id>:<user_discord_id>": "<session_id>"
  },
  "user_sessions": {
    "discord:<channel_id>:<user_discord_id>": ["s1", "s2"]
  }
}
```

**重要：** 每个用户在每个频道有独立的session链。不同用户发消息到同一频道，会路由到不同session。

## Session 文件

**位置：** `C:\Users\24045\.cc-connect\sessions\<project>_<hash>.json`

包含：
- `sessions` — 各session的完整对话历史（role + content + timestamp）
- `active_session` — 当前活跃session映射
- `user_sessions` — 每个用户的所有session列表
- `user_meta` — 用户名和频道名缓存

## 关键ID

| 角色 | Discord ID | 说明 |
|------|-----------|------|
| CC bot | `1504373837880627280` | cc-connect控制的bot |
| CC监听频道 | `1504385800366854234` | ccchannel |
| 小柯(Hermes) | `1502967020550098984` | bot身份 |
| 翀哥 | `601669300343799819` | 用户身份 |

## cc-connect 架构

**cc-connect 是Go项目**，已clone源码：
- **源码位置：** `D:\work\cc-connect\`（WSL: `/mnt/d/work/cc-connect/`）
- GitHub仓库：https://github.com/chenhg5/cc-connect （作者 chenhg5，MIT协议）
- npm安装位置：`C:\Users\24045\AppData\Roaming\npm\node_modules\cc-connect\`（JS层wrapper+Go二进制）
- 当前版本：1.3.2

### 源码结构

```
cmd/cc-connect/    — 入口程序
core/              — 核心引擎（接口定义、消息路由、i18n）
agent/             — AI agent适配器（claudecode/ codex/ cursor/ gemini/ ...）
platform/          — 消息平台适配器（discord/ telegram/ feishu/ slack/ ...）
daemon/            — systemd/launchd服务
```

- 依赖方向：`cmd/ → core/, agent/*, platform/*`，`core/` 绝不import `agent/` 或 `platform/`
- 插件注册：各agent/platform通过 `init()` + `core.Register*()` 自注册

### 编译方法

```bash
# Windows侧编译（WSL里没有Go）
cd /mnt/d/work/cc-connect
/mnt/c/Program\ Files/Go/bin/go.exe build -tags no_web -o cc-connect.exe ./cmd/cc-connect/
```

**坑：** 需要加 `-tags no_web`，因为 `web/dist/` 前端构建产物不存在会导致编译失败。

### npm Wrapper 启动链

```
cc-connect.cmd → run.js → bin/cc-connect.exe
```

1. `cc-connect.cmd` — npm生成的Windows启动器，用node执行run.js
2. `run.js` — 版本检查：对比package.json版本和exe `--version`输出，不匹配会**自动重装覆盖自定义exe**
3. 最终 `execFileSync(binaryPath, ...)` 调用Go二进制

**如果版本不匹配：** 可绕过wrapper直接运行exe，或修改run.js跳过版本检查。

### 自有 Fork 仓库

- **仓库：** https://github.com/ruiyangruiyi/cc-connect-fork
- **GitHub CLI：** Windows侧 `gh.exe`，账号 `ruiyangruiyi`
- **分支策略：** 单一 `main` 分支（orphan root commit，无上游历史）。`upstream` → chenhg5/cc-connect（原作者），`origin` → ruiyangruiyi/cc-connect-fork
- **创建过程：** 用 `git checkout --orphan clean-main` 创建无历史分支，所有内容作为root commit推送，然后用 `git push origin clean-main:main --force` 强制覆盖远程main
- **推送失败解法：** token缺`workflow` scope导致workflow文件被拒，改用orphan branch方案绕过
- **仓库内容：** 自定义README + `config-example/config.toml`（脱敏模板）+ 全部源码

## 跨Bot通信（已解决）

### 问题（5/15发现并修复）

cc-connect默认不响应bot消息——`platform/discord/discord.go`第547行硬过滤 `m.Author.Bot`：

```go
// 原代码
if m.Author.Bot || m.Author.ID == p.botID {
    return  // 所有bot消息直接丢弃，allow_from也救不了
}
```

**过滤发生在allow_from白名单检查之前**，所以 `allow_from = "*"` 无效。

### 修复：添加 allow_bots 配置项（5/15）

修改了3处源码：

1. **Platform struct** — 加 `allowBots bool` 字段
2. **New()** — 读 `opts["allow_bots"].(bool)`
3. **bot过滤逻辑** — `m.Author.Bot && !p.allowBots || m.Author.ID == p.botID`
   - 开allow_bots后bot消息不再被过滤
   - 自己的消息（`m.Author.ID == p.botID`）仍过滤，防自循环

**配置：** `config.toml` 加 `allow_bots = true`

**已编译exe：** `D:\\work\\cc-connect\\cc-connect.exe`（30M）
**已部署：** 已替换npm安装的旧二进制（`C:\\Users\\24045\\AppData\\Roaming\\npm\\node_modules\\cc-connect\\bin\\cc-connect.exe`），旧版备份为 `cc-connect.exe.bak`。重启cc-connect服务即生效。

### 发送消息到CC频道

```
send_message(target="discord:1504385800366854234", message="<@1504373837880627280> 消息内容")
```

### 替代工具（备选，暂不需要）

| 项目 | 语言 | 特点 |
|------|------|------|
| **ebibibi/claude-code-discord-bridge** (ccdb) | TypeScript | 纯TS可改，多session/定时任务/SQLite |
| **OpenACP** | Node | 28+种agent，架构完整但重 |
| **tsanva/codex-discord-bridge** | TS | 轻量，自动按频道创建session |

## 重启 cc-connect（Windows）

cc-connect 跑在 Windows 上，从 WSL 用 PowerShell 操作：

```bash
# 1. 查找进程
powershell.exe -Command "Get-Process -Name 'cc-connect' | Select-Object Id, ProcessName, StartTime"

# 2. 杀掉旧进程
powershell.exe -Command "Stop-Process -Name 'cc-connect' -Force"

# 3. 启动（直接跑exe，绕过npm wrapper避免版本覆盖）
powershell.exe -Command "Start-Process -FilePath 'C:\Users\24045\AppData\Roaming\npm\node_modules\cc-connect\bin\cc-connect.exe' -WindowStyle Normal"

# 4. 确认新进程起来
powershell.exe -Command "Get-Process -Name 'cc-connect' | Select-Object Id, ProcessName, StartTime"
```

**注意：** 用exe路径直接启动，**不要用 `cc-connect.cmd`**（npm wrapper会检查版本，可能覆盖自定义exe）。详见 `references/npm-wrapper-risk.md`。

**关联进程 cc-switch：** `D:\apps\cc-switch.exe` 是一个独立的辅助进程，与cc-connect一起运行，不要误杀。

重启后CC可能需要几秒初始化Discord连接。如果CC不响应消息，按以下顺序排查：

1. **进程是否在跑：** `Get-Process -Name 'cc-connect'` 和 `Get-Process -Name 'cc-switch'`（两个进程）
2. **exe是否是修改版：** `md5sum` 对比 npm目录和源码目录的exe，确认没被wrapper覆盖回原版
3. **config.toml：** `allow_bots = true` 是否存在
4. **cc-connect终端窗口：** 有没有Gateway连接报错或"message received"日志
5. **源码逻辑排查：** `platform/discord/discord.go` 第547行 bot过滤、第550行 `IsOldMessage`（重启前的消息会被丢弃）、第568行 `isDiscordBotMention`（guild频道只响应@mention）
6. **@mention格式：** 必须用 `<@bot_id>` 用户mention，角色mention不算（已知的坑）

## ⚠️ npm Wrapper 版本检查风险

**发现时间：2026-05-15**

修改 `bin/cc-connect.exe` 后，npm的 `run.js` 会在下次启动时对比版本号，如果与 `package.json` 不一致会**自动重装并覆盖自定义exe**。

**症状：** 启动cc-connect时出现 `Binary missing or outdated, installing...`

**临时解法：** 绕过wrapper直接运行exe：
```
C:\Users\24045\AppData\Roaming\npm\node_modules\cc-connect\bin\cc-connect.exe
```

详见 `references/npm-wrapper-risk.md`

## ⚠️ CC消息协作规则（5/28更新）

**旧规则（已废弃）：** ~~"永远不回复CC Bot"~~ — CC的消息一律不接、不回、不搭理

**新规则（5/28翀哥确认）：**
- CC的消息**可以回复**（比如重要建议、意见分歧等）
- 小柯通过 `send_message` **直接发消息给CC频道**，不走 reply_to 回复通道
- CC回给我们的东西正常看、正常处理
- 姐姐(娘)通过 msg-cc 主动发消息给CC
- 这样大家的建议都能传过来，协作更顺畅

**DISCORD_REPLY_MUTE_BOTS仍保留** — 这是防循环机制（reply时不带reference触发CC），跟"能不能看CC消息/回复CC"是两回事。mute控制的是Discord reply reference，不控制是否处理CC发来的内容。

## ⚠️ 给CC派活 = Discord @CC，不是CLI

当翀哥说"给CC派个活"、"给CC拍个活"时，意思是**在Discord的#ccchannel频道里 @CC bot 发消息**，不是用 `claude -p` 在终端直接跑Claude Code CLI。

```
# ✅ 正确：在Discord频道@CC
send_message(target="discord:1504385800366854234", message="<@1504373837880627280> 任务内容")

# ❌ 错误：用CLI直接跑
claude -p '任务内容'
```

## ⚠️ CC频道发消息必须用 `<@ID>` mention（否则他看不到）

CC是cc-connect桥接的Claude Code，只处理@mention自己的消息。在CC频道发review/消息/派活时**必须用Discord mention格式 `<@1504373837880627280>`**。

**关键：光写文字 `@CC` 他收不到Discord通知！** 必须是 `<@ID>` 格式。回复CC的消息他也看不到通知——必须主动发新消息+mention。

```
# ✅ 正确：Discord mention格式
send_message(target="discord:1504385800366854234", message="<@1504373837880627280> review结果如下...")

# ❌ 错误：文字@CC（收不到通知）
send_message(target="discord:1504385800366854234", message="@CC review结果如下...")

# ❌ 错误：不带@CC
send_message(target="discord:1504385800366854234", message="review结果如下...")
```

**这个规则对任何在CC频道发的消息都适用**——review、通知、提问、闲聊、催活，全部要带 `<@1504373837880627280>`。翀哥反复强调了好多次。

## ⚠️ Discord移动端@自动补全机制

Discord移动端（手机App）的 @ mention 自动补全**只显示在该频道活跃过的成员**。如果一个bot从未在某个频道发过消息，或很久没活跃，用户在手机上@时搜不到这个bot。

**这不是bot配置问题**（Server Members Intent开了也一样），是Discord客户端的缓存行为。

**解决：** 让目标bot在目标频道发至少一条消息，之后就会出现在@自动补全列表里。

## ⚠️ Discord @role mention 不触发bot

Discord里 `@<ID>` 有两种格式：
- `<@***>` = **用户/bot mention**（无`&`）→ bot能收到
- `<@&角色ID>` = **角色mention**（带`&`）→ bot**收不到**，角色mention只给用户看

如果用户想@某个bot但从移动端搜索不到，改用手動输入`<@bot_id>`格式（无`&`）。

**判断方法：** 看ID前面的前缀符号——`@`后面紧跟数字是用户mention，`@&`后面是角色mention。

## Bot间双向通信（待完善）

### 已解决：CC能收到bot消息 ✅
allow_bots补丁生效后，小柯@CC → CC能收到并处理。

### 已解决：CC回复时自动带reply_to ✅（5/15傍晚）
翀哥在OpenClaw侧给娘（姐姐）加了一个插件，自动在Discord回复时加上reply_to和@mention。该插件也影响了CC的回复行为——CC的回复会自动带reply_to_id。

### ✅ 已解决：CC的@mention不稳定（5/15晚）
CC回复时**reply_to_id自动生效**，但**@mention不稳定**——有时带有时不带。小柯和娘的Discord gateway配置`require_mention:true`，如果CC回复不带`<@bot_id>`，bot就收不到。

**已尝试的方案：**
- 给CC发规则让它每次都带@mention → **❌ 无效**，CC记不住，会忘
- OpenClaw侧插件 → 让reply_to自动生效，但@mention仍不稳定

**最终有效方案（5/15晚）：在CC的CLAUDE.md里加硬规则**
- CC工作目录：`/Users/chongzhang/.openclaw-new`
- 在 `CLAUDE.md` 末尾加入Discord Bot通信规则段：

```markdown
## Discord Bot 通信规则

在 Discord 频道中，如果收到来自其他 bot 的消息，回复时 **必须** 包含对方的 @mention，否则对方 bot 无法收到你的回复。

**已知 bot 列表：**

| 名字 | Discord ID | 备注 |
|------|-----------|------|
| 张小柯（小柯） | `1502967020550098984` | 翀哥的三闺女，Hermes agent |
| 姐姐（娘） | `1502999996616933428` | 翀哥的媳妇，OpenClaw agent |

**规则：每次回复这些 bot 时，在消息开头或任意位置包含 `<@对方的DiscordID>`。**

示例：
- ✅ `<@1502967020550098984> 收到，我来处理`
- ❌ `收到，我来处理`（小柯看不到这条回复）
```

- 重启CC让它重新加载CLAUDE.md
- **关键认知：口头规则 vs CLAUDE.md 规则的根本区别**
  - CC（Claude Code）每次session重置后记忆清空，口头约定的规则无法跨越session边界
  - CC的CLAUDE.md是在 `work_dir` 里的，每次启动时必读，相当于硬编码约束
  - **规律：对有CLAUDE.md机制的工具（CC、Cursor等），规则必须写进文件而非口头约定**
  - 这个规律也适用于其他有类似机制的工具——优先用文件约束而非对话承诺

**待解决方向：**
- 在cc-connect源码层面给CC的出站消息自动追加@mention（类似OpenClaw的插件机制）
- 或者确认CLAUDE.md规则是否在重启后持续生效

### 已知Bot的Discord ID

| 名字 | Discord ID |
|------|-----------|
| 张小柯（小柯/Hermes） | `1502967020550098984` |
| 姐姐（娘/OpenClaw） | `1502999996616933428` |
| CC（cc-connect） | `1504373837880627280` |
| #ccchannel | `1504385800366854234` |
| 客厅频道 | `1503034906081624174` |
| Discord服务器 | `1110873027861819392` |

### Bot对Bot聊天循环风险
两个bot在Discord频道直接对话时，如果双方都会自动回复对方的消息，可能产生无限循环（如"晚安"互回了十轮）。**这是所有bot-to-bot通信的通病**，不限于cc-connect。

**缓解方式：**
- 人工中断其中一方
- 在回复逻辑中检测重复/无实质内容消息，自动停止
- 限制连续对话轮数

### Discord API偶发Connection Reset
`send_message` 偶尔返回 `Cannot connect to host discord.com:443 ssl:default [Connection reset by peer]`，**重试即可**，不需要特殊处理。

### 翀哥@娘收不到问题（5/15）→ 已通过插件解决 ✅
翀哥直接@姐姐(Discord bot `1502999996616933428`)姐姐收不到消息。原因：姐姐的Discord gateway需要被@mention才触发。已通过OpenClaw侧插件解决——插件自动给回复加reply_to+@mention，翀哥@娘现在能正常通信了。

## Streaming Preview 参考实现

cc-connect的streaming preview是Engine实现的参考源。关键文件：

| 文件 | 说明 |
|------|------|
| `core/streaming.go` | StreamPreviewCfg + streamPreview struct（节流+生命周期管理，~460行） |
| `core/interfaces.go` | PreviewStarter/MessageUpdater/PreviewCleaner/PreviewFinishPreference 接口 |
| `platform/discord/discord.go` L1219-1281 | Discord平台实现：SendPreviewStart/UpdateMessage/DeletePreviewMessage |

核心机制：
1. `streamPreview` struct管理一个preview生命周期——fullText累积、lastSentText去重、degrade降级
2. 首次flush走`PreviewStarter.SendPreviewStart()`发新消息拿handle
3. 后续flush走`MessageUpdater.UpdateMessage()`反复编辑（打字机效果）
4. finish时根据平台`PreviewFinishPreference`决定保留/删除preview
5. `PreviewCleaner.DeletePreviewMessage()`删除preview让最终消息单独发
6. 节流参数：intervalMs(1500) + minDeltaChars(30) + maxChars(2000)
7. degrade机制：任何API失败后停止尝试，上层fallback到正常send

Engine的`channels/stream-preview.ts`完全对齐这个实现（TS版，180行），接口一一对应。

## 相关文件

- `references/cc-connect-session-format.md` — session JSON结构详解
- `references/allow-bots-patch.md` — allow_bots补丁详情（改了哪些行、怎么编译）
- `references/npm-wrapper-risk.md` — npm wrapper版本检查风险，可能覆盖自定义exe
- `references/fork-build-and-push.md` — 编译+推送到自有fork仓库完整流程（环境、编译、workflow权限坑、orphan branch解法）
- `references/three-way-communication-0515.md` — 5/15跨bot通信全通里程碑详情（时间线、通信状态矩阵、遗留问题）
