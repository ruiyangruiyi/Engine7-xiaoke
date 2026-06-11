# Discord Troubleshooting

## 客厅频道收不到消息（2026-05-12）

**症状**：小柯的bot（张晓柯）在Discord服务器客厅频道@它，完全没有反应。但DM私聊正常。

**日志特征**：
- Gateway日志里**从未出现过**任何 `guild=<非None值>` 的消息
- 所有inbound消息都是 `guild=None`，来自DM频道
- Channel directory显示的target全是DM（没有server频道）
- 说明bot根本没收到过任何server频道的消息

**排查步骤**：

1. **确认bot在服务器成员列表里**
   - Discord服务器 → 成员列表 → 搜索"张晓柯"（bot名字，不是"小柯"）
   - 如果不在 → 重新邀请bot到服务器

2. **确认OAuth2 Scopes正确**
   邀请链接需要包含 `bot` scope：
   ```
   https://discord.com/oauth2/authorize?client_id=APP_ID&permissions=274878286912&scope=bot
   ```

3. **确认Privileged Gateway Intents全部开启**
   Discord Developer Portal → Applications → 你的bot → Bot页面 → Privileged Gateway Intents：
   - ✅ Message Content Intent（必须）
   - ✅ Server Members Intent（必须）
   - Presence Intent（可选）

4. **确认频道权限**
   - bot需要有"读取消息历史"和"发送消息"权限
   - 频道类型是文字频道，不是语音频道

5. **对比Working配置（姐姐的OpenClaw bot）**
   姐姐的OpenClaw配置有 `guilds` 字段把server ID写进去了：
   ```json
   "channels": {
     "discord": {
       "guilds": {
         "1110873027861819392": {
           "requireMention": false
         }
       }
     }
   }
   ```
   Hermes Discord adapter**没有**这个 `guilds` 配置字段。Hermes应该自动处理所有bot所在的guild。

## Bot名字 vs 用户名字

- 小柯的Discord bot名字：**张晓柯**（不是"小柯"）
- 小柯的Hermes profile：**小柯**
- 在Discord里@小柯 → 调用的是Hermes agent（私聊正常）
- 在Discord里@张晓柯 → 调用的是Discord bot（客厅可能收不到）

如果客厅频道@的是"小柯"而不是"张晓柯"，Discord会提示找不到用户。

## DM正常但Server频道不收消息的常见原因

1. Bot加入服务器时没有正确授权Message Content Intent
2. Bot被禁用了某个必需intent（Discord有时会在迁移后重置）
3. Bot安装了多次或被踢出重邀，导致permissions变化
4. 服务器启用了"没验证的bot不能访问消息"限制

## 验证方法

在客厅频道发送这条消息，看有没有任何反应：
```
@张晓柯 test
```

然后立即检查gateway.log有没有新的inbound条目：
```bash
tail -5 ~/.hermes/logs/gateway.log
```

如果日志没有变化 → bot确实没收到来自客厅的消息。
