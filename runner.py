#!/usr/bin/env python3
"""
runner.py — Orchestrator: fetch → filter → transform → pick → post → state.

Run 1x per jam (via cron/scheduled task). Posts at most ONE tweet per run.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sources import fetch_all
from pipeline import transform
import state
from post_executor import post_tweet

ACTIVE_HOURS = (6, 22)  # WIB window; outside = skip

def in_active_hours():
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone(timedelta(hours=7)))
    return ACTIVE_HOURS[0] <= now.hour < ACTIVE_HOURS[1]

def main():
    print(f"=== media-x-posting runner ===")
    
    if not in_active_hours():
        print(f"[runner] di luar jam aktif {ACTIVE_HOURS} — skip")
        return 0

    # 1. Fetch
    items = fetch_all()

    # 2. Filter: buang yang udah dilihat/diposting
    fresh = []
    for it in items:
        if not it["link"]:
            continue
        if state.is_posted(it["link"]) or state.is_seen(it["link"]):
            continue
        fresh.append(it)
        state.mark_seen(it["link"])
    print(f"[runner] fresh items setelah dedupe: {len(fresh)}")

    if not fresh:
        print("[runner] tidak ada konten baru — selesai tanpa post")
        return 0

    # 3. Transform
    tweets = transform(fresh)
    if not tweets:
        print("[runner] tidak ada yang layak jadi tweet")
        return 0

    # 4. Pick satu teratas (bisa dikembangkan: scoring by engagement/topic)
    chosen = tweets[0]
    print(f"[runner] POSTING: {chosen['tweet_text'][:100]}...")

    # 5. Post
    ok, msg = post_tweet(chosen["tweet_text"])
    if ok:
        state.mark_posted(
            chosen["item"]["link"], chosen["item"]["title"],
            chosen["tweet_text"], "single"
        )
        print(f"[runner] SUCCESS: {msg}")
        return 0
    else:
        print(f"[runner] FAILED: {msg}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
