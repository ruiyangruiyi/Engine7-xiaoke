#!/usr/bin/env python3
"""
人物抠图：去掉背景输出透明 PNG，供 make_creator_covers.py --person 使用。

Usage:
  python3 cutout_person.py <input.jpg> [output.png]

依赖：video-editing/.venv-cutout（rembg，首次运行自动下载 u2net 模型 ~170MB）
用法二（直接用 skill venv）：
  ../../.venv-cutout/bin/python3 cutout_person.py me.jpg
"""

import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"文件不存在: {src}")
        sys.exit(1)
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".cutout.png")

    from rembg import remove
    data = src.read_bytes()
    out = remove(data)  # 自动下载 u2net 模型（首次）
    dst.write_bytes(out)
    print(f"OK: {dst}")


if __name__ == "__main__":
    main()
