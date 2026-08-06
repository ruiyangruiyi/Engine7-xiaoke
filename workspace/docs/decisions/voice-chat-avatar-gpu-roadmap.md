# Voice-Chat Avatar GPU 路线规划

## 背景
6/28 翀哥提出：voice-chat 后续加 avatar 后，本地跑不起 FlashHead，最终需要 4090 渲染。

## 现有管线
- **直播管线**（姐姐）：文字→My Livestream skill→云端4090实时渲染(嘴型同步+身体动作)→RTMP推流
- **voice-chat 管线**：语音→ASR→engine→TTS音频→WebRTC→浏览器
  - avatar 已设计为可插拔：`create_avatar` + provider 模式
  - 当前 provider: none / flashhead（本地）

## 规划方向
两条管线最终合并：
1. voice-chat 的 avatar provider 新增 `RemoteGPUAvatar`
2. 音频驱动视频帧在 4090 上渲染
3. 视频帧通过 WebRTC video track 回传浏览器
4. 音画用同一套 PTS 对齐（当前音频 PTS 框架已就绪）

## 关键坑（来自直播经验）
- 音画同步
- 渲染延迟叠加在 TTS 后面
- WebRTC 视频轨道带宽远大于音频
- 网络抖动对视频影响更大

## 优先级
- 先让音频走通（当前吞音修复）
- 再优化 engine 延迟（4.8s 瓶颈）
- 再考虑 avatar + GPU
