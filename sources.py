#!/usr/bin/env python3
"""
sources.py — Fetch news from RSS feeds (AI, affiliate/business, Indonesian politics).

All keyless RSS. Returns list of dicts: {source, title, link, summary, published}.
"""

import xml.etree.ElementTree as ET
import urllib.request
import re
from datetime import datetime, timezone

FEEDS = {
    # --- AI & Tech ---
    "ai_techcrunch": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "ai_venturebeat": "https://venturebeat.com/category/ai/feed/",
    "ai_hackernoon": "https://hackernoon.com/tagged/ai/feed",
    # --- Affiliate / Bisnis online ---
    "biz_techinasia": "https://www.techinasia.com/feed",
    "biz_entrep_indo": "https://www.liputan6.com/feed/rss/bisnis",
    # --- Politik Indonesia (feed aktif terverifikasi) ---
    "pol_antara": "https://www.antaranews.com/rss/politik",
    "pol_republika": "https://www.republika.co.id/rss/nasional/",
    "pol_cnbcindo": "https://www.cnbcindonesia.com/news/rss",
}

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def _clean(text):
    """Strip HTML tags + collapse whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def fetch_feed(name, url, timeout=15):
    """Fetch one RSS feed, return list of items."""
    items = []
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        root = ET.fromstring(data)
        # RSS 2.0
        for item in root.iter("item"):
            title = _clean(item.findtext("title", ""))
            link = item.findtext("link", "") or ""
            desc = _clean(item.findtext("description", ""))
            pub = item.findtext("pubDate", "")
            if title and link:
                items.append({
                    "source": name,
                    "title": title[:300],
                    "link": link.strip(),
                    "summary": desc[:500],
                    "published": pub,
                })
        # Atom fallback
        if not items:
            ns = {"a": "http://www.w3.org/2005/Atom"}
            for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
                title = _clean(entry.findtext("a:title", "", ns))
                link_el = entry.find("a:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
                summary = _clean(entry.findtext("a:summary", "", ns))
                if title and link:
                    items.append({
                        "source": name,
                        "title": title[:300],
                        "link": link.strip(),
                        "summary": summary[:500],
                        "published": "",
                    })
    except Exception as e:
        print(f"[sources] {name}: FAILED ({e})")
    return items

def fetch_all():
    """Fetch all feeds. Returns combined item list."""
    all_items = []
    for name, url in FEEDS.items():
        items = fetch_feed(name, url)
        print(f"[sources] {name}: {len(items)} items")
        all_items.extend(items)
    print(f"[sources] TOTAL: {len(all_items)} raw items")
    return all_items

if __name__ == "__main__":
    items = fetch_all()
    for it in items[:3]:
        print(f"\n--- {it['source']} ---\n{it['title']}\n{it['link']}")
