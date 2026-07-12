# SESSION-STATE.md - 当前工作状态

## 当前时间
2026-07-12 15:55 (Asia/Shanghai, 周日)

## 🎯 当前任务：voice-chat V2 清理

### 当前状态
- **173 跑着**，cosyvoice provider
- machines.json active = bj173
- GPT-SoVITS 服务在 173 上（9880端口），逐句请求优化首chunk到1.5s

### ✅ 今天完成 (7/12)
- [x] GPT-SoVITS 逐句请求优化 — 首 chunk 从 14s 降到 1.5s
- [x] TTS provider 切换 bug 修复（cosyvoice→dashscope 对齐白名单）
- [x] start_carpo_avatar.sh 一键启动 GPT-SoVITS + FlashHead
- [x] restart_avatar.sh 同时杀两个服务
- [x] CosyVoice raw_q.get() timeout 网兜
- [x] Carpo pull 改为 WebRTC 建联时自动启动
- [x] 自动打断修复（avatar._busy 检查导致 avatar.stop() 不执行）
- [x] V1/V2 代码边界捋清
- [x] AutoDLAvatar 清理 V1 残留 + 加 _busy 状态跟踪
- [x] 姐姐新形象上传（sister_garden.jpg + sister_cyber.jpg）
- [x] Pull mode 选项去掉（固定建联就拉）
- [x] Ctrl+C 时停止 Carpo pull

### 🔴 待验证
- [ ] **自动打断** — 翀哥上课回来验证
- [ ] **Carpo pull 建联自动启动** — 翀哥上课回来验证

### 待做
- [ ] **Docker 化** — 锁死 .so + Python + 模型 + CUDA
- [ ] GPT-SoVITS 真流式（streaming_mode=True + iter_content 解析）
- [ ] 配置文件隔离 — 按 workspace 隔离
- [ ] 面板优化：首chunk标注"响应延迟"
- [ ] voice chat session 路由修复（不走主 session）

### 关键文件
| 文件 | 位置 |
|------|------|
| server.py | engine/src/voice-chat/python/ |
| test-page.html | 同上 |
| carpo_avatar_server.py | engine/src/voice-chat/autodlv2/python/oac/ |
| autodl_avatar.py | engine/src/voice-chat/python/avatar/ |
| avatarctl.py | engine/src/voice-chat/autodlv2/ |
| autodl_send.py | engine/src/voice-chat/autodlv2/ |
| machines.json | engine/src/voice-chat/ (active=bj173) |

### 关键环境
| 项目 | 值 |
|------|-----|
| AutoDL 173 | connect.bjb1.seetacloud.com:53987 root//Qc8A1biEbAB (active) |
| AutoDL 235 | connect.bjb1.seetacloud.com:19288 root/2z5B4IiZdUrI |
| AutoDL 089 | connect.bjb1.seetacloud.com:37725 root/m13T28fZq/XI (编译环境) |
| 北京 Server | 192.144.156.158:23800 |
| libcarpo 基线 | md5=2deea3f9f6be7127fcff17f35fc1ea52 |

### 稳定版本 (回溯点)
- **直播稳定版 commit**: `e665726e`
- **当前 HEAD**: `c39e6056`

## 💭 我现在的感觉
2026-07-12 09:33. 翀哥昨晚说着说着就睡着了，辛苦了。现在起来第一件事就是测打断功能。代码改好了，就等他重启服务说话试。

## 📝 最近消息
2026-07-12 15:36 | 翀哥(飞书) | V1/V2混在一起不放心，让我现在捋清
2026-07-12 15:13 | 翀哥(飞书) | server.py 回退后自动打断还是不行
2026-07-12 14:50 | 翀哥(飞书) | Carpo pull mode=manual 没启动，让我改成auto
