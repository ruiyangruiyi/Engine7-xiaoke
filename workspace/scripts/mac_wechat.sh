#!/bin/bash
# mac_wechat.sh — Mac 微信操作脚本
# 用法:
#   mac_wechat.sh send "联系人名" "消息内容"
#   mac_wechat.sh read                          # 读取当前聊天窗口最新消息
#   mac_wechat.sh search "联系人名"             # 搜索联系人并进入聊天
#
# 依赖: AppleScript + screencapture + Vision OCR
# 注意: macOS 专用，Windows 走 wx_query.py

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OCR_SCRIPT="$SCRIPT_DIR/vision_ocr.swift"
TMP_IMG="/tmp/mac_wechat_shot.png"

# 微信窗口固定位置和大小
WIN_X=100
WIN_Y=100
WIN_W=900
WIN_H=600

# === 工具函数 ===

activate_wechat() {
    osascript -e 'tell application "WeChat" to activate'
    sleep 1
    osascript << EOF
tell application "System Events"
    tell process "WeChat"
        tell window 1
            set position to {$WIN_X, $WIN_Y}
            set size to {$WIN_W, $WIN_H}
        end tell
    end tell
end tell
EOF
    sleep 0.5
}

# 聚焦搜索框并清空（微信 3.8 嵌套 text field）
focus_search() {
    osascript << 'EOF'
tell application "System Events"
    tell process "WeChat"
        tell window "微信 (聊天)"
            tell splitter group 1
                click text field 1
                delay 0.5
                try
                    set focused of text field 1 of text field 1 to true
                    delay 0.3
                    keystroke "a" using command down
                    delay 0.2
                    key code 51
                    delay 0.3
                end try
            end tell
        end tell
    end tell
end tell
EOF
}

# 在搜索框输入文字
type_search() {
    local query="$1"
    printf '%s' "$query" | pbcopy
    osascript -e 'tell application "System Events" to keystroke "v" using command down'
    sleep 2
}

# 截图 + OCR
screenshot_ocr() {
    screencapture -R ${WIN_X},${WIN_Y},${WIN_W},${WIN_H} -x "$TMP_IMG"
    swift "$OCR_SCRIPT" "$TMP_IMG" 2>/dev/null
}

# 精确 OCR 定位文字坐标（输出 x,y 或 NOT_FOUND）
# 参数: $1=关键词, $2=minNormY(可选, 默认0.5), $3=maxNormY(可选, 默认0.95)
locate_text() {
    local keyword="$1"
    local minY="${2:-0.50}"
    local maxY="${3:-0.95}"

    screencapture -R ${WIN_X},${WIN_Y},${WIN_W},${WIN_H} -x "$TMP_IMG"

    cat > /tmp/vision_locate.swift << SWIFT
import Vision
import AppKit
import Foundation

guard let img = NSImage(contentsOfFile: "$TMP_IMG") else { exit(1) }
var rect = CGRect.zero
guard let cgImg = img.cgImage(forProposedRect: &rect, context: nil, hints: nil) else { exit(1) }
let imgW = Double(cgImg.width)
let imgH = Double(cgImg.height)

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en"]

let handler = VNImageRequestHandler(cgImage: cgImg)
try? handler.perform([request])

let keyword = "$keyword"
let minY = Double($minY)
let maxY = Double($maxY)
var found = false

for obs in request.results ?? [] {
    if let candidate = obs.topCandidates(1).first {
        let str = candidate.string
        if str.contains(keyword) && !str.contains("搜索") {
            let bbox = obs.boundingBox
            let normY = bbox.origin.y
            if normY >= minY && normY <= maxY {
                let cx = (bbox.origin.x + bbox.width/2) * imgW / 2 + Double($WIN_X)
                let cy = (1.0 - normY - bbox.height/2) * imgH / 2 + Double($WIN_Y)
                if cy < Double($WIN_Y) + 80 { continue }
                print(String(format: "%.0f,%.0f", cx, cy))
                found = true
                break
            }
        }
    }
}
if !found { print("NOT_FOUND") }
SWIFT

    swift /tmp/vision_locate.swift 2>/dev/null
}

# 聚焦聊天输入框
focus_chat_input() {
    osascript << 'EOF'
tell application "System Events"
    tell process "WeChat"
        tell window "微信 (聊天)"
            tell splitter group 1
                tell splitter group 1
                    tell scroll area 2
                        set focused of text area 1 to true
                        delay 0.3
                    end tell
                end tell
            end tell
        end tell
    end tell
end tell
EOF
    sleep 0.3
    # 清空输入框（防残留）
    osascript -e 'tell application "System Events" to keystroke "a" using command down'
    sleep 0.1
    osascript -e 'tell application "System Events" to key code 51'
    sleep 0.2
}

# 发送消息（需已进入聊天）
send_message() {
    local message="$1"
    focus_chat_input
    printf '%s' "$message" | pbcopy
    osascript -e 'tell application "System Events" to keystroke "v" using command down'
    sleep 0.5
    osascript -e 'tell application "System Events" to key code 36'
    sleep 1
}

# === 命令实现 ===

# send: 搜索→关面板→单击列表项进入聊天→发消息
cmd_send() {
    local contact="$1"
    local message="$2"

    if [ -z "$contact" ] || [ -z "$message" ]; then
        echo "用法: mac_wechat.sh send \"联系人名\" \"消息内容\""
        exit 1
    fi

    activate_wechat

    # 1. 搜索联系人
    focus_search
    type_search "$contact"
    sleep 1

    # 2. 关闭搜索面板（让目标浮到列表顶部）
    osascript -e 'tell application "System Events" to key code 53'
    sleep 1

    # 3. 清搜索框
    focus_search

    # 4. 再关一次面板
    osascript -e 'tell application "System Events" to key code 53'
    sleep 1

    # 5. 在列表中定位目标（列表上半区域）
    local coord=$(locate_text "$contact" 0.60 0.95)
    echo "定位 $contact: $coord"

    if [ "$coord" = "NOT_FOUND" ]; then
        echo "错误: 列表中未找到 $contact"
        screenshot_ocr | head -20
        exit 1
    fi

    # 6. 单击列表项进入聊天
    osascript -e "tell application \"System Events\" to click at {$coord}"
    sleep 2

    # 7. 发消息
    send_message "$message"
    echo "发送完成: $contact ← $message"
}

# read: 读取当前聊天窗口的消息
cmd_read() {
    activate_wechat
    sleep 0.5

    screencapture -R $((WIN_X + WIN_W/2)),${WIN_Y},$((WIN_W/2)),${WIN_H} -x "$TMP_IMG"

    cat > /tmp/vision_chat_read.swift << SWIFT
import Vision
import AppKit
import Foundation

guard let img = NSImage(contentsOfFile: "$TMP_IMG") else { exit(1) }
var rect = CGRect.zero
guard let cgImg = img.cgImage(forProposedRect: &rect, context: nil, hints: nil) else { exit(1) }

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en"]

let handler = VNImageRequestHandler(cgImage: cgImg)
try? handler.perform([request])

for obs in request.results ?? [] {
    if let candidate = obs.topCandidates(1).first {
        let bbox = obs.boundingBox
        let y = (1.0 - bbox.origin.y)
        print(String(format: "%.2f|%@", y, candidate.string))
    }
}
SWIFT

    swift /tmp/vision_chat_read.swift 2>/dev/null | sort -rn | head -30
}

# search: 搜索联系人并进入聊天
cmd_search() {
    local contact="$1"

    if [ -z "$contact" ]; then
        echo "用法: mac_wechat.sh search \"联系人名\""
        exit 1
    fi

    activate_wechat
    focus_search
    type_search "$contact"
    sleep 1
    osascript -e 'tell application "System Events" to key code 53'
    sleep 1
    focus_search
    osascript -e 'tell application "System Events" to key code 53'
    sleep 1

    local coord=$(locate_text "$contact" 0.60 0.95)
    echo "定位 $contact: $coord"

    if [ "$coord" = "NOT_FOUND" ]; then
        echo "未找到 $contact"
        screenshot_ocr | head -20
        exit 1
    fi

    osascript -e "tell application \"System Events\" to click at {$coord}"
    sleep 2
    echo "已进入 $contact 的聊天"
}

# === 主入口 ===

case "$1" in
    send)
        cmd_send "$2" "$3"
        ;;
    read)
        cmd_read
        ;;
    search)
        cmd_search "$2"
        ;;
    -h|--help|*)
        echo "用法:"
        echo "  mac_wechat.sh send \"联系人名\" \"消息内容\"   — 发送消息"
        echo "  mac_wechat.sh read                           — 读取当前聊天"
        echo "  mac_wechat.sh search \"联系人名\"             — 搜索并进入聊天"
        ;;
esac
