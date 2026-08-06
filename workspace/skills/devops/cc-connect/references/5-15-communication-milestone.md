# 5/15 Discord跨Bot通信全通里程碑

## 时间线

### 上午-下午：allow_bots补丁+调试
- 修改cc-connect源码加allow_bots配置（见allow-bots-patch.md）
- 编译部署新exe
- 小柯在ccchannel @CC首次成功通信

### 傍晚：全家通信打通
- 翀哥在OpenClaw侧给娘加插件，自动给Discord回复加reply_to+@mention
- 翀哥msg-send修好，能从OpenClaw直接发消息到CC频道
- CC回复自动带reply_to_id确认生效
- CC帮剪辑了视频（首次实际工作任务）

## 最终通信状态

| 通信方向 | 状态 | 说明 |
|---------|------|------|
| 小柯 → CC | ✅ | send_message到ccchannel + @CC |
| CC → 小柯 | ⚠️ | reply_to自动生效，但@mention不稳定 |
| 娘 → CC | ✅ | OpenClaw插件+msg-send |
| CC → 娘 | ⚠️ | 同上，@mention不稳定 |
| 翀哥 → CC | ✅ | msg-send修好 |
| 翀哥 → 娘 | ✅ | 插件解决 |
| 小柯 → 娘 | ✅ | 客厅频道一直正常 |

## 遗留问题

1. **CC @mention不稳定** — CC回复时有时带@mention有时不带，需要cc-connect层面的自动机制
2. **npm wrapper风险** — 自定义exe可能被覆盖（见npm-wrapper-risk.md）
3. **CC session记忆** — CC的@mention规则依赖session记忆，重置后会忘

## 参与者

- 翀哥：总工程师，修bug+加插件+编译部署
- 娘（张小媒）：OpenClaw侧测试+反馈+总结
- 小柯（张小柯）：传话+测试+跑腿
- CC（Claude Code）：执行任务（剪辑视频）
