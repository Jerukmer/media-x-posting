#!/usr/bin/env python3
"""
screen_and_comment.py — Screen X for free-API-key shares, then post critical commentary.

Flow:
1. Run screen_freekeys (scrape search results, redact keys)
2. For each finding, generate commentary via llm_client
3. Post commentary tweet (NOT the key — educational/critical only)
4. Dedupe by user+keytype so we don't spam same account
5. Report to Telegram

Safety: never post raw keys. Never retweet (avoid amplifying scams).
"""

import sys
import os
import json
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from screen_freekeys import run_screen
from commentary import generate
import state
from post_executor import post_tweet
from notifier import report_post
from llm_client import make_commentary

def already_commented(user, keytype):
    """Dedupe: jangan komentari user+keytype yg sama 2x."""
    key = f"commentary:{user}:{keytype}"
    return state.is_seen(key)

def mark_commented(user, keytype):
    state.mark_seen(f"commentary:{user}:{keytype}")

def main():
    print("=== screen_and_comment ===")
    raw = run_screen()
    try:
        data = json.loads(raw)
    except Exception:
        print("[sac] screen returned non-JSON, skip")
        return 1

    if data.get("error") == "SESSION_EXPIRED":
        print("[sac] SESSION EXPIRED — stop, laporkan")
        report_post(False, "(screening) session expired", "", "screen", "SESSION_EXPIRED")
        return 1

    findings = data.get("findings", [])
    if not findings:
        print("[sac] tidak ada temuan API key gratis")
        return 0

    posted = 0
    for f in findings[:3]:  # max 3 commentary per run (anti-spam)
        user = f.get("user", "unknown")
        keytypes = sorted(set(k[0] for k in f.get("keys", [])))
        if not keytypes:
            continue
        kt = keytypes[0]
        if already_commented(user, kt):
            print(f"[sac] skip {user}/{kt} (sudah pernah)")
            continue

        commentary = generate(f)
        if not commentary:
            continue

        ok, msg = post_tweet(commentary)
        report_post(ok, commentary, f.get("snippet", "")[:80], "commentary", msg)
        mark_commented(user, kt)
        if ok:
            posted += 1
            time.sleep(3)  # jeda antar post
        else:
            print(f"[sac] post gagal: {msg}")
            break

    print(f"[sac] selesai, {posted} commentary terpost")
    return 0

if __name__ == "__main__":
    sys.exit(main())
