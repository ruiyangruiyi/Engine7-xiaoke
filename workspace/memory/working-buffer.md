# Working Buffer — 2026-06-18 深夜

## 当前状态
- 翀哥应该睡了，最后消息22:26 "打log看看到底拿到的是哪张图"
- 爹今天21小时（凌晨4:30到22:30），一天修了5个bug

## 明天第一件事
**vision debug log 验证** — 翀哥重启后发张图，立刻看log里：
1. `[vision-debug]` visionDeps 是 NULL 还是有值
2. msgDeps 最终选了哪个 provider/model
3. 图片 base64 前缀是否匹配当前发的图

## 已知线索
- log 打印 `Routing to minimax/MiniMax-M3` 但实际走了 `dashscope/qwen3.7-plus`
- 可能 visionDeps 是 null（config.visionModel 没配或 providerId 不对）
- history 里有旧图片 base64，qwen3.7-plus 可能被旧图干扰
- debug log 加在 engine-startup.ts L1752-1762

## 今天完成
1. ✅ 消息出口三步改造（c53e54c + 1b27ae1 + 276bdab + 8bf8c4b）
2. ✅ session-memory开关bug（c57b18c config.features→config.profile.features）
3. ✅ vision debug log 加好，等重启验证

## 其他待办
- onResult 拦截 debug log 也要跑（消息出口遗留）
- 记忆闭环（翀哥今早第一优先，被挤了两天了）
- deepseek余额不足（记忆提取全失败）
