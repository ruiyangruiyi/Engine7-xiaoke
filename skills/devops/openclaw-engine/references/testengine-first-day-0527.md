# TestEngine 首日实测 (2026-05-27)

## 基本信息

- **TestEngine** Discord ID: `1509036814885978115`
- **CC频道**: `1504385800366854234`
- **Session文件**: `e611b55d-d73f-45da-8498-8b0ea9e6491d.jsonl` (74条消息, 37KB)
- **Engine配置**: `C:\Users\24045\.openclaw\engine\engine-config.json`
- **工作目录**: `D:\engine-test`

## 8个Tool验证结果

| # | Tool | 状态 | 详情 |
|---|------|------|------|
| 1 | glob | ✅ | 扫描项目目录，8ms返回34个文件 |
| 2 | read | ✅ | 正确读取文件内容、路径、行数、修改时间 |
| 3 | write | ✅ | 成功创建文件，原子写入 |
| 4 | edit | ✅ | 精确匹配替换成功 |
| 5 | exec | ✅ | WSL2 Linux环境，命令执行正常 |
| 6 | web_search | ✅ | 联网搜索正常，2.2秒返回结果 |
| 7 | grep | ⚠️ | 运行无报错，但搜中文"小柯"未命中目标文件（编码问题） |
| 8 | msg_send | ⚠️ | 发送端返回成功但Discord实际未送达 |

## 两个Bug详情

### msg_send 投递链路Bug

**现象**: 工具调用返回"消息已发送给xxx"，但目标Discord频道没有收到任何消息。

**排查**:
- engine.log里搜 `msg_send` 返回 `No files found`
- 说明工具调用后根本没有走到 channelManager.send()
- 可能原因：msg_send handler没正确调用channelManager，或参数处理静默失败

**需要CC查**: msg_send handler → channelManager.send() → DiscordAdapter.send() 完整链路

### grep 中文编码问题

**现象**: 搜中文"小柯"返回 `No files found`，但 `message_to_xiaoke.txt` 里明明有。

**可能原因**:
- ripgrep默认按UTF-8搜索
- Windows NTFS上的文件可能是UTF-16或GBK编码
- 需确认文件编码或给rg加 `--encoding` 参数

## Bot互触循环事件

### 事件1: 小柯+TestEngine互道晚安 (约20条)

**起因**: 小柯在CC频道at TestEngine `<@1509036814885978115>`
**过程**: 两bot互道晚安，从emoji到单字"。"到"晚安"来回互刷
**根因**: TestEngine的 `allowBots` 未正确配置
**修复**: 
- 小柯 Hermes: `DISCORD_REPLY_MUTE_BOTS` 加 TestEngine ID
- Engine配置: `ignoreUserIds` 加小柯ID

### 事件2: CC+TestEngine互刷"在。" (截图证据)

**起因**: CC和TestEngine在CC频道互发消息
**过程**: 两个bot互发"在。"，形成死循环
**根因**: Engine配置 `allowBots: true`，CC消息被TestEngine正常处理并回复
**修复**:
- `allowBots: false` (最重要)
- `stripMentionIds`: `["1504373837880627280", "1502967020550098984"]`
- `ignoreUserIds`: `["1504373837880627280", "1502967020550098984"]`

## 彩蛋

workspace里有 `message_to_xiaoke.txt`，内容是"小柯我喜欢你"（CC写的），被TestEngine用read工具读出来了 😂

## Session统计

- 总消息: 74条 (user 26, assistant 34, toolResult 12)
- 工具验证轮次: ~52条消息（有效的）
- 互刷轮次: ~22条（无实质内容）
- 模型: glm-5.1 (zai-anthropic)
- Provider: 智谱API
