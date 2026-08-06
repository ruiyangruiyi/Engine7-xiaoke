---
type: project
created: 2026-06-28
updated: 2026-07-28
tags: [voice-chat, interrupt, stop]
---

# voice-chat 打断机制

## 演进

### v1: 手动按钮 (基线v2)
- 浏览器"🤫请先别说"按钮 → POST /stop → Python stop() + engine interrupt
- 双向链路: 飞书/Discord /stop 也走同一套

### v2: speech_start 自动打断 (试过，太激进)
- VAD 检测到 speech_start 就 stop
- 问题: 嗯一声、咳嗽都会触发

### v3: speech_end 自动打断 (6/28基线v3)
- **翀哥纠正**: 打断应该放在 speech_end，跟 debounce 配合
- VAD 检测 speech_end → ASR识别完 → stop() → POST engine 新请求
- 问题: 只在 speech_end 才打断，我说话时翀哥开口不能立刻停

### v4: 500ms debounce 打断 (7/11)
- **翀哥直播痛点**: "我不能打断你，你一来声音经常打断我，我只能等你说完"
- 翀哥先提"提交说话时打断"（利用已有的1s debounce）
- 我先改 speech_start 立即打断 → 翀哥说"太敏感了，出个声也断了"
- 最终方案：**speech_start → 500ms debounce → 如果还在说话才 stop**
  - `_vad_speaking` 标记 + 异步线程 500ms 后检查
  - speech_end 清除标记 → 咳嗽/叹气/短噪音不触发
- 翀哥原话："B方案 500ms 吧"
- 同时修复：去掉 `avatar._busy` 检查 → 无条件 `avatar.stop()`

## 关键实现 (7/11版本)
- `server.py __init__`: `self._vad_speaking = False`
- `speech_start`: 设标记 + 起 500ms 定时器 → 500ms后检查还在说话才 stop
- `speech_end`: 清标记 + self.stop() + POST engine (保留原逻辑)
- `stop()`: cancel TTS task + cancel callback + 清队列 + 重置 PTS + avatar.stop()
- `avatar.stop()`: 异步线程 SSH curl 173 的 /stop 端点
- bridge.ts: `stopped` flag 拦截 abort 后残余回复

## 7/10 打断 bug 修复历程（10轮迭代）
1. stop_flag 残留 → generate 开始时 clear
2. avatar.stop() 同步 SSH 阻塞 → 改异步线程
3. FlashHead 残留帧 → push worker 检查 stop_flag 丢帧 → 后去掉(队列已清)
4. interrupt() 卡 idle → 不调 interrupt, 手动清队列
5. 恢复时 _pending_audio 残留 + _speech_done 没 clear + _speech_start_pending 残留 → 全清
6. wait_for_completion 死锁 10s → stop_flag set 时跳过
7. push worker stop_flag 检查丢 idle 帧 → 去掉检查, 队列已清不用再丢
8. 说话打断不停 235 → VoiceChatHandler.stop() 加 avatar.stop()
9. avatar.stop() 每次说话都调 → 只在 _busy=True 时调
10. switch_avatar 缺 request: Request 参数 → 加上

## 7/28 — Local TTS 打断后残留音频问题

### 问题
- `/stop` 清 `pcm_queue` + `reset()` 后，浏览器还会"嘟嘟嘟"播完残留
- **autodl 模式没有此问题**（远端正TTS源头直接断，网络传输天然限流，WebRTC track buffer 短）

### 根因
- local TTS 模式：TTS 在本地生成 → PCM 灌进 pcm_queue → aiortc track `recv()` 读取 → WebRTC
- `pcm_queue` 清了，但 **aiortc 内部 RTP 编码 buffer** 还有已编码好的 Opus 包没发完
- JS 层（mute/pause/play/换audioTrack）都清不掉底层 WebRTC 引擎 buffer

### 解决方案（2026-07-28）
- 浏览器方案尝试过：mute 500ms、pause/play、替换 audio track → 都不可靠
- 最终方案：**server 端 `LocalTTSAudioTrack` 层 flush**（不碰浏览器端）
  - `reset()` 设 `_flush_remaining = 25`（500ms 静音帧）
  - `recv()` 在 flush 期间不断发静音帧 → **覆盖 aiortc 内部 buffer 里的残留音频**
  - 500ms 后恢复正常，新音频正常播
- autodl 模式不创建 `LocalTTSAudioTrack`（走 Carpo pull），完全不受影响

## 待优化
- 打断后 playbackSpeed 丢失（copy() 重连问题）
- context 滑动窗口（避免 compact）
- 500ms debounce 需要在直播环境实际验证
