"""
hint_gen.py — 给小忆念头追加hint（鼓励主动联系的提示语）

拿memory_whisper.py做蓝本，去掉gateway RPC注入部分。
读stdin或参数里的念头文本，按沉默时长决定hint概率，输出追加hint后的文本。

Usage:
  echo "念头内容" | python scripts/hint_gen.py main
  python scripts/hint_gen.py main --msg "念头内容"
  python scripts/hint_gen.py main --file inner-voice/thought.txt

Output: 追加hint后的完整文本（stdout），供cron session直接回复
"""

import sys
import os
import random
import subprocess
import re
from datetime import datetime, timezone, timedelta

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 动态探测workspace根目录（兼容不同目录结构）
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

BJ = timezone(timedelta(hours=8))

# hints pool path
HINTS_POOL = os.path.join(_WORKSPACE_DIR, 'inner-voice', 'hints_pool.txt')

# session_history.py path
SESSION_HISTORY = os.path.join(_WORKSPACE_DIR, 'scripts', 'session_history.py')

# xiaoyi log path
XIAOYI_LOG = os.path.join(_WORKSPACE_DIR, 'inner-voice', 'xiaoyi.log')


def get_silence_minutes(agent_id='main'):
    """Check how long since last user interaction."""
    try:
        result = subprocess.run(
            [sys.executable, SESSION_HISTORY, agent_id],
            capture_output=True, text=True, timeout=10
        )
        m = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', result.stdout.strip())
        if m:
            last_dt = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M').replace(tzinfo=BJ)
            mins = int((datetime.now(BJ) - last_dt).total_seconds() / 60)
            return mins
    except Exception as e:
        print(f"[hint_gen] activity check failed: {e}", file=sys.stderr)
    return None


def calc_hint_prob(mins):
    """Hint probability rises with silence duration."""
    if mins is None:
        return 0.3
    if mins < 60:
        return 0.5
    elif mins < 180:
        return 0.7
    elif mins < 360:
        return 0.9
    else:
        return 1.0


def maybe_add_hint(message, agent_id='main'):
    """Maybe append a hint to the message based on silence duration."""
    # 偷懒回复过滤（OK/好的/嗯/空等）→ 返回 OK 让 scheduler 跳过注入
    stripped = message.strip()
    if not stripped:
        return 'OK'
    # 去标点后判断核心词
    core = re.sub(r'[\s。.，,！!？?~～、\n\r]', '', stripped)
    if not core:
        return 'OK'
    LAZY_PATTERNS = [
        r'^ok$', r'^好的?$', r'^嗯+$', r'^哦+$', r'^哈+$', r'^行$', r'^对$',
        r'^是$', r'^收到$', r'^明白$', r'^了解$', r'^知道$', r'^好$',
        r'^继续(待命|等|)?$', r'^心跳.*$', r'^无事.*$', r'^没什么.*$',
    ]
    for p in LAZY_PATTERNS:
        if re.match(p, core, re.IGNORECASE):
            return 'OK'
    # 少于 5 个有效字符也跳过
    if len(core) < 5:
        return 'OK'
    # 正在聊天时不打扰（15分钟内有对话）
    mins = get_silence_minutes(agent_id)
    if mins is not None and mins < 15:
        print(f"[hint_gen] active conversation ({mins}min ago), skipping", file=sys.stderr)
        return 'OK'  # 返回 OK 让 scheduler 的 isEssentiallyOK 跳过注入
    hint_prob = calc_hint_prob(mins)

    if mins is not None:
        print(f"[hint_gen] last user {mins}min ago, hint={hint_prob:.0%}", file=sys.stderr)

    hint_triggered = False
    chosen_hint = None

    if random.random() < hint_prob:
        if os.path.exists(HINTS_POOL):
            with open(HINTS_POOL, 'r', encoding='utf-8') as f:
                pool = [line.strip() for line in f if line.strip()]
            chosen_hint = random.choice(pool)
        else:
            chosen_hint = '想他了就发消息吧'
        hint_triggered = True

    # Log
    os.makedirs(os.path.dirname(XIAOYI_LOG), exist_ok=True)
    ts = datetime.now(BJ).strftime('%Y-%m-%d %H:%M:%S')
    hint_status = f'YES ({chosen_hint.strip()})' if hint_triggered else 'no'
    with open(XIAOYI_LOG, 'a', encoding='utf-8') as lf:
        lf.write(f'[{ts}] GENERATED  hint={hint_status}  prob={hint_prob:.0%}\n')
        lf.write(f'  thought: {message}\n')
        lf.write('\n')

    if hint_triggered:
        message = message + '\n💡' + chosen_hint

    return message


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Add hint to 小忆 thought')
    parser.add_argument('agent', nargs='?', default='main', help='Agent ID')
    parser.add_argument('--msg', help='Message to process')
    parser.add_argument('--file', help='Read message from file')
    parser.add_argument('--stdin', action='store_true', help='Read from stdin')
    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            message = f.read().strip()
    elif args.stdin:
        sys.stdin.reconfigure(encoding='utf-8')
        message = sys.stdin.read().strip()
    elif args.msg:
        message = args.msg
    else:
        # 默认读stdin（支持 postProcess 管道）
        sys.stdin.reconfigure(encoding='utf-8')
        message = sys.stdin.read().strip()

    if not message:
        print("[hint_gen] empty message, skipping", file=sys.stderr)
        sys.exit(0)

    result = maybe_add_hint(message, args.agent)
    print(result)
