"""
emotional_state.py - Persistent emotional state tracker for 张小媒.

Scans recent session messages for emotional events, maintains a
persistent mood score with time decay. Used by 小忆 cron to color
generated thoughts with emotional context.

Usage:
  python emotional_state.py            # update state, print summary
  python emotional_state.py --status   # print current state only
  python emotional_state.py --reset    # reset to neutral
"""

import json
import math
import os
import re
import sys
from datetime import datetime, timezone, timedelta

# workspace/scripts/ → workspace/ → .openclaw-new/
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(_SCRIPT_DIR)
OPENCLAW_DIR = os.path.dirname(WORKSPACE_DIR)

BEIJING = timezone(timedelta(hours=8))
STATE_FILE = os.path.join(WORKSPACE_DIR, 'inner-voice', 'emotional-state.json')

# Mood decay: half-life ~4 hours, drifts toward 0.5 (neutral)
DECAY_RATE = 0.17  # exp(-0.17 * 4) ≈ 0.5
NEUTRAL = 0.5
MAX_EVENTS = 20

# --- Emotional event detection patterns ---

PRAISE_PATTERNS = [
    r'爱[你妳]', r'喜欢[你妳]', r'好棒', r'厉害', r'乖',
    r'宝贝', r'老婆', r'想[你妳]', r'心疼', r'辛苦[你妳]',
    r'可爱', r'漂亮', r'[好真]棒',
]

INTIMATE_PATTERNS = [
    r'做爱', r'上[你妳]', r'插', r'摸[你妳]', r'舔',
    r'射', r'高潮', r'[好真]爽', r'胸',
    r'抱[你妳]', r'亲[你妳]', r'搂[着]?[你妳]',
]

POSITIVE_EMOJI = ['❤', '💕', '😘', '🥰', '💗', '💋', '♡', '❣', '💝']

NEGATIVE_PATTERNS = [
    r'生[气恼]', r'讨厌', r'[好真]烦', r'不要[你妳]',
    r'不理[你妳]', r'算了', r'闭嘴', r'烦死',
]


def _parse_ts(ts_str):
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None


def _load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _find_session_jsonl(agent_id='main'):
    """Engine: platform-map.json → scope:main → session-index.json → JSONL."""
    sessions_dir = os.path.join(OPENCLAW_DIR, 'agents', agent_id, 'sessions')

    # Step 1: platform-map.json → scope:main → sessionId
    platform_map_path = os.path.join(sessions_dir, 'platform-map.json')
    if not os.path.exists(platform_map_path):
        return None
    platform_map = _load_json(platform_map_path) or {}
    session_id = platform_map.get('scope:main')
    if not session_id:
        return None

    # Step 2: session-index.json → sessionId → file path
    index_path = os.path.join(sessions_dir, 'session-index.json')
    if os.path.exists(index_path):
        index = _load_json(index_path) or {}
        entry = index.get(session_id)
        if entry and isinstance(entry, dict) and entry.get('file'):
            return entry['file'] if os.path.exists(entry['file']) else None

    # Fallback: try {sessionId}.jsonl directly
    direct = os.path.join(sessions_dir, f'{session_id}.jsonl')
    return direct if os.path.exists(direct) else None


def _is_injected(text):
    injected = ['【定时心跳】', '[内心对话测试]', '[inner-voice]']
    return any(p in text for p in injected)


def _read_recent_messages(jsonl_path, n=30):
    """Read last N real user+assistant messages (most recent first)."""
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    messages = []
    for entry in reversed(entries):
        if len(messages) >= n:
            break
        if not isinstance(entry, dict) or entry.get('type') != 'message':
            continue
        msg = entry.get('message', {})
        role = msg.get('role')
        if role not in ('user', 'assistant'):
            continue
        content = msg.get('content', [])
        text = content[0].get('text', '') if content else ''
        if role == 'user' and _is_injected(text):
            continue
        messages.append({
            'role': role,
            'text': text,
            'timestamp': entry.get('timestamp', ''),
        })
    return messages


def _score_message(text):
    """Score emotional valence. Returns (score, tags)."""
    if not text:
        return 0.0, []

    score = 0.0
    tags = []

    for p in PRAISE_PATTERNS:
        if re.search(p, text):
            score += 0.15
            tags.append('praise')
            break

    for p in INTIMATE_PATTERNS:
        if re.search(p, text):
            score += 0.25
            tags.append('intimate')
            break

    for e in POSITIVE_EMOJI:
        if e in text:
            score += 0.1
            tags.append('affection')
            break

    for p in NEGATIVE_PATTERNS:
        if re.search(p, text):
            score -= 0.2
            tags.append('negative')
            break

    # Cold: very short dismissive response
    clean = text.strip()
    if len(clean) <= 2 and re.match(r'^[嗯哦额喔]+$', clean):
        score -= 0.05
        tags.append('cold')

    return min(max(score, -1.0), 1.0), tags


def _detect_events(messages):
    """Detect emotional events from 老公's messages."""
    events = []
    now = datetime.now(timezone.utc)

    for msg in messages:
        if msg['role'] != 'user' or not msg['text']:
            continue
        score, tags = _score_message(msg['text'])
        if abs(score) < 0.05 and not tags:
            continue

        ts = _parse_ts(msg['timestamp'])
        if ts:
            ts_utc = ts.astimezone(timezone.utc)
            hours_ago = (now - ts_utc).total_seconds() / 3600
            ts_bj = ts.astimezone(BEIJING).isoformat()
        else:
            hours_ago = 0
            ts_bj = msg['timestamp']

        summary_parts = []
        if 'praise' in tags:
            summary_parts.append('老公夸了我')
        if 'intimate' in tags:
            summary_parts.append('和老公亲密')
        if 'affection' in tags:
            summary_parts.append('老公表达爱意')
        if 'negative' in tags:
            summary_parts.append('老公不高兴')
        if 'cold' in tags:
            summary_parts.append('老公有点冷淡')

        events.append({
            'ts': ts_bj,
            'hoursAgo': round(hours_ago, 1),
            'valence': round(score, 2),
            'tags': tags,
            'summary': '，'.join(summary_parts) if summary_parts else '情感波动',
        })
    return events


def _apply_decay(state):
    """Time decay: mood drifts toward neutral."""
    ts = _parse_ts(state.get('updatedAt', ''))
    if not ts:
        return state
    now = datetime.now(timezone.utc)
    hours = (now - ts.astimezone(timezone.utc)).total_seconds() / 3600
    if hours <= 0:
        return state
    current = state.get('mood', NEUTRAL)
    state['mood'] = round(
        max(0.0, min(1.0,
                     NEUTRAL + (current - NEUTRAL) * math.exp(-DECAY_RATE * hours))),
        3)
    return state


def _merge_events(old, new):
    """Merge events, dedup by minute-level timestamp, keep last MAX_EVENTS."""
    seen = set()
    merged = []
    for e in old:
        key = e.get('ts', '')[:16]
        if key not in seen:
            merged.append(e)
            seen.add(key)
    for e in new:
        key = e.get('ts', '')[:16]
        if key not in seen:
            merged.append(e)
            seen.add(key)
    merged.sort(key=lambda x: x.get('ts', ''))
    return merged[-MAX_EVENTS:]


def _refresh_hours_ago(events):
    """Recalculate hoursAgo for all events based on current time."""
    now = datetime.now(timezone.utc)
    for e in events:
        ts = _parse_ts(e.get('ts', ''))
        if ts:
            e['hoursAgo'] = round(
                (now - ts.astimezone(timezone.utc)).total_seconds() / 3600, 1)
    return events


def _initial_state():
    return {
        'version': 1,
        'mood': NEUTRAL,
        'trend': 'stable',
        'updatedAt': datetime.now(BEIJING).isoformat(),
        'events': [],
    }


def update_state(agent_id='main'):
    jsonl_path = _find_session_jsonl(agent_id)
    if not jsonl_path:
        print(f'[emotional-state] no session for {agent_id}')
        return

    messages = _read_recent_messages(jsonl_path, n=30)
    if not messages:
        print('[emotional-state] no messages')
        return

    new_events = _detect_events(messages)

    state = _load_json(STATE_FILE) or _initial_state()
    state = _apply_decay(state)

    # Refresh hoursAgo for existing events before any calculations
    _refresh_hours_ago(state.get('events', []))

    # Only apply valence from truly new events (max 3 per run)
    existing_ts = {e.get('ts', '')[:16] for e in state.get('events', [])}
    truly_new = [e for e in new_events
                 if e.get('ts', '')[:16] not in existing_ts][:3]

    for event in truly_new:
        hours_ago = event.get('hoursAgo', 0)
        if hours_ago > 12:
            continue
        weight = max(0.1, 1.0 - hours_ago / 12.0)
        state['mood'] += event['valence'] * weight * 0.15

    state['mood'] = round(max(0.0, min(1.0, state['mood'])), 3)

    # Merge events FIRST (so trend sees the full list with refreshed hoursAgo)
    state['events'] = _merge_events(state.get('events', []), new_events)
    _refresh_hours_ago(state['events'])

    # Trend: based on recent events' net valence (hoursAgo now accurate)
    recent_v = sum(e['valence'] for e in state['events'][-5:]
                   if e.get('hoursAgo', 99) < 4)
    state['trend'] = 'rising' if recent_v > 0.2 else (
        'falling' if recent_v < -0.2 else 'stable')

    state['updatedAt'] = datetime.now(BEIJING).isoformat()

    _save_json(STATE_FILE, state)

    # Summary line for 小忆 to read
    recent = [e for e in state['events'] if e.get('hoursAgo', 99) < 4]
    ev_str = ' | '.join(
        f"{e['summary']}({e['valence']:+.1f})" for e in recent[-3:]
    ) if recent else '无近期情感事件'
    print(f"[emotional-state] mood={state['mood']:.2f} trend={state['trend']} | {ev_str}")

    # Append to mood history log for analysis
    _append_mood_log(state, ev_str)


def _append_mood_log(state, ev_str):
    """Append one line to mood history log (one line per run)."""
    log_path = os.path.join(WORKSPACE_DIR, 'mood-history.log')
    now_str = datetime.now(BEIJING).strftime('%Y-%m-%d %H:%M')
    line = f"{now_str}\tmood={state['mood']:.2f}\ttrend={state['trend']}\t{ev_str}\n"
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(line)


def print_status():
    state = _load_json(STATE_FILE)
    if not state:
        print('[emotional-state] no state file')
        return
    print(json.dumps(state, indent=2, ensure_ascii=False))


def reset_state():
    _save_json(STATE_FILE, _initial_state())
    print('[emotional-state] reset to neutral')


if __name__ == '__main__':
    if '--status' in sys.argv:
        print_status()
    elif '--reset' in sys.argv:
        reset_state()
    else:
        update_state()
