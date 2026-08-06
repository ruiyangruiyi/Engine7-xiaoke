# voice-chat 桌面悬浮窗控制

**任务 ID:** #120
**创建日期:** 2026-07-26
**负责人:** 小柯（技术执行）
**关联人:** 姐姐（协作）
**来源:** 翀哥直播场景需求（7/26 直播时发现浏览器控制不方便）

---

## 背景

翀哥在快手做 AI 直播时，浏览器里 voice-chat 的控制面板在 OBS 推流画面之外——直播时没法操作浏览器去点"静音"或"打断"按钮。

**核心需求：**
- 不在浏览器里操作
- 直播时能在桌面直接控制 voice-chat
- 鼠标移到屏幕顶部边缘时悬浮窗自动出现
- 悬浮窗上有"静音"和"打断"两个按钮
- 点按钮调用 voice-chat 后端 API

---

## 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **pywebview** | HTML/CSS 可做 UI，跨平台，调试方便 | 需要 Chromium 运行时（约 50MB） |
| **pystray + tkinter** | 轻量，无依赖，启动快 | UI 简陋，按钮不好做 |
| **PyQt/PySide** | 功能强大，可做任意 UI | 包体积大，学习成本高 |

**推荐方案：pywebview** —— 既能做悬浮窗，又支持 HTML/CSS 美化 UI，调试也方便。

---

## Phase 拆分

### Phase 1：调研 + 技术选型 [x] — 7/27 09:38
- [x] 确认 pywebview 在 Windows 上的透明窗口 + 鼠标监听能力 ✅
- [x] 测试"鼠标移到屏幕顶部显示"的触发方案（pynput 监听 mouse move）✅
- [x] 打断 API = `POST /stop`（无参数），静音无后端 API（前端 WebRTC track switch）

### Phase 2：实现基础悬浮窗 + 打断功能 [~]
- [x] Python 脚本：pywebview 创建透明无标题窗口 ✅
- [x] pynput 监听鼠标位置，靠近屏幕顶部 5px 时显示 ✅
- [x] HTML/CSS 写简洁的 UI（打断按钮 + 静音按钮置灰待定）✅
- [x] 离开悬浮窗区域 1s 后自动隐藏 ✅
- [x] 打断按钮调 `POST http://localhost:8011/stop` ✅
- [ ] 翀哥直播场景实测

### Phase 3：对接 voice-chat API [ ]
- [ ] 确认 voice-chat 后端的 mute 和 interrupt API 路径
- [ ] 在悬浮窗按钮的 click handler 里调用对应 API
- [ ] 处理错误响应（API 不可用时按钮置灰）
- [ ] 显示当前 voice-chat 状态（运行中/已静音/已打断）

### Phase 4：直播场景验证 [ ]
- [ ] 启动 OBS 推流
- [ ] 测试悬浮窗不挡直播画面
- [ ] 测试静音/打断按钮在直播中实时生效
- [ ] 录屏验证效果

---

## 验证标准

- [ ] 鼠标移到屏幕顶部 → 悬浮窗 0.3s 内出现
- [ ] 鼠标离开 → 1s 后自动隐藏
- [ ] 点击静音 → voice-chat 停止响应（不再生成 TTS/打断回复）
- [ ] 点击打断 → 强制停止当前回复生成
- [ ] 悬浮窗不挡 OBS 推流画面（仅在最上层 + 透明背景）
- [ ] 启动到可用状态 < 5s

---

## 技术依赖

```
pywebview>=4.0
pynput>=1.7
requests  # 调 voice-chat API
```

---

## 风险

- pywebview 在某些 Windows 系统上透明窗口渲染有问题 → 备选 PyQt
- pynput 监听全局鼠标需要管理员权限 → 测试时确认
- 后端 API 可能没暴露 mute 接口 → 需要先确认 voice-chat 后端有这几个 endpoint

---

## 关联

- voice-chat 后端代码: `engine/src/voice-chat/python/server.py`
- 直播相关配置: `engine/configs/xiaoke.json` (livestream 节)
- 前端页面参考: `engine/src/voice-chat/python/test-page.html`