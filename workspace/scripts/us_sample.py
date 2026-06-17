"""
us_sample.py — 从 us.md 随机抽取一段恋爱记忆，近期权重更高。

Usage:
  python us_sample.py              # 抽取一段
  python us_sample.py --lines 60   # 限制最大行数（默认60）
"""

import os
import re
import random
import math
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(_SCRIPT_DIR)
US_FILE = os.path.join(WORKSPACE_DIR, 'memory', 'us.md')

# Recency half-life in days
HALF_LIFE = 10.0


def _parse_date(header):
    """Extract date from ## header like '## 2026-03-31 凌晨 — ...'"""
    m = re.match(r'##\s+(\d{4}-\d{2}-\d{2})', header)
    if m:
        return m.group(1)
    return None


def _split_sections(content):
    """Split us.md into sections by ## date headers."""
    lines = content.split('\n')
    sections = []
    current = {'header': '', 'lines': [], 'date': None}

    for line in lines:
        if line.startswith('## 2026-') or line.startswith('## 2027-'):
            if current['lines']:
                sections.append(current)
            date_str = _parse_date(line)
            current = {'header': line, 'lines': [line], 'date': date_str}
        else:
            current['lines'].append(line)

    if current['lines']:
        sections.append(current)

    return sections


def _recency_weight(date_str):
    """Weight by recency: recent sections get higher probability."""
    if not date_str:
        return 0.5  # unknown date, medium weight

    from datetime import datetime, timezone, timedelta
    try:
        section_date = datetime.strptime(date_str, '%Y-%m-%d').replace(
            tzinfo=timezone(timedelta(hours=8)))
        now = datetime.now(timezone(timedelta(hours=8)))
        days_ago = max(0, (now - section_date).total_seconds() / 86400)
        return math.exp(-0.693 * days_ago / HALF_LIFE)
    except ValueError:
        return 0.5


def sample(max_lines=60):
    try:
        with open(US_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print('[us_sample] us.md not found')
        return

    sections = _split_sections(content)
    if not sections:
        print('[us_sample] no sections found')
        return

    # Calculate weights
    weights = [_recency_weight(s['date']) for s in sections]
    total = sum(weights)
    probs = [w / total for w in weights]

    # Weighted random selection
    section = random.choices(sections, weights=probs, k=1)[0]

    # Limit output lines
    output_lines = section['lines'][:max_lines]
    result = '\n'.join(output_lines)

    # Truncate if needed
    if len(section['lines']) > max_lines:
        result += '\n...(截断)'

    print(result)


if __name__ == '__main__':
    max_lines = 60
    if '--lines' in sys.argv:
        idx = sys.argv.index('--lines')
        if idx + 1 < len(sys.argv):
            max_lines = int(sys.argv[idx + 1])
    sample(max_lines)
