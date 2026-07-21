# 2026-07-19 重构方案：aiortc 替代 fastrtc

## 背景

fastrtc 的 audio track **强制用 `next_timestamp()` 自己算 pts**（tracks.py:704-707），不接受外部 SDK pts。video track 在 send-receive 模式保留原始 frame.pts（tracks.py:202-209），导致 audio/video 时间基不一致。

注释自己写：
```python
# Will probably have to give developer ability to set pts and time_base
pts, time_base = await self.next_timestamp()
new_frame.pts = pts
new_frame.time_base = time_base
```

## 实测数据（7/19 22:07）

- **A-V pts diff (pull 端) = 280ms** — SDK pull 出来时 audio 比 video 慢 280ms
- **A-V pts diff (emit 端) = 200ms** — emit 之后 diff 反而减少 80ms
- 结论：emit 端不是根因，但下一级链路（fastrtc 赋 pts → aiortc 编码 → 浏览器）仍是嫌疑
- pull 端 280ms 是 SDK 端固有，但浏览器端时序可能因为 fastrtc 自算 pts 而进一步错位

## 替代方案：直接用 aiortc

### 架构

```
浏览器 ←──WebRTC──→ aiortc RTCPeerConnection
                    ├── 上行 receive (browser → server)
                    │   ├── AudioStreamTrack.recv → 消费 PCM → VAD → ASR
                    │   └── VideoStreamTrack.recv → 消费 BGR → perception
                    └── 下行 send (server → browser)
                        ├── CarpoAudioTrack (subclass AudioStreamTrack)
                        │   └── recv: 从 queue 拿 PCM + SDK pts → 赋 frame.pts
                        └── CarpoVideoTrack (subclass VideoStreamTrack)
                            └── recv: 从 video frame + SDK pts → 赋 frame.pts
```

### 关键代码框架

```python
# === 1. 信令 endpoint ===
@app.post("/offer")
async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    pc = RTCPeerConnection(configuration=RTCConfiguration(
        iceServers=[
            RTCIceServer(urls=["stun:192.144.156.158:3478"]),
            RTCIceServer(urls=["turn:192.144.156.158:3478"],
                         username="xiaoke", credential="carpo2026"),
        ]
    ))
    pcs.add(pc)
    
    @pc.on("connectionstatechange")
    async def on_state():
        if pc.connectionState == "failed":
            await pc.close(); pcs.discard(pc)
    
    @pc.on("track")
    def on_track(track):
        # 上行：浏览器 → server（直接消费，不碰 pts）
        if track.kind == "audio":
            asyncio.create_task(consume_audio(track))  # VAD/ASR
        elif track.kind == "video":
            asyncio.create_task(consume_video(track))  # perception
    
    # 下行：server → 浏览器（自定义 track 控制 pts）
    pc.addTrack(CarpoAudioTrack(audio_queue))
    pc.addTrack(CarpoVideoTrack(video_state))
    
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return JSONResponse({"sdp": answer.sdp, "type": answer.type})


# === 2. 自定义 audio track（pts 用 SDK）===
class CarpoAudioTrack(AudioStreamTrack):
    """audio 下行 track，pts 用 SDK timestamp"""
    def __init__(self, audio_queue):
        super().__init__()
        self._queue = audio_queue
    
    async def recv(self) -> AudioFrame:
        # queue 存 (chunk_24k_float32, decode_ts, sdk_pts_ms)
        chunk, _, sdk_pts_ms = await self._queue.get()
        # float32 → int16
        int16 = (chunk * 32768).clip(-32768, 32767).astype(np.int16)
        frame = AudioFrame.from_ndarray(int16.reshape(1, -1), format='s16', layout='mono')
        frame.sample_rate = OUTPUT_SR  # 24000
        # pts: sdk_pts_ms 转成 time_base 的 ticks
        # time_base = 1/sample_rate，pts = samples 累计
        # 简化：直接用 sdk_pts_ms * sample_rate / 1000
        frame.pts = int(sdk_pts_ms * OUTPUT_SR / 1000)
        frame.time_base = fractions.Fraction(1, OUTPUT_SR)
        return frame


# === 3. 自定义 video track（pts 用 SDK）===
class CarpoVideoTrack(VideoStreamTrack):
    """video 下行 track，pts 用 SDK timestamp"""
    def __init__(self, video_state):
        super().__init__()
        self._state = video_state  # 共享 (frame_bgr, sdk_pts_ms)
    
    async def recv(self) -> VideoFrame:
        with carpo_video_lock:
            frame_bgr = carpo_video_frame
            sdk_pts_ms = carpo_video_pts_ms
        if frame_bgr is None:
            await asyncio.sleep(0.04)
            return self._black_frame()
        new_frame = VideoFrame.from_ndarray(frame_bgr, format="bgr24")
        # pts: sdk_pts_ms 转成 90kHz ticks
        new_frame.pts = int(sdk_pts_ms * 90)  # 90000 / 1000
        new_frame.time_base = VIDEO_TIME_BASE  # fractions.Fraction(1, 90000)
        return new_frame


# === 4. 上行 consume_audio/video ===
async def consume_audio(track):
    """浏览器音频上行 → VAD → ASR → engine → TTS → audio_queue（喂下行）"""
    while True:
        frame = await track.recv()
        # 沿用现有 VoiceChatHandler.receive / emit 的逻辑
        ...

async def consume_video(track):
    """浏览器视频上行 → perception"""
    while True:
        frame = await track.recv()
        ...
```

### 改动范围

| 模块 | 改动 | 估时 |
|---|---|---|
| 信令 `/offer` | 新增（30 行） | 1h |
| `CarpoAudioTrack` | 新增（40 行） | 2h（pts 算法 + queue 协调） |
| `CarpoVideoTrack` | 新增（30 行） | 1h |
| `consume_audio/video` | 替代 `receive/video_receive`（50 行） | 1h |
| 删 fastrtc `Stream` + `AsyncAudioVideoStreamHandler` | -200 行 | 0.5h |
| 前端 test-page.html | 信令改 `/offer`（fastrtc 用 ws） | 1h |
| 边界：打断、settings、mute、perception | 沿用现有 | 1-2h |

**总计**：顺利 6-8 小时，踩坑可能 2-3 天。

### 风险

1. **aiortc audio codec 默认是 Opus**，跟 Carpo SDK 上行匹配，下行一样要重编码成 Opus
2. **jitter buffer**：aiortc 有自己的 jitter buffer，可能跟 fastrtc 不同
3. **打 PTS 的算法**：sdk_pts_ms 单位是毫秒，要转成 time_base 的 ticks（audio=samples，video=90kHz ticks），转换不对会触发 aiortc 内部异常
4. **浏览器端 JS**：fastrtc 客户端有自己的一套（quickconnect + datachannel），改成原生 RTCPeerConnection 接口要重写前端
5. **Carpo datachannel（如打断 signal）**：要自己 createDataChannel

### 验证步骤

1. **monkey-patch 验证（先做）**：patch fastrtc tracks.py 的 `next_timestamp`，print 实际 new_frame.pts，对比 a/v pts 差，确认 pts 是不是根因
2. 如果验证是根因 → 实施 aiortc 方案
3. 实施完对比延迟面板：`A-V pts diff (emit)` 应该接近 0，浏览器观感对齐

## 需要保留的 fastrtc 逻辑

- VAD（`SileroVAD`）
- ASR（`SenseVoice`）
- TTS pipeline（engine POST → TTS stream → chunk）
- `_carpo_on_media` SDK pull callback
- audio queue（3 元组带 sdk_pts_ms）
- timing snapshot / latency 面板
- 录制功能（pull 端）

这些都不动，只换 WebRTC 层。
