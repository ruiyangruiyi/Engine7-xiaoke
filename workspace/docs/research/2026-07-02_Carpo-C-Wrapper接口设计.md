# Carpo C Wrapper 接口设计 (#20 准备)

**目标：** 把 C++ 虚函数接口（PushSender/PullReceiver）包装成 C ABI，供 Python ctypes 调用。

## 设计原则

1. 最小接口——只暴露 voice-chat 需要的方法
2. C ABI（extern "C"）——ctypes 直接调用，不用 C++ name mangling
3. 回调用函数指针——Python 传 callback 进来

## C API（carpo_capi.h）

```c
#ifdef __cplusplus
extern "C" {
#endif

// ===== 类型 =====
typedef struct carpo_pusher carpo_pusher_t;
typedef struct carpo_puller carpo_puller_t;

typedef enum {
    CARPO_MEDIA_AUDIO = 0,
    CARPO_MEDIA_VIDEO = 1,
} carpo_media_type_t;

// ===== 回调 =====
// PushSender 事件回调
typedef void (*carpo_push_event_cb)(int event_id, int code, void* user_data);
// PullReceiver 数据回调
typedef void (*carpo_media_recv_cb)(int media_type, const uint8_t* data, int len, uint32_t timestamp, void* user_data);
// PullReceiver 事件回调
typedef void (*carpo_pull_event_cb)(int event_id, int code, void* user_data);

// ===== PushSender =====
// 创建推流器
carpo_pusher_t* carpo_push_create(carpo_push_event_cb cb, void* user_data);
// 设置 SSRC
int carpo_push_set_ssrc(carpo_pusher_t* p, uint32_t audio_ssrc, uint32_t video_ssrc, const char* uid);
// 设置视频码率
int carpo_push_set_video_br(carpo_pusher_t* p, int bps, int min_bps, int max_bps);
// 设置 Carpo 服务端地址
int carpo_push_set_server(carpo_pusher_t* p, const char* ip, uint16_t port);
// 开始推流
int carpo_push_start(carpo_pusher_t* p);
// 发送媒体数据（核心方法）
// type: CARPO_MEDIA_AUDIO(传 Opus) 或 CARPO_MEDIA_VIDEO(传 H.264 NAL)
int carpo_push_send(carpo_pusher_t* p, carpo_media_type_t type, const uint8_t* buf, uint32_t size, uint64_t timestamp);
// 停止推流
int carpo_push_stop(carpo_pusher_t* p);
// 销毁
void carpo_push_destroy(carpo_pusher_t* p);

// ===== PullReceiver =====
// 创建拉流器
carpo_puller_t* carpo_pull_create(carpo_media_recv_cb media_cb, carpo_pull_event_cb event_cb, void* user_data);
// 设置 SSRC
int carpo_pull_set_ssrc(carpo_puller_t* p, uint32_t audio_ssrc, uint32_t video_ssrc, const char* uid);
// 设置 Carpo 服务端地址
int carpo_pull_set_server(carpo_puller_t* p, const char* ip, uint16_t port, const char* remote_ip);
// 开始拉流
int carpo_pull_start(carpo_puller_t* p);
// 停止拉流
int carpo_pull_stop(carpo_puller_t* p);
// 销毁
void carpo_pull_destroy(carpo_puller_t* p);

#ifdef __cplusplus
}
#endif
```

## C Wrapper 实现（carpo_capi.cpp）

```cpp
#include "carpo_capi.h"
#include "factory.h"
#include <cstring>

using namespace carpo;

struct carpo_pusher {
    PushSender* sender;
    PushSenderCb* cb;
    void* user_data;
    carpo_push_event_cb event_cb;
};

// C++ 回调适配器
class PushCbAdapter : public PushSenderCb {
    carpo_push_event_cb cb_;
    void* user_data_;
public:
    void set(carpo_push_event_cb cb, void* ud) { cb_ = cb; user_data_ = ud; }
    int onPushEvent(PushSenderCbEvent eventId, int code, void* data, int dataLen, void* userData) override {
        if (cb_) cb_((int)eventId, code, user_data_);
        return 0;
    }
};

extern "C" {

carpo_pusher_t* carpo_push_create(carpo_push_event_cb cb, void* user_data) {
    auto* p = new carpo_pusher;
    auto* adapter = new PushCbAdapter();
    adapter->set(cb, user_data);
    p->sender = Factory::getNewPushSender(adapter, user_data);
    p->cb = adapter;
    p->user_data = user_data;
    p->event_cb = cb;
    return p;
}

int carpo_push_send(carpo_pusher_t* p, carpo_media_type_t type, const uint8_t* buf, uint32_t size, uint64_t timestamp) {
    if (!p || !p->sender) return -1;
    return p->sender->sendMediaData((CP_MEDIA_TYPE)type, (uint8_t*)buf, size, timestamp);
}

// ... 其余方法类似，直接转发

} // extern "C"
```

## Python ctypes 绑定（预览）

```python
import ctypes

lib = ctypes.CDLL('./carpo_sdk.dll')  # or libcarpo_sdk.so

# 定义回调类型
PUSH_EVENT_CB = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
MEDIA_RECV_CB = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.POINTER(ctypes.c_uint8),
                                  ctypes.c_int, ctypes.c_uint32, ctypes.c_void_p)

class CarpoPusher:
    def __init__(self):
        self._cb = PUSH_EVENT_CB(self._on_event)  # 保持引用防 GC
        self._ptr = lib.carpo_push_create(self._cb, None)

    def send(self, media_type, data, timestamp):
        return lib.carpo_push_send(self._ptr, media_type, data, len(data), timestamp)

    def _on_event(self, event_id, code, user_data):
        print(f"push event: {event_id} code={code}")
```

## 文件清单

```
carpo_capi/
├── carpo_capi.h          ← C ABI 头文件
├── carpo_capi.cpp        ← C Wrapper 实现
├── CMakeLists.txt        ← 跨平台编译（Windows .dll + Linux .so）
└── python/
    └── carpo.py          ← ctypes 绑定
```
