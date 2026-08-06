"""
replace_hints_pool.py — Atomically replace inner-voice/hints_pool.txt

Usage:
  python replace_hints_pool.py <source_file>
"""
import sys, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POOL_DIR = os.path.join(SCRIPT_DIR, '..', 'inner-voice')
POOL_PATH = os.path.normpath(os.path.join(POOL_DIR, 'hints_pool.txt'))

if len(sys.argv) < 2:
    print(f"Usage: python {os.path.basename(__file__)} <source_file>")
    sys.exit(1)

src = sys.argv[1]
if not os.path.exists(src):
    print(f"Source file not found: {src}")
    sys.exit(1)

# Validate: must have lines
with open(src, 'r', encoding='utf-8') as f:
    lines = [l.strip() for l in f if l.strip()]

if len(lines) < 10:
    print(f"Too few hints ({len(lines)}), keeping old pool")
    sys.exit(1)

# Atomic replace: write to .tmp then rename
tmp_path = POOL_PATH + '.tmp'
with open(tmp_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

os.replace(tmp_path, POOL_PATH)
print(f"Replaced hints_pool.txt with {len(lines)} hints")
