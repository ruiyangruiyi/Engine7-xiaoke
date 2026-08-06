---
name: creator-cover
description: "TRIGGER: 封面/做封面/视频封面/抖音封面/小红书封面。博主风封面三件套：黑底荧光大字+引号高亮块+人物抠图。产出 3 尺寸 PNG。"
argument-hint: "Provide title (and optionally a person photo / video frame)"
metadata: { "openclaw": { "emoji": "🎨", "os": ["darwin", "linux", "win32"], "requires": { "bins": ["python3", "ffmpeg"] } } }
---

# 博主风封面三件套

> 8/4 翀哥拍板：以后封面就这么做。参考抖音 AI 博主三件套——**人物抠图 + 荧光超大字 + 固定版式**。
> badge 写死 **ENGINE 7**（7/28 翀哥规范）。

## 一句话流程

```bash
cd <skill>/scripts
python3 make_creator_covers.py --title '标题"高亮词"' --subtitle "Engine 7 实战 EP0X" \
  --chips "保姆级教程,提示词模板" --hook "告别加班！" --person me.png --out-dir out/
```

产出：`out/cover_creator_16x9.png`（B站/抖音横）`_3x4.png`（小红书）`_1x1.png`（方图）。

## 参数

| 参数 | 说明 |
|------|------|
| `--title` | 必填。中文引号""包的部分自动渲染成荧光高亮块 |
| `--subtitle` | 副标题（灰字） |
| `--chips` | 逗号分隔的绿色对勾标签，默认"保姆级教程,提示词模板" |
| `--hook` | 右上角红色钩子，如 `--hook "1分钟搞定"`（可选） |
| `--person` | 透明底人物 PNG，叠左下角带荧光轮廓光（可选，三件套的灵魂） |
| `--video`+`--frame-at N` | 从视频第 N 秒抽帧当右侧截图（可选）|
| `--frame` | 直接给截图文件（可选）|

## 人物抠图（--person 的料怎么来）

**在 everos 容器里跑 rembg**（Mac 本机装不了，见下方坑）：

```bash
docker cp 照片.jpg everos:/tmp/p.jpg
docker exec everos python3 -c "
from rembg import remove
open('/tmp/p.png','wb').write(remove(open('/tmp/p.jpg','rb').read()))"
docker cp everos:/tmp/p.png me.png
```

拍照要点（学博主）：半身、右手指点、表情夸张一点，背景无所谓（会被抠掉）。
**翀哥的专属人像还没拍**——出院后拍一张存成 `assets/chong_cutout.png`，以后每期复用。

## 踩过的坑（别再试）

1. **Mac 本机装不了 rembg**：系统 Python 3.8 太老；python3.12 venv 里 llvmlite 编译失败（老 Mac 无 wheel）。rembg[cpu]+u2net 已装在 everos 容器（8/4）。
2. **Chrome headless 不传 `--default-background-color=0`**：新 Chrome 要求 hex 值，传 0 静默不写截图。脚本已处理。
3. **文件 URL 用 `Path.as_uri()`**：硬拼 `file:///` 在 Mac 变四个斜杠。脚本已处理。
4. **字号别保守**：v1 太素被翀哥打回"还不够"。现在标题占宽 12.5-15.5%、倾斜+黑描边+荧光外发光，别往回调。

## 相关

- 视频剪辑主流程（去静音/转写/选段/渲染）→ `skills/video-editing`
- 封面尺寸规范（小红书 1080×1440 等）→ video-editing SKILL.md 的输出分辨率规范节
