---
name: Chrome HTML→图片 在 Mac 上的两个坑（headingless 截图脚本）
description: 2026-08-04 写博主风封面模板时踩的 Chrome 渲染坑——file:// 四斜杠 + --default-background-color=0 参数不再被接受
type: reference
date: 2026-08-04
---

# Chrome HTML→图片 在 Mac 上的两个坑

8/4 晚给 video-editing skill 写博主风封面（黑底荧光大字）模板，跑通 Python 脚本时遇到两个 Chrome rendering 坑，都跟"老 techcard 脚本只在 Windows 跑过"有关。

## 坑 1：file:// 四斜杠

Python 脚本里写 `file:///{html_path}` （3 个斜杠），Mac 上 html_path 已经以 `/` 开头，结果变成 `file:////var/...`（4 个斜杠），Chrome 报 ERR_FILE_NOT_FOUND。

**修法**：用 `pathlib.Path(html_path).as_uri()` 直接产出标准 `file://...` URI（双斜杠），别手拼字符串。

**Why:** Windows 路径 `C:\...` 不带前导 `/`，所以 `file:///` + 路径刚好 3 斜杠；Mac/Linux 路径都带前导 `/`，需要 `file://` + 路径（双斜杠）。

## 坑 2：--default-background-color=0 被新 Chrome 拒绝

老 techcard 用了 `chromium-browser --headless --default-background-color=0 ...`。新 Chrome 不再接受十进制 `0`，必须十六进制（如 `00000000`）。

**修法**：去掉这个参数（背景已经被 `<html>` 自己的 `background:#000` 覆盖掉，参数只是冗余）。

## Why

- 老脚本只 Windows 跑过，Mac 渲染链路（Linux + Chrome）一次都没暴露 → 这两个坑一起炸
- 以后写"截图 HTML"类脚本（封面、卡片、生成图）都走 `pathlib.Path.as_uri()` + 别预设 background-color 参数

## How to apply

- **Mac 上 Chrome headless 截图 HTML**：路径走 `Path.as_uri()`，不要 `f"file:///{path}"`
- **background-color 参数**：能省就省（CSS 里写），省了反而 Chrome 版本兼容
- **跨平台脚本**：跟 Windows 同事/自己过去的脚本合并前，先在目标平台跑一次最小 case，别直接信"Windows 通 Mac 也通"
