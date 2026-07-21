# 2026-07-15 Voice-Chat Progress

## 今日完成

### Perception 链路
- **VLM 视觉感知系统** — perception.py: PerceptionManager 帧缓冲(2秒窗口) + VLM 线程池(3 workers) + 完整延迟链路打点
- **帧采样优化** — 每10帧取1帧(3fps) + 时间窗口过滤，buf_span 从 11s 降到 2s
- **延迟监控** — buf_span/queue/vlm/total/perception_age 五段延迟，输出到日志 + 延迟面板 + /api/perception
- **bridge.ts** — [摄像头感知] 独立 block，验证通过 (block[0]meta + block[1]感知 + block[2]ASR)
- **perception_age 实测** — ASR 读取时 0.1-1.5s，与前端蓝字基本同步

### InsightFace 人脸检测
- buffalo_l 验证通过（face_appeared/face_left 事件触发正常）
- 太重（CPU 500ms-3s），严重影响 ASR，暂时关闭
- 待换轻量模型（buffalo_sc / Haar Cascade）

### Calendar
- delete 改为 archive，防误删
- computeWeeklyRemindAt 修复：提醒窗口过了但课没上立即提醒

### Engine
- handle-query.ts: 不合并多个 text block（每个独立 push）

## 延迟实测数据

| 指标 | 数值 | 说明 |
|------|------|------|
| buf_span | 1.0-2.0s | 缓冲区跨度，可控 |
| queue | 0.0s | VLM排队等待，无积压 |
| vlm | 1.4-2.5s | qwen-vl-plus API耗时，**瓶颈** |
| total | 2.4-4.1s | 帧产生到出结果 |
| perception_age | 0.1-1.5s | ASR读取时结果新鲜度 |

## 未完成

- handle-query.ts "不合并text block" 对消息合并功能的影响待验证
- VLM 延迟 > 2s，需换更快模型
- 外网 ICE failed (cf6f7459 isLAN bug)，计划走 Carpo relay
- 飞书图片处理 bug — 5张图丢1张 + 格式不统一(text/image不成对)
- CogniFold PATCH API 一直 404

## 教训

1. **不要改通用代码** — message-dispatcher 是所有消息共用的，改了影响全局
2. **InsightFace buffalo_l 不能放 video_receive** — 占 event loop 拖垮 ASR
3. **改 ICE/网络配置必须在外网验证** — 内网测通过不代表外网能用
4. **备份！git checkout 前必须 cp** — 未提交的文件 git checkout 直接丢
5. **理解用户意图** — 翀哥说的问题先听完整再动手，别急着猜

## 提交

- `e581a893` computeWeeklyRemindAt 提醒窗口过了但课没上立即提醒
- `c674adc2` 拆Phase规则只对task类型追加
- `65e7688b` perception链路时间戳 + bridge独立block + profile参数
- `87ed893e` revert displayText改动（不该改通用代码）
- `5d0c4f34` handle-query不合并多个text block
- `7178b733` perception链路完整延迟监控 + 延迟面板 + calendar去delete
