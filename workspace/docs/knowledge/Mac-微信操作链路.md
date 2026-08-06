# Mac 微信操作链路 — 2026-08-02 完整总结

## 三件套

| 工具 | 作用 | 文件 |
|------|------|------|
| AppleScript | 窗口控制、点击、键盘输入 | osascript |
| screencapture | 按区域截图 | 系统自带 |
| Vision OCR | 读文字（免费、准确） | scripts/vision_ocr.swift |

## 关键技术点

### 1. 搜索框是嵌套的
```
text field 1 of text field 1 of splitter group 1 of window "微信 (聊天)"
```
外层 text field 1 是容器，内层 text field 1 才是真正的输入框。
**必须用 `set focused of text field 1 of text field 1` 才能聚焦。**

### 2. printf '%s' 替代 echo -n
macOS sh 的 `echo -n` 把 `-n` 当文字输出。粘贴中文一律用：
```bash
printf '%s' "消息内容" | pbcopy
osascript -e 'tell application "System Events" to keystroke "v" using command down'
```

### 3. 进入聊天的正确路径（群聊）
搜索→双击搜索结果 **不切换聊天窗口**（只打开搜索面板）。

正确路径：
```
1. 搜索联系人/群名（嵌套 text field 聚焦 + paste）
2. 等搜索结果出现
3. 关搜索面板（Esc）
4. 目标浮到列表顶部
5. Vision OCR 定位列表中的目标
6. 单击列表项 → 进入聊天
7. text area 聚焦输入框
8. paste 消息 → Enter 发送
```

### 4. 聊天输入框路径
```
text area 1 of scroll area 2 of splitter group 1 of splitter group 1 of window "微信 (聊天)"
```
用 `set focused of text area 1 to true` 聚焦，不靠坐标。

### 5. Vision OCR 坐标换算
截屏是 retina 2x，Vision bbox 是归一化(0~1)左下原点：
```
screen_x = bbox.origin.x * pixelW / 2 + windowX
screen_y = (1 - bbox.origin.y - bbox.height/2) * pixelH / 2 + windowY
```

## 脚本文件

| 文件 | 用途 |
|------|------|
| `scripts/vision_ocr.swift` | Vision OCR 核心 |
| `scripts/mac_ocr.sh` | 截图+OCR 一键（支持 app/区域/文件/全屏）|
| `scripts/mac_wechat.sh` | 微信发消息（send/read/search）|

## 待优化

- mac_wechat.sh 的 send 路径：搜索→关面板→单击列表项（当前还是搜索→双击搜索结果）
- 搜索框清空逻辑需要用嵌套 text field
- 群聊和单聊的进入路径统一

## 大模型视觉 vs Vision OCR

| 模型 | 读微信 UI | 结论 |
|------|----------|------|
| qwen3.7-plus | 全错 | 文本模型不是视觉模型 |
| qwen3.8-max-preview | 全错 | 同上 |
| qwen3.5-flash | 全错 | 同上 |
| qwen-vl-max | 全错 | 真视觉模型但读 UI 文字仍幻觉 |
| **macOS Vision OCR** | **全对** | 原生 OCR，免费，碾压 |

**结论：读 UI 文字用 Vision OCR，看照片用 my_eyes（qwen-vl-max）。**
