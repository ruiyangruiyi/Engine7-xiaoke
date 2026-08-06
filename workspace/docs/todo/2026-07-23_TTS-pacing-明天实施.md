# avatar=none 本地 TTS 节奏问题 — 调研结果

## 问题
LocalTTSAudioTrack.recv() 没有 pacing，生产速率 > 消费速率，浏览器 NetEQ 累积 → 快速放音

## 已试过（都不对）
1. `expected = t0 + count * 0.02s`（_count 累加） → 错误，停顿后失同步
2. `expected = t0 + _pts / 24000`（_pts 累加） → 错误，可能有别的 bug
3. `else: reset _t0` → 错误，累积误差

## 调研结论（明天实施）
aiortc 完全靠你自己在 recv() 里 sleep，pts 不参与发送节拍。

```python
class TTSAudioTrack(AudioStreamTrack):
    sample_rate = 24000
    def __init__(self):
        super().__init__()
        self._start = None
        self._timestamp = 0

    async def recv(self):
        frame = await self.tts_queue.get()
        if self._start is None:
            self._start = time.time()
            self._timestamp = 0
        else:
            wait = self._start + (self._timestamp / self.sample_rate) - time.time()
            if wait > 0:
                await asyncio.sleep(wait)
        frame.pts = self._timestamp
        frame.sample_rate = self.sample_rate
        frame.time_base = fractions.Fraction(1, self.sample_rate)
        self._timestamp += frame.samples  # 用 frame.samples 不是 len(pcm)
        return frame
```

## 要点
1. pts 必须单调递增
2. 用 `asyncio.sleep(wait)` 不是 time.sleep
3. 生产 > 消费时用 `asyncio.Queue(maxsize=N)` 背压
4. TTS chunk 对齐 `sample_rate/50 = 480` samples（20ms 帧）
5. **本地不限或 maxsize=6000（2 分钟），满了就丢**（不要阻塞 callback）

## 参考
- aiortc discussion #1196
- fastrtc tracks.py 的 next_timestamp
- https://github.com/gradio-app/fastrtc/blob/main/src/fastrtc/tracks.py