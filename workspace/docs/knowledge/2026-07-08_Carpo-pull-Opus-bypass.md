# Carpo Pull 端 Opus 旁路方案调研

**日期**：2026-07-08
**背景**：NetEq 解码后的 PCM 有尖峰/电流音（pyAV mono roundtrip 干净，neteq_pre.opus 干净，但 NetEq 输出不干净）。目标是绕过 NetEq，让 callback 收到原始 Opus 包。

---

## 1. 完整数据通路（push → pull → callback）

```
268 push:
  TTS audio → carpo_oac_bridge.push_audio(audio, pts_ms)
  → Opus encode (mono, 48kHz, 20ms/frame)
  → RTP pack (RTPPacker::packOpusRTPData)
  → calcPtsHZ: delta_pts_hz = (pts - first_stream_pts_) * 48000 / 1000
  → RTP timestamp = 毫秒 × 48
  → UdpPeer::SendTo (UDP)
  → Server: 192.144.156.158:23800
  → MediaReceiver::dealWithRTP → sendPacketToPullers

Pull 接收:
  UdpPeer::processIO (recv RTP)
  → RTPTransport::processIncomingRTP
  → MediaReceiverRegister::incomingPacket
    → RtpHeader = head->getSSRC()
    → getMediaReceiver(SSRC) → AudioRTPReceiver
  → AudioRTPReceiver::IncomingPacket(buf, buf_len)
    → 解析 RTP header (rtp_header_parser_->Parse)
    → payload = buf + 12 (RTP header 12 bytes)
    → 走 KN_ENABLE_NETEQ 分支:
      - neteq_->InsertPacket(rtp_header, payload, buf_len-12)
    → NetEq 内部 JitterBuffer 缓冲 + PLC + stretch
  → popAndDecode (在 pcm_thread_ 里循环)
    → neteq_->GetAudio(...) → decoded PCM
    → packet->length = out_len * num_channels
    → packet->media_buf = int16_t* PCM
  → PullReceiverInner::audioFrameCb
    → getOutPutTimeStamp (PTS rebase)
    → doMediaDataCb(CP_MEDIA_AUDIO, data, dataLen, out_pkt_ts)
  → _delegate.cb->onMediaDataRecv(type, data, dataLen, ts, userdata)
  → Python ctypes callback (carpo.py::PULL_MEDIA_CB)
  → on_media(media_type, data, length, timestamp, user_data)
  → user code: player.write(raw) or save file
```

**关键**：NetEq 在 `AudioRTPReceiver::InsertPacket` 和 `popAndDecode::GetAudio` 之间。

---

## 2. 绕过 NetEq 的四个方案

### 方案 A：在 popAndDecode 里直接返回 Opus 字节

**改动**：`AudioRTPReceiver::popAndDecode` 不调 NetEq.GetAudio，从 NetEq 内获取刚 InsertPacket 的 raw bytes 直接返回。

**SDK 改动**：
- `AudioRTPReceiver::popAndDecode`：改成走 pkt_buffer 简单队列
- `AudioRTPReceiver.hpp`：加 pkt_buffer 字段

**问题**：`packet->media_buf` 类型是 `int16_t*`，callback 把它当 PCM 处理。要么改 capi 接口加 type，要么 Python 端按 Opus 解析。

**复杂度**：SDK 改 1 个文件约 50 行；callback 接口要明确。

---

### 方案 B：新增 MEDIA_TYPE_OPUS 旁路通道

**改动**：
- `capi.h`：加 `CP_MEDIA_TYPE_OPUS = 3`
- `AudioRTPReceiver::IncomingPacket`：NetEq 前直接构造 MediaDataPacket type=OPUS
- `doMediaDataCb` 加 type 分发
- `carpo.py`：加 `MEDIA_OPUS = 2` 常量
- `pull_decode_play.py`：on_media 加 MEDIA_OPUS 处理

**问题**：兼容旧代码（type 还是 1=video），但 callback 逻辑变复杂。

**复杂度**：SDK 改 3-4 个文件约 100 行；Python 加分支。

---

### 方案 C：pkt_buffer 简化路径（最简单）

**改动**：
1. `popAndDecode` 走 `pkt_buffer_->popPacket()`（当 KN_ENABLE_NETEQ 关闭时已经走这个分支，但 popAndDecode 本身还在调 NetEq.GetAudio——这就是之前 receive=0 的原因）
2. 修改 `popAndDecode`：判 `KN_ENABLE_NETEQ` 关闭时从 `pkt_buffer_` 拿 raw bytes 返回
3. Python callback 拿 raw bytes（int16_t* 实际是 Opus bytes），自己 PyAV 解码再 pyaudio 播

**SDK 改动**：`AudioRTPReceiver::popAndDecode` 1 处约 20 行

**Python 改动**：`pull_play_auto.py` 的 on_media 改成 raw bytes + PyAV 解码 + pyaudio 播

**复杂度**：**最小**

---

### 方案 D：SDK 外部 raw socket 抓 RTP

**改动**：Python 用 raw socket 监听 23800 端口（不同 SSRC），解析 RTP header + Opus payload，自己 PyAV 解码 + 播放。

**问题**：
- 需要另起一个 SSRC（不能和 SDK puller 冲突）
- server 端可能限制同一 uid 的拉流数
- 需要手动实现 RTP jitter buffer

**复杂度**：Python 200 行，SDK 不动

---

## 3. 方案对比

| 方案 | SDK 改动 | Python 改动 | 兼容性 | 推荐度 |
|------|---------|-----------|--------|--------|
| A. popAndDecode 改 | 50 行 | 30 行 | 需明确 callback 格式 | ★★ |
| B. 加 MEDIA_TYPE_OPUS | 100 行 | 20 行 | 兼容旧 | ★★ |
| C. pkt_buffer 简化路径 | 20 行 | 30 行 | 完全无 NetEq 路径 | ★★★★ |
| D. 外部 raw socket | 0 行 | 200 行 | SDK 旁路 | ★ |

---

## 4. 推荐：方案 C

**理由**：
- 改动最小（SDK 20 行 + Python 30 行）
- 彻底绕开 NetEq（不需要解码器修正）
- push 端已经验证 opus mono 干净（neteq_pre_mono.pcm + pyav roundtrip）
- Python 端已经有 PyAV 解码代码（之前验证过）
- pyaudio 播单声道 48000Hz 完全可行

**实施步骤**：
1. SDK: `AudioRTPReceiver::popAndDecode` 加 `pkt_buffer` 分支返回 raw bytes
2. SDK: 关掉 `KN_ENABLE_NETEQ`（已经在 AudioRTPReceiver.hpp）
3. Python: `pull_play_auto.py` on_media 收 raw bytes + PyAV opus decode + pyaudio 写
4. push 端保持现状（mono Opus 编码已干净）

**风险**：
- pkt_buffer 满了会丢包（NetEq 有 JitterBuffer + PLC 抗丢包）
- 没有 NetEq 的 stretch/squeeze → 长时间播放可能漂移
- 但 pull_play_auto.py 是短期验证，可接受

---

## 5. 现状文件路径

- `D:/work/code/LovePea/Carpo/Carpo/RtpRtcp/AudioRTPReceiver.cpp` line 296 popAndDecode
- `D:/work/code/LovePea/Carpo/Carpo/RtpRtcp/AudioRTPReceiver.hpp` line 23 KN_ENABLE_NETEQ
- `D:/work/code/LovePea/Carpo/carpo_capi/python/pull_play_auto.py` line 40 on_media
- `D:/work/code/LovePea/Carpo/carpo_capi/python/carpo.py` PULL_MEDIA_CB

## 6. 已验证的事实

- `push_pre_opus.pcm` (编码前 48kHz mono int16 PCM) → 干净 ✅
- `push_post_opus.opus` (本地 PyAV opus roundtrip) → 干净 ✅
- `neteq_pre_mono.pcm` (NetEq 前 Opus, PyAV mono 解码) → 基本干净 ✅
- `neteq_out.pcm` (NetEq 解码后) → 有尖峰 ❌
- 2ch vs 1ch NetEq decoder 都不干净（不只是声道不匹配的问题）
