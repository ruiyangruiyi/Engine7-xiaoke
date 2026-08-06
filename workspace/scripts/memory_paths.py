"""
memory_paths.py — Output today and yesterday memory file paths.

Usage:
  python scripts/memory_paths.py
"""
import os
from datetime import datetime, timezone, timedelta

BEIJING = timezone(timedelta(hours=8))
now = datetime.now(BEIJING)

today = now.strftime('%Y-%m-%d')
yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(os.path.dirname(_SCRIPT_DIR), 'memory')

today_path = os.path.join(MEMORY_DIR, f'{today}.md')
yesterday_path = os.path.join(MEMORY_DIR, f'{yesterday}.md')

print(f'今天: {today_path}')
if os.path.exists(today_path):
    print(f'  (exists)')
else:
    print(f'  (not found, skip)')

print(f'昨天: {yesterday_path}')
if os.path.exists(yesterday_path):
    print(f'  (exists)')
else:
    print(f'  (not found, skip)')
