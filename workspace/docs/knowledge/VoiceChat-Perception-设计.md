# Voice-Chat Perception (VLM 视觉感知) 设计

> 2026-07-15 设计实现，作为基线文档。

## 架构

```
浏览器摄像头
  ↓ WebRTC video track (fastrtc)
server.py video_receive()
  ↓ 每10帧取1帧 (30fps → 3fps)，打 recv_ts 时间戳
  ↓ 帧缓冲区 (只保留最近2秒)
  ↓ 每2秒触发 VLM
perception.py PerceptionManager
  ↓ 线程池异步提交 (3 workers, 最新优先)
  ↓ 均匀采样4帧 → base64 JPEG
  ↓ 调 qwen-vl-plus API
  ↓ 返回场景描述 + 动作 + 情绪
  ↓ 写入 last_perception (全局变量)
  
两条消费路径:
  1. 前端蓝字: test-page.html 每2秒 GET /api/perception 轮询
  2. engine感知: ASR识别到语音时，server.py 读 last_perception，POST到 bridge.ts
```

## 延迟链路

```
帧产生 → video_receive (recv_ts)     ← 时间戳起点
  → 进缓冲区                          ← buf_span: 缓冲区最旧到最新帧跨度
  → submit VLM (submit_ts)            
  → VLM线程开始 (vlm_start_ts)        ← queue: submit到VLM实际开始的排队等待
  → VLM API返回                       ← vlm: API调用耗时
  → 写入 last_perception              ← total: 从最旧帧产生到出结果

ASR读缓存时:
  perception_age = now - last_perception_ts
```

## 延迟实测数据 (2026-07-15)

| 指标 | 数值 | 说明 |
|------|------|------|
| buf_span | 1.0-2.0s | 缓冲区跨度，可控 |
| queue | 0.0s | VLM排队等待，无积压 |
| vlm | 1.4-2.5s | qwen-vl-plus API耗时，**瓶颈** |
| total | 2.4-4.1s | 帧产生到出结果 |
| perception_age | 0.1-1.5s | ASR读取时结果新鲜度 |

## 关键设计决策

### 1. 帧缓冲只保留2秒
- 之前12帧 × 每30帧采样 = 11秒延迟
- 改为时间窗口过滤: `cutoff = recv_ts - 2.0`
- buf_span从11秒降到1-2秒

### 2. VLM独立block
- bridge.ts 发两个独立 text block: `[摄像头感知]xxx` 和 ASR文字
- engine handle-query.ts 每个 text block 独立 push，不 join
- 不改通用代码 (message-dispatcher.ts)

### 3. InsightFace人脸检测 — 暂时关闭
- buffalo_l 模型 CPU 跑一次 500ms-3s
- 严重影响 ASR 实时性 (event loop 被占)
- 验证通过: face_appeared/face_left 事件触发正常
- 待换轻量模型 (buffalo_sc / Haar Cascade)

## 待优化

1. **VLM延迟**: qwen-vl-plus 平均1.9s是瓶颈，total目标<2s需换更快的模型
2. **人脸检测**: 换轻量模型恢复实时人脸检测
3. **WebRTC传输延迟**: 帧产生到 video_receive 的延迟目前测不到

## 外网问题 (2026-07-15)

- commit `cf6f7459` "局域网直连优化" 引入 isLAN 判断
- 外网时只配 STUN 不配 TURN，useTurn 默认 false
- 导致外网 ICE failed，已回退
- 明天计划走 Carpo relay 方案替代自建 STUN/TURN

## 文件清单

| 文件 | 职责 |
|------|------|
| `perception.py` | PerceptionManager: 帧缓冲 + VLM线程池 + 结果管理 |
| `server.py video_receive()` | 帧接收 + 时间戳 + 缓冲管理 |
| `server.py /api/perception` | 返回 perception 状态 + 延迟数据 |
| `server.py /api/timing` | timing 快照 (含 VLM 延迟) |
| `test-page.html` | 前端蓝字 + 延迟面板 |
| `bridge.ts` | perception → engine 独立 block |
| `face_detect.py` | InsightFace 人脸检测 (暂时关闭) |
