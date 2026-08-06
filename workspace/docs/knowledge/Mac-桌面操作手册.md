# Engine 7 Mac 桌面操作手册

## 概述

Engine 7 agent 通过 `exec` 调用 macOS 原生工具链，实现桌面自动化操作。无需任何第三方依赖（除 cliclick）。

## 工具链

| 工具 | 用途 | 安装 |
|------|------|------|
| `screencapture` | 截屏/录屏 | 系统自带 |
| `my_eyes` | AI 视觉识别截屏内容 | engine 内置 |
| `osascript` | AppleScript 自动化 | 系统自带 |
| `cliclick` | 鼠标点击/键盘输入 | `brew install cliclick` |

## 权限要求

**系统偏好设置 → 安全性与隐私 → 隐私**

1. **辅助功能** — Terminal + osascript（控制 app）
2. **屏幕录制** — Terminal（截屏/录屏）

## 核心模式

### 1. 截屏 → 看图 → 操作

```bash
# 截屏
screencapture -x /tmp/screen.png

# AI 识别（注意：my_eyes 可能幻觉，精确内容用 osascript 确认）
my_eyes → 识别页面布局和大致位置

# 鼠标点击
cliclick c:x,y        # 单击坐标
cliclick dc:x,y       # 双击
cliclick p            # 获取当前鼠标位置

# 键盘输入
cliclick t:"hello"    # 输入文字
cliclick kd:cmd ku:cmd  # 按住/释放 cmd
```

### 2. AppleScript 直接控制 app（优先用这个）

比模拟点击更可靠——直接告诉 app 做什么。

#### Mail
```applescript
tell application "Mail"
  set msg to make new outgoing message with properties {subject:"标题", content:"正文"}
  set sender of msg to "账号名"
  make new to recipient at end of to recipients of msg with properties {address:"email@example.com"}
end tell
```

#### Finder
```applescript
tell application "Finder"
  make new folder at desktop with properties {name:"文件夹名"}
  make new file at (folder "文件夹名" of desktop) with properties {name:"文件.txt"}
end tell
```

#### Safari
```applescript
tell application "Safari"
  activate
  make new document with properties {URL:"https://example.com"}
  set URL of document 1 to "https://www.baidu.com/s?wd=关键词"
end tell
```

#### Chrome
```applescript
tell application "Google Chrome"
  tell window 1
    make new tab with properties {URL:"https://example.com"}
  end tell
end tell
```

#### 通用快捷键
```applescript
tell application "System Events"
  keystroke "n" using command down    -- Cmd+N
  keystroke "文字内容"                   -- 输入文字
  keystroke "c" using command down    -- Cmd+C 复制
  keystroke "v" using command down    -- Cmd+V 粘贴
end tell
```

### 3. 读 UI 元素树

```applescript
-- 当前前台 app
tell application "System Events"
  get name of first process whose frontmost is true
end tell

-- 运行中的 app 列表
tell application "System Events"
  get name of every process whose background only is false
end tell

-- 窗口列表
tell application "System Events"
  tell process "Safari"
    get name of every window
  end tell
end tell

-- 完整 UI 树（慎用，输出很长）
tell application "System Events"
  tell process "Google Chrome"
    tell window 1
      entire contents
    end tell
  end tell
end tell
```

### 4. 录屏

```bash
# 录制视频（需交互停止，或用 -T 设时长）
screencapture -v /tmp/video.mov -T 10   # 录10秒
```

## 注意事项

1. **my_eyes 幻觉**：视觉识别可能编造内容，精确值必须用 osascript 读 `value of elem`
2. **app 切换**：操作前先 `activate` 目标 app，否则窗口可能被遮挡
3. **Notes 支持差**：AppleScript 读不到 Notes 的内容，只能用快捷键盲操作
4. **盒盖不休眠**：`caffeinate -s` 后台运行 + `sudo pmset -c sleep 0`
5. **中文路径**：osascript 支持，但 shell 命令里要加引号

## 各 app 支持度

| App | AppleScript | Accessibility | 最佳操作方式 |
|-----|-------------|---------------|-------------|
| Mail | ⭐⭐⭐⭐⭐ | 好 | AppleScript 直接创建 |
| Finder | ⭐⭐⭐⭐⭐ | 好 | AppleScript 直接操作 |
| Safari | ⭐⭐⭐⭐ | 好 | AppleScript 设 URL |
| Chrome | ⭐⭐⭐ | 好 | make new tab |
| Notes | ⭐⭐ | 差 | 快捷键 + keystroke |
