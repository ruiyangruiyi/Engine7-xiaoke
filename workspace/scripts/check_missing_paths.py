import sqlite3
import os

db = sqlite3.connect('C:/Users/24045/.openclaw/agents/main/memory/memory.db')
c = db.cursor()

c.execute("SELECT DISTINCT path FROM chunks WHERE source='memory'")
paths = [r[0] for r in c.fetchall()]

workspace = "C:/Users/24045/.openclaw/workspace"
backslash = chr(92)
missing = []
existing = []
for p in paths:
    norm = p.replace(backslash, '/')
    abs_path = os.path.join(workspace, norm)
    if os.path.exists(abs_path):
        existing.append(p)
    else:
        missing.append(p)

print(f"DB 中 memory paths: {len(paths)}")
print(f"workspace 实际存在: {len(existing)}")
print(f"workspace 不存在（会丢）: {len(missing)}")
print(f"\n缺失的路径示例（top 15）:")
for p in missing[:15]:
    print(f"  {p}")

db.close()
