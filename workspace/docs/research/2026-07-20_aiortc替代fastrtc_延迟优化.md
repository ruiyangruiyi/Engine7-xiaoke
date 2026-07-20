# aiortc 替代 fastrtc 调研

> 日期：2026-07-20
> 背景：voice-chat audio 延迟 1 分钟，定位到 fastrtc 的 recv() asyncio.sleep 积压问题

## 核心发现

### 1分钟延迟的根因
fastrtc `AudioCallback.recv()`（tracks.py L866-877）用 `frame.time` 计算 `wait` 做"播放速率控制"：
```python
wait = frame.time - (time.monotonic() - _start)
await asyncio.sleep(wait)
```
- 上游 callback 断流后恢复，`_start` 不重置 → wait 变巨大 → 积压
- 这不是 aiortc 的问题，是 fastrtc 自己加的控制

### aiortc 本身
- **sender 侧没有 jitter buffer**（只在 receiver 侧有）
- sender 只管把 `frame.pts` 塞进 RTP timestamp 发出去
- pts 不连续不关心——浏览器 jitter buffer 会补偿（小窗口内）

### sender 侧延迟来源
| 来源 | 延迟 |
|------|------|
| recv() 的 asyncio.sleep | **巨大（fastrtc 坑）** |
| PCM→Opus 编码 | ~20ms |
| H264 编码 | ~33ms@30fps |
| 网络传输 | RTT/2 |

## 设计原则（省延迟）

1. **recv() 不 sleep**，来一帧发一帧
2. **queue maxsize 小**（50左右），满了丢帧不积压
3. **H.264 NAL 直传**需 passthrough encoder（省 33ms 编码）
4. **直传 Opus**需 passthrough encoder（省 decode+encode ~40ms）

## 代码模式

### 自定义 AudioStreamTrack
```python
class PCMTrack(AudioStreamTrack):
    async def recv(self):
        pcm = await audio_queue.get()  # 不 sleep！
        frame = av.AudioFrame.from_ndarray(pcm.reshape(1,-1), format="s16", layout="mono")
        frame.sample_rate = 24000
        frame.pts = self._pts
        frame.time_base = fractions.Fraction(1, 24000)
        self._pts += pcm.shape[0]
        return frame
```

### 自定义 VideoStreamTrack
```python
class BGRTrack(VideoStreamTrack):
    async def recv(self):
        bgr = await video_queue.get()
        frame = av.VideoFrame.from_ndarray(bgr, format="bgr24")
        frame.pts = self._pts
        frame.time_base = fractions.Fraction(1, 90000)
        self._pts += int(90000 / 30)
        return frame
```

### Signaling
- HTTP POST /offer 交换 SDP（最简）
- 浏览器 createOffer → POST → 服务器 createAnswer → 返回

### Queue 满策略
```python
def sdk_audio_callback(pcm):
    try: audio_queue.put_nowait(pcm)
    except asyncio.QueueFull: pass  # 满了直接丢，绝不 sleep
```

## 待验证
- [ ] 写最小 demo：carpo SDK callback → aiortc track → 浏览器
- [ ] 测延迟（对比 fastrtc）
- [ ] H.264 passthrough encoder 可行性
- [ ] pts 不连续时浏览器行为

## 参考
- aiortc 官方 examples: github.com/aiortc/aiortc/tree/main/examples
- fastrtc 源码: D:/work/fastrtc-fork/backend/fastrtc/
- fastrtc 延迟根因: tracks.py L866-877 (AudioCallback.recv 的 asyncio.sleep)
