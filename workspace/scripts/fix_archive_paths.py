"""
修复 DB 里 chunks 路径：把已归档的 topics 路径修正为 topics/archive/...
这样 engine sync 时能找到文件，不会再丢失 chunks。
"""
import sqlite3
import os

db_path = 'C:/Users/24045/.openclaw/agents/main/memory/memory.db'
workspace = 'C:/Users/24045/.openclaw/workspace'
backslash = chr(92)

db = sqlite3.connect(db_path)
c = db.cursor()

# 取所有 memory source 的 distinct path
c.execute("SELECT DISTINCT path FROM chunks WHERE source='memory'")
paths = [r[0] for r in c.fetchall()]

updated = 0
not_found = 0
examples = []

for p in paths:
    norm = p.replace(backslash, '/')
    abs_path = os.path.join(workspace, norm)
    if os.path.exists(abs_path):
        continue  # 原路径存在，不动
    
    # 尝试在 archive 目录里找同名文件
    basename = os.path.basename(norm)
    dirname = os.path.dirname(norm)
    
    # topics/feedback/xxx.md → topics/archive/feedback/xxx.md
    if dirname.startswith('topics/') and dirname != 'topics':
        subdir = dirname[len('topics/'):]
        archive_path = f'topics/archive/{subdir}/{basename}'
        abs_archive = os.path.join(workspace, archive_path.replace('/', os.sep))
        if os.path.exists(abs_archive):
            # 更新 DB：chunks + files + chunks_fts
            c.execute("UPDATE chunks SET path=? WHERE path=? AND source='memory'", (archive_path, p))
            try:
                c.execute("UPDATE files SET path=? WHERE path=? AND source='memory'", (archive_path, p))
            except sqlite3.IntegrityError:
                pass  # 新路径已有 files 记录，跳过
            c.execute("UPDATE chunks_fts SET path=? WHERE path=? AND source='memory'", (archive_path, p))
            updated += 1
            continue
    
    # 尝试整个 archive 目录下搜索同名文件
    found = False
    for root, dirs, files in os.walk(os.path.join(workspace, 'topics', 'archive')):
        if basename in files:
            rel = os.path.relpath(os.path.join(root, basename), workspace).replace(backslash, '/')
            c.execute("UPDATE chunks SET path=? WHERE path=? AND source='memory'", (rel, p))
            try:
                c.execute("UPDATE files SET path=? WHERE path=? AND source='memory'", (rel, p))
            except sqlite3.IntegrityError:
                pass
            c.execute("UPDATE chunks_fts SET path=? WHERE path=? AND source='memory'", (rel, p))
            updated += 1
            found = True
            break
    if not found:
        not_found += 1
        if len(examples) < 10:
            examples.append(p)

db.commit()

print(f"✅ 路径已修正: {updated}")
print(f"❌ 找不到对应文件: {not_found}")
if examples:
    print(f"\n找不到的示例:")
    for e in examples:
        print(f"  {e}")

# 验证
c.execute("SELECT DISTINCT path FROM chunks WHERE source='memory'")
all_paths = [r[0] for r in c.fetchall()]
missing_count = 0
for p in all_paths:
    abs_path = os.path.join(workspace, p.replace(backslash, '/'))
    if not os.path.exists(abs_path):
        missing_count += 1
print(f"\n最终验证: {len(all_paths)} 个路径，{missing_count} 个仍找不到")

db.close()
