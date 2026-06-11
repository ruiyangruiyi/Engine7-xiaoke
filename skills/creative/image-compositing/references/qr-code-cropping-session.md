# QR Code Cropping — Session Findings

## Problem
Replacing a QR code in a poster image. The source QR image (WeChat card) included avatar, nickname, and white borders — needed to isolate only the pure QR matrix.

## Key Discovery: Edge Energy Analysis

When the source image contains extra content (avatar + text above, white border below), simple bounding-box detection fails. The trick is **edge energy** — QR codes have high-frequency 黑白交错 pattern, while avatars/text/borders have low variance.

### WeChat QR Card Analysis (72ba80c456817491ff34c2655dc4f31.jpg)

Original size: 888×1233

**Row energy scan** (每20像素行):
```
y=0-80:    全白 (std=0, 暗=0.00)
y=80-240:  白色过渡区 (std≈57, 暗≈0.05)
y=280:     全白 (std=0)
y=320-880: QR主体区域 (std≈100-115, 暗≈0.21-0.31)  ← 高方差=二维码
y=920+:    全白 (std=0)
```

**Final working crop boundaries**:
```
top = 320      # 第一个高方差行
bottom = 880    # 最后一个高方差行
left = 145     # 列能量突变处
right = 745    # 列能量突变处
```

Cropped size: 600×560 → pad to 600×600 square → resize to 350×350

## Code Pattern

```python
import numpy as np
from PIL import Image

img = Image.open("qr-card.jpg")
arr = np.array(img)
gray = np.mean(arr[:,:,:3], axis=2)

# 1. Edge energy (no scipy needed — diff is enough)
diff_x = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
diff_y = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
edge = diff_x + diff_y

row_energy = np.sum(edge, axis=1)
col_energy = np.sum(edge, axis=0)

# 2. Find boundary where energy crosses threshold
threshold = np.max(row_energy) * 0.03
top = np.argmax(row_energy > threshold)
bottom = len(row_energy) - np.argmax(row_energy[::-1] > threshold)

# 3. Crop and square
cropped = img.crop((left, top, right, bottom))
w, h = cropped.size
size = max(w, h)
square = Image.new('RGB', (size, size), (255, 255, 255))
square.paste(cropped, ((size - w)//2, (size - h)//2))
qr_final = square.resize((350, 350), Image.Resampling.LANCZOS)
```

## WeChat QR Specifics

- 三个定位点在: 左上、右上、左下
- 中心有微信logo (黑色方块+白色气泡)
- 数据区 ≈ 600×560 when cropped from original 888×1233
- 转为正方形后边长 600 → 缩放至 350 效果正好

## Common Failure Modes

1. **裁剪后仍有头像/文字**: 阈值设太高 → top太低。微信卡片的文字区 std≈57，二维码区 std≈100-115，阈值用 max*0.03 可以区分开
2. **RGBA paste错误**: 先 `.convert('RGB')` 再paste
3. **位置偏了**: 用 vision_analyze 验证裁剪结果后再合并到海报
