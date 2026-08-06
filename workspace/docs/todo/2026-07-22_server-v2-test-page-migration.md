# server_v2 Phase 3 — test-page.html 搬迁差异分析

## 现状

| test-page.html 需要 | server_v2 有 | 差距 |
|---|---|---|
| `/webrtc/offer` POST | `/offer` | ⚠️ 路由名不同 |
| `/api/settings` GET/POST | ❌ | 需加：tts_provider/avatar_provider/pull_mode/interrupt_mode/machine/avatar_image |
| `/api/machines` GET | ❌ | 需加：读 machines.json |
| `/api/avatars` GET | ❌ | 需加：扫本地+SSH查235形象列表 |
| `/api/status_235` GET | ❌ | 需加：SSH查235运行状态 |
| `/api/timing_235` GET | ❌ | 需加：SSH查235 timing |
| `/api/perception` GET | ❌ | 占位返回空（perception 以后做） |
| `/api/pull/start` POST | ❌ | carpo_pull 已有，加路由即可 |
| `/api/pull/stop` POST | ❌ | carpo_pull 已有，加路由即可 |
| `/api/pull/status` GET | ❌ | carpo_pull 已有，加路由即可 |
| `/api/avatar/switch` POST | ❌ | 需加：SSH触发235切换形象 |
| `/api/debug/record/*` POST | ❌ | 低优先级，跳过 |
| `/events` SSE | ❌ | 需加：SSE 推 asr/reply/latency |
| `/stop` POST | ❌ | interrupt.py 已有逻辑，加路由即可 |
| `/carpo-trigger` POST | `/generate` | ⚠️ 名称不同 |

## 前端 WebRTC 差异

test-page.html 的 WebRTC 逻辑和 server_v2 不同：

| 项目 | test-page (fastrtc) | server_v2 (aiortc) |
|---|---|---|
| offer 端点 | `/webrtc/offer` | `/offer` |
| addTrack 方式 | getUserMedia(audio+video) | getUserMedia(audio only) |
| video 上行 | 有（摄像头 perception） | 无（recvonly） |
| ICE 超时 | 2s race | 等待 complete |
| STUN/TURN | 有 | 无 |

## 迁移计划

### Phase 3a：核心路由适配（先跑起来）
1. `/webrtc/offer` 改名（或加 alias）
2. `/stop` 路由 → 调 interrupt.py
3. `/api/pull/start` `/api/pull/stop` `/api/pull/status` → 调 carpo_pull
4. `/api/settings` GET/POST → 内存存配置（简单版）
5. SSE `/events` → 广播 asr/reply

### Phase 3b：设置面板
6. `/api/machines` → 读 machines.json
7. `/api/avatars` → 扫本地目录
8. `/api/avatar/switch` → SSH 触发 235
9. `/api/status_235` → SSH 查状态

### Phase 3c：延迟面板（可选）
10. `/api/timing_235` → SSH 查 timing
11. SSE 推 latency 事件

### 前端改动
- WebRTC offer 端点改 `/offer`（或后端加 `/webrtc/offer` alias）
- video 上行暂时跳过（server_v2 没有 perception）
- ICE gathering 改成等 complete（aiortc 需要）

## 决策点

1. **路由名统一**：test-page 用 `/webrtc/offer`，server_v2 用 `/offer`。建议 server_v2 加 alias。
2. **settings 存储**：先用内存 dict，以后落 JSON 文件。
3. **SSE**：aiohttp 原生支持 WebSockets，SSE 用 web.StreamResponse 即可。
4. **video 上行**：test-page 有摄像头 video track（perception），server_v2 暂时跳过（recvonly）。
