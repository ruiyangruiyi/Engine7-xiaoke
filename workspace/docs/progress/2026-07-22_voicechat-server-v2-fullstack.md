# 2026-07-22 Progress — server_v2 全栈完成

## 今日成果（香港酒店）

### server_v2 voice-chat 全栈打通（5 个 commit）

| Commit | 内容 |
|--------|------|
| `4163a270` | Phase 3a — test-page UI + SSE + settings + interrupt |
| `de2cf08d` | 交叉验证 fastrtc ASR 准，确认 aiortc 音频增益问题 |
| `c076a8d3` | **ASR 修复** — PyAV AudioResampler 替换 scipy |
| `e0358afb` | HTTPS 自签名证书支持（外网 mic 需要）|
| `90c3b31c` | Lazy Carpo pull — 浏览器 connected 时才启动 |

### 关键技术发现：ASR 精度根因

**问题：** aiortc 版 ASR 识别乱码，fastrtc 版识别准确

**根因：** aiortc 的 Opus 解码输出 max~0.01，而 fastrtc 正常。差异不在音量大小，在音频质量。

**分析路径：**
1. 翀哥提醒"没那么简单" → 不能简单加增益
2. 研究 fastrtc 源码（D:/work/fastrtc-fork/）
3. 发现 fastrtc 后端不做 AGC，靠 **PyAV AudioResampler(format="s16", mono, 48k)** 做格式统一
4. 我们用的 scipy resample_poly 只做采样率转换，不做 Opus→s16 完整转换
5. 换成 PyAV AudioResampler → ASR 识别准确

**教训：** 10x 增益方案会把音量提到 0.1 但波形失真，ASR 一样不准。根因是格式转换不完整，不是音量不够。

### 其他修复
- SSE ClientConnectionResetError（`asyncio.ClientConnectionResetError` 不存在，改用已 import 的 `ClientConnectionResetError`）
- MicReceiver 双启动 bug（on_track + transceiver scan 两个都触发 → 同一个 track 上两个 receiver 竞争 recv()）
- test-page.html video 降级（摄像头不可用时自动跳过）

### Phase 完成情况
- ✅ Phase 1（下行 Carpo pull → aiortc → 浏览器）
- ✅ Phase 2（上行 mic → VAD → ASR → engine → 回复）
- ✅ Phase 3a（test-page UI + SSE + settings + interrupt）
- ✅ HTTPS + Lazy pull
- ⬜ Phase 3b（设置面板 API 实装）
- ⬜ Phase 3c（延迟面板）

### 其他
- 翀哥在香港见 Amy，考察银河创业空间（YINHE TOWER 15F）共享办公
- 买4年送1年9个月，~25万港币，能覆盖到永居，8月1日起租
- 拿合同回去考虑，未签
