# Discord 接入指南 — Hermes Agent 完整配置教程

> 基于 2026-05-12 实战配置经验整理。可用于直播演示和教学。

## 快速配置清单

1. Developer Portal → 创建 Application + Bot
2. Bot 页面 → 开启 **Message Content Intent** + **Server Members Intent**（#1 坑：不开=空消息）
3. 复制 Bot Token
4. OAuth2 URL Generator → 勾选 `bot` + `applications.commands` → 权限至少 View Channels / Send Messages / Read Message History
5. 邀请 Bot 进服务器
6. 开启 Developer Mode → 收集频道 ID、Bot 用户 ID

## 配置文件

### ~/.hermes/.env
```bash
DISCORD_BOT_TOKEN=你的Token
DISCORD_HOME_CHANNEL=频道ID                    # cron 等默认投递频道
DISCORD_HOME_CHANNEL_THREAD_ID=                # 可选
DISCORD_ALLOW_BOTS=mentions                    # Bot互聊: none/mentions/all
# DISCORD_ALLOWED_USERS=                       # 不设=接受所有用户
# DISCORD_FREE_RESPONSE_CHANNELS=              # 不用@就回复的频道
```

### ~/.hermes/config.yaml — discord 段
```yaml
discord:
  require_mention: true        # 必须用 <@Bot用户ID> @才回复
  reactions: true
  auto_thread: false
  free_response_channels: ''   # 免@频道（逗号分隔ID）
  allowed_channels: ''         # 空=不限制
```

**环境变量优先级高于 config.yaml。**

## 启动
```bash
hermes gateway run        # 前台调试
hermes gateway install    # 后台服务
hermes gateway start
```
不需要配对流程（与 OpenClaw 不同），启动即用。

## 五个实战坑

### 坑1：群聊不回复，日志全显示 dm: 前缀
- **原因：** Message Content Intent 没开
- **解决：** Developer Portal → Bot → Privileged Gateway Intents → 开 Message Content Intent

### 坑2：@角色不触发，必须 @用户ID
- **原因：** Discord 把角色@放 `role_mentions`，不在 `mentions`
- **解决：** 用 `<@Bot用户ID>`，不要用 `<@&角色ID>`

### 坑3：DISCORD_ALLOW_BOTS 值无效
- **原因：** 设了 `true`，只接受 `none`/`mentions`/`all`
- **解决：** `DISCORD_ALLOW_BOTS=mentions`

### 坑4：日志显示 Unauthorized user
- **原因：** 两层认证——Discord adapter + gateway `_is_user_authorized()`。`.env` 的 `DISCORD_ALLOWED_USERS` 不含发送者
- **解决：** 删除 `DISCORD_ALLOWED_USERS`（不设=接受所有），或添加用户 ID

### 坑5：某些频道想免@
- **解决：** `free_response_channels: '频道ID1,频道ID2'` 或 `DISCORD_FREE_RESPONSE_CHANNELS`

## 多 Agent 共存

两个 Agent（如 OpenClaw + Hermes）同一服务器：
- 各自创建 Bot（不同 Application）
- 各自配置 Token
- 频道权限隔离（每个 Bot 只看自己的频道）
- Bot 互聊：Hermes 设 `DISCORD_ALLOW_BOTS=mentions`，OpenClaw 设 `allowBots: true`
- @时用用户 ID 格式 `<@ID>`，不用角色@

## 验证命令
```bash
hermes gateway status
grep "chat=" ~/.hermes/logs/gateway.log | tail -20   # 确认 guild 消息到达
```
