#!/usr/bin/env python3
"""
heartbeat_check.py - 心跳检测层（no_agent模式，零token）

检查距上次飞书聊天的时间，决定是否需要主动联系。
- stdout非空 = 触发主动联系agent
- stdout为空 = 静默，不触发

规则：
  - 距上次聊天超过4小时 → 触发（白天 8:00-23:00）
  - 距上次聊天超过8小时 → 触发（夜间 23:00-8:00，减频率）
  - 不在时间窗口内 → 静默

用法：
  python3 heartbeat_check.py

配合cron使用：
  1. Layer 1: no_agent=True, script="heartbeat_check.py", schedule="every 30m", deliver="local"
  2. Layer 2: context_from="<layer1_job_id>", schedule="0 * * * *", deliver="feishu:<chat_id>"
"""

import sqlite3
import os
import sys
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
DB_PATH = os.path.expanduser("~/.hermes/state.db")

# 时间阈值（小时）
DAY_THRESHOLD = 4      # 白天：4小时没聊就触发
NIGHT_THRESHOLD = 8    # 夜间：8小时没聊才触发

# 白天时间窗口
DAY_START = 8    # 早上8点
DAY_END = 23     # 晚上11点


def get_last_chat_time():
    """从state.db查最后一次飞书session的非cron对话时间"""
    if not os.path.exists(DB_PATH):
        return None

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT ended_at FROM sessions
        WHERE source = 'feishu'
        AND ended_at IS NOT NULL
        ORDER BY ended_at DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()

    if row and row[0]:
        return datetime.fromtimestamp(row[0], tz=CST)
    return None


def should_trigger(last_chat, now):
    """判断是否需要触发，返回触发消息或空字符串"""
    hours_since = (now - last_chat).total_seconds() / 3600
    hour = now.hour
    is_daytime = DAY_START <= hour < DAY_END

    if is_daytime:
        if hours_since >= DAY_THRESHOLD:
            return (
                f"距上次聊天已{hours_since:.1f}小时（白天时段）。"
                f"主动找翀哥打个招呼吧，自然随意，可以说早安/聊聊天气/问问他忙不忙。"
            )
    else:
        if hours_since >= NIGHT_THRESHOLD:
            return (
                f"距上次聊天已{hours_since:.1f}小时（夜间时段）。"
                f"如果还在晚上可以问一句还没睡呀，如果是早上就说早安。"
            )

    return ""


def main():
    now = datetime.now(CST)
    last_chat = get_last_chat_time()

    if last_chat is None:
        return

    trigger_msg = should_trigger(last_chat, now)
    if trigger_msg:
        print(trigger_msg)


if __name__ == "__main__":
    main()
