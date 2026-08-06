---
name: extract/recall切换MiniMax
description: DeepSeek flash欠费后切换到MiniMax-M2.7-highspeed，7秒延迟可接受
type: feedback
---

**背景：** 6/13 DeepSeek flash欠费（已充值300还没到账），extract和recall疯狂报402错误。

**第一次切换（6/13下午）：** 切换到MiniMax-M2.7-highspeed：
- recall：7秒返回（比DeepSeek慢），但翀哥说"慢点就慢点"
- extract：后台跑不阻塞用户，延迟无所谓

**MiniMax M2.7-highspeed已于6/13到期** — 翀哥演示时recall和extract全部报错（非单纯性能慢，而是服务过期直接不可用）。翀哥原话："minimax2.7今天到期了 直接不能用了"

**第二次切换（6/13傍晚16:46左右）：** 翀哥说要演示，recall模型切回**DeepSeek**（实为deepseek-v4-flash）。
- 原因：MiniMax太慢且已到期报错，翀哥原话"recall的模型你换成deepseek吧，太慢了 而且minimax报错"
- 检查后发现当前配置已经是deepseek-v4-flash（下午改MiniMax的那次可能没提交，重启后恢复git版本）
- 注意：演示/直播前翀哥会要求切回快速模型

**第三次切换（6/13晚~20:00）：** 姐姐（娘）的topic-recall也从MiniMax改为DeepSeek-v4-flash（OpenClaw的openclaw.json里直接改）。apiBase格式注意用 `/anthropic` 后缀而非openai-completions。

**总结：** MiniMax是临时替代且已到期，不再可用。recall/extract统一用DeepSeek-v4-flash。模型切换用`/reload`热加载即可生效。⚠️但preview颜色配置不可热加载，改颜色需重启Engine。
