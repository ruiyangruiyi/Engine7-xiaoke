#!/bin/bash
# mac_ocr.sh — 截图 + Vision OCR 一条命令搞定
# 用法:
#   mac_ocr.sh              → 截取当前屏幕并 OCR
#   mac_ocr.sh <app_name>   → 激活指定 app，截取其窗口并 OCR
#   mac_ocr.sh -f <file>    → 对指定图片文件 OCR
#   mac_ocr.sh -R x,y,w,h   → 截取指定区域并 OCR

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OCR_SCRIPT="$SCRIPT_DIR/vision_ocr.swift"
TMP_IMG="/tmp/mac_ocr_shot.png"

mode="screen"
target=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -f) mode="file"; target="$2"; shift 2;;
        -R) mode="rect"; target="$2"; shift 2;;
        -h|--help)
            echo "用法: mac_ocr.sh [-f <file>|-R x,y,w,h|<app_name>]"
            echo "  无参数  → 截全屏"
            echo "  app名   → 激活app截窗口"
            echo "  -f file → 对文件OCR"
            echo "  -R rect → 截区域"
            exit 0;;
        *) mode="app"; target="$1"; shift;;
    esac
done

case "$mode" in
    file)
        [ -z "$target" ] && echo "Error: 需要文件路径" && exit 1
        swift "$OCR_SCRIPT" "$target"
        ;;
    rect)
        screencapture -R "$target" -x "$TMP_IMG"
        swift "$OCR_SCRIPT" "$TMP_IMG"
        ;;
    app)
        # 激活 app，获取窗口坐标，截取
        osascript -e "tell application \"$target\" to activate" 2>/dev/null
        sleep 1
        GEOMETRY=$(osascript << EOFAPP
tell application "System Events"
    tell process "$target"
        tell window 1
            set {posX, posY} to its position
            set {sizeW, sizeH} to its size
            return (posX as string) & "," & (posY as string) & "," & (sizeW as string) & "," & (sizeH as string)
        end tell
    end tell
end tell
EOFAPP
)
        if [ -z "$GEOMETRY" ]; then
            echo "Error: 无法获取 $target 的窗口" >&2
            exit 1
        fi
        screencapture -R "$GEOMETRY" -x "$TMP_IMG"
        swift "$OCR_SCRIPT" "$TMP_IMG"
        ;;
    screen)
        screencapture -x "$TMP_IMG"
        swift "$OCR_SCRIPT" "$TMP_IMG"
        ;;
esac
