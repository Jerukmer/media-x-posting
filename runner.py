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

    # 2. Filter: buang yang udah diposting. mark_seen DILAKUKAN SETELAH post sukses
    #    (kalau gagal post, item masih boleh dicoba cycle berikutnya).
    fresh = []
    for it in items:
        if not it["link"]:
            continue
        if state.is_posted(it["link"]) or state.is_seen(it["link"]):
            continue
        fresh.append(it)
    print(f"[runner] fresh items setelah dedupe: {len(fresh)}")

    if not fresh:
        print("[runner] tidak ada konten baru — selesai tanpa post")
        return 0

    # 3. Transform — LLM hanya untuk kandidat teratas (hemat quota + cepat).
    #    Strategi: template dulu buat semua, LLM paraphrase khusus yang akan dipost.
    tweets = transform(fresh, use_llm=False)
    if not tweets:
        print("[runner] tidak ada yang layak jadi tweet")
        return 0

    # 4. Pick satu teratas, lalu LLM-paraphrase tweet final itu
    chosen = tweets[0]
    from paraphraser import llm_paraphrase
    llm_text = llm_paraphrase(chosen["item"].get("title",""), chosen["item"].get("summary",""))
    if llm_text:
        print(f"[runner] LLM rewrite: {llm_text[:80]}...")
        chosen["tweet_text"] = llm_text
        chosen["method"] = "llm"
    print(f"[runner] POSTING ({chosen.get('method','?')}): {chosen['tweet_text'][:100]}...")

    # 5. Post
    ok, msg = post_tweet(chosen["tweet_text"])
    if ok:
        state.mark_posted(
            chosen["item"]["link"], chosen["item"]["title"],
            chosen["tweet_text"], "single"
        )
        print(f"[runner] SUCCESS: {msg}")
    else:
        print(f"[runner] FAILED: {msg}")

    # 6. Report ke Telegram Boss (selalu, sukses atau gagal)
    try:
        from notifier import report_post
        report_post(ok, chosen["tweet_text"], chosen["item"].get("link",""),
                    chosen.get("method","template"), msg)
    except Exception as e:
        print(f"[runner] notifier error (abaikan): {e}")

    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
