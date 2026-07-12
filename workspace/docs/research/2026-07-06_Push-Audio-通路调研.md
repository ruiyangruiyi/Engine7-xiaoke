# Carpo Push 端 Audio 发送完整通路

**日期：** 2026-07-06
**目的：** 搞清 audio 从 Python 到 UDP 的完整调用链，定位"push connected 但 audio 没到 server"的问题

---

## 完整调用链

```
Python: pusher.send_audio(opus_bytes, ts)
    ↓
carpo_capi.cpp: carpo_push_send()                    [C ABI]
    ↓
PushSenderInner.cpp: sendMediaData()                 [上层封装]
    ↓ (check _sender.status == Connected)
RTPTransport.cpp: forwardMediaPacket()               [RTP 传输]
    ↓ (check is_connected_)
RTPPaker.cpp: packRTPData() → packOpusRTPData()      [RTP 打包]
    ↓
PacketSender.cpp: SendPacket()                       [包发送]
    ↓
UdpPeer.cpp: 队列 → SendThreadLoop → sendto()        [UDP 发送]
```

---

## 逐步分析 + 关键失败点

### Step 1: `carpo_push_send()` — C ABI 入口

**文件：** `carpo_capi/carpo_capi.cpp:166-170`

```cpp
int carpo_push_send(carpo_pusher_t* p, carpo_media_type_t type,
                    const uint8_t* buf, uint32_t size, uint64_t timestamp) {
    if (!p || !p->sender) return -1;
    return p->sender->sendMediaData((CP_MEDIA_TYPE)type, (uint8_t*)buf, size, timestamp);
}
```

**失败条件：** p 或 p->sender 为 NULL → 返回 -1

---

### Step 2: `PushSenderInner::sendMediaData()` — ⚠️ 关键失败点 #1

**文件：** `Carpo/src/PushSenderInner.cpp:120-183`

```cpp
int PushSenderInner::sendMediaData(CP_MEDIA_TYPE type, uint8_t *buf, uint32_t size, uint64_t timestamp) {
    if(NULL==buf) return KN_FUNCTION_INVALID_ARG;
    if(_comm.exit) return KN_FUNCTION_STATUS_ERROR;

    // 同步模式（CP_PUSHER_ASYNC_MODE 未定义）
    if (_sender.status == _sender.Connected) {
        uint32_t ts = getPacketTimestamp(type, timestamp);
        PacketType rtp_type = (CP_MEDIA_AUDIO == type) ? pkt_audio : pkt_video;
        _sender.rtp->forwardMediaPacket(buf, size, ts, rtp_type);  // ← audio 出口
    } else {
        CP_ERR_LOG("Rtp not connected! drop frame.\n");
    }
    return 0;  // ← 注意：即使 drop 也返回 0！
}
```

**⚠️ 关键：**
1. `_sender.status == _sender.Connected` —— 这是 PushSenderInner 自己的状态机，跟 RTPTransport 的 `is_connected_` **不是同一个！**
2. **即使 drop 帧也返回 0** —— Python 层检查返回值没用
3. `getPacketTimestamp` 把 ms 级 timestamp 转成相对值（减去 baseMediaTs）

**🔴 建议 log 位置 #1：** 这里加 log 看 `_sender.status` 的值。如果不是 Connected，audio 在这里就被丢了。

---

### Step 3: `RTPTransport::forwardMediaPacket()` — ⚠️ 关键失败点 #2

**文件：** `Carpo/RtpRtcp/RTPTransport.cpp:203-234`

```cpp
void RTPTransport::forwardMediaPacket(void *payload, int length, uint32_t pts,
                                PacketType type) {
    if (!is_connected_)        // ← 静默 return！
        return;

    rtp_list = packer->packRTPData(payload, length, pts, rtp_type);
    if (!rtp_list) {           // ← 打包失败
        CP_ERR_LOG("packet rtp list err or sps+pps, type %d.\n", type);
        return;
    }

    for (auto &node : *rtp_list) {
        fixLocalSSRC(node.rtp, type);
        if (type == pkt_video) {
            paced_sender_->EnqueuePacket(...);  // video 走 PacedSender
        } else {
            if (packet_sender_) {
                packet_sender_->SendPacket(...);  // ← audio 直发！
            }
        }
    }
}
```

**⚠️ 两个 is_connected_：**
- Step 2 的 `_sender.status == Connected` — PushSenderInner 的状态
- Step 3 的 `is_connected_` — RTPTransport 的状态

**两层检查都要通过 audio 才能发出去！**

**🔴 建议 log 位置 #2：** line 205 `if (!is_connected_)` 内加 log。
**🔴 建议 log 位置 #3：** line 211 `packRTPData` 返回 NULL 时加 log（已有但加 size 信息）。
**🔴 建议 log 位置 #4：** line 226 `SendPacket` 前后加 log 看 ret 值。

---

### Step 4: `RTPPaker::packRTPData()` → `packOpusRTPData()`

**文件：** `Carpo/RtpRtcp/RTPPaker.cpp:334-412` + `125-166`

```cpp
std::vector<rtp_list_node_t> *RTPPaker::packRTPData(void *payload, int payload_len,
                                                     uint32_t pts, RtpPayloadType type) {
    uint64_t delta_pts_hz = calcPtsHZ(type, pts);
    // audio: delta_pts_hz = pts * 48000 / 1000 = pts * 48
    switch (type) {
        case RTP_PAYLOAD_AUDIO_OPUS:
            return packOpusRTPData(payload, payload_len, delta_pts_hz);
    }
}
```

```cpp
std::vector<rtp_list_node_t> *packOpusRTPData(void *payload, int payload_len, uint32_t pts) {
    int max_real_payload_len = 1390 - 12 - 28 = 1350;
    if (payload_len > 1350) return NULL;  // ← Opus 包太大

    // 构造 RTP 包
    rtp->setPayloadType(OPUS_48000_PT);   // PT = 111
    rtp->setSeqNumber(audio_seq_num_++);
    rtp->setTimestamp(pts);
    rtp->setSSRC(local_audio_ssrc_);
    memcpy(payload区域, payload, payload_len);

    rtp_list->push_back(node);
    return rtp_list;
}
```

**失败条件：** payload > 1350 bytes（Opus 不会这么大）

---

### Step 5: `PacketSender::SendPacket()`

**文件：** `Carpo/RtpRtcp/PacketSender.cpp`

```cpp
int PacketSender::SendPacket(const void *data, int len, CP_UDP_TYPE type) {
    return udp_peer_->sendData(data, len);
}
```

---

### Step 6: `UdpPeer::sendData()` → `sendto()`

**文件：** `Carpo/Network/UdpPeer.cpp`

```cpp
int UdpPeer::sendData(const void *data, int len) {
    // 入队列
    send_queue_.push(data);
    // SendThreadLoop 线程异步发
}
```

或者直接 sendto（看实现）。

---

## 两层状态机总结

```
┌─────────────────────────────────────────────┐
│ PushSenderInner                              │
│   _sender.status: Disconnected → Connected  │
│   ↓ check status == Connected               │
│ RTPTransport                                 │
│   is_connected_: false → true               │
│   ↓ check is_connected_ == true             │
│ forwardMediaPacket → packRTPData → SendPacket│
└─────────────────────────────────────────────┘
```

**push connected log 只代表 RTPTransport::is_connected_=true，不代表 PushSenderInner::_sender.status==Connected！**

---

## 🔴 建议加 log 的 5 个关键位置

| # | 文件:行号 | 函数 | 打什么 | 为什么 |
|---|-----------|------|--------|--------|
| 1 | PushSenderInner.cpp:163 | sendMediaData | `_sender.status` + Connected 值 | **最可能失败点：两层状态机不同步** |
| 2 | RTPTransport.cpp:205 | forwardMediaPacket | `is_connected_` 值 | 确认 RTP 层检查通过 |
| 3 | RTPTransport.cpp:226 | forwardMediaPacket SendPacket 前 | seq + len + ret | 确认包真正发出 |
| 4 | RTPPaker.cpp:131 | packOpusRTPData | payload_len | 确认打包没 NULL |
| 5 | PushSenderInner.cpp:167 | sendMediaData forwardMediaPacket 前 | type + ts + size | 确认数据进入 RTP 层 |

**最关键的是 #1** —— 如果 `_sender.status != Connected`，audio 在 Step 2 就被丢了，根本到不了 RTPTransport。
