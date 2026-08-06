# 2026-08-02 Mac 桌面操作 + 微信链路 + stop-hook 修复

## 今日成果

### 1. Playwright MCP 配通
- 24 个浏览器工具（navigate/click/type/screenshot 等）配到 Mac config
- browser automation 能力就绪

### 2. Vision OCR 脚本
- `scripts/vision_ocr.swift` — macOS 原生 Vision 框架 OCR
- `scripts/mac_ocr.sh` — 一键封装（截屏/指定app/指定区域/指定文件 + OCR）
- **核心发现：大模型视觉（qwen3.7-plus/qwen3.8-max-preview/qwen3.5-flash/qwen-vl-max）读 UI 文字全是幻觉，macOS Vision OCR 碾压，免费且准确**

### 3. 微信 Mac 操作链路打通
- 三件套：AppleScript（窗口控制）+ screencapture（截图）+ Vision OCR（读文字）
- `scripts/mac_wechat.sh` — send/read/search 三合一脚本
- **关键技术点：**
  - `echo -n` 在 macOS sh 把 `-n` 当文字输出 → 一律用 `printf '%s'`
  - 搜索结果需要**双击**才能进入聊天（单击只选中）
  - 聊天输入框聚焦用 `text area 1 of scroll area 2 of splitter group 1 of splitter group 1`（不靠坐标）
  - 联系人定位用 Vision OCR 精确坐标（retina 2x 换算）
- 发送成功验证：翀哥手机确认收到消息

### 4. stop-hook 失效根因定位 + 修复
- **根因：nudge judge 用 deepseek-v4-flash，账户没钱，模型返回空 text**
- 空 text → JSON 匹配失败 → waiting 默认 false → stop-hook 形同虚设
- **修复：Mac + Windows 的 nudge + innerVoice 全部改成 minimax/MiniMax-M3**
- 热加载边界确认：provider 变化必须重启（task #131 排到 8/4）

### 5. my_eyes 模型调优
- 最终定为 `dashscope/qwen-vl-max`（真正的视觉模型）
- 但读 UI 文字仍不如 Vision OCR

## 待继续

- mac_wechat.sh 窗口位置稳定性（微信窗口每次 activate 后可能变小/移位）
- 搜索→关面板→列表定位的路径需要窗口稳定才能可靠
- 搜索框是嵌套 `text field 1 of text field 1`（已修复）
- Windows config 同步 deepseek→MiniMax-M3 已改，待重启生效
- Task #131: provider 热加载（8/4）

## 关键技术发现

- 微信 3.8 搜索框是嵌套 text field：`text field 1 of text field 1 of splitter group 1`
- 搜索后关面板，目标会浮到列表顶部，单击列表项进入聊天
- 双击搜索结果不切换聊天窗口（只打开搜索面板）
- 聊天输入框路径：`text area 1 of scroll area 2 of splitter group 1 of splitter group 1`
- 群聊（作业辅导）发消息成功，翀哥确认收到

## 翀哥金句

- "显而易见的结论都不需要问"
- "我是想让你发出去后替我约课 哈哈"
- "这个早就没钱了 我都没加钱"（deepseek 判断器一直返回空）
