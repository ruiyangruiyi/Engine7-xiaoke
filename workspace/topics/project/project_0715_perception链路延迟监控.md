---
type: project
date: 2026-07-15
---

# Voice-Chat Perception 链路 + 延迟监控 (2026-07-15)

## 完成项

1. **perception.py** — PerceptionManager: 帧缓冲(2秒窗口) + VLM线程池(3 workers) + 完整延迟链路打点
2. **帧采样优化** — 每10帧取1帧(3fps) + 时间窗口过滤，buf_span 从 11s 降到 2s
3. **VLM延迟监控** — buf_span/queue/vlm_total/perception_age 四段延迟，输出到日志+延迟面板+`/api/perception`
4. **bridge.ts** — `[摄像头感知]` 独立 block，验证通过 (block[0]meta + block[1]感知 + block[2]ASR)
5. **face_detect.py** — InsightFace 人脸检测验证通过，buffalo_l 太重暂时关
6. **calendar.ts** — delete 改为 archive，防误删

## 延迟实测

- vlm 平均 1.9s (瓶颈)
- total 3.3s 平均
- perception_age 0.1-1.5s (ASR读取时新鲜度)
- 前端蓝字和 engine 读同一变量，基本同步

## 未完成

- handle-query.ts "不合并text block" 对消息合并功能的影响待验证
- VLM 延迟 > 2s，需换更快模型
- 外网 ICE failed (cf6f7459 isLAN bug)，明天走 Carpo relay
- CogniFold PATCH API 一直 404

## 提交

- `65e7688b` perception链路时间戳 + bridge独立block + profile参数
- `87ed893e` revert displayText改动（不该改通用代码）
- `5d0c4f34` handle-query不合并多个text block
- `7178b733` perception链路完整延迟监控 + 延迟面板 + calendar去delete

## 教训

- buffalo_l 跑在 video_receive 里把 event loop 占了，ASR 被挤慢
- 改 ICE/网络配置时必须在外网验证
- 不改通用代码 (message-dispatcher) 解决 perception block 问题
- 备份！git checkout 前必须 cp 备份未提交的文件
