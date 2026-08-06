# Carpo SDK H.264 码流输入结构

**日期：** 2026-07-06

## 总览

Carpo SDK 的 push 端接收 H.264 码流，经 RTPPacker 打 RTP 包发送。pull 端 VideoRTPReceiver 收 RTP 包，RtpDepacketizer 解析，VCMReceiver (jitter buffer) 组帧后回调。

## Push 端：sendMediaData 输入格式

### 数据格式
- **必须带 start code**：`00 00 00 01` + NAL data
- `PushSenderInner.cpp:130`：`int naluType = buf[4] & 0x1f`（buf[0..3] = start code，buf[4] = NAL header）
- 每次调用 `sendMediaData(CP_MEDIA_VIDEO, buf, size, timestamp)` 传**一个 NAL unit**（含 start code）

### NAL type 判断（RTPPacker.cpp:265-304 `getH264PayloadType`）
```
nal_type = data[0] & 0x1f  （skip start code 后的第一个字节）

type=7 → SPS（如果 payload_len > SPS_PPS_MAX_LEN，检查是否 SPS+PPS+IDR 组合）
type=8 → PPS
type=5 → IDR (keyframe)
其他 → P (delta frame)
```

### marker bit 规则（RTPPacker.cpp:67-115 `genH264RTPPacket`）
- **Single NAL**（FU_TYPE_NONE，整个 NAL 一个 RTP 包）→ `marker = 1`（帧结束）
- **FU-A 分片**（NAL > MTU）→ 只有最后一片 `marker = 1`
- **SPS/PPS** → `marker_assinged = 0`（强制 marker=0，不是帧结束）

### RTPPacker 处理 SPS/PPS/IDR 的特殊逻辑
```cpp
// RTPPacker.cpp:344-399 packRTPData
case RTP_PAYLOAD_VIDEO_H264:
    type = getH264PayloadType(payload, payload_len);
    if (type == H264_PAYLOAD_SPS) {
        marker_assinged = 0;  // SPS 不标记帧结束
    } else if (type == H264_PAYLOAD_PPS) {
        marker_assinged = 0;  // PPS 不标记帧结束
    }
    // 注释掉的逻辑：原来会把 SPS+PPS+IDR 合成一个包，现在注释了
    return packH264RTPData(payload, payload_len, delta_pts_hz, marker_assinged);
```

## Pull 端：VideoRTPReceiver 解码路径

### IncomingPacket（VideoRTPReceiver.cpp:71-149）
1. `RtpHeaderParser::Parse` — 解析 RTP header
2. `RtpDepacketizer::Parse` — 解析 H.264 payload，判断 frame_type
   - IDR(5) → `frame_type = kVideoFrameKey (3)`
   - non-IDR(1) → `frame_type = kVideoFrameDelta (4)`
3. `receiver_->InsertPacket(vcm_packet)` — 插入 VCMReceiver jitter buffer
4. `GetOrderedVideoPacketLoop` 线程循环调 `GetFrameForDecoding(50ms)`

### JitterBuffer 关键行为
- **必须先收到 keyframe 才会出帧**
- 如果一直没收到 keyframe → `request_key_frame is true`（每 30ms 打一次日志）
- `SetDecodeErrorMode(kNoErrors)` — 不允许解码错误（严格模式）

### 帧回调（VideoRTPReceiver.cpp:283-322 GetOrderedVideoPacketLoop）
```cpp
VCMEncodedFrame* vcm_frame = GetFrameForDecoding(50ms);
if (!vcm_frame) continue;  // 没帧就跳过
// 有帧了
RecvCbParam param;
param.buf = vcm_frame->Buffer();
param.len = vcm_frame->Length();
param.pts = vcm_frame->TimeStamp() / 90;  // 90kHz → ms
param.type = pkt_video;
callback_->videoRtpRecvCallback(&param);  // 回调上层
```

## iOS 端编码器（VideoToolbox）

iOS 端用 VTCompressionSession 编码：
- 输出格式：每个 NAL 带 start code（CMSampleBuffer 里的 CMBlockBuffer）
- keyframe：`CMFormatDescription` 包含 SPS/PPS，IDR 帧的 NAL type=5
- 通过 `fillExternalVideoFrame` → `sendMediaData(CP_MEDIA_VIDEO, ...)` 传入
- **SPS/PPS 单独发**（VideoToolbox 在关键帧前会输出 SPS/PPS 作为单独的 CMBlockBuffer）

## 当前问题（video pull 不出帧）

### 现象
- RTP 包全到了 VideoRTPReceiver（pt=107）
- `depacketizer->Parse` 成功（frame_type=3 或 4）
- `InsertPacket` ret=0（成功插入）
- 但 jitter buffer 一直 `request_key_frame is true`，不出帧

### 根因分析
- frame_type=3（keyframe）只出现在 SPS(type=7) 上
- **IDR(type=5) 应该也是 keyframe(3)，但 push 脚本的 H.264 文件可能没有 IDR slice**
- ffmpeg baseline 生成的第一个 slice 是 type=1（non-IDR），不是 type=5（IDR）
- jitter buffer 要求完整的 IDR keyframe 才能开始解码

### 需要确认
1. push 脚本是否正确发送了 IDR(type=5) 的 NAL
2. ffmpeg `-g 25` 是否真的生成了 IDR slice
3. iOS 端 VideoToolbox 输出的关键帧 NAL type 是否为 5

## 关键代码位置

| 功能 | 文件:行 |
|------|---------|
| sendMediaData NAL type 读取 | `PushSenderInner.cpp:130` |
| getH264PayloadType | `RTPPacker.cpp:265-304` |
| SPS/PPS marker=0 | `RTPPacker.cpp:361,372` |
| genH264RTPPacket marker 逻辑 | `RTPPacker.cpp:67-115` |
| packH264RTPData NAL 分片 | `RTPPacker.cpp:414-470` |
| VideoRTPReceiver::IncomingPacket | `VideoRTPReceiver.cpp:71-149` |
| RtpDepacketizer::Parse | `VideoRTPReceiver.cpp:129` |
| VCMReceiver InsertPacket | `VideoRTPReceiver.cpp:141` |
| GetOrderedVideoPacketLoop | `VideoRTPReceiver.cpp:283-322` |
| JitterBuffer request_key_frame | `VideoRTPReceiver.cpp:213-215` |
