---
type: project
date: 2026-07-11
tags: [voice-chat, CPU, 性能, 架构, FlashHead]
---

# voice-chat CPU 高根因分析

## 现象
- 235: CPU 60%+，268: CPU 74%
- GPU 利用率接近 0%
- 512x512 25fps 不该吃这么多 CPU

## 根因（翀哥 7/11 分析）
**直播版 vs voice-chat 版架构差异：**

### 直播版（低 CPU）
```
FlashHead → C++ streamer → RTMP push
```
全程 C++，无 Python 中转。

### voice-chat 版（高 CPU）
```
FlashHead → Python → PyAV encode → SDK push
```
中间 Python 做数据搬运，每帧都经历：
- C→Python bytes (memory copy)
- bytes→numpy (memory copy)
- numpy→PyAV (memory copy)
- GIL 切换
- 25fps 视频 + 50fps 音频 = 每秒 75 次拷贝 + GIL 争抢

## 验证方法
```bash
top -H -p $(pgrep -f carpo_avatar_server) | head -20
```
看哪个线程在吃 CPU，如果是 Python 主线程就确认了。

## 优化方向
1. **短期**：zero-copy（memoryview / buffer protocol）减少拷贝
2. **长期**：参考直播版 streamer，FlashHead→SDK push 走 C++ 直连，Python 只管 HTTP + TTS

## 关键区别
- 直播版不需要实时交互（RTMP 有 buffer），voice-chat 需要低延迟
- voice-chat 的 PyAV decode→WebRTC emit 也不在直播版里
- 但直播版的 streamer 思路可以复用
