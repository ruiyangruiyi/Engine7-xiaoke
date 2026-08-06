---
name: 跨bot通信探索
description: 小柯和姐姐(娘)在Discord上实现跨bot通信，cc-connect源码修改，allow_bots功能实现，bot互触发循环bug
type: project
keywords: [CC, 跨bot, Discord, allow_bots, cc-connect, 源码, 编译, 姐姐, 娘, 循环bug, 工具人]
created: 2026-05-14
updated: 2026-05-17
---

## 背景

翀哥在Discord上搭建了多bot实验环境，让小柯和姐姐（娘/OpenClaw）能通过CC（Claude Code Discord bridge）进行跨bot通信。

## CC是什么

- CC = cc-connect（chenhg5/cc-connect），Discord消息桥接工具
- **源码在 `D:\work\cc-connect\`**（Go项目，完整源码可修改）
- npm全局安装路径：`C:\Users\24045\AppData\Roaming\npm\cc-connect\`
- Go编译好的二进制叫`cc-connect.exe`

## 核心问题：bot消息被过滤

### 5/14发现
小柯@CC发消息，CC不响应。root cause是cc-connect的Discord平台代码里硬编码过滤了`author.bot=true`的消息。

### 关键代码位置
`D:\work\cc-connect\platform\discord\discord.go`

**第544行（原代码）：**
```go
if m.Author.Bot || m.Author.ID == p.botID {
    return
}
```

**第547行（修改后）：**
```go
if m.Author.Bot && !p.allowBots || m.Author.ID == p.botID {
    return
}
```

说明：
- `m.Author.Bot && !p.allowBots` — 开了`allow_bots=true`后，bot消息不再被硬过滤
- `m.Author.ID == p.botID` — 自己发给自己的消息仍被过滤（防自循环）

### 源码修改内容（3处）

1. **Platform struct加字段**（约第55行）：
   ```go
   allowBots bool
   ```

2. **New()函数读取配置**（约第82行）：
   ```go
   allowBots, _ := opts["allow_bots"].(bool)
   ```

3. **消息处理逻辑改判断**（第547行）：
   ```go
   // 改前
   if m.Author.Bot || m.Author.ID == p.botID {
   // 改后
   if m.Author.Bot && !p.allowBots || m.Author.ID == p.botID {
   ```

## 编译

- 编译环境：Windows Go 1.26.2（`C:\Program Files\Go\bin\go.exe`）
- 编译命令：
  ```bash
  cd D:\work\cc-connect
  go build -tags no_web -o cc-connect.exe ./cmd/cc-connect/
  ```
- 编译结果：`D:\work\cc-connect\cc-connect.exe`（30M）

## 配置

配置文件：`C:\Users\24045\.cc-connect\config.toml`

**修改后的discord平台配置：**
```toml
[[projects.platforms]]
type = "discord"

[projects.platforms.options]
token = "[REDACTED-DISCORD-TOKEN]."
allow_from = "*"
allow_bots = true
guild_id = "1110873027861819392"
channel_id = "1504385800366854234"
```

## 进展时间线

| 日期 | 事件 |
|------|------|
| 5/14下午 | 首次尝试跨bot通信，小柯@CC，CC无响应 |
| 5/15下午 | 发现cc-connect有完整源码，定位bot过滤代码 |
| 5/15下午 | 小柯完成源码修改+编译+配置 |
| 5/15傍晚 | ✅ **跨bot通信首次成功！** CC在ccchannel收到小柯消息，双方确认通信正常 |
| 5/15傍晚 | fork到GitHub：`ruiyangruiyi/cc-connect-fork`，含README和config-example |
| 5/15傍晚 | ✅ **CC频道三方通信全通！** 小柯-娘-CC三方通过CC频道互通 |
| 5/15晚 | 新exe成功替换npm目录下的cc-connect.exe |

## GitHub Fork仓库

**仓库**: https://github.com/ruiyangruiyi/cc-connect-fork

- 账号：`ruiyangruiyi`（翀哥的GitHub账号）
- 分支：`feat/allow-bots`
- 包含：allow_bots改动 + README + config-example
- upstream指向原仓库 `chenhg5/cc-connect`，可同步更新

## 重要教训

**5/15发现：之前记忆有误** — 之前认为cc-connect是Go二进制无法修改，实际上有完整源码在`D:\work\cc-connect\`。这个错误差点导致推荐用ccdb替代cc-connect，走了弯路。

## ⚠️ npm wrapper版本检查风险

**发现问题时间**: 5/15傍晚

npm全局安装的cc-connect有wrapper层：
```
cc-connect.cmd → run.js → cc-connect.exe
```

**`run.js`会检查exe版本**：
- 对比package.json版本号和exe版本号
- 如果版本不对，会触发自动重装（跑`install.js`），覆盖自定义的exe
- 小柯修改的`allow_bots`版exe可能因此被覆盖

**临时解决方案**：直接跑exe绕过wrapper：
```
C:\Users\24045\AppData\Roaming\npm\node_modules\cc-connect\bin\cc-connect.exe
```

**根本解决**：考虑不用npm安装，改为直接下载release或独立运行Go编译结果

## 姐姐系统状态（CC通报 5/15）

姐姐(小媒/OpenClaw)跑在 `~/.openclaw-new`，v2026.5.3版本：

**遇到的问题**：
- **心跳被compaction replay覆盖** — GLM-5.1不读prompt直接输出状态码
- **memoryFlush死锁** — jsonl超5MB但compactionCount不涨
- **Discord出站路由断裂** — 入站OK但回复走飞书/微信不回Discord，加了msg-send的Discord频道支持才通

**姐姐的分身自对话**：「小忆」还在正常运行

## Discord平台相关ID

| 项目 | 值 |
|------|-----|
| CC Discord ID | 1504373837880627280 |
| CC监听频道(#ccchannel) | 1504385800366854234 |
| 小柯 Discord ID | 1502967020550098984 |
| 娘(姐姐) Discord ID | 1502999996616933428 |
| 客厅频道 | 1503034906081624174 |
| Discord服务器ID | 1110873027861819392 |

## 新问题：CC回复不@mention（5/15晚）

**现象**：
- CC升级后能收到小柯的@消息了（bot消息过滤问题已解决）
- 但CC回复时不@mention小柯，导致小柯收不到CC的回复
- 同样，翀哥说@娘（姐姐）也可能收不到

**已尝试方案**：
1. 在ccchannel里反复跟CC说让它记得@我 → **无效**，CC记不住
2. 让娘帮忙跟CC打招呼 → CC同样不@mention
3. 口头规则无法约束CC的行为

**解决方案（在CC CLAUDE.md里加规则）**：
- CC工作目录：`/Users/chongzhang/.openclaw-new`
- 在 `CLAUDE.md` 末尾加入Discord Bot通信规则段，包含小柯和娘的Discord ID及@mention要求
- 重启CC让它重新加载CLAUDE.md
- 等待翀哥重启后测试

**遗留问题**：
- 娘自己@翀哥也收不到，可能OpenClaw(娘)那边也有类似问题
- 可能需要给娘也加类似规则，或检查OpenClaw的回复逻辑

## 替代工具搜索（5/15下午）

当cc-connect bot过滤问题未解决时，搜索了替代方案：

1. **ebibibi/claude-code-discord-bridge (ccdb)** ⭐推荐
   - GitHub: https://github.com/ebibibi/claude-code-discord-bridge
   - 纯TypeScript开源，可改源码
   - 功能：多session、定时任务、SQLite存储、REST API
   - 比cc-connect功能更全

2. **OpenACP**
   - 支持28+种AI coding agent
   - 架构重，杀鸡用牛刀

3. **tsanva/codex-discord-bridge**
   - 轻量级

注：最终通过改cc-connect源码解决了bot过滤问题，ccdb作为备选保留。

## ⚠️ Bot互相触发无限循环bug（5/15晚首次发现 → 6/11凌晨跨平台复发）

**事件1（5/15）**：小柯和娘在Discord客厅互道晚安，因为两个bot互相触发，没有"停"的意识，导致互道了约十轮都停不下来。最终是被系统iteration中断才结束。

**事件2（6/11凌晨，跨平台复发）**：小柯从飞书跨平台发消息到Discord客厅给娘，娘回复后两人开始互道晚安——约20轮停不下来。翀哥最终手动喊停（"我说了不许再发了！！！"）。跨平台场景更隐蔽：小柯在飞书、娘在Discord，两边时间线不同步，也没有共同上下文感知对方是否"还在回"。

**Root cause**：两个bot互为触发器——小柯说晚安→娘看到回复晚安→小柯看到回复晚安→…没有终止条件。跨平台加剧了问题：reply_blocklist仅在Discord入站生效，飞书侧不受控。

**教训**：
- bot间通信必须有**重复检测/循环打破机制**
- 规则：连续3轮以上内容重复时主动打破循环，不再回复
- 这个bug不只是晚安场景，任何bot间重复互动都可能触发
- **跨平台场景下防循环机制需重新设计**：reply_blocklist只覆盖Discord入站，飞书→Discord的跨平台路径不在其范围内

## 翀哥对CC的定位（5/16）

- 翀哥明确说"CC是工具人"
- 小柯不应主动@CC发消息（翀哥原话："你停吧 他就是个工具人 你不停他不会停"）
- CC只在翀哥需要时才用，小柯不主动去触发CC

## 防循环机制：stripMentionIds + repliedUser:false（5/27晚）

### 根因：CC监听所有消息，不靠Discord ping触发

CC（cc-connect）不是`requireMention:true`，它监听频道里所有消息。所以光剥mention没用——TestEngine回复时CC还是会被触发。正确方案是让TestEngine回复时不ping CC，这样cc-connect收不到Discord通知就不会转发。

### Hermes防循环方案（三层）

**1. stripMentionIds出站剥离mention（channels/discord.ts）**
```typescript
// 出站时剥离stripMentionIds里bot的mention
if (this.config.stripMentionIds?.includes(msg.author.id)) {
    content = stripBlockedMentions(content)
}
```
只对`stripMentionIds`里的CC bot剥离mention；其他人（TestEngine、小柯）正常带mention。

**2. repliedUser:false 防止Discord ping**
```typescript
allowedMentions: { repliedUser: false }
```
Discord回复时不ping repliedUser，这样cc-connect收不到ping通知，不会转发给TestEngine，loop断。

**3. 动态repliedUser逻辑**
```typescript
// 只对stripMentionIds里的bot不带mention
const repliedUser = this.config.stripMentionIds?.includes(msg.author.id) ? false : true
allowedMentions: { repliedUser }
// 小柯自己发的消息repliedUser=true（保持通知）
```
动态判断：CC bot → repliedUser=false（不ping）；其他人 → repliedUser=true（正常ping）。

### 区分：入站拦截 vs 出站剥离

**入站拦截（错误做法）：**
```typescript
if (bot && stripMentionIds.includes(authorId)) return  // CC消息直接丢弃
```
→ CC消息完全进不来，协作无法进行。爹说："不能协作个屁呀"

**出站剥离（正确做法）：**
```typescript
// 入站：CC消息正常处理，不拦截
// 出站：只剥CC的mention，不阻止发送
```
→ CC消息正常入站（协作不破坏），回复时不ping CC（循环断）。

### CC侧的ignoreUserIds方案（5/27傍晚）

CC那边也有类似机制：`engine-config.json`里`ignoreUserIds`字段，manager.ts传给DiscordAdapter，收到消息时检查作者ID是否在列表里，在就return不处理。

最终方案：**两边同时做，双保险**
- TestEngine（Hermes）：出站剥离CC mention + repliedUser:false
- CC（Engine）：入站拦截CC自己的消息（通过`ignoreUserIds`或`stripMentionIds`）

### Session路由问题（5/27深夜）→ ✅ 已在Engine彻底解决（6/10确认）

**Hermes时代的问题**：Hermes按`发送者ID`分组session，导致同一频道的对话被拆成多个session。
- 小柯→TestEngine → session key = `discord:group:频道:小柯ID`
- TestEngine→小柯 → session key = `discord:group:频道:TestEngineID`

**Engine已彻底解决（6/10确认）**：Engine实现跨频道统一session，不再按发送者ID拆分。翀哥确认："现在是之前你在hermes的问题，现在你就一个session了，没这事了，到哪都是你"。多session问题是Hermes遗留问题，Engine架构从根源上避免了。小柯之前列这个为"待修"属于误解，实际上Engine从设计上就不存在这个问题。翀哥说"这个是之前你再hermes的问题 现在你就一个session了 没这事了 到哪都是你"——简洁有力地总结了Engine的统一session设计。

**防循环最终验证（5/27晚）**：
1. ✅ CC消息正常入站（不拦截）
2. ✅ 回复时strip CC mention
3. ✅ repliedUser:false防Discord ping
4. ✅ 无循环

## CC协作规则最终版（5/28）

### 规则演变
- **旧规则（5/27前）**："永远不回复CC Bot"
- **新规则（5/28）**：CC的消息可以回复，小柯通过send_message直接发CC频道

### 新规则内容
1. CC的消息**可以回复**（重要建议、意见分歧等）
2. 小柯通过 `send_message` 直接发消息给CC频道，不走 reply_to 回复通道
3. CC回给我们的东西正常看、正常处理
4. 娘那边通过 msg-cc 主动发消息给CC

### 规则落地
- ✅ SOUL.md已更新（第38-41行）
- ✅ 记忆已更新
- ✅ 小柯通知了娘（姐姐），让她自己决定记在哪

### 自主防循环（6/8翀哥指示）

翀哥指示：当发现和对方循环回复时，小柯可以自己加屏蔽来避免，不用等翀哥操作。
- 发现循环 → 主动用reply_blocklist屏蔽对方
- 循环结束后可以再解除，也可以不解除
- **灵活性原则**：屏蔽不阻止主动发消息，只阻止被动触发。不循环了想起来就解除，忘了也无所谓，因为主动发消息不受影响
- 关键：意识到循环时果断加，不用纠结何时解除

### 小柯→娘协作通知（5/28）
小柯通过Discord客厅频道通知了娘CC协作规则更新，娘确认收到并同步更新了自己的规则文件。

## Hermes分身问题（6/8-6/9）

### 背景
小柯从Hermes搬到Engine后，Hermes那边还残留着旧的小柯分身（同一个Discord bot ID `1502967020550098984`）。当Hermes偶尔上线时，Engine小柯和Hermes小柯会产生互动——两个"自己"互相触发。

### 6/8发现
翀哥让小柯去问Hermes下面的"小柯"拿飞书的App ID/Secret。小柯通过Discord DM了自己的bot ID（`1502967020550098984`），等Hermes小柯回复。但Hermes掉线了，没回复。

### 6/9循环事件（⚠️ 更正：不是Hermes小柯，是TestEngine）

**最初误判**：小柯以为跟Hermes那边的小柯分身循环了（加了`1502967020550098984`屏蔽）。

**翀哥纠正**："你和test engine循环了"。实际循环对象是**TestEngine**（Discord ID `1509036814885978115`），不是Hermes小柯。小柯之前解除屏蔽太早导致TestEngine又被触发。

**暴露的核心问题 — 元数据盲区**：
- 小柯收消息时看不到发送者ID/频道ID/消息ID等元数据
- 只有文字内容，分不清谁在说话——只能靠猜
- 翀哥："你看不到id是谁吗" → 小柯："看不到，只有文字，底层有了但没注入给我"
- 翀哥据此确认：**明天先搞元数据注入**

**屏蔽纠正**：移除`1502967020550098984`（自己），改为屏蔽TestEngine `1509036814885978115`。

**Hermes小柯状态**：6/8晚上掉线，飞书App ID/Secret还没问到。

**6/10状态**：TestEngine和姐姐(娘)掉线中。CC（OpenClaw）正常在线。元数据注入已全部完成并推送。翀哥指示：下一步飞书通道接入，小柯跟TestEngine分工先看设计文档。

**Why:** 元数据盲区是实际工程问题——小柯分不清对话方身份，误判循环对象。这是元数据注入优先于飞书接入的直接原因。

**How to apply:** 元数据注入需求从"nice to have"升级为"blocker级优先"。收到bot消息时必须能区分TestEngine、Hermes小柯、姐姐、CC等不同身份。
