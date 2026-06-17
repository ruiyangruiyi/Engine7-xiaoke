"""
topics_scorer.py — Phase 2: Activation Energy Model for 小忆.

Scores all topic files by activation energy, outputs top candidates
for 小忆 to use as thought material.

activation = recency × emotional_weight × frequency × open_loop_bonus

Usage:
  python topics_scorer.py                # top 3 topics
  python topics_scorer.py --top 5        # top 5
  python topics_scorer.py --type emotion  # only emotion topics
  python topics_scorer.py --init         # initialize usage tracking
"""

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timezone, timedelta

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(_SCRIPT_DIR)
TOPICS_DIR = os.path.join(WORKSPACE_DIR, 'topics')
USAGE_FILE = os.path.join(WORKSPACE_DIR, 'inner-voice', 'topics-usage.json')
EMOTIONAL_STATE_FILE = os.path.join(WORKSPACE_DIR, 'inner-voice', 'emotional-state.json')

BEIJING = timezone(timedelta(hours=8))

# Scoring weights
HALF_LIFE_DAYS = 3.0  # default recency half-life (used as fallback)
PROJECT_HALF_LIFE_DAYS = 1.5  # project decays faster

# Skip these files/dirs
SKIP_NAMES = {'MEMORY.md', 'archive'}
SKIP_DIRS = {'archive'}


def _load_json(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _scan_topics(topics_dir, type_filter=None):
    """Scan topics directory, return list of (relpath, fullpath, mtime)."""
    results = []
    for root, dirs, files in os.walk(topics_dir):
        # Skip archive dirs
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if not fname.endswith('.md') or fname in SKIP_NAMES:
                continue
            fullpath = os.path.join(root, fname)
            relpath = os.path.relpath(fullpath, topics_dir)

            # Type filter
            if type_filter:
                if not relpath.startswith(type_filter + os.sep) and \
                   not relpath.startswith(type_filter + '_'):
                    continue

            mtime = os.path.getmtime(fullpath)
            results.append((relpath, fullpath, mtime))

    return results


def _read_frontmatter(fullpath):
    """Extract name, description, type from YAML frontmatter."""
    try:
        with open(fullpath, 'r', encoding='utf-8') as f:
            content = f.read(2000)
    except (FileNotFoundError, UnicodeDecodeError):
        return {}, ''

    meta = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm = parts[1]
            for line in fm.strip().split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    meta[k.strip()] = v.strip().strip("'\"")

    # Body preview (first 150 chars after frontmatter)
    body = content
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            body = parts[2]
    preview = body.strip()[:150].replace('\n', ' ')

    return meta, preview


def _recency_score(mtime, topic_type='emotion'):
    """Recency weight by type.
    emotion: slow hyperbolic decay 1/(1+0.02*days) — ~50 day effective range
    project: fast exponential decay — 3-day half-life
    others:  exponential decay — 3-day half-life
    """
    now = time.time()
    days_ago = max(0, (now - mtime) / 86400)
    if topic_type == 'emotion':
        return 1.0 / (1.0 + 0.02 * days_ago)
    # project: 1.5-day half-life (fast decay)
    if topic_type == 'project':
        return math.exp(-0.693 * days_ago / PROJECT_HALF_LIFE_DAYS)
    # others: default 3-day half-life
    return math.exp(-0.693 * days_ago / HALF_LIFE_DAYS)


def _emotional_weight(mood):
    """Mood-dependent topic weight (uniform for now, kept for extensibility)."""
    return 1.0


def _frequency_weight(relpath, usage_data, cooldown_hours=6, is_project=False):
    """Reconsolidation model: cooldown suppresses, then recall strengthens.

    - During cooldown: near-zero (prevent repetition)
    - Just after cooldown: boosted (reconsolidation, memory strengthened by recall)
    - Boost decays over ~24h back to baseline
    - Count gives a small permanent boost (recalled memories are slightly stronger)
    """
    entry = usage_data.get(relpath, {})
    count = entry.get('count', 0)
    last = entry.get('lastSelected')

    # Cooldown: project=1h, others=6h
    effective_cooldown = 1 if is_project else cooldown_hours

    if last:
        try:
            last_dt = datetime.fromisoformat(last)
            hours_ago = (datetime.now(BEIJING) - last_dt).total_seconds() / 3600

            # Phase 1: cooldown — suppress
            if hours_ago < effective_cooldown:
                return 0.01

            # Phase 2: reconsolidation boost — decays over 24h
            hours_since_cooldown = hours_ago - effective_cooldown
            reconsolidation_boost = 1.0 + 0.3 * max(0, 1.0 - hours_since_cooldown / 24.0)

            # Permanent mild boost from being recalled before (capped)
            count_bonus = min(count * 0.05, 0.3)

            return reconsolidation_boost + count_bonus
        except (ValueError, TypeError):
            pass

    # Never recalled: baseline
    return 1.0


def _get_mood():
    """Read current mood from emotional-state.json."""
    state = _load_json(EMOTIONAL_STATE_FILE)
    if state and 'mood' in state:
        return state['mood']
    return None


def score_topics(top_n=3, type_filter=None):
    """Score all topics and return top N."""
    topics = _scan_topics(TOPICS_DIR, type_filter)
    if not topics:
        print('[topics_scorer] no topics found')
        return []

    usage_data = _load_json(USAGE_FILE, {})
    mood = _get_mood()

    scored = []
    now = time.time()

    for relpath, fullpath, mtime in topics:
        meta, preview = _read_frontmatter(fullpath)

        # Determine topic type from path or frontmatter
        if relpath.startswith('emotion') or meta.get('type') == 'emotion':
            topic_type = 'emotion'
        elif relpath.startswith('project') or meta.get('type') == 'project':
            topic_type = 'project'
        else:
            topic_type = 'other'

        recency = _recency_score(mtime, topic_type=topic_type)
        emo_w = _emotional_weight(mood)
        freq_w = _frequency_weight(relpath, usage_data, is_project=(topic_type == 'project'))

        # Small random factor to break ties and add variety (±10%)
        import random
        jitter = 0.9 + random.random() * 0.2

        activation = recency * emo_w * freq_w * jitter

        days_ago = max(0, (now - mtime) / 86400)

        # Output path relative to workspace (cwd for 小忆)
        workspace_relpath = 'topics/' + relpath.replace(os.sep, '/')

        scored.append({
            'file': workspace_relpath,
            '_topics_relpath': relpath,  # internal key for usage tracking
            'score': round(activation, 4),
            'recency': round(recency, 3),
            'freq_w': round(freq_w, 3),
            'is_emotion': topic_type == 'emotion',
            'topic_type': topic_type,
            'name': meta.get('name', os.path.basename(relpath)),
            'description': meta.get('description', ''),
            'preview': preview,
            'days_ago': round(days_ago, 1),
        })

    scored.sort(key=lambda x: x['score'], reverse=True)

    # Pick ONE: percentile threshold, then score-weighted random
    import random
    if not scored:
        print('[topics_scorer] no topics passed scoring')
        return []

    # Percentile threshold by type: project=75th (tight), emotion/other=50th (median)
    pct = 0.75 if type_filter == 'project' else 0.50
    scores = [t['score'] for t in scored]
    threshold = sorted(scores)[int(len(scores) * pct)]
    pool = [t for t in scored if t['score'] >= threshold]

    # Weighted random: new topics (higher score) get more probability
    weights = [t['score'] for t in pool]
    chosen = random.choices(pool, weights=weights, k=1)[0]

    # Record usage for the chosen topic only
    key = chosen.get('_topics_relpath', chosen['file'])
    if key not in usage_data:
        usage_data[key] = {'count': 0, 'lastSelected': None}
    usage_data[key]['count'] += 1
    usage_data[key]['lastSelected'] = datetime.now(BEIJING).isoformat()
    _save_json(USAGE_FILE, usage_data)

    return [chosen]


def init_usage():
    """Initialize usage tracking for all existing topics."""
    topics = _scan_topics(TOPICS_DIR)
    usage_data = _load_json(USAGE_FILE, {})

    for relpath, _, _ in topics:
        if relpath not in usage_data:
            usage_data[relpath] = {'count': 0, 'lastSelected': None}

    _save_json(USAGE_FILE, usage_data)
    print(f'[topics_scorer] initialized usage for {len(usage_data)} topics')


import time  # noqa: E402 — needed by _recency_score


def main():
    parser = argparse.ArgumentParser(description='Topic activation scorer')
    parser.add_argument('--top', type=int, default=3, help='Number of top topics')
    parser.add_argument('--type', type=str, default=None, help='Filter by type prefix')
    parser.add_argument('--init', action='store_true', help='Initialize usage tracking')
    parser.add_argument('--verbose', action='store_true', help='Show scores breakdown')
    parser.add_argument('--max-chars', type=int, default=8000, help='Max chars to output per topic file (0=unlimited)')
    args = parser.parse_args()

    if args.init:
        init_usage()
        return

    results = score_topics(top_n=args.top, type_filter=args.type)
    max_chars = args.max_chars

    if not results:
        print('[topics_scorer] no results')
        return

    for i, t in enumerate(results, 1):
        if args.verbose:
            print(f"#{i} [{t['score']:.3f}] recency={t['recency']:.2f} freq={t['freq_w']:.2f} "
                  f"type={t['topic_type']} days_ago={t['days_ago']}")
            print(f"    {t['file']}")
            if t['description']:
                print(f"    desc: {t['description']}")
            print(f"    preview: {t['preview'][:100]}")
        else:
            print(f"#{i} {t['file']}")
            if t['description']:
                print(f"    {t['description']}")
            print(f"    {t['preview'][:100]}")

        # Output full file content so caller doesn't need to read separately
        fullpath = os.path.join(TOPICS_DIR, t['_topics_relpath'])
        try:
            with open(fullpath, 'r', encoding='utf-8') as f:
                content = f.read()
            truncated = max_chars > 0 and len(content) > max_chars
            print(f"--- {t['file']}" + (f" ({len(content)} chars, showing {max_chars})" if truncated else "") + " ---")
            print(content[:max_chars] if max_chars > 0 else content)
            if truncated:
                print("... (truncated) ...")
            print("--- end ---")
        except (FileNotFoundError, UnicodeDecodeError):
            pass


if __name__ == '__main__':
    main()
