---
name: VoiceChat桌面悬浮窗控制
description: 7/26翀哥需求——桌面悬浮窗控制VoiceChat，4 Phase拆解
type: project
date: 2026-07-27
---

# VoiceChat 桌面悬浮窗控制（#120）

**提出：** 2026-07-26，翀哥在EP03剪辑完成后提出
**文档：** docs/todo/2026-07-27_voicechat-overlay-control.md

## 4 Phase 拆解

1. Phase 1 - 悬浮窗显示（桌面始终置顶小窗）
2. Phase 2 - 点击悬浮窗切换VoiceChat启用/禁用
3. Phase 3 - 悬浮窗显示状态（通话中/静音/离线）
4. Phase 4 - 快捷键绑定

## Phase 1-2 完成（2026-07-27）

### 调研发现：底部bar按钮分两类

| 按钮 | 后端API | 悬浮窗可调 |
|------|---------|-----------|
| 🤫 打断 (shush) | `POST /stop` ✅ | ✅ |
| ⏺ 录制 (toggleRecord) | `POST /api/debug/record/start\|stop` ✅ | ✅ |
| 🟢 开始 (startCall) | 前端WebRTC，无后端API ❌ | 需加API |
| 🎤 静音 (toggleMute) | 前端WebRTC，无后端API ❌ | 需加API |
| 🔴 停止 (stopCall) | 前端WebRTC，无后端API ❌ | 需加API |

### 已完成
- transparent + frameless + on_top 透明窗口 Demo 验证可行（pywebview）
- overlay.py 核心功能：鼠标移屏幕顶部↔悬浮窗显示，打断/录制按钮可用，其他灰掉
- **文件位置：** `engine/src/voice-chat/python/overlay.py`
- 默认端口 8011

### 换到 v2 版（2026-07-27）
- 翀哥指出应该用 voice-chat v2，不是 v1
- v2 端口 8116，有 SSL 证书 → https://localhost:8116
- overlay.py 已更新为 v2 版 API 地址 + https
- 自签证书可能需要 pywebview 忽略证书错误，待翀哥实测确认
- service tool 的 start/stop 控制模式待后续加（跟 v1 一样的 service 模式）

### Phase 2 验证（2026-07-27）
- ✅ 静音功能可用——翀哥实测说"静音了，你忙你的"
- ⚠️ 打断按钮有bug：pywebview返回的Python dict在JS端是字符串，`d.ok`访问不到——加`JSON.parse`修复中
- ⏳ 打断按钮待翀哥重跑验证

### Phase 2-3 完成（2026-07-28）

#### ×按钮改为退出（不再隐藏）
- 翀哥点×后：断开通话 → `window.destroy()` → 退出进程
- 鼠标移开 → 3秒自动隐藏（保留）
- 两者并存：隐藏(自动) + 退出(主动×)

#### Service tool 整合 - 第一版（service start 一把拉）
- `service action=start name=voice-chat` 同时拉起 server_v2 + overlay
- start_service.cmd 改为启动 server_v2.py（端口 8116）
- v1（server.py, port 8011）已下线
- carpo_rtc_server.py（早期实验版）已删除
- 已有端口检测：检测到已运行则返回不重启

### 7/28 全天调试——启动流程修复（8 commits）

#### 发现的问题链
1. **启动顺序bug**：overlay 放在 server_v2 后面，但 server_v2 是阻塞进程 → overlay 永远执行不到
2. **进程名不匹配**：`service stop` 用 `WINDOWTITLE eq voice-chat*` 杀 `python.exe`，但实际进程是 `python3.10.exe` → stop 杀不掉，进程残留
3. **spawn detached 无 GUI session**：service tool 用 `spawn detached` 后台拉起 overlay，但 pywebview 需要桌面 GUI 环境 → overlay 创建窗口失败

#### 最终方案
- **server_v2**：走 `service start`（spawn detached 后台进程，纯Python server没问题）
- **overlay**：翀哥手动跑 `python overlay.py`（需要桌面 GUI session）
- **stop 简化**：不再依赖进程名匹配，改为按端口 8116 找 PID，`taskkill //T /F` 连子进程一起杀
- overlay 手动启动，stop 不会误杀它

#### 调试过程
- 手动跑 `python server_v2.py local` 能正常工作 → 不是 server_v2 本身问题
- `start "voice-chat overlay" python -u overlay.py` 中 `python` 找不到（应改为 `python3.10`），但即使改对，spawn detached 下 pywebview 也起不来
- 服务端 `health` 能通，但 overlay 窗口一直不出现 → 确认是 GUI 环境问题
- 翀哥说"小窗出来了"——证明 overlay 手动跑可行

### 待确认
- 翀哥确认打断修复后，再决定是否加 mute/start/stop 后端 API
