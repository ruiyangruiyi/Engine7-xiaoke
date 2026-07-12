# OAC WebRTC→VAD→ASR 管线移植调研

> 日期：2026-06-26 | 作者：小柯 | 目的：把 OAC 的语音管线核心抠出来，移植到 engine
> 源码位置：`D:/work/OpenAvatarChat/src/`

---

## 1. 一句话总结

OAC 语音管线 = **浏览器 WebRTC → fastrtc 收音频 → Silero VAD 切语音段 → SenseVoice ASR 转中文**。

移植到 engine 需要 3 个 Python 依赖 + 2 个模型文件，核心逻辑不到 300 行。

---

## 2. 数据流全图

```
浏览器 getUserMedia(audio: 16kHz mono)
    │
    │ WebRTC (ICE/DTLS/SRTP)
    ▼
fastrtc.Stream (Python aiortc 后端)
    │ POST /webrtc/offer → 创建 RTCPeerConnection
    │ track.on("frame") 回调收到音频帧
    │
    │ 每帧 = (sample_rate: int, numpy.ndarray float32[N,])
    │ fastrtc 自动重采样到 input_sample_rate (16kHz)
    ▼
MIC_AUDIO (numpy float32, 16kHz mono)
    │
    ▼
SileroVAD (ONNX 推理, 512 samples/clip = 32ms)
    │ 状态机: END→PRE_START→START→POST_END→END
    │ START 期间持续累积 HUMAN_AUDIO
    │ POST_END 超时 → is_last_data=True (说话结束)
    ▼
HUMAN_AUDIO (numpy float32, 16kHz, 一整段说话)
    │
    ▼
SenseVoice ASR (funasr AutoModel, 整段推理)
    │ model.generate(input=audio_numpy, batch_size_s=10)
    │ 输出: "<|zh|><|HAPPY|><|Speech|>你好啊"
    │ 正则清理: re.sub(r"<\|.*?\|>", "", text) → "你好啊"
    ▼
HUMAN_TEXT (str, 纯中文文字)
```

---

## 3. 每个环节详解

### 3.1 WebRTC 入口（fastrtc）

**技术**：fastrtc 库（封装了 aiortc）
**作用**：浏览器建立 WebRTC 连接，接收麦克风音频帧

**核心流程：**
1. 浏览器 POST `/webrtc/offer`，body 带 SDP offer
2. fastrtc 创建 RTCPeerConnection，setRemoteDescription
3. 挂载音视频 track，生成 answer 返回浏览器
4. ICE 建连后，音频帧通过回调流入

**音频帧回调：**
```python
async def receive(self, frame: tuple[int, np.ndarray]):
    sample_rate, array = frame
    # array = numpy float32, shape=(N,), 16kHz mono
```

**浏览器端约束（getUserMedia）：**
```javascript
audio: {
    sampleRate: 16000,
    channelCount: 1,
    autoGainControl: false,      // 关闭浏览器 AGC
    noiseSuppression: false,     // 关闭浏览器降噪
    echoCancellation: true       // 打开 AEC
}
```

**回传音频给浏览器（emit 回调）：**
```python
async def emit(self) -> tuple[int, np.ndarray]:
    # 从队列拿 AVATAR_AUDIO，返回 (24000, numpy)
    # 24000 Hz = TTS 输出采样率
```

**移植方案：** Python 微服务用 fastrtc 起 WebRTC endpoint，engine 做大脑（LLM+记忆+工具），两者 HTTP 通信。

---

### 3.2 VAD（Silero VAD ONNX）

**模型**：Silero VAD（ONNX 格式，~2.2MB）
**位置**：`silero_vad/src/silero_vad/data/silero_vad.onnx`
**推理后端**：onnxruntime（CPU，强制单线程）

**核心推理代码：**
```python
import onnxruntime
import numpy as np

model = onnxruntime.InferenceSession(
    "silero_vad.onnx",
    providers=["CPUExecutionProvider"]
)

state = np.zeros((2, 1, 128), dtype=np.float32)

def vad_inference(clip: np.ndarray, sr: int = 16000):
    """输入 512 samples float32，返回语音概率 0.0~1.0"""
    global state
    inputs = {
        "input": np.expand_dims(clip.squeeze(), axis=0),  # (1, 512)
        "sr": np.array([sr], dtype=np.int64),
        "state": state,
    }
    prob, state = model.run(None, inputs)
    return prob[0][0]
```

**状态机（4 个状态）：**

```
                    prob > threshold (0.5)
       END ─────────────────────────► PRE_START
       ▲                                 │
       │                                 │ 连续语音 ≥ start_delay (2048 = 128ms)
       │                                 ▼
       │                            START (累积 HUMAN_AUDIO)
       │                                 │
       │                                 │ 连续静音 ≥ end_delay (5000 = 312ms)
       │                                 ▼
       │ ◄── POST_END (监控期 16000 samples = 1秒) ────┘
       │      │
       │      │ 超时且无新语音 → 确认结束 → 输出整段语音给 ASR
       └──────┘
              │
              │ 期间有新语音 且间隔 < reconnect_threshold (8000 = 0.5秒)
              │ → 重连（继续累积）
              ▼
           START (重连)
```

**关键参数（默认值）：**

| 参数 | 默认值 | 含义 |
|------|--------|------|
| speaking_threshold | 0.5 | Silero 概率阈值 |
| start_delay | 2048 (128ms) | 连续语音确认开始 |
| end_delay | 5000 (312ms) | 连续静音确认结束 |
| buffer_look_back | 1024 | 回看补全语音头部 |
| post_end_monitor_samples | 16000 (1s) | 判停后监控期 |
| reconnect_threshold_samples | 8000 (0.5s) | 重连判定窗口 |
| volume_threshold | -40 dB | 能量门限（低于此值强制 prob=0） |

---

### 3.3 ASR（SenseVoice via funasr）

**模型**：SenseVoiceSmall（阿里达摩院多语言 ASR）
**大小**：~900MB（model.pb + config）
**推理后端**：funasr（PyTorch + CUDA）

**模型加载：**
```python
from funasr import AutoModel

model = AutoModel(
    model="iic/SenseVoiceSmall",     # 或本地路径
    disable_update=True,
    language="zh",                   # ← 强制中文！避免多语言猜歪导致乱码
)
```

**⚠️ 关键发现：language 参数**

`AutoModel.generate()` **没有 language 参数**。签名：
```python
def generate(self, input, input_len=None, progress_callback=None, cfg=None)
```

language 要在 **AutoModel 构造时**传。OAC 原始代码没传，所以 SenseVoice 自动猜语言——在 Docker POSIX locale 下猜歪了，输出多语言混合乱码。

**推理：**
```python
# input = numpy float32, shape=(N,), 16kHz mono
res = model.generate(input=audio_numpy, batch_size_s=10)
text_raw = res[0]['text']
# text_raw 可能是: "<|zh|><|HAPPY|><|Speech|>你好啊"
# 清理标签
import re
text = re.sub(r"<\|.*?\|>", "", text_raw)
# text = "你好啊"
```

**ASR 处理逻辑：**
1. VAD 输出语音段时持续累积音频
2. VAD 标记 `is_last_data=True`（说话结束）时，一次性推理整段
3. 不是流式 ASR——等说完才整段识别

**采样率要求：16kHz mono float32**

---

## 4. OAC 框架机制（移植时可扔掉换 engine 的）

| OAC 概念 | 作用 | 移植时替换为 |
|----------|------|-------------|
| DataSink 订阅 | handler 间自动路由数据 | engine 的 dispatcher |
| StreamManager | 数据流生命周期 | engine 的 session |
| ChatDataType | MIC_AUDIO→HUMAN_AUDIO→HUMAN_TEXT | 直接用变量传递 |
| HandlerBase | handler 注册/加载 | Python 函数 |

**移植时只保留核心逻辑：VAD 状态机 + ASR 推理。**

---

## 5. 依赖清单

### Python 依赖

| 包 | 用途 | 大小 |
|----|------|------|
| `onnxruntime` | Silero VAD 推理 | ~50MB |
| `funasr` | SenseVoice ASR 推理 | ~100MB |
| `torch` | funasr 依赖 | ~2GB (CUDA) |
| `numpy` | 音频处理 | ~20MB |
| `fastrtc` | WebRTC 服务端（仅浏览器接入需要） | ~50MB |

### 模型文件

| 模型 | 路径 | 大小 | 下载方式 |
|------|------|------|----------|
| Silero VAD ONNX | `silero_vad/data/silero_vad.onnx` | 2.2MB | OAC git submodule |
| SenseVoiceSmall | `models/iic/SenseVoiceSmall/` | ~900MB | modelscope download |

### 最小安装

```bash
pip install onnxruntime funasr torch numpy
# WebRTC 浏览器接入
pip install fastrtc
```

---

## 6. 最小可运行管线（独立 Python 脚本）

脱离 OAC 框架，可在任何 Python 环境运行：

```python
"""
最小 VAD+ASR 管线 — 从麦克风/音频文件检测语音并转文字
依赖：onnxruntime, funasr, torch, numpy
"""
import numpy as np
import onnxruntime
from funasr import AutoModel
import re

# ========== 1. 加载 VAD ==========
vad_model = onnxruntime.InferenceSession(
    "silero_vad.onnx",
    providers=["CPUExecutionProvider"]
)
vad_state = np.zeros((2, 1, 128), dtype=np.float32)

def vad_predict(clip_512: np.ndarray, sr=16000):
    """输入 512 samples float32，返回语音概率"""
    global vad_state
    inputs = {
        "input": np.expand_dims(clip_512.squeeze(), axis=0),
        "sr": np.array([sr], dtype=np.int64),
        "state": vad_state,
    }
    prob, vad_state = vad_model.run(None, inputs)
    return prob[0][0]

# ========== 2. 加载 ASR ==========
asr_model = AutoModel(
    model="iic/SenseVoiceSmall",
    disable_update=True,
    language="zh",
)

# ========== 3. VAD 状态机 ==========
THRESHOLD = 0.5
START_DELAY = 2048     # 128ms
END_DELAY = 5000       # 312ms

status = "END"
speech_buffer = []
speech_length = 0
silence_length = 0

def process_clip(clip: np.ndarray):
    """处理一个 512-sample clip，返回 (status, audio_or_none)"""
    global status, speech_buffer, speech_length, silence_length
    prob = vad_predict(clip)

    if status == "END":
        if prob > THRESHOLD:
            status = "PRE_START"
            speech_buffer.extend(clip)
        return ("wait", None)

    elif status == "PRE_START":
        if prob > THRESHOLD:
            speech_length += len(clip)
            speech_buffer.extend(clip)
            if speech_length >= START_DELAY:
                status = "START"
        else:
            status = "END"
            speech_buffer.clear()
            speech_length = 0
        return ("wait", None)

    elif status == "START":
        speech_buffer.extend(clip)
        if prob < THRESHOLD:
            silence_length += len(clip)
            if silence_length >= END_DELAY:
                audio = np.array(speech_buffer, dtype=np.float32)
                status = "END"
                speech_buffer.clear()
                speech_length = 0
                silence_length = 0
                return ("speech_end", audio)
        else:
            silence_length = 0
        return ("speaking", None)

    return ("wait", None)

# ========== 4. 处理函数 ==========
def audio_to_text(audio_float32: np.ndarray, sr=16000):
    """整段音频 → VAD 切段 → ASR 转文字"""
    results = []
    for i in range(0, len(audio_float32) - 512, 512):
        clip = audio_float32[i:i+512]
        status, speech = process_clip(clip)
        if status == "speech_end" and speech is not None:
            # ASR 推理
            res = asr_model.generate(input=speech, batch_size_s=10)
            text = re.sub(r"<\|.*?\|>", "", res[0]['text'])
            results.append(text)
            print(f"  ASR: {text}")
    return results

# ========== 5. 从文件测试 ==========
if __name__ == "__main__":
    import wave
    wav_path = "test.wav"
    with wave.open(wav_path, "rb") as wf:
        sr = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

    print(f"音频: {len(audio)/sr:.1f}s, {sr}Hz")
    texts = audio_to_text(audio, sr)
    print(f"\n识别结果: {texts}")
```

---

## 7. 移植到 engine 的建议架构

```
┌─────────────────────────────────────────────────┐
│  浏览器                                          │
│  getUserMedia(audio: 16kHz mono)                │
│  WebRTC → POST /webrtc/offer                    │
└──────────────────┬──────────────────────────────┘
                   │ WebRTC
                   ▼
┌─────────────────────────────────────────────────┐
│  Python 语音微服务（独立进程）                    │
│  端口：9002                                       │
│                                                   │
│  fastrtc.Stream (WebRTC endpoint)                │
│    ↓ MIC_AUDIO (numpy float32 16kHz)             │
│  Silero VAD (onnxruntime CPU)                    │
│    ↓ HUMAN_AUDIO (语音段)                        │
│  SenseVoice ASR (funasr + torch, language="zh") │
│    ↓ HUMAN_TEXT (中文文字)                       │
│  POST → engine webhook                           │
│                                                   │
│  ← POST /oc-reply (engine 回复)                  │
│    ↓ AVATAR_TEXT                                 │
│  百炼 CosyVoice TTS → AVATAR_AUDIO (24kHz)       │
│    ↓ emit → 浏览器                                │
└──────────────────┬──────────────────────────────┘
                   │ HTTP (localhost)
                   ▼
┌─────────────────────────────────────────────────┐
│  Engine (TypeScript, 现有)                       │
│  /webhook/oac-bridge → dispatcher → LLM         │
│  小柯回复 → OnResult hook → POST /oc-reply       │
└─────────────────────────────────────────────────┘
```

**关键决策点：**

1. **Python 微服务 vs 嵌入 engine**：Python 微服务更简单（直接复用 OAC 代码），engine 不用装 Python
2. **fastrtc 必须在 Python 端**：WebRTC 的 aiortc 是 Python 库
3. **TTS 放哪**：可以在 Python 微服务里（百炼 CosyVoice API），也可以让 engine 回复文字后 Python 端做 TTS
4. **engine 侧改动最小**：只需 oac-bridge webhook（已有）+ OnResult hook（已有）

---

## 8. 移植取舍清单

| 组件 | OAC 原始 | 移植后 | 改不改 |
|------|---------|--------|--------|
| WebRTC (fastrtc) | Python | Python 微服务 | 不改，直接用 |
| VAD (Silero) | OAC handler | 独立函数 | 抠出来，~50 行 |
| ASR (SenseVoice) | OAC handler | 独立函数 | 抠出来，~20 行，加 language="zh" |
| TTS (CosyVoice) | OAC handler | 百炼 API 调用 | 不改，直接用 |
| LLM | 百炼 qwen-plus | engine 小柯 | engine 侧已有 |
| OAC 框架 | DataSink/StreamManager | 扔掉 | 用 HTTP 通信代替 |
| Avatar | LiteAvatar/FlashHead | 后续 | 先不管 |
| Docker | 完整镜像 | 不需要 | 直接跑 Python 脚本 |

---

## 9. 下一步行动

1. **写 Python 微服务**：fastrtc + VAD + ASR + HTTP POST to engine（~200 行）
2. **测试 ASR 中文**：先跑 `language="zh"` 的 SenseVoice，确认中文识别正常
3. **接 engine**：Python 微服务 POST 到 engine webhook，engine 回复 POST 回来
4. **TTS**：engine 回复的文字 → 百炼 CosyVoice → 回传浏览器
5. **Avatar**：后续再接
