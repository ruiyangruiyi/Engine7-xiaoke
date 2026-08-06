# Carpo 音频链路修复总结

**日期：** 2026-07-05

## 完整链路

```
AutoDL TTS (CosyVoice) → Opus 编码 → Carpo push → 北京 server (UDP 23800) → 本机 Carpo pull → NetEq 解码 → PCM → stereo→mono → 48k→24k resample → buffer 累积 → fastrtc emit → WebRTC → 浏览器
```

## 今天修复的 6 个问题

### 1. PyGILState (callback GIL crash)
Carpo callback 在 C 线程调 Python 函数，没持有 GIL → crash。
**修法：** `carpo_capi.cpp` 用 `PyGILState_Ensure()/Release()` 包裹 callback。

### 2. WebRtcSpl 函数指针 null
x86 平台没初始化 9 个 signal processing 函数指针。
**修法：** `stub_spl.c` 手动指向 C 实现。

### 3. stereo→mono 提取
NetEq 输出 stereo（2ch interleaved），1920B/包 = 480 frames × 2ch × 2B。当 mono 播放变慢 2 倍。
**修法：** `stereo[::2]` 取左声道。

### 4. timestamp 倍率错误
`calcPtsHZ` 把 pts 当毫秒 × sample_rate/1000。push 端传 sample count（960）被乘 48 倍。
**修法：** 加 `DBG_USE_RTP_PTS` 让 timestamp 直接传递。

### 5. remote_ip 缺失
`set_server` 没传 remote_ip（push 端公网 IP），server 不知道转发给谁。
**修法：** 加 remote_ip 参数。

### 6. emit 断音
fastrtc emit timeout=0.1s 太短，queue 短暂为空就返回静音帧打乱节奏。
**修法：** timeout 改 2.0s + buffer 累积到 480 samples 再发。

## fastrtc 集成方案

### server.py (8011) 加 /carpo-trigger 端点

```python
@app.post("/carpo-trigger")
async def carpo_trigger():
    # 1. restart_pull (重新建立 Carpo pull 连接)
    # 2. SSH 到 AutoDL 触发 test_push_stay.py
    # Carpo callback 收到 PCM → asyncio.run_coroutine_threadsafe → _active_handler._audio_queue
    # fastrtc emit() 从 _audio_queue 消费 → 浏览器
```

### 关键代码结构

- **Carpo callback（C 线程）→ asyncio queue：** `asyncio.run_coroutine_threadsafe(queue.put(data), loop)`
- **buffer 累积：** Carpo 每包 48k→24k 后 240 samples，累积到 480 再 push（emit frame_size=480 @24kHz）
- **module-level callback：** ctypes callback 必须是模块级函数，局部函数会被 GC

### test-page.html 加按钮

```javascript
// 连接后显示 "🎧 Carpo推流" 按钮
async function carpoPush() {
    await fetch('http://localhost:8011/carpo-trigger', { method: 'POST' });
}
```

## 已知限制

- push/pull 同公网 IP 时 server 不转发（跨 IP 正常）
- Carpo pull 连接 idle 超时后需要 restart_pull
- 纯 video push 时 `is_connected_` 需要 audio AND video 都 ACK

## 验证结果

- 753 帧 PCM 收到 ✅
- 浏览器播放清晰人声 ✅（翀哥确认"对这次是好的"）
- commit: `95e67caf2`

## aiortc vs fastrtc 对比

| 维度 | aiortc | fastrtc |
|------|--------|---------|
| 底层 | 原生 Python WebRTC | 封装 aiortc |
| WebRTC 协商 | 手动 RTCPeerConnection | 自动（Stream.mount） |
| recvonly | 支持但 track.recv() 不被调（bug） | 不支持（需要 send-receive） |
| send-receive | 需要 MediaStreamTrack | AsyncStreamHandler.emit() |
| Gradio UI | 无 | 自带 Blocks UI |
| 适合场景 | 纯定制 | 快速集成 |

**结论：** 用 fastrtc send-receive 模式（需要浏览器麦克风），emit() 从 Carpo queue 拿 PCM。
