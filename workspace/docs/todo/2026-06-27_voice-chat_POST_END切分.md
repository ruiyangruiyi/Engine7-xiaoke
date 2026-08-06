# 2026-06-27 voice-chat POST_END 切分机制实施计划

## 背景
voice-chat 连续说话时消息碎片化（12条排队）。翀哥指示：复刻 OAC POST_END 机制，直接搬，先看效果。

## 调研依据
[OAC 语音切分机制调研](../research/2026-06-27_OAC语音切分机制调研.md)

## 任务清单

### Phase 1: POST_END 状态机（核心）
- [ ] 在 server.py 的 VoiceChatHandler 里加 POST_END 状态
  - speech_end 后不立即 POST，进入 POST_END
  - POST_END 等 1 秒（post_end_monitor_samples = 16000）
  - 1 秒内有新 speech_start → 合并，回到 START 状态
  - 1 秒无新语音 → 才 POST 给 engine
- [ ] 验证：连续说话不再碎片化

### Phase 2: 音频累积 + 重连
- [ ] accumulated_speech_audio 累积机制
- [ ] 重连逻辑：POST_END 期间检测到新语音 → cancel + 重发完整音频
- [ ] 验证：停顿后继续说话，ASR 拿到完整音频

### Phase 3（可选）: Smart Turn EOU
- [ ] 加载 smart-turn-v3.1 ONNX 模型
- [ ] 语义判断"说完了吗"
- [ ] 后面再做

## 验证标准
1. 说话有正常停顿 → 不再切成多条消息
2. engine 日志队列 queueSize 不超过 2-3
3. 停顿后继续说 → ASR 结果是完整句子
