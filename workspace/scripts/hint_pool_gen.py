#!/usr/bin/env python3
"""
hint_pool_gen.py — 把LLM生成的hint列表写入hints_pool.txt

postProcess脚本：scheduler把LLM result（每行一条hint）通过--file传入，
脚本直接写入hints_pool.txt（原子替换）。

Usage:
  python hint_pool_gen.py main --file path/to/thought.txt
"""
import os, sys
import argparse
from datetime import datetime, timezone, timedelta

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 动态探测workspace根目录
_p = _SCRIPT_DIR
while True:
    if os.path.basename(_p) == 'workspace':
        _WORKSPACE_DIR = _p
        break
    _parent = os.path.dirname(_p)
    if os.path.basename(_parent) == 'workspace':
        _WORKSPACE_DIR = _parent
        break
    _p = _parent

HINTS_POOL = os.path.join(_WORKSPACE_DIR, 'inner-voice', 'hints_pool.txt')
XIAOYI_LOG = os.path.join(_WORKSPACE_DIR, 'inner-voice', 'xiaoyi.log')
BJ = timezone(timedelta(hours=8))


def main():
    parser = argparse.ArgumentParser(description='Generate hints pool')
    parser.add_argument('agent', nargs='?', default='main')
    parser.add_argument('--file', type=str, help='Read from file')
    args = parser.parse_args()

    # 读取LLM生成的hint列表
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
    else:
        sys.stdin.reconfigure(encoding='utf-8')
        content = sys.stdin.read().strip()

    if not content:
        print("hint_pool_gen: empty input, skip", file=sys.stderr)
        return

    # 解析每行一条hint，过滤空行
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        print("hint_pool_gen: no valid lines, skip", file=sys.stderr)
        return

    # 原子写入hints_pool.txt
    os.makedirs(os.path.dirname(HINTS_POOL), exist_ok=True)
    tmp = HINTS_POOL + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')
    os.replace(tmp, HINTS_POOL)

    # 写日志
    ts = datetime.now(BJ).strftime('%Y-%m-%d %H:%M:%S')
    os.makedirs(os.path.dirname(XIAOYI_LOG), exist_ok=True)
    with open(XIAOYI_LOG, 'a', encoding='utf-8') as lf:
        lf.write(f'[{ts}] HINTS_POOL UPDATED  count={len(lines)}\n')
        lf.write(f'  first: {lines[0][:80]}\n')
        lf.write('\n')

    # stdout返回摘要（给result文件）
    print(f"已更新hints_pool.txt（{len(lines)}条）")
    print(f"ERROR" if len(lines) < 5 else f"OK", end='')


if __name__ == '__main__':
    main()
