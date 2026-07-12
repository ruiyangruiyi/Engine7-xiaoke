# Carpo C Wrapper + Python ctypes 接口

**日期**：2026-07-02
**目标**：把 Carpo C++ 虚函数接口（PushSender）包装成 C ABI，供 Python ctypes 调用。

## 架构

```
Python (carpo.py)
    │ ctypes.CDLL
    ▼
Carpo.dll (C ABI exports)
    │ extern "C"
    ▼
carpo_capi.cpp (C→C++ 桥接)
    │ PushSender virtual interface
    ▼
Carpo SDK (RTP/RTCP + WebRTC)
    │ UDP
    ▼
Carpo Server (Docker)
```

## C ABI 设计

### 文件位置
```
D:/work/code/LovePea/Carpo/carpo_capi/
├── carpo_capi.h      ← C ABI 头文件（56 行）
├── carpo_capi.cpp    ← C Wrapper 实现（91 行）
└── python/
    ├── carpo.py      ← ctypes 绑定（114 行）
    └── test_carpo.py ← 验证脚本
```

### 导出函数（8 个）

```c
// 创建/销毁
carpo_pusher_t* carpo_push_create(carpo_push_event_cb cb, void* user_data);
void carpo_push_destroy(carpo_pusher_t* p);

// 配置
int carpo_push_set_ssrc(carpo_pusher_t* p, uint32_t audio_ssrc, uint32_t video_ssrc, const char* uid);
int carpo_push_set_video_br(carpo_pusher_t* p, int bps, int min_bps, int max_bps);
int carpo_push_set_server(carpo_pusher_t* p, const char* ip, uint16_t port);

// 控制
int carpo_push_start(carpo_pusher_t* p);
int carpo_push_stop(carpo_pusher_t* p);

// 发送数据（核心）
int carpo_push_send(carpo_pusher_t* p, carpo_media_type_t type,
                    const uint8_t* buf, uint32_t size, uint64_t timestamp);
```

### 回调机制

C++ 的 `PushSenderCb` 是虚函数类，通过 `PushCbAdapter` 桥接成 C 函数指针：

```cpp
class PushCbAdapter : public PushSenderCb {
    carpo_push_event_cb cb_;  // C 函数指针
    void* user_data_;
public:
    int onPushEvent(PushSenderCbEvent eventId, int code,
                    void* data, int dataLen, void* userData) override {
        if (cb_) cb_((int)eventId, code, user_data_);
        return 0;
    }
};
```

### 事件 ID

| ID | 名称 | 说明 |
|----|------|------|
| 1001 | BWE | Bandwidth Estimation 带宽估计 |
| 1002 | PUBLISH_TIMEOUT | 推流超时 |
| 1003 | PACKET_LOST | 丢包 |
| 1004 | ROUND_TIME | 往返延迟 |
| 1005 | SBE | Sender Bandwidth Estimation |
| 1006 | PACED_SENDER | 平滑发送 |
| 1008 | SBE_LOST | 发送端丢包估计 |
| 1009 | RBE | Receiver Bandwidth Estimation |
| 1010 | NET_SCORE | 网络评分 |

## Python ctypes 绑定

### CarpoPusher 类

```python
import carpo

lib = carpo.load_lib(r'D:\path\to\Carpo.dll')

with carpo.CarpoPusher(lib, on_event=callback) as p:
    p.set_ssrc(audio_ssrc=12345, video_ssrc=67890, uid='user1')
    p.set_server('127.0.0.1', 23800)
    p.set_video_br(800_000, 400_000, 1_200_000)
    p.start()

    # 发送 Opus 音频帧
    p.send_audio(opus_bytes, timestamp_ms)

    # 发送 H.264 NAL
    p.send_video(h264_nal_bytes, timestamp_ms)

    p.stop()
```

### DLL 加载

Python 加载 Carpo.dll 需要设置 DLL 搜索路径：

```python
import os
CARPO_DLL_DIR = r'D:\...\x64\Release'
os.add_dll_directory(CARPO_DLL_DIR)
os.environ['PATH'] = CARPO_DLL_DIR + ';' + os.environ['PATH']
lib = ctypes.CDLL(r'D:\...\x64\Release\Carpo.dll')
```

或者把 Carpo.dll 及其依赖 DLL 全放到同一个目录。

## 推流验证结果

### 测试脚本
`test_carpo_push.py` — 向 Docker 里的 Carpo Server 推流

### 结果
```
set_ssrc -> 0          ✅
set_server -> 0        ✅ (127.0.0.1:23800)
start -> 0             ✅
send_audio × 5 -> 0    ✅
send_video × 3 -> 0    ✅
```

回调事件流：
- BWE(1001) — 带宽估计持续工作
- PACKET_LOST(1003) — 丢包检测持续工作
- ROUND_TIME(1004) — 往返延迟测量
- SBE(1005) — 发送端带宽估计

服务端返回 HTTP JSON 响应，确认双向通信正常。

## 下一步

- [x] 写 PullReceiver C wrapper（7/3 完成）
- [x] 推真实 Opus 音频 + 双向推拉流测试（7/3 完成，翀哥人耳验证）
- [x] Windows wheel 打包（7/3 完成）
- [ ] Linux .so 编译（等 AutoDL）
- [ ] 集成到 voice-chat 管线

## PullReceiver C Wrapper（7/3 新增）

### 架构

跟 PushSender 对称设计，但多了**媒体数据回调**——收到的远端音视频帧通过 `onMediaDataRecv` 回调返回。

```
Carpo Server ──UDP──→ PullReceiver
                        │
                     onMediaDataRecv (回调)
                        │
                     carpo_pull_media_cb → Python
```

### 导出函数（6 个）

```c
carpo_puller_t* carpo_pull_create(carpo_pull_media_cb media_cb,
                                   carpo_pull_event_cb event_cb,
                                   void* user_data);
int carpo_pull_set_ssrc(carpo_puller_t* p, int ssrc_type,
                        uint32_t audio_ssrc, uint32_t video_ssrc, const char* uid);
int carpo_pull_set_server(carpo_puller_t* p, const char* ip,
                          uint16_t port, const char* remote_ip);
int carpo_pull_start(carpo_puller_t* p);
int carpo_pull_stop(carpo_puller_t* p);
void carpo_pull_destroy(carpo_puller_t* p);
```

### 回调类型

| 类型 | 签名 | 说明 |
|------|------|------|
| `carpo_pull_media_cb` | `void(int type, uint8* data, int len, uint32 ts, void* ud)` | 收到远端音视频帧 |
| `carpo_pull_event_cb` | `void(int event_id, int code, void* ud)` | NETEQ_DELAY/CONNECT_TIMEOUT/NET_SCORE |

### Python 类：CarpoPuller

```python
puller = carpo.CarpoPuller(lib, on_media=my_media_cb, on_event=my_event_cb)
puller.set_ssrc(carpo.SSRC_LOCAL, 12345, 67890, 'user1')
puller.set_ssrc(carpo.SSRC_REMOTE, 12345, 67890, 'user1')
puller.set_server('127.0.0.1', 23800)
puller.start()
# ... on_media 回调接收远端帧 ...
puller.stop()
```

### PullReceiver 事件 ID

| ID | 名称 | 说明 |
|----|------|------|
| 1001 | NETEQ_DELAY | NetEq 抖动缓冲延迟 |
| 1002 | FRAME_DELAY | 帧延迟 |
| 1003 | CONNECT_TIMEOUT | 连接超时 |
| 1004 | PCM_VOLUME | PCM 音量 |
| 1005 | NET_SCORE | 网络评分 |

### 验证结果（7/3）

```
create -> ok            ✅
set_ssrc LOCAL -> 0     ✅
set_ssrc REMOTE -> 0    ✅
set_server -> -1        (UDP 特性，非错误)
start -> 0              ✅
stop -> 0               ✅
```

**注意**：`set_server` 返回 -1 不是错误。UDP 是无连接协议，`connectToMediaServer` 返回异步状态码。PushSender 也有同样行为（-1 但 start/send 全部正常工作）。
