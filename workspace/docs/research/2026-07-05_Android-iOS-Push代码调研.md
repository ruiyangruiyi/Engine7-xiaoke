# Android/iOS Carpo Push 代码调研

**日期：** 2026-07-05

## 调研目的

了解移动端 Carpo push 的完整调用链，排查视频推流问题。

## Android 端

### Push 调用链

```
LocalUser.startPush()
 ├─ Factory::getNewPushSender() → new PushSenderInner() → RTPTransport(true)
 ├─ setSSRC(audioSSRC, videoSSRC, uid)
 │   └─ RTPTransport::setLocalSSRC() → paced_sender_->SetLocalVideoSsrc()
 ├─ setVideoBr(bitrate, min, max)
 │   └─ RTPTransport::setVideoSenderBr() → CongestionController::initSbeBitrate()
 ├─ setRtcServerAddr(ip, port)
 │   └─ RTPTransport::connectToMediaServer(ip, port, kPublish)
 │       └─ askPublish() → askVideoPublish() + askAudioPublish()
 └─ startPush() → 启动异步线程（无 pacing 操作）
```

### 视频编码参数 (H264HardEncoder.java)

| 参数 | 值 |
|------|-----|
| 编码器 | MediaCodec (硬件) |
| profile | Baseline (默认) |
| bitrate | 1Mbps (CBR) |
| frameRate | 24 fps |
| GOP | 2 秒 (KEY_I_FRAME_INTERVAL=2) |
| B-frame | 无 (Baseline) |

### onSampleCaptured → sendMediaData

```java
// LocalUser.onSampleCaptured()
if (mediaFormat == VIDEO_BIT_STREAM) {
    mSender.sendMediaDataDB(data, len, pts, CP_MEDIA_VIDEO);
}
```

### SSRC 数据来源

由信令服务器（Horae）在房间信息更新时分发，填充到 `UserInfo`：
- `localAudioSSRC` / `localVideoSSRC` — 本端 SSRC
- `remoteAudioSSRC` / `remoteVideoSSRC` — 远端 SSRC

## iOS 端

通过 `LovePeaLive` 框架（闭源二进制），公开 API：
```objc
[self.lovePeaLive joinRoomWithRoomID:userID:userName:]
```
内部走同样的 C++ PushSenderInner 路径。无额外 pacing 初始化接口。

## 关键发现

### 1. 没有 PacingRates 显式设置接口

Android/iOS 的 push 流程中，**没有任何代码显式调用 SetPacingRates**。PacedSender 靠 CongestionController 构造时的 `SetBitrates(300000)` 初始激活，之后靠 RTCP ReceiverReport 回传更新。

### 2. initSbeBitrate 不触发回调

`setVideoBr` 调 `initSbeBitrate` → `SetSendBitrate` + `SetMinMaxBitrate`，**不触发** `OnNetworkChanged` 回调。所以用户设的码率不会传给 PacedSender。

### 3. push ACK 后无额外初始化

push 连接 ACK（`kaskPublish`）后只启动 `kTimerSenderReport`（每 200ms 发 SR），**不启动 pacing 相关定时器**。

## 文件清单

| 文件 | 说明 |
|------|------|
| `platform/Android/.../LocalUser.java` | push 入口，编码参数设置 |
| `platform/Android/.../H264HardEncoder.java` | MediaCodec H.264 编码器 |
| `platform/Android/.../CarpoPushSender.java` | JNI 封装 |
| `Carpo/Carpo/src/PushSenderInner.cpp` | C++ push 实现 |
| `Carpo/Carpo/android/jni/carpo_jni.cpp` | JNI 桥接 |
