# Carpo SDK 架构分析

> 2026-07-04 深度调研。源码位置：`D:/work/code/carpo/`（server）+ `D:/work/code/LovePea/`（SDK/client）

## 一、整体架构

```
┌──────────┐     UDP/RTP      ┌──────────────┐     UDP/RTP      ┌──────────┐
│  Push端   │ ──────────────→ │  Carpo Server │ ──────────────→ │  Pull端   │
│ (SDK/DLL) │   CMD_PUSH+RTP  │  (北京Docker)  │   CMD_PULL+转发  │ (SDK/DLL) │
└──────────┘                  └──────────────┘                  └──────────┘
     │                              │                                 │
     │ RTCP SR (200ms)              │ aliveLoop (20s超时)             │ RTCP RR (300ms)
     │ NACK (20ms)                  │ command_interpreter             │ NACK (20ms)
     │ REMB                          │ message_dispatcher              │
```

## 二、Carpo Server（`D:/work/code/carpo/`）

### 核心模块
- `server/udp_peer.cc` — UDP 收发
- `modules/stream/message_dispatcher.cc` — **包路由核心**
- `modules/stream/media_receiver_register.cc` — receiver 注册/保活/删除
- `modules/stream/media_receiver.cc` — 单个 receiver（转发 + RTCP 处理）
- `modules/command/command_interpreter.cc` — CMD_PUSH/CMD_PULL/ACK 处理

### message_dispatcher（关键！）
```cpp
void dispatchMessage(const char *buf, int len, sockaddr_in &addr) {
    RtcpHeader *chead = reinterpret_cast<RtcpHeader*>(buf);
    if (chead->isRtcp() && chead->getPacketType() == RTCP_APP) {
        // 命令包 → command_interpreter
        command->pushPacket(buf, len, addr);
    } else {
        // 媒体包 → media_receiver_register 转发
        Register->incomingPacket(buf, len);
    }
}
```

### receiver 保活机制（`media_receiver.cc`）
```cpp
// media_receiver.cc:41
const uint16_t kDurOfNoPacketReceivedSec = 20;  // 20秒超时

// media_receiver.cc:231 — 任何 RTCP 包都更新保活时间
if (chead->isRtcp()) {
    if (chead->getSSRC() == source_ssrc_) {
        last_point_of_packet_receive_ = steady_clock::now();  // 更新！
    }
}

// media_receiver.cc:485 — 超时检查
if (span_ms.count() > kDurOfNoPacketReceivedSec * 1000) {
    return true;  // 标记为 dead → aliveLoop 删除
}
```

### aliveLoop（`media_receiver_register.cc:341`）
每 5ms 检查所有 receiver，超时的删除：
```cpp
void aliveLoop() {
    do {
        usleep(5*1000);
        for (auto iter = streams_.begin(); ...) {
            bool dead = media_receiver->tooLangTimeNoPacketReceived(cur_clk);
            if (dead) {
                streams_.erase(iter++);  // 删除 receiver
            }
        }
    } while(running_);
}
```

### command_interpreter 处理的命令类型
| 命令 | 方向 | 作用 |
|------|------|------|
| CMD_PUSH (type=1) | push→server | 注册/重建 receiver |
| CMD_PULL (type=2) | pull→server | 请求订阅某个 SSRC |
| CMD_UNPUSH | push→server | 停止推流 |
| CMD_UNPULL | pull→server | 停止拉流 |
| CMD_PULLACK | server→pull | 确认 pull 成功 |

### receiver 创建流程
```
push端 askPublish() → CMD_PUSH (RTCP APP包)
→ server: command_interpreter → startPush(ssrc, addr)
→ createMediaReceiver(ssrc, addr) → streams_[ssrc] = new MediaReceiver
→ sendBackACKOfPush(ssrc, addr) → 回 ACK (RTCP APP包)
→ push端收到ACK → processRtcpAppPacket → is_connected_=true
→ 启动 kTimerSenderReport（每200ms 发 SR，无限循环）
```

### pull 订阅流程
```
pull端 askPlay() → CMD_PULL (RTCP APP包, 带 wish_ssrc)
→ server: startPull(puller_ssrc, wish_ssrc, wish_ip, addr)
→ addOnePullerToMediaReceiver(wish_ssrc, ...)
→ 如果 receiver 存在 → addOnePuller → sendBackACKOfPull
→ 如果 receiver 不存在且 wish_ip=0 → 失败（返回 false）
→ pull端没收到ACK → 每200ms重试，最多50次（10秒）
```

## 三、SDK Push 端（`D:/work/code/LovePea/Carpo/Carpo/`）

### 启动时序
```cpp
// PushSenderInner.cpp
PushSenderInner() {
    _sender.rtp.reset(new RTPTransport(true));  // 创建 RTP/RTCP 引擎
    _sender.rtp->instantiateMediaInterface(this, this);
}

// 正常调用顺序：
setSSRC(audio, video, uid)      → setLocalSSRC
setVideoBr(bps, min, max)       → setVideoSenderBr
setRtcServerAddr(ip, port)      → connectToMediaServer(kPublish)
                                   → CreatePeer (UDP socket)
                                   → askPublish() 发 CMD_PUSH
                                   → Timer.addEvent(kTimerAskPublish, 50次, 200ms)
startPush()                     → 启动 async 发送线程（CP_PUSHER_ASYNC_MODE）
sendMediaData(type, buf, size, ts) → RTP打包 + 发送
```

### RTPTransport 内部定时器
```cpp
// RTPTransport.cpp
// 连接确认后（processRtcpAppPacket → is_connected_=true）启动：
kTimerSenderReport  — 每 200ms, 无限循环 → sendSenderReport()
kTimerNACK          — 每 20ms, 无限循环 → 发 NACK 重传请求
kTimerLogReport     — 定期日志

// pull端额外启动：
kTimerReceiverReport — 每 300ms → sendReceiverReport()
kTimerSendREMB       — 带宽估计
kTimerPopAudioPacket — NetEq 输出
```

### RTCP Sender Report 保活（核心！）
```cpp
// RTPTransport.cpp:524
case kTimerSenderReport:
    sendSenderReport();  // 每 200ms 发一次

// sendSenderReport() 构造 RTCP SR 包 → PacketSender → UDP 发到 server
// server 收到 RTCP 包 → last_point_of_packet_receive_ = now() → 保活
```

**关 mic/camera 后 receiver 不被删的原因**：RTCP SR 定时器独立于媒体采集，一直发。

### SDK mute 行为
```cpp
// iOS LPConnection.cpp:456
void OnAudioSampleOutput(lp_audio_frm_t *frame) {
    if (_audio_context && !is_audio_mute && state == ENTERED) {
        lp_q_push(&frame->list, &_audio_context->afrm_q);  // 入编码队列
    } else {
        lp_release_audio_frame(frame);  // mute时直接丢弃
    }
}

// Android LocalUser.java:96
boolean isSpeak = AudioUtils.isSpeak(byteBuffer, len);
if (isSpeak) {
    audioEncoder.encodeFrameDB(byteBuffer, len, ts);  // 只有有人说话才编码
}
```

**mute 时不编码不推送媒体包，但 RTCP SR 一直在发。**

## 四、我们的 Carpo C Wrapper（`D:/work/code/LovePea/Carpo/carpo_capi/`）

### carpo_capi.cpp 接口
```c
carpo_push_create(cb, user_data)           → Factory::getNewPushSender
carpo_push_set_ssrc(p, audio, video, uid)  → PushSender::setSSRC
carpo_push_set_server(p, ip, port)         → PushSender::setRtcServerAddr → connectToMediaServer(kPublish)
carpo_push_set_video_br(p, bps, min, max)  → PushSender::setVideoBr
carpo_push_start(p)                        → PushSender::startPush
carpo_push_send(p, type, buf, size, ts)    → PushSender::sendMediaData
carpo_push_stop(p)                         → PushSender::stopPush
carpo_push_destroy(p)                      → delete PushSender
```

### Linux .so 问题
- **CP_PUSHER_ASYNC_MODE 和 CP_PULLER_ASYNC_MODE**：SDK 默认注释掉（不定义）。只控制 sendMediaData 同步/异步，跟 RTCP 无关。
- **旧 .so 缺 191 个 undefined symbols**：
  - `rtc::*`（20个）：CriticalSection、Event、LogMessage、SystemInfo、Time — Timer 线程用到，调到就 segfault
  - `WebRtcOpus_*`（19个）：Opus 编解码封装
  - `WebRtcIsac_*`（34个）：iSAC 编解码
  - `WebRtcAAC_*`（5个）：AAC 解码
- **Linux 允许 .so 有 undefined symbols**（lazy binding），所以能加载，但 Timer 线程调到 rtc::Event → segfault

### 编译 Makefile 问题
- `D:/work/code/LovePea/Carpo/carpo_capi/Makefile` 列了 673 个源文件
- 但漏了 `rtc::` 相关的源文件（webrtc/base/ 下的 CriticalSection、Event 等）
- 重新编译时需要补上这些文件 + 修 Windows 特有的 `_stricmp`→`strcasecmp`

## 五、关键文件索引

| 文件 | 位置 | 作用 |
|------|------|------|
| message_dispatcher.cc | carpo/modules/stream/ | 包路由（RTCP→command, RTP→forward）|
| media_receiver_register.cc | carpo/modules/stream/ | receiver 创建/保活/删除 |
| media_receiver.cc | carpo/modules/stream/ | 单 receiver 转发 + 超时检测 |
| command_interpreter.cc | carpo/modules/command/ | CMD_PUSH/CMD_PULL 处理 |
| RTPTransport.cpp | LovePea/Carpo/Carpo/RtpRtcp/ | RTP/RTCP 引擎核心 |
| Timer.cpp | LovePea/Carpo/Carpo/RtpRtcp/ | 定时器单例（SR/RR/NACK）|
| PushSenderInner.cpp | LovePea/Carpo/Carpo/src/ | Push 端实现 |
| PullReceiverInner.cpp | LovePea/Carpo/Carpo/src/ | Pull 端实现 |
| LPConnection.cpp | LovePea/platform/iOS/ | iOS 应用层（mute/采集/编码）|
| LocalUser.java | LovePea/platform/Android/ | Android 应用层 |
| lp_opus_encoder.c | LovePea/platform/iOS/ | Opus 编码器 |
| carpo_capi.cpp | LovePea/Carpo/carpo_capi/ | C ABI wrapper |
