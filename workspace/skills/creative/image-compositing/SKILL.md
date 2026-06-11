---
name: image-compositing
description: PIL/Pillow-based image compositing — overlay, crop, replace regions, resize, and composite multiple images. Use when you need to edit existing images rather than generate new ones.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [image, PIL, Pillow, compositing, crop, resize, overlay, 海报, 二维码]
    related_skills: [claude-design]
---

# Image Compositing with PIL/Pillow

Use `PIL/Pillow` for tasks like:
- Replacing a region in one image with content from another (e.g., swap a QR code in a poster)
- Precise cropping of sub-regions (e.g., extract only the QR code from a screenshot)
- Overlaying images with transparency
- Resizing and placing images onto a canvas

## Install Pillow

```bash
pip install pillow
# or in WSL/Unix:
pip3 install pillow
```

Verify:
```python
from PIL import Image
print(Image.open("test.jpg").size)
```

---

## Core Workflow: Replace a Region in an Existing Image

### Step 1: Analyze the target image

When replacing something in an existing image (like a QR code in a poster), you need to:
1. Find the location and size of the region to replace
2. Read both the source image (what goes in) and target image (the poster/layout)

```python
from PIL import Image
import numpy as np

target = Image.open("poster.png")
source = Image.open("new-qr.jpg")

print(f"Target size: {target.size}")
print(f"Source size: {source.size}")
```

### Step 2: Find the region to replace (edge detection)

Use numpy to detect high-frequency (complex) regions — 二维码 (QR codes) have high variance due to 黑白交错:

```python
arr = np.array(target)
gray = np.mean(arr[:,:,:3], axis=2)

# Approximate edge detection via absolute difference
diff_x = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
diff_y = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
edge = diff_x + diff_y

# Sum energy per row/column to find dense regions
row_energy = np.sum(edge, axis=1)
col_energy = np.sum(edge, axis=0)

threshold = np.max(row_energy) * 0.03  # 3% of peak

top = np.argmax(row_energy > threshold)
bottom = len(row_energy) - np.argmax(row_energy[::-1] > threshold)
left = np.argmax(col_energy > threshold)
right = len(col_energy) - np.argmax(col_energy[::-1] > threshold)
```

### Step 3: Crop the source to isolate the pure element

When the source image has extra content (avatar, text, white borders), crop to the pure element:

```python
# For QR codes: the 主体 has high entropy, borders are solid white
# Detected bounds from step 2 give you the crop region
cropped = source.crop((left, top, right, bottom))
```

Convert to square by padding with white:
```python
w, h = cropped.size
size = max(w, h)
square = Image.new('RGB', (size, size), (255, 255, 255))
square.paste(cropped, ((size - w) // 2, (size - h) // 2))
```

### Step 4: Resize to appropriate size

```python
target_size = 250  # pixels — adjust based on context
resized = cropped.resize((target_size, target_size), Image.Resampling.LANCZOS)
```

### Step 5: Cover the old region and paste the new one

```python
from PIL import ImageDraw

# Cover old region with white (or relevant background color)
draw = ImageDraw.Draw(target)
draw.rectangle([x1, y1, x2, y2], fill=(255, 255, 255))

# Paste — use the image itself as mask if it has alpha, otherwise paste directly
target.paste(resized, (x, y), resized if resized.mode == 'RGBA' else None)

target.save("output.png", quality=95)
```

---

## Key Pitfalls

1. **RGBA transparency errors**: If `paste()` fails with "bad transparency mask", the image has a palette or mode issue. Fix with:
   ```python
   img = img.convert('RGB')  # before pasting
   ```
   Or if the image has an alpha channel you want to use as mask:
   ```python
   img = img.convert('RGBA')
   target.paste(img, (x, y), img)  # paste using alpha as mask
   ```

2. **Pasting without alpha mask**: When the source image has no transparency, paste directly:
   ```python
   target.paste(resized, (paste_x, paste_y))  # no third argument
   ```
   The third (mask) argument only works with RGBA/L mode images.

2. **Pasting without alpha mask**: When the source image has no transparency, paste directly:
   ```python
   target.paste(resized, (paste_x, paste_y))  # no third argument
   ```
   The third (mask) argument only works with RGBA/L mode images.

3. **Cropped QR code still has extra content**: When cropping QR codes from screenshots that include avatar/text:
   - Use edge/entropy analysis to find the QR code body (high variance region)
   - White borders have zero variance — look for where variance starts
   - Manual boundary refinement may be needed; always verify with vision tool

3. **Image size and paste coordinates**: Remember PIL uses (left, top) for paste origin, not (x, y) center. When placing in bottom-left or bottom-right:
   ```python
   margin = 30
   x = margin                              # bottom-left
   x = poster.width - img.width - margin   # bottom-right
   y = poster.height - img.height - margin
   ```

4. **Overlapping paste regions**: If the new element overlaps old content you want removed, always draw a filled rectangle (fill color) over the old region **before** pasting, not after.

5. **jpeg quality artifacts**: When saving composites over jpeg sources, use `quality=95` or higher to avoid further compression artifacts.

---

## Workflow B: Replace an Existing Element in a Poster

When a poster has a placeholder QR code you need to swap with a new one, and the placeholder QR is mixed with background/green-WeChat-icon nearby:

### Step 1: Find the old QR's exact pixel location

```python
from PIL import Image
import numpy as np

poster = Image.open("poster.png")
arr = np.array(poster)
pw, ph = poster.size

# Scan bottom-right corner for black+white high-contrast region
# QR = black pixels < 30 AND white pixels > 220, both present (~50-80%)
best_coords = None
best_score = 0

for size in range(80, 200, 5):   # expected size range
    for y in range(ph - size - 50, ph - size - 10, 5):
        for x in range(int(pw * 0.7), pw - 50, 5):
            region = arr[y:y+size, x:x+size]
            white = ((region[:,:,0]>220) & (region[:,:,1]>220) & (region[:,:,2]>220)).mean()
            black = ((region[:,:,0]<30) & (region[:,:,1]<30) & (region[:,:,2]<30)).mean()
            if 0.5 < white + black < 0.85 and white > 0.15 and black > 0.15:
                score = white + black
                if score > best_score:
                    best_score = score
                    best_coords = (x, y, size)

if best_coords:
    qr_left, qr_top, _ = best_coords
    print(f"QR region approx starts at ({qr_left}, {qr_top})")
```

### Step 2: Refine to exact boundaries

```python
# Find left edge: scan right-to-left at a dark row
qr_right = pw
for x in range(qr_left, pw, 1):
    if (arr[qr_top, x] < 30).all():
        qr_right = x
        break

# Find bottom edge: scan bottom-to-top at a dark column
qr_bottom = 0
for y in range(qr_top, ph, 1):
    if (arr[y, qr_left] < 30).all():
        qr_bottom = y
        break

qr_w = qr_right - qr_left + 1
qr_h = qr_bottom - qr_top + 1
print(f"QR exact size: {qr_w} x {qr_h}")
```

### Step 3: Resize new QR to match and paste

```python
qr_new = Image.open("new-qr.png")
target_size = max(qr_w, qr_h)   # QR codes are square
qr_resized = qr_new.resize((target_size, target_size), Image.Resampling.LANCZOS)

result = poster.copy()
paste_x = qr_left - (target_size - qr_w) // 2
paste_y = qr_top - (target_size - qr_h) // 2
result.paste(qr_resized, (paste_x, paste_y),
             qr_resized if qr_resized.mode == 'RGBA' else None)
result.save("output.png", "PNG")
```

### Step 4: Always verify with vision_analyze

Use `vision_analyze` on the output — pixel-level code can't catch visual misalignments.

### Common Pitfalls for Poster QR Replacement

- **Green WeChat icon nearby**: The green icon has high G channel relative to R and B. Exclude it when scanning:
  ```python
  not_green = ~((region[:,:,1] > region[:,:,0] + 20) & (region[:,:,1] > region[:,:,2] + 20))
  ```
- **Non-square detected region**: QR codes are square. Use `max(qr_w, qr_h)` as target size and center the paste.
- **QR mixed with white card background**: The multi-scale scan in Step 1 finds it directly — no edge detection needed.

---

## Workflow A: Crop Pure Element from Mixed Source

Use edge-energy analysis when the source image contains extra content (avatar, text, borders) you need to strip away. Detailed workflow in `references/qr-code-cropping-session.md`.

---

## Quick Reference

| Operation | Command |
|-----------|---------|
| Install | `pip install pillow` |
| Open | `Image.open("path")` |
| Crop | `img.crop((l, t, r, b))` |
| Resize | `img.resize((w, h), Image.Resampling.LANCZOS)` |
| Paste | `canvas.paste(img, (x, y), img)` |
| Draw rect | `ImageDraw.Draw(img).rectangle([x1,y1,x2,y2], fill=(255,255,255))` |
| Save | `img.save("out.png", quality=95)` |
| To numpy | `np.array(Image.open(...))` |
| Edge energy | `np.abs(np.diff(gray, axis=1)) + np.abs(np.diff(gray, axis=0))` |

---

## When NOT to use this skill

- Generating images from scratch → use appropriate generation skill (Stable Diffusion, DALL-E, etc.)
- Pure HTML/CSS design artifacts → use `claude-design`
- PDF manipulation → use `ocr-and-documents`
- Very large-scale batch processing → consider OpenCV instead of PIL for speed
