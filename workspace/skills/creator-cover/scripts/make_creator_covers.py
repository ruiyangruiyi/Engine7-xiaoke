#!/usr/bin/env python3
"""
Creator-style covers: black bg + neon-green oversized title, blogger-template look.

Ref: 8/4 翀哥发的抖音博主封面（人物抠图+固定版式+荧光大字三件套）。
本脚本做"荧光大字"版式；人物抠图层可选叠加（--person）。

Usage:
  python3 make_creator_covers.py --title 'AI做PPT"对话式"修改' --subtitle "Engine 7 实战"
  python3 make_creator_covers.py --title "..." --video final.mp4 --frame-at 10
  python3 make_creator_covers.py --title "..." --frame shot.png --person me.png

Title 里用中文引号""包起来的部分会渲染成荧光高亮块。
产出 3 尺寸: cover_creator_16x9.png / 3x4 / 1x1（--out-dir 默认当前目录）。
"""

import argparse
import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

NEON = "#c8ff00"          # 荧光绿（主高亮）
NEON2 = "#39ff5e"         # 荧光绿2（装饰）
BG = "#0c0e0c"            # 近黑背景
FONT = '"PingFang SC","Hiragino Sans GB","Noto Sans SC",system-ui,sans-serif'

SKILL_DIR = Path(__file__).resolve().parent.parent


def find_chrome():
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return shutil.which("chrome") or shutil.which("google-chrome")


def img_b64(path):
    if not path or not os.path.exists(path):
        return None
    return base64.b64encode(Path(path).read_bytes()).decode()


def video_frame_b64(video, ts):
    tmp = tempfile.mktemp(suffix=".png")
    r = subprocess.run(
        ["ffmpeg", "-y", "-ss", str(ts), "-i", video, "-frames:v", "1",
         "-q:v", "2", "-update", "1", tmp],
        capture_output=True)
    if r.returncode == 0 and os.path.exists(tmp):
        data = Path(tmp).read_bytes()
        os.unlink(tmp)
        return base64.b64encode(data).decode()
    return None


def title_html(title, fs):
    """中文引号包起来的部分 → 荧光高亮块。"""
    parts = re.split(r'("[^"]*")', title)
    out = []
    for p in parts:
        if p.startswith('"') and p.endswith('"'):
            out.append(f'<span class="hl">{p[1:-1]}</span>')
        else:
            out.append(p)
    return "".join(out)


def common_css(w, h, fs):
    return f"""
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{w}px;height:{h}px;overflow:hidden;background:{BG}}}
body{{font-family:{FONT};color:#fff}}
.bg{{position:fixed;inset:0;
  background:
    radial-gradient(circle at 12% 88%, rgba(200,255,0,0.10) 0, transparent 30%),
    radial-gradient(circle at 90% 10%, rgba(57,255,94,0.08) 0, transparent 28%),
    {BG}}}
.grid{{position:absolute;inset:0;opacity:0.10;
  background-image:linear-gradient(rgba(200,255,0,0.35) 1px, transparent 1px),
    linear-gradient(90deg, rgba(200,255,0,0.35) 1px, transparent 1px);
  background-size:{max(24,int(w*0.045))}px {max(24,int(w*0.045))}px;
  mask-image:radial-gradient(circle at 50% 50%, rgba(0,0,0,0.9), transparent 80%)}}
.badge{{display:inline-flex;align-items:center;gap:{int(fs*0.12)}px;
  padding:{int(fs*0.14)}px {int(fs*0.32)}px;border-radius:999px;
  border:{max(2,int(fs*0.05))}px solid {NEON};color:{NEON};
  font-size:{int(fs*0.30)}px;font-weight:800;letter-spacing:0.12em}}
.badge::before{{content:"";width:{int(fs*0.22)}px;height:{int(fs*0.22)}px;border-radius:50%;background:{NEON}}}
.title{{font-size:{fs}px;font-weight:900;line-height:1.10;letter-spacing:0.01em;
  transform:rotate(-4deg) skewX(-4deg);color:#fff;
  -webkit-text-stroke:{max(2,int(fs*0.02))}px #000;
  text-shadow:{int(fs*0.06)}px {int(fs*0.07)}px 0 #000, 0 0 {int(fs*0.5)}px rgba(200,255,0,0.45)}}
.title .hl{{display:inline-block;background:{NEON};color:#000;-webkit-text-stroke:0;
  padding:{int(fs*0.03)}px {int(fs*0.14)}px;border-radius:{int(fs*0.10)}px;
  transform:rotate(-2deg);text-shadow:none;
  box-shadow:{int(fs*0.07)}px {int(fs*0.07)}px 0 #000, 0 0 {int(fs*0.8)}px rgba(200,255,0,0.8)}}
.subtitle{{font-size:{int(fs*0.34)}px;font-weight:600;color:rgba(255,255,255,0.62);letter-spacing:0.04em}}
.chips{{display:flex;gap:{int(fs*0.16)}px;flex-wrap:wrap}}
.chip{{display:inline-flex;align-items:center;gap:{int(fs*0.10)}px;
  padding:{int(fs*0.10)}px {int(fs*0.24)}px;border-radius:{int(fs*0.10)}px;
  background:rgba(200,255,0,0.12);border:1px solid rgba(200,255,0,0.45);
  font-size:{int(fs*0.26)}px;font-weight:700;color:{NEON}}}
.chip::before{{content:"✓";font-weight:900}}
.hook{{position:absolute;top:{int(h*0.05)}px;right:{int(w*0.05)}px;z-index:2;
  background:#ff2e2e;color:#fff;font-size:{int(fs*0.36)}px;font-weight:900;
  padding:{int(fs*0.10)}px {int(fs*0.26)}px;transform:rotate(6deg);
  border-radius:{int(fs*0.08)}px;box-shadow:{int(fs*0.06)}px {int(fs*0.06)}px 0 #000, 0 0 {int(fs*0.6)}px rgba(255,46,46,0.6);
  letter-spacing:0.06em}}
.shot{{border-radius:{int(fs*0.24)}px;overflow:hidden;
  border:{max(2,int(fs*0.05))}px solid rgba(200,255,0,0.6);
  box-shadow:0 0 {int(fs*0.8)}px rgba(200,255,0,0.25), 0 {int(fs*0.4)}px {int(fs*1.2)}px rgba(0,0,0,0.6);
  transform:rotate(2deg)}}
.shot img{{width:100%;height:100%;object-fit:cover;display:block;
  filter:saturate(0.9) contrast(1.08) brightness(0.92)}}
.person{{position:absolute;bottom:0;left:{int(w*0.03)}px;height:{int(h*0.52)}px;
  filter:drop-shadow(0 0 {int(fs*0.5)}px rgba(200,255,0,0.35))}}
.person img{{height:100%;object-fit:contain;display:block}}
.arrow{{position:absolute;font-size:{int(fs*0.6)}px;color:{NEON};font-weight:900}}
"""


def html_16x9(w, h, fs, t, sub, chips, frame, person, hook=None):
    chips_html = "".join(f'<div class="chip">{c}</div>' for c in chips)
    shot_html = f'<div class="shot" style="width:{int(w*0.36)}px;height:{int(h*0.62)}px"><img src="data:image/png;base64,{frame}"></div>' if frame else ""
    person_html = f'<div class="person"><img src="data:image/png;base64,{person}"></div>' if person else ""
    hook_html = f'<div class="hook">{hook}</div>' if hook else ""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{common_css(w,h,fs)}
.layout{{position:relative;z-index:1;width:100%;height:100%;display:flex;align-items:center;
  justify-content:space-between;padding:{int(w*0.06)}px;gap:{int(w*0.04)}px}}
.copy{{flex:1 1 auto;display:flex;flex-direction:column;gap:{int(fs*0.30)}px;max-width:{int(w*0.55)}px}}
</style></head><body><div class="bg"><div class="grid"></div>
<div class="layout">
  <div class="copy">
    <div class="badge">ENGINE 7</div>
    <div class="title">{t}</div>
    <div class="subtitle">{sub}</div>
    <div class="chips">{chips_html}</div>
  </div>
  {shot_html}
</div>{person_html}{hook_html}</div></body></html>"""


def html_3x4(w, h, fs, t, sub, chips, frame, person, hook=None):
    chips_html = "".join(f'<div class="chip">{c}</div>' for c in chips)
    shot_html = f'<div class="shot" style="width:{int(w*0.84)}px;height:{int(h*0.36)}px"><img src="data:image/png;base64,{frame}"></div>' if frame else ""
    person_html = f'<div class="person" style="height:{int(h*0.30)}px"><img src="data:image/png;base64,{person}"></div>' if person else ""
    hook_html = f'<div class="hook">{hook}</div>' if hook else ""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{common_css(w,h,fs)}
.layout{{position:relative;z-index:1;width:100%;height:100%;display:flex;flex-direction:column;
  padding:{int(w*0.07)}px;gap:{int(fs*0.30)}px}}
</style></head><body><div class="bg"><div class="grid"></div>
<div class="layout">
  <div class="badge">ENGINE 7</div>
  <div class="title">{t}</div>
  <div class="subtitle">{sub}</div>
  <div class="chips">{chips_html}</div>
  {shot_html}
</div>{person_html}{hook_html}</div></body></html>"""


def html_1x1(w, h, fs, t, sub, chips, frame, person, hook=None):
    chips_html = "".join(f'<div class="chip">{c}</div>' for c in chips)
    shot_html = f'<div class="shot" style="width:{int(w*0.78)}px;height:{int(h*0.32)}px"><img src="data:image/png;base64,{frame}"></div>' if frame else ""
    person_html = f'<div class="person" style="height:{int(h*0.30)}px"><img src="data:image/png;base64,{person}"></div>' if person else ""
    hook_html = f'<div class="hook">{hook}</div>' if hook else ""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{common_css(w,h,fs)}
.layout{{position:relative;z-index:1;width:100%;height:100%;display:flex;flex-direction:column;
  align-items:flex-start;justify-content:center;padding:{int(w*0.07)}px;gap:{int(fs*0.28)}px}}
</style></head><body><div class="bg"><div class="grid"></div>
<div class="layout">
  <div class="badge">ENGINE 7</div>
  <div class="title">{t}</div>
  <div class="subtitle">{sub}</div>
  <div class="chips">{chips_html}</div>
  {shot_html}
</div>{person_html}{hook_html}</div></body></html>"""


def render(html, w, h, out):
    chrome = find_chrome()
    if not chrome:
        print("Chrome not found!")
        return False
    tmp = tempfile.mkdtemp(prefix="ccover_")
    hp = os.path.join(tmp, "cover.html")
    Path(hp).write_text(html, encoding="utf-8")
    # as_uri() 兼容 Mac(/) 和 Windows(C:\) —— 硬拼 file:/// 在 Mac 上变四个斜杠
    # 不传 --default-background-color：新 Chrome 要求 hex 值，传 0 直接不写截图；背景本就不透明
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                    f"--screenshot={out}", f"--window-size={w},{h}",
                    Path(hp).as_uri()],
                   capture_output=True, timeout=30)
    shutil.rmtree(tmp, ignore_errors=True)
    return os.path.exists(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--chips", default="保姆级教程,提示词模板", help="逗号分隔")
    ap.add_argument("--video", help="从视频抽帧")
    ap.add_argument("--frame", help="直接用截图")
    ap.add_argument("--frame-at", type=float, default=10)
    ap.add_argument("--person", help="人物抠图透明PNG（可选叠加）")
    ap.add_argument("--hook", help="右上角红色钩子标签，如 '1分钟搞定'（可选）")
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()

    frame = img_b64(args.frame)
    if not frame and args.video:
        frame = video_frame_b64(args.video, args.frame_at)
    person = img_b64(args.person)
    t = title_html(args.title, 0)  # placeholder, fs set per size
    chips = [c for c in args.chips.split(",") if c.strip()]

    # 字号比例对标抖音博主：标题占宽 ~10-13%，手机缩略图也一眼看清
    sizes = [("cover_creator_16x9.png", 1920, 1080, html_16x9, 0.125),
             ("cover_creator_3x4.png", 1080, 1440, html_3x4, 0.155),
             ("cover_creator_1x1.png", 1080, 1080, html_1x1, 0.125)]
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    for fname, w, h, builder, ratio in sizes:
        fs = int(w * ratio)
        html = builder(w, h, fs, title_html(args.title, fs), args.subtitle,
                       chips, frame, person, args.hook)
        out = str(Path(args.out_dir) / fname)
        ok = render(html, w, h, out)
        print(f"  [{'OK' if ok else 'FAIL'}] {fname} ({w}x{h})")


if __name__ == "__main__":
    main()
