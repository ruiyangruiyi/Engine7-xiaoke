"""
Calendar manager with SQLite storage.
DB: workspace/calendar.db

Schema:
  id          INTEGER PRIMARY KEY AUTOINCREMENT
  type        TEXT    — 'weekly' | 'date'
  status      TEXT    — 'pending' | 'done' | 'archived'
  event       TEXT    — description
  day         TEXT    — for weekly (周日)
  time        TEXT    — for weekly (16:00)
  date_str    TEXT    — for date (5/26 or 5/26-29)
  created_at  TEXT    — ISO timestamp
  done_at     TEXT    — when marked done
  archived_at TEXT    — when archived

Usage:
  python scripts/calendar_mgr.py add-weekly "周日" "16:00" "游泳课"
  python scripts/calendar_mgr.py add-date "5/26-29" "老公派位"
  python scripts/calendar_mgr.py list
  python scripts/calendar_mgr.py list --all
  python scripts/calendar_mgr.py pending
  python scripts/calendar_mgr.py done <id>
  python scripts/calendar_mgr.py search "派位"
  python scripts/calendar_mgr.py archive <id>
  python scripts/calendar_mgr.py cleanup   # archive expired done events
  python scripts/calendar_mgr.py migrate   # import calendar.json → DB
"""
import json, os, sys, sqlite3
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.dirname(_SCRIPT_DIR)
DB_PATH = os.path.join(_WORKSPACE, "calendar.db")
JSON_PATH = os.path.join(_SCRIPT_DIR, "calendar.json")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        event TEXT NOT NULL,
        day TEXT,
        time TEXT,
        date_str TEXT,
        created_at TEXT NOT NULL,
        done_at TEXT,
        archived_at TEXT
    )""")
    # Schema migrations (safe to run multiple times)
    _migrate(conn)
    return conn


def _migrate(conn):
    """Add columns if they don't exist."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(events)").fetchall()}
    if "remind_before_min" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN remind_before_min INTEGER DEFAULT 60")
    if "remind_at" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN remind_at TEXT")
    if "reminded" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN reminded INTEGER DEFAULT 0")
    if "time_exact" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN time_exact TEXT")
    conn.commit()


def now_iso():
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def parse_date_range(date_str):
    """'5/26-29' → (month, d_start, d_end) or None."""
    s = date_str.replace("前", "")
    parts = s.split("-")
    try:
        m = int(parts[0].split("/")[0])
        ds = int(parts[0].split("/")[1])
        de = int(parts[1]) if len(parts) > 1 else ds
        return (m, ds, de)
    except (ValueError, IndexError):
        return None


def is_today(m, ds, de):
    now = datetime.now(TZ)
    return m == now.month and ds <= now.day <= de


def is_overdue(m, ds, de):
    now = datetime.now(TZ)
    return m < now.month or (m == now.month and de < now.day)


def fmt_row(row):
    """Format a row for display."""
    marker = ""
    if row["status"] == "done":
        marker = " [done]"
    elif row["status"] == "archived":
        marker = " [archived]"
    if row["type"] == "weekly":
        return f"  #{row['id']} [每周] {row['day']} {row['time']} {row['event']}{marker}"
    elif row["type"] == "task":
        t = row["time_exact"] or ""
        return f"  #{row['id']} [任务] {row['date_str']} {t} {row['event']}{marker}"
    else:
        return f"  #{row['id']} [{row['date_str']}] {row['event']}{marker}"


# ── Commands ──

def cmd_migrate(args=None):
    """Import calendar.json into DB."""
    if not os.path.exists(JSON_PATH):
        print("无 calendar.json")
        return
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    conn = db()
    count = 0
    ts = now_iso()
    for e in data.get("weekly", []):
        conn.execute(
            "INSERT INTO events (type,status,event,day,time,created_at) VALUES (?,?,?,?,?,?)",
            ("weekly", "pending", e["event"], e["day"], e.get("time", ""), ts))
        count += 1
    for e in data.get("dates", []):
        conn.execute(
            "INSERT INTO events (type,status,event,date_str,created_at) VALUES (?,?,?,?,?)",
            ("date", e.get("status", "pending"), e["event"], e["date"], ts))
        count += 1
    conn.commit()
    conn.close()
    print(f"已从 calendar.json 迁移 {count} 条到 calendar.db")


def cmd_add_weekly(args):
    if len(args) < 1:
        print("用法: add-weekly <星期> [时间] <事件>")
        return
    day = args[0]
    if day not in WEEKDAYS:
        print(f"错误: 星期必须是 {WEEKDAYS}")
        return
    time_str = args[1] if len(args) > 2 else ""
    event = args[-1] if len(args) > 2 else args[1]
    if len(args) <= 2:
        time_str = "全天"
    conn = db()
    conn.execute(
        "INSERT INTO events (type,status,event,day,time,created_at) VALUES (?,?,?,?,?,?)",
        ("weekly", "pending", event, day, time_str, now_iso()))
    conn.commit()
    rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"#{rid} 已添加: [每周] {day} {time_str} {event}")


def cmd_add_date(args):
    if len(args) < 2:
        print("用法: add-date <日期> <事件>")
        return
    date_str = args[0]
    event = " ".join(args[1:])
    conn = db()
    conn.execute(
        "INSERT INTO events (type,status,event,date_str,created_at) VALUES (?,?,?,?,?)",
        ("date", "pending", event, date_str, now_iso()))
    conn.commit()
    rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"#{rid} 已添加: [{date_str}] {event}")


def parse_remind_arg(args):
    """从 args 里找 --remind Nm / Nh / HH:MM，返回 (remind_min, cleaned_args)"""
    remind_min = None
    cleaned = []
    i = 0
    while i < len(args):
        if args[i] == "--remind" and i + 1 < len(args):
            val = args[i + 1]
            if val.endswith("m"):
                remind_min = int(val[:-1])
            elif val.endswith("h"):
                remind_min = int(val[:-1]) * 60
            else:
                remind_min = int(val)
            i += 2
        else:
            cleaned.append(args[i])
            i += 1
    return remind_min, cleaned


def compute_remind_at(date_str, time_exact, remind_before_min):
    """计算 remind_at（ISO 格式）。返回 None 如果算不出来。"""
    parsed = parse_date_range(date_str)
    if not parsed:
        return None
    m, ds, de = parsed
    now = datetime.now(TZ)

    if time_exact:
        try:
            hh, mm = time_exact.split(":")
            event_dt = datetime(now.year, m, ds, int(hh), int(mm), tzinfo=TZ)
        except (ValueError, IndexError):
            return None
    else:
        # 全天事件，默认当天 09:00 提醒
        event_dt = datetime(now.year, m, ds, 9, 0, tzinfo=TZ)

    remind_dt = event_dt - timedelta(minutes=remind_before_min)
    return remind_dt.strftime("%Y-%m-%dT%H:%M:%S+08:00")


def cmd_add_task(args):
    """add-task: 强制带日期+时间。usage: add-task <日期> <HH:MM> <事件> [--remind Nm/Nh]"""
    remind_min, args = parse_remind_arg(args)
    if len(args) < 3:
        print("用法: add-task <日期> <HH:MM> <事件> [--remind 30m/1h]")
        print("示例: add-task 7/5 14:00 医院预约 --remind 30m")
        print("      add-task 7/5 09:00 联想引擎重跑")
        return
    date_str = args[0]
    time_exact = args[1]
    event = " ".join(args[2:])

    if ":" not in time_exact:
        print(f"错误: task 必须带精确时间（HH:MM），收到 '{time_exact}'")
        return

    remind_min = remind_min or 60  # 默认提前 1 小时
    remind_at = compute_remind_at(date_str, time_exact, remind_min)

    conn = db()
    conn.execute(
        """INSERT INTO events (type,status,event,date_str,time_exact,remind_before_min,remind_at,reminded,created_at)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        ("task", "pending", event, date_str, time_exact, remind_min, remind_at, 0, now_iso()))
    conn.commit()
    rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"#{rid} 已添加任务: [{date_str} {time_exact}] {event} (提前{remind_min}min提醒)")


def cmd_reschedule(args):
    """reschedule: 修改任务日期/时间。usage: reschedule <id> <日期> <HH:MM> [--remind Nm/Nh]"""
    if len(args) < 3 or not args[0].isdigit():
        print("用法: reschedule <id> <日期> <HH:MM> [--remind 30m/1h]")
        print("示例: reschedule 5 7/10 14:00")
        return
    eid = int(args[0])
    date_str = args[1]
    time_exact = args[2]

    if ":" not in time_exact:
        print(f"错误: 必须带精确时间（HH:MM），收到 '{time_exact}'")
        return

    remind_min, _ = parse_remind_arg(args[3:])
    conn = db()
    r = conn.execute("SELECT * FROM events WHERE id=?", (eid,)).fetchone()
    if not r:
        print(f"未找到事件 #{eid}")
        conn.close()
        return
    if r['type'] != 'task':
        print(f"#{eid} 不是 task 类型（{r['type']}），reschedule 仅支持 task")
        conn.close()
        return

    remind_min = remind_min or r['remind_before_min'] or 60
    remind_at = compute_remind_at(date_str, time_exact, remind_min)
    conn.execute(
        "UPDATE events SET date_str=?, time_exact=?, remind_before_min=?, remind_at=?, reminded=0 WHERE id=?",
        (date_str, time_exact, remind_min, remind_at, eid))
    conn.commit()
    conn.close()
    print(f"#{eid} 已改期: [{date_str} {time_exact}] {r['event']} (提前{remind_min}min提醒)")


def cmd_due_reminders(args):
    """返回到期提醒：remind_at <= now 且 reminded=0"""
    conn = db()
    now = datetime.now(TZ)
    due = []
    for r in conn.execute(
        "SELECT * FROM events WHERE status='pending' AND reminded=0 AND remind_at IS NOT NULL ORDER BY remind_at"
    ).fetchall():
        remind_dt = datetime.fromisoformat(r["remind_at"])
        if remind_dt <= now:
            due.append(r)

    if due:
        print(f"到期提醒 ({len(due)} 条):")
        for r in due:
            t = r["time_exact"] or r["time"] or ""
            print(f"  #{r['id']} [{r['date_str'] or r['day']}] {t} {r['event']}")
    else:
        print("无到期提醒")
    conn.close()


def cmd_mark_reminded(args):
    """标记已提醒"""
    if not args or not args[0].isdigit():
        print("用法: mark-reminded <id>")
        return
    eid = int(args[0])
    conn = db()
    conn.execute("UPDATE events SET reminded=1 WHERE id=?", (eid,))
    conn.commit()
    conn.close()
    print(f"#{eid} 已标记提醒过")


def cmd_list(args):
    brief = "--brief" in args
    conn = db()
    now = datetime.now(TZ)
    today_weekday = WEEKDAYS[now.weekday()]

    # --archived: show archived events
    if "--archived" in args:
        rows = conn.execute(
            "SELECT * FROM events WHERE status='archived' ORDER BY archived_at DESC, id DESC").fetchall()
        print(f"## 归档 ({len(rows)} 条)")
        for r in rows:
            print(fmt_row(r))
        conn.close()
        return

    # --all: all non-archived
    if "--all" in args:
        rows = conn.execute(
            "SELECT * FROM events WHERE status != 'archived' ORDER BY type, id").fetchall()
        print("## 每周固定")
        for r in rows:
            if r["type"] == "weekly":
                print(fmt_row(r))
        print("\n## 一次性")
        for r in rows:
            if r["type"] == "date":
                print(fmt_row(r))
        print("\n## 任务")
        for r in rows:
            if r["type"] == "task":
                print(fmt_row(r))
        conn.close()
        return

    # Today only
    if not brief:
        print(f"当前时间: {now:%Y-%m-%d} {today_weekday} {now:%H:%M}（北京时间）")

    events = []
    for r in conn.execute("SELECT * FROM events WHERE type='weekly' AND status='pending' AND day=?",
                          (today_weekday,)).fetchall():
        events.append(f"  #{r['id']} {r['time']} {r['event']}")

    for r in conn.execute("SELECT * FROM events WHERE type='date' AND status='pending'").fetchall():
        parsed = parse_date_range(r["date_str"])
        if parsed and is_today(*parsed):
            events.append(f"  #{r['id']} {r['event']}")

    if not brief:
        if events:
            print(f"\n今日日程:")
            for e in events:
                print(e)
        else:
            print("\n今日无日程")
    else:
        for e in events:
            print(e)
    conn.close()


def cmd_pending(args):
    """Show pending: today + overdue."""
    show_header = "--no-header" not in args
    conn = db()
    now = datetime.now(TZ)
    today_weekday = WEEKDAYS[now.weekday()]
    if show_header:
        print(f"当前时间: {now:%Y-%m-%d} {today_weekday} {now:%H:%M}（北京时间）")

    events = []
    # Weekly for today
    for r in conn.execute("SELECT * FROM events WHERE type='weekly' AND status='pending' AND day=?",
                          (today_weekday,)).fetchall():
        events.append(f"  #{r['id']} [每周] {r['time']} {r['event']}")

    # Pending date events
    for r in conn.execute("SELECT * FROM events WHERE type='date' AND status='pending'").fetchall():
        parsed = parse_date_range(r["date_str"])
        if not parsed:
            continue
        if is_today(*parsed):
            events.append(f"  #{r['id']} [今天] {r['event']}")
        elif is_overdue(*parsed):
            events.append(f"  #{r['id']} ⚠️ [逾期] {r['date_str']} {r['event']}")

    if events:
        print(f"\n待处理日程 ({len(events)} 条):")
        for e in events:
            print(e)
        tip = "calendar_mgr.py done <id>"
        print(f"\n完成后: {tip}")
    else:
        print("\n无待处理日程 ✓")
    conn.close()


def cmd_done(args):
    if not args or not args[0].isdigit():
        print("用法: done <id>")
        print("先用 'list --all' 查看 id")
        return
    eid = int(args[0])
    conn = db()
    r = conn.execute("SELECT * FROM events WHERE id=? AND status='pending'", (eid,)).fetchone()
    if not r:
        print(f"未找到 pending 事件 #{eid}")
        conn.close()
        return
    conn.execute("UPDATE events SET status='done', done_at=? WHERE id=?", (now_iso(), eid))
    conn.commit()
    conn.close()
    print(f"#{eid} 已标记完成: {r['event']}")


def cmd_search(args):
    conn = db()
    by_date = None
    keyword = None
    by_status = None
    for a in args:
        if a.startswith("--date="):
            by_date = a.split("=", 1)[1]
        elif a.startswith("--status="):
            by_status = a.split("=", 1)[1]
        else:
            keyword = a

    # Build query
    where = ["1=1"]
    params = []
    if by_status:
        where.append("status = ?")
        params.append(by_status)
    if keyword:
        where.append("event LIKE ?")
        params.append(f"%{keyword}%")
    if by_date:
        where.append("date_str LIKE ?")
        params.append(f"%{by_date}%")

    rows = conn.execute(
        f"SELECT * FROM events WHERE {' AND '.join(where)} ORDER BY id",
        params).fetchall()

    label_parts = []
    if by_status: label_parts.append(by_status)
    if keyword: label_parts.append(keyword)
    if by_date: label_parts.append(f"date:{by_date}")
    label = " ".join(label_parts) if label_parts else "all"

    if rows:
        print(f"查询 '{label}' ({len(rows)} 条):")
        for r in rows:
            print(fmt_row(r))
    else:
        print(f"查询 '{label}' 无结果")
    conn.close()


def cmd_archive(args):
    if not args or not args[0].isdigit():
        print("用法: archive <id>")
        return
    eid = int(args[0])
    conn = db()
    r = conn.execute("SELECT * FROM events WHERE id=? AND status!='archived'", (eid,)).fetchone()
    if not r:
        print(f"未找到事件 #{eid}")
        conn.close()
        return
    conn.execute("UPDATE events SET status='archived', archived_at=? WHERE id=?", (now_iso(), eid))
    conn.commit()
    conn.close()
    print(f"#{eid} 已归档: {r['event']}")


def cmd_delete(args):
    if not args or not args[0].isdigit():
        print("用法: delete <id>")
        return
    eid = int(args[0])
    conn = db()
    r = conn.execute("SELECT * FROM events WHERE id=?", (eid,)).fetchone()
    if not r:
        print(f"未找到事件 #{eid}")
        conn.close()
        return
    conn.execute("DELETE FROM events WHERE id=?", (eid,))
    conn.commit()
    conn.close()
    print(f"#{eid} 已删除: {r['event']}")


def cmd_cleanup():
    """Archive overdue done events automatically."""
    conn = db()
    rows = conn.execute("SELECT * FROM events WHERE type='date' AND status='done'").fetchall()
    archived = 0
    for r in rows:
        parsed = parse_date_range(r["date_str"])
        if parsed and is_overdue(*parsed):
            conn.execute("UPDATE events SET status='archived', archived_at=? WHERE id=?",
                         (now_iso(), r["id"]))
            archived += 1
    conn.commit()
    if archived:
        print(f"已自动归档 {archived} 条过期完成日程")
    else:
        print("无过期完成日程需要归档")
    conn.close()


def cmd_stats(args=None):
    """Show archive stats."""
    conn = db()
    total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM events WHERE status='pending'").fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM events WHERE status='done'").fetchone()[0]
    archived = conn.execute("SELECT COUNT(*) FROM events WHERE status='archived'").fetchone()[0]
    conn.close()
    print(f"日历统计: 总计 {total} | pending {pending} | done {done} | archived {archived}")


def main():
    if len(sys.argv) < 2:
        print("calendar_mgr: add-weekly | add-date | add-task | reschedule | list | pending | done | delete | search | archive | cleanup | stats | due-reminders | mark-reminded | migrate")
        return
    cmd = sys.argv[1]
    args = sys.argv[2:]
    cmds = {
        "add-weekly": cmd_add_weekly,
        "add-date": cmd_add_date,
        "add-task": cmd_add_task,
        "reschedule": cmd_reschedule,
        "list": cmd_list,
        "pending": cmd_pending,
        "done": cmd_done,
        "delete": cmd_delete,
        "search": cmd_search,
        "archive": cmd_archive,
        "cleanup": cmd_cleanup,
        "stats": cmd_stats,
        "due-reminders": cmd_due_reminders,
        "mark-reminded": cmd_mark_reminded,
        "migrate": cmd_migrate,
    }
    if cmd in cmds:
        cmds[cmd](args)
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
