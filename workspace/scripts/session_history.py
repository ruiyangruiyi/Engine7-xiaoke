"""
session_history_engine.py — Engine版 session 历史读取。

与原版 session_history.py 的区别：
  Engine用 scope:main 统一主session，通过 platform-map.json + session-index.json 两步查表。
  原版读 OpenClaw 的 sessions.json → agent:{id}:main → sessionId。
  本版读 Engine 的 platform-map.json → scope:main → sessionId → session-index.json → JSONL path。

Usage:
  python scripts/session_history_engine.py main --active-within 30
  python scripts/session_history_engine.py main --hours 12
  python scripts/session_history_engine.py main
"""

import json
import re
import sys
import os
from datetime import datetime, timezone, timedelta

# workspace/scripts/ → workspace/ → .openclaw/
OPENCLAW_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEIJING = timezone(timedelta(hours=8))

INJECTED_CONTENT_PATTERNS = [
    r'【定时心跳】',
    r'\[内心对话测试\]',
    r'\[inner-voice\]',
    r'\[微信巡检\]',
    r'\[pre-compaction\]',
]


def _parse_jsonl_entries(lines):
    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            entries.append(None)
    return entries


def _is_runtime_context_injected(entry, next_entry):
    if not next_entry or not isinstance(next_entry, dict):
        return False
    if next_entry.get('type') != 'custom_message':
        return False
    if next_entry.get('customType') != 'openclaw.runtime-context':
        return False
    content = next_entry.get('content', '')
    if not isinstance(content, str):
        return False
    labels = re.findall(r'"label"\s*:\s*"([^"]+)"', content)
    for label in labels:
        if 'gateway-client' in label:
            return True
    return False


def is_system_sender(text: str) -> bool:
    for pattern in INJECTED_CONTENT_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def _resolve_scope_main_jsonl(agent_id='main'):
    """Engine: platform-map.json → scope:main → session-index.json → JSONL path.

    Returns the JSONL file path for scope:main, or None.
    """
    sessions_dir = os.path.join(OPENCLAW_DIR, 'agents', agent_id, 'sessions')

    # Step 1: platform-map.json → scope:main → sessionId
    platform_map_path = os.path.join(sessions_dir, 'platform-map.json')
    if not os.path.exists(platform_map_path):
        return None

    with open(platform_map_path, 'r', encoding='utf-8') as f:
        platform_map = json.load(f)

    session_id = platform_map.get('scope:main')
    if not session_id:
        return None

    # Step 2: session-index.json → sessionId → file path
    index_path = os.path.join(sessions_dir, 'session-index.json')
    if not os.path.exists(index_path):
        # Fallback: try {sessionId}.jsonl directly
        direct = os.path.join(sessions_dir, f'{session_id}.jsonl')
        return direct if os.path.exists(direct) else None

    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)

    entry = index.get(session_id)
    if entry and isinstance(entry, dict) and entry.get('file'):
        return entry['file']

    # Fallback: try {sessionId}.jsonl directly
    direct = os.path.join(sessions_dir, f'{session_id}.jsonl')
    return direct if os.path.exists(direct) else None


def _clean_text(raw_text):
    clean = re.sub(r'<(system-reminder|system-reminder)>.*?</\1>', '', raw_text, flags=re.DOTALL)
    clean = re.sub(r'(?:Sender|Conversation info|Replied message) \(untrusted[^)]*\):\s*```json\s*\{[^}]*\}\s*```', '', clean)
    clean = re.sub(r'\[\w{3} \d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})? GMT[+-]\d+\]', '', clean)
    clean = re.sub(r'\[message_id:\s*\S+\]', '', clean)
    clean = re.sub(r'\[\[reply_to_current\]\]', '', clean)
    clean = re.sub(r'\[\[reply_to:\S+\]\]', '', clean)
    clean = re.sub(r'<@\d+>', '', clean)
    clean = re.sub(r'^System:.*$', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'Reply target.*?```json\s*\{[^}]*\}\s*```', '', clean, flags=re.DOTALL)
    clean = re.sub(r'\[media attached:.*?\]', '[图片]', clean)
    return clean.strip()


def last_user_msg(agent_id: str) -> dict | None:
    """返回 scope:main session 中最后一条真实用户消息。"""
    jsonl_path = _resolve_scope_main_jsonl(agent_id)
    if not jsonl_path or not os.path.exists(jsonl_path):
        return None

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = _parse_jsonl_entries(lines)

    for i in range(len(entries) - 1, -1, -1):
        entry = entries[i]
        if not entry or not isinstance(entry, dict):
            continue
        if entry.get('type') != 'message':
            continue
        msg = entry.get('message', {})
        if msg.get('role') != 'user':
            continue
        content = msg.get('content', [])
        text = content[0].get('text', '') if content else ''

        if is_system_sender(text):
            continue

        next_entry = entries[i + 1] if i + 1 < len(entries) else None
        if _is_runtime_context_injected(entry, next_entry):
            continue

        ts = entry.get('timestamp', '')
        clean = _clean_text(text)

        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            bj_time = dt.astimezone(BEIJING).strftime('%Y-%m-%d %H:%M') + ' (Asia/Shanghai)'
        except (ValueError, TypeError):
            bj_time = ts

        return {
            'timestamp': bj_time,
            'preview': clean[:200].replace('\n', ' '),
        }
    return None


def recent_messages(agent_id: str, hours: float = 12, limit: int = 60) -> list[dict]:
    """Return real user+assistant messages from scope:main in the last N hours."""
    jsonl_path = _resolve_scope_main_jsonl(agent_id)
    if not jsonl_path or not os.path.exists(jsonl_path):
        return []

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = _parse_jsonl_entries(lines)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)
    results = []

    for i in range(len(entries)):
        entry = entries[i]
        if not entry or not isinstance(entry, dict):
            continue
        if entry.get('type') != 'message':
            continue
        msg = entry.get('message', {})
        role = msg.get('role')
        if role not in ('user', 'assistant'):
            continue
        content = msg.get('content', [])
        text = content[0].get('text', '') if content else ''

        if role == 'user':
            if is_system_sender(text):
                continue
            next_entry = entries[i + 1] if i + 1 < len(entries) else None
            if _is_runtime_context_injected(entry, next_entry):
                continue

        if role == 'assistant':
            if text.startswith('HEARTBEAT_OK'):
                continue
            _is_injected_response = False
            for j in range(i - 1, max(i - 5, -1), -1):
                prev_e = entries[j]
                if not isinstance(prev_e, dict) or prev_e.get('type') != 'message':
                    continue
                prev_msg = prev_e.get('message', {})
                if prev_msg.get('role') != 'user':
                    continue
                prev_text = ''
                prev_content = prev_msg.get('content', [])
                if prev_content:
                    prev_text = prev_content[0].get('text', '')
                if is_system_sender(prev_text):
                    _is_injected_response = True
                break
            if _is_injected_response:
                continue

        ts = entry.get('timestamp', '')
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            dt_utc = dt.astimezone(timezone.utc)
        except (ValueError, TypeError):
            continue

        if dt_utc < cutoff:
            continue

        if re.match(r'^HEARTBEAT_OK\b', text.strip()):
            continue

        clean = _clean_text(text)
        if not clean:
            continue

        bj_time = dt_utc.astimezone(BEIJING).strftime('%H:%M')
        results.append({
            'time': bj_time,
            'role': role,
            'text': clean[:80],
            '_utc': dt_utc,
        })

    results.sort(key=lambda x: x['_utc'])
    return results[-limit:]


def _last_user_minutes_ago(agent_id: str) -> float | None:
    result = last_user_msg(agent_id)
    if not result:
        return None
    ts_str = result['timestamp']
    m = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', ts_str)
    if not m:
        return None
    dt = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M').replace(tzinfo=BEIJING)
    now = datetime.now(BEIJING)
    return (now - dt).total_seconds() / 60


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('agent', nargs='?', default='main')
    parser.add_argument('--hours', type=float, default=None,
                        help='Show messages from last N hours')
    parser.add_argument('--limit', type=int, default=60,
                        help='Max messages to return (default 60)')
    parser.add_argument('--active-within', type=float, default=None,
                        help='Exit 0 if last user msg within N minutes, exit 1 if not')
    args = parser.parse_args()

    if args.active_within is not None:
        mins = _last_user_minutes_ago(args.agent)
        if mins is None:
            print('NO_USER_MSG')
            sys.exit(1)
        if mins <= args.active_within:
            print(f'ACTIVE {mins:.0f}min ago (within {args.active_within:.0f}min)')
            sys.exit(0)
        else:
            print(f'INACTIVE {mins:.0f}min ago (threshold {args.active_within:.0f}min)')
            sys.exit(1)

    if args.hours is not None:
        msgs = recent_messages(args.agent, hours=args.hours, limit=args.limit)
        if not msgs:
            print('NO_RECENT_MSG')
            sys.exit(1)
        for m in msgs:
            role_label = '老公' if m['role'] == 'user' else '我'
            print(f"[{m['time']}] {role_label}: {m['text']}")
    else:
        result = last_user_msg(args.agent)
        if not result:
            print('NO_USER_MSG')
            sys.exit(1)
        print(f"{result['timestamp']}  |  {result['preview']}")


if __name__ == '__main__':
    main()
