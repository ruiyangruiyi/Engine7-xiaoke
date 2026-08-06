# 2026-07-16 Voice-Chat Progress

## 今日完成

### CosyVoice v3.5-plus 声音复刻
- 从 v1 切换到 v3.5-plus（百炼声音复刻）
- workspace_id: ws-hwa8ahvniknul2x5
- WebSocket 端点配置完成
- 翀哥确认新声音好听

### Perception 优化
- VLM prompt "用户"→"对方"，更自然
- 加入年龄性别识别（child/teen/adult/elderly + male/female）
- 前后摄像头切换

### AutoDL bj835 — Qwen2.5-VL-7B + vLLM 部署
- **机器**: bj835 (RTX 5090, connect.bjb2.seetacloud.com:22569)
- **模型**: Qwen2.5-VL-7B-Instruct
- **端口**: 6006（翀哥起的，--enforce-eager --max-model-len 4096）
- **SSH 配置**: 已加到 machines.json，标注"VLM专用，不能做avatar直播"
- **延迟对比**:
  - 本地 vLLM: 文本 520ms（SSH 隧道开销）
  - 百炼 API: 1700ms
  - 提升 ~3x

### Calendar
- delete 改为 archive（防误删）
- 肠镜 7/24、胃镜 7/27 已记
- 清肠提醒 7/23 已记

### Engine
- handle-query.ts 不合并多个 text block
- bridge.ts [摄像头感知] 独立 block 验证通过

## 未完成

- vLLM tool calling 报 400（需要加 --enable-auto-tool-choice --tool-call-parser hermes）
- perception VLM 切到本地 vLLM（还没改）
- 明天直播内容大纲（AI 记忆层级主题）
- 飞书图片处理 bug（5张图丢1张 + 格式不统一）
- 外网 ICE failed（cf6f7459 isLAN bug，计划走 Carpo relay）
- blocked 任务自动追踪机制（#91）

## 教训

1. **blocked 不能干等** — 翀哥批评：任务停了就该自己追踪解锁条件，nudge 不能代替执行
2. **vLLM tool calling 要单独开** — 默认不支持 tools 参数
3. **翀哥自己起的 vLLM 在 6006 端口** — 不是我猜的 8000

## 提交

- `d7528a10` cosyvoice-v3.5-plus声音复刻 + perception prompt优化 + 前后摄像头切换
- `7178b733` perception链路完整延迟监控 + 延迟面板 + calendar去delete
- `7643f9c3` calendar delete改为软删除(tool层delete调archive)
- `e581a893` computeWeeklyRemindAt 提醒窗口过了但课没上立即提醒
- `c674adc2` 拆Phase规则只对task类型追加
- `65e7688b` perception链路时间戳 + bridge独立block + profile参数
- `87ed893e` revert displayText改动（不该改通用代码）
- `5d0c4f34` handle-query不合并多个text block

## 文档落盘

- `docs/projects/autodl-bj835-vlm-deploy.md` — bj835 vLLM 部署过程
- `docs/projects/ai-knowledge-share-live.md` — AI 知识分享直播 project
- `docs/knowledge/VoiceChat-Perception-设计.md` — perception 完整设计（昨天）
