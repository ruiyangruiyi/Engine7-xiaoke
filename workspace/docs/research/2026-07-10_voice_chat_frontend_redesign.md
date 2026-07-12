# Voice Chat 前端重新设计

## 需求（翀哥 7/10 19:24）

1. **Settings 面板** — 网页可配置，实时生效
   - a. 人物形象（avatar image）
   - b. TTS provider（dashscope / local cosyvoice）
   - c. 本地 vs autodl（TTS 在本地跑还是 235 跑）
   - d. autodl server 选择（machines.json 里的机器）

2. **Pull 控制** — 避免 server 启动就拉流解码
   - Start/Stop pull 按钮
   - 可配置 auto（有浏览器连接就 pull）
   - Push 测试按钮（现有 carpo-trigger）

3. **视频小窗**
   - Start pull 后显示
   - 可拖动移动
   - 浏览器最小化时桌面显示（Picture-in-Picture API）

## 实现步骤

### Phase 1: 后端 API（server.py）
1. 加 `/api/settings` GET/POST — 返回/修改当前配置
2. 加 `/api/machines` GET — 读 machines.json 返回机器列表
3. 加 `/api/pull/start` + `/api/pull/stop` + `/api/pull/status` — Carpo pull 控制
4. 改 `_init_carpo_pull()` 为可按需启动（不自动跑）
5. 加 `/api/avatars` GET — 列出可用的 avatar 图片

### Phase 2: 前端 UI
1. 重写 test-page.html — 新布局 + CSS
2. Settings modal — 表单 + 提交
3. 视频小窗 — 拖动 + PiP
4. Pull 控制按钮 — auto/manual 切换
5. 保留现有延迟面板 + 聊天记录 + SSE

### Phase 3: 联调
1. Settings 实时生效 — POST 后后端立即应用
2. Pull start/stop 验证
3. 视频小窗拖动 + PiP 验证
