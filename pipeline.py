#!/usr/bin/env python3
"""
pipeline.py — Transform raw news items into tweet-ready content.

Tone: varied (critical, analytical, straight, provocative-but-smart).
Not locked to Gen Z. Indonesian for Indo sources, English allowed for AI news.
Content types: single tweet (v1). Thread/quote/retweet later.
"""

import re
import random

# Tone openers — dipakai bervariasi, kadang tanpa opener sama sekali
TONES = [
    "",  # straight, no framing
    "Menarik. ",
    "Ini worth dicermati: ",
    "Fakta baru: ",
    "Hmm. ",
    "Catat ini. ",
    "Bukan isu kecil: ",
]

CLOSERS_ID = [
    "",
    " Gimana pandangan lo?",
    " Worth diwatch.",
    " Ini sinyal apa?",
    " Kita lihat ke depan.",
    " Jangan anggap remeh.",
]

def _pick(seq):
    return random.choice(seq)

def _trim_to(text, limit=270):
    """Trim to N chars at word boundary."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    # potong di spasi terakhir
    if " " in cut:
        cut = cut[:cut.rfind(" ")]
    return cut.rstrip(" ,;:") + "…"

def _strip_source_noise(title):
    """Remove trailing source names like ' - Detik', ' | Kompas'."""
    return re.sub(r"\s*[-|]\s*(Detik|Kompas|Tempo|Liputan6?|CNBC|TechCrunch|VentureBeat).*", "", title, flags=re.I)

def make_single_tweet(item):
    """Turn a news item into one single tweet text. Returns str or None if not suitable."""
    title = _strip_source_noise(item.get("title", "")).strip()
    summary = item.get("summary", "").strip()

    if len(title) < 25:
        return None  # too short to be meaningful

    # Base content: judul + sedikit konteks dari summary
    base = title
    if summary and len(summary) > 60:
        # ambil kalimat pertama summary yang beda dr judul
        first_sent = re.split(r"(?<=[.!?])\s+", summary)[0]
        if len(first_sent) > 30 and first_sent.lower() not in base.lower():
            base = f"{title}. {first_sent}"

    tone = _pick(TONES)
    closer = _pick(CLOSERS_ID)
    tweet = f"{tone}{base}{closer}"

    return _trim_to(tweet)

def transform(items, use_llm=True):
    """Given raw items, return list of {item, tweet_text, method} ready to post.
    use_llm: coba LLM paraphrase dulu; kalau gagal fallback ke template lokal."""
    from paraphraser import llm_paraphrase
    results = []
    llm_ok = 0
    for it in items:
        tweet = None
        method = "template"
        if use_llm:
            tweet = llm_paraphrase(it.get("title", ""), it.get("summary", ""), it.get("source", ""))
            if tweet:
                method = "llm"
                llm_ok += 1
        if not tweet:
            tweet = make_single_tweet(it)
        if tweet:
            results.append({"item": it, "tweet_text": tweet, "method": method})
    print(f"[pipeline] transformed {len(results)}/{len(items)} items (LLM: {llm_ok}, template: {len(results)-llm_ok})")
    return results

if __name__ == "__main__":
    from sources import fetch_all
    items = fetch_all()
    tweets = transform(items)
    for t in tweets[:5]:
        print("\n---")
        print(t["item"]["source"], "|", t["item"]["link"][:80])
        print(t["tweet_text"])
