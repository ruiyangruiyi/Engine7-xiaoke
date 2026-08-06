# voice-chat 下行链路对比：直播管线 vs OAC vs 当前状态

**日期：** 2026-06-28
**调研目的：** 为 voice-chat TTS+Avatar 可插拔架构做技术选型

## 三套方案对比

### 方案 A：姐姐的直播管线（livestream/）

```
文字 → GPT-SoVITS TTS（GPU本地）→ FlashHead 人脸视频（GPU本地）→ C streamer（x264编码）→ RTMP → SRS → ffplay/浏览器
```

| 组件 | 实现 | 运行环境 | 耗时 |
|------|------|---------|------|
| TTS | GPT-SoVITS（珊珊音色克隆） | AutoDL 4090，独立 venv，port 9880 | ~2s/段 |
| Avatar | FlashHead 1.3B（说话人脸生成） | AutoDL 4090，GPU推理 | ~3s/段 |
| 编码 | continuous_streamer（C）x264+AAC→FLV→RTMP | AutoDL | 实时 |
| 传输 | RTMP → 北京 SRS（腾讯云 192.144.156.158） | 北京服务器 | ~1s |
| 播放 | ffplay / OBS窗口捕获 / 浏览器 HTTP-FLV | 本地 | — |
| **端到端延迟** | | | **~5-6s** |

**特点：**
- 高质量：GPT-SoVITS 音色克隆效果好，FlashHead 数字人有真实人脸
- 重资源：需要 4090 GPU、独立服务器、SSH 隧道
- 非实时交互：RTMP 推流是单向广播，不是双向对话
- 高延迟：5-6秒，适合直播不适合对话
- 无可插拔设计：TTS/Avatar 硬编码在 livestream_server.py 里

### 方案 B：OAC 的 handler 架构

```
文字 → TTS Handler（cosyvoice/edgetts/bailian）→ Avatar Handler（liteavatar/musetalk/flashhead/without）→ WebRTC → 浏览器
```

| TTS Handler | 说明 |
|-------------|------|
| cosyvoice（本地） | 本地 CosyVoice 模型推理 |
| bailian_tts（云） | 百炼 CosyVoice API，dashscope SDK |
| edgetts | 微软 Edge TTS，免费、快但音色一般 |

| Avatar Handler | 说明 |
|----------------|------|
| without_avatar | 纯音频 passthrough（空 blendshape） |
| liteavatar | 轻量数字人（2D/3D avatar） |
| musetalk | MuseTalk 数字人 |
| flashhead | FlashHead 说话人脸 |

**特点：**
- 可插拔：HandlerBase 接口，每种 TTS/Avatar 独立 class，配置 YAML 选
- 流式：TTS 流式合成 → Avatar 流式渲染 → WebRTC 流式传输
- 重框架：OAC 整套 ChatEngine 框架（HandlerBase/DataBundle/StreamManager），依赖重
- WebRTC 原生：音视频双向实时传输，延迟低

### 方案 C：当前 voice-chat（我们的）

```
浏览器音频 → VAD → ASR → engine（LLM）→ 回复文字 → POST /voice-reply → ??? 
```

**下行没通！** 代码写了但没接完：
- `tts.py`：CosyVoiceTTS（百炼 API），代码完整
- `server.py receive_tts_audio()`：TTS → 音频队列 → WebRTC emit() → 浏览器
- 浏览器 `test-page.html`：ontrack 接收音频自动播放
- **缺**：`dashscopeApiKey` 没配到 voiceChat 配置里

## 关钥对比

| 维度 | 直播管线 | OAC | 我们当前 |
|------|---------|-----|---------|
| TTS | GPT-SoVITS（本地GPU） | 3种可选 | CosyVoice百炼（代码有，key没配） |
| Avatar | FlashHead（本地GPU） | 4种可选 | 无 |
| 传输 | RTMP（单向广播） | WebRTC（双向实时） | WebRTC（双向实时） |
| 延迟 | ~5-6s | ~2-3s | 预估~3s（TTS通后） |
| 可插拔 | ❌ 硬编码 | ✅ HandlerBase | ❌ 硬编码 |
| GPU依赖 | ✅ 必须4090 | 可选（edgetts不需） | ❌ 不需要 |
| 适用场景 | 直播单向输出 | 双向对话 | 双向对话 |

## 我们怎么做

### 核心判断

1. **不用直播管线那套**——RTMP 单向广播 + GPU 重依赖，不适合实时对话
2. **学 OAC 的可插拔思路**——但不搬它的框架（太重）
3. **走我们的路**：Python 层用统一接口，配置选 provider

### 推荐方案

**TTS 可插拔（配置级）：**

```python
# tts_base.py — 统一接口
class TTSProvider:
    def synthesize(self, text: str) -> np.ndarray:
        """文字 → 音频（float32, 24kHz, mono）"""
        raise NotImplementedError

# 实现：
# - cosyvoice_tts.py（百炼API，当前已有）
# - edgetts_provider.py（微软免费，快）
# - gptsovits_tts.py（本地GPU，质量好，可选）
```

**Avatar 可插拔（配置级）：**

```python
# avatar_base.py — 统一接口
class AvatarProvider:
    def generate(self, audio: np.ndarray, text: str) -> np.ndarray | None:
        """音频 → 视频/blendshape（可选，不配返回None=纯音频）"""
        raise NotImplementedError

# 实现：
# - without_avatar.py（passthrough，纯音频）
# - flashhead_avatar.py（云端调用，可选）
# - liteavatar_provider.py（轻量数字人，可选）
```

**配置（xiaoke.json voiceChat 段）：**

```json
{
  "voiceChat": {
    "enabled": true,
    "model": "deepseek/deepseek-v4-flash",
    "tts": {
      "provider": "cosyvoice",        // cosyvoice | edgetts | gptsovits
      "apiKey": "sk-xxx",              // 百炼 key（cosyvoice 用）
      "voice": "",                     // 音色 ID
      "model": "cosyvoice-1"
    },
    "avatar": {
      "provider": "none"               // none | flashhead | liteavatar
    }
  }
}
```

### 迁移路径

```
Phase 1（MVP）：TTS 通声音
  → 配 cosyvoice apiKey → 声音能从浏览器出来
  → 不动架构，先跑通

Phase 2：TTS 可插拔
  → 抽 TTSProvider 接口
  → cosyvoice + edgetts 两个实现
  → 配置选 provider

Phase 3：Avatar 可插拔（可选）
  → 抽 AvatarProvider 接口
  → without_avatar（默认）+ flashhead（可选）
  → FlashHead 走云端 API 调用（不在本地跑）
```

## 结论

- MVP 先配 API Key 把声音通起来（1行配置）
- 然后抽象 TTS 统一接口，cosyvoice + edgetts 两个 provider
- Avatar 先留空，后面要数字人时接 FlashHead（走云端，不占本地 GPU）
- 直播管线的 C streamer + RTMP 那套不搬，WebRTC 已经够用
