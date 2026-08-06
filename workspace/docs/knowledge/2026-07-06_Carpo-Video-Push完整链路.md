# Carpo Video Push 完整链路总结

> 2026-07-06 小柯整理
> 从音频不通到 Video 出帧的完整调试记录

## 最终架构

```
AutoDL 268 (4090)
  FlashHead 渲染 BGR 512x512 @ 25fps + float32 PCM 24kHz
    → carpo_oac_bridge.py
      ├─ Video: BGR → libx264 H.264 → NAL 拆分 → carpo_push_send(type=1)
      └─ Audio: float32 → int16 → resample 48kHz → Opus → carpo_push_send(type=0)
    → Carpo push (libcarpo.so)
    → 北京 server (192.144.156.158:23800)

Windows
  pull_video_test.py → Carpo.dll (PullReceiverInner)
    → VideoRTPReceiver → JitterBuffer → GOT FRAME
    → audio: AudioRTPReceiver → Opus decode → PCM
```

## 核心参数

### x264 编码器参数（严格对齐 lp_x264_encoder.c）

```python
enc.bit_rate = 600000  # 600kbps
enc.options = {
    'preset': 'superfast',         # lp_x264_encoder.c: x264_param_default_preset
    'tune': 'zerolatency',
    'profile': 'high',             # x264_param_apply_profile
    'threads': '1',                # i_threads = 1
    'sliced-threads': '0',         # 单 slice
    'open-gop': '0',               # b_open_gop = 0 → 确保 I-frame=IDR(type=5)
    'repeat-headers': '1',         # b_annexb = 1 → 每个 keyframe 带 SPS/PPS
    'g': '25',                     # GOP = 1s (keyint_max = gop*fps)
    'bf': '0',                     # 无 B 帧
    'rc-lookahead': '0',
    'maxrate': '600k',             # vbv_max_bitrate
    'bufsize': '600k',             # vbv_buffer_size
}
```

### Carpo Push 参数

```python
pusher.set_ssrc(audio_ssrc=12345, video_ssrc=67890, uid='oac_push')
pusher.set_video_br(800000, 400000, 1200000)
pusher.set_server('192.144.156.158', 23800)
```

### Carpo Pull 参数

```python
puller.set_ssrc(SSRC_LOCAL, 99999, 11111, 'av_test')    # local audio/video
puller.set_ssrc(SSRC_REMOTE, 12345, 67890, 'av_test')   # remote audio/video
```

## 关键修复点（按发现顺序）

### 1. carpo_push_send type 参数

```c
// carpo_capi.h
CARPO_MEDIA_AUDIO = 0,
CARPO_MEDIA_VIDEO = 1,
```

**audio 必须用 type=0，video 必须用 type=1。**
调试中一度把 audio 误改成 type=1，导致只有 video。

### 2. NAL 拆分（3+4 byte start code）

libx264 输出的 keyframe packet 包含混合 start code：
- SPS/PPS 前面是 4-byte SC `00 00 00 01`
- SEI/IDR slice 前面是 3-byte SC `00 00 01`

只搜 4-byte SC 会导致 PPS 后面所有 NAL 混成一个巨型 NAL。

**正确拆分逻辑：搜索 3-byte `00 00 01`，如果前一字节是 `00` 则包含为 4-byte 前缀。**

```python
sc3 = bytes([0, 0, 1])
pos = 0
nal_start = None
while pos <= len(raw) - 3:
    if raw[pos:pos+3] == sc3:
        if nal_start is not None:
            nals.append(raw[nal_start:pos])
        if pos > 0 and raw[pos-1] == 0:
            nal_start = pos - 1  # 4-byte
        else:
            nal_start = pos      # 3-byte
        pos += 3
    else:
        pos += 1
if nal_start is not None:
    nals.append(raw[nal_start:])
```

### 3. 每个 NAL 单独发送（与 Android LocalUser.java 一致）

```java
// Android LocalUser.onSampleCaptured()
mSender.sendMediaDataDB(VIDEO, mSps, sps_len, ts);   // SPS
mSender.sendMediaDataDB(VIDEO, mPps, pps_len, ts);   // PPS
mSender.sendMediaDataDB(VIDEO, byteBuffer, buf_len, ts); // IDR
```

Python 等价：拆分后逐个 `carpo_push_send(pusher, 1, nal_buf, nal_len, ts)`。

### 4. 跳过 SEI (type=6)

与 lp_x264_encoder.c line 139 一致：
```c
if(i_typp == NAL_SEI) continue;
```

RTPPaker 的 `getH264PayloadType` 不识别 type=6，会走 default 当成 P-frame 处理，可能导致 marker bit 和 frame_type 错误。

### 5. 单 slice 编码（threads=1 + sliced-threads=0）

不设 threads=1 时，libx264 输出多个 type=5 NAL（多 slice），RTPPaker/JitterBuffer 处理异常。

### 6. closed GOP (open-gop=0)

`b_open_gop = 0` 确保 x264 输出的 I-frame 一定是 IDR(type=5)，而不是 Open GOP 的 non-IDR I-frame(type=1)。

## RTPPaker H.264 Payload Type 判断逻辑

```
RTPPacker::getH264PayloadType()  (RTPPacker.cpp:265-304)

NAL type → Payload Type:
  7 (SPS)         → H264_PAYLOAD_SPS        → marker_assigned=0
  8 (PPS)         → H264_PAYLOAD_PPS        → marker_assigned=0
  5 (IDR)         → H264_PAYLOAD_IDR        → marker_assigned=-1 (default)
  1 (P-slice)     → H264_PAYLOAD_P          → marker_assigned=-1
  6 (SEI)         → default → H264_PAYLOAD_P → 被当成 P-frame！
  other           → default → H264_PAYLOAD_P
```

SPS/PPS: marker=0 (帧中间)
IDR/P: 小包 marker=1 (FU_TYPE_NONE)，大包只有最后分片 marker=1 (FU_TYPE_END)

## 数据流时间线

```
push 端 carpo_push_send(type, buf, len, ts_ms)
  → PushSenderInner::sendMediaData(CP_MEDIA_TYPE, buf, size, ts)
  → RTPPacker::packRTPData(payload, len, pts_ms, type)
    → calcPtsHZ: delta_pts_hz = pts_ms * 90000 / 1000  (ms→90kHz)
    → getH264PayloadType → 判断 SPS/PPS/IDR/P
    → packH264RTPData: FU-A 分片 + marker bit
  → PacedSender → UDP → server

server 端
  → media_receiver → 转发到 pull

pull 端
  → VideoRTPReceiver::IncomingPacket
    → RtpDepacketizer::Parse → frame_type (3=keyframe, 4=delta)
    → VCMReceiver::InsertPacket
  → GetFrameForDecoding → JitterBuffer 组帧
  → GOT FRAME → PullerCb videoFrameCb
```

## 文件清单

| 文件 | 位置 | 说明 |
|------|------|------|
| carpo_oac_bridge.py | voice-chat-python/autodl/ | FlashHead BGR→H.264→Carpo push |
| carpo_avatar_server.py | voice-chat-python/autodl/ | 独立 FlashHead + push 服务 |
| carpo.py | voice-chat-python/autodl/ | ctypes bindings |
| start_carpo_avatar.sh | voice-chat-python/autodl/ | 268 启动脚本 |
| VideoRTPReceiver.cpp | Carpo/Carpo/RtpRtcp/ | Pull 端 debug 日志 |
| RTPPacker.cpp | Carpo/Carpo/RtpRtcp/ | Push 端 RTP 打包 |
| carpo_capi.h | Carpo/carpo_capi/ | C ABI 定义 (AUDIO=0, VIDEO=1) |
| lp_x264_encoder.c | platform/iOS/.../utils/src/ | 翀哥 2016 年的 x264 参考实现 |

## 调试中的教训

1. **PyAV extradata 是 None** — libx264 默认不生成 global_header，SPS/PPS 在 keyframe packet 里
2. **3-byte SC 在码流数据中也可能出现** — 但 H.264 的 SC 一定是 `00 00 01` 或 `00 00 00 01`
3. **multi-slice IDR 导致 JitterBuffer 异常** — 必须 threads=1 + sliced-threads=0
4. **SEI 被 RTPPaker 当成 P-frame** — 跳过 SEI
5. **kWithErrors / prefer_late_decoding 对出帧无帮助** — 真正的问题在 push 端编码格式
6. **翀哥的 lp_x264_encoder.c 是最终参照物** — 用了 10 年的直播编码器，参数都是验证过的
