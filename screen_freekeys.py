#!/usr/bin/env python3
"""
screen_freekeys.py — Screen X timeline for tweets sharing FREE API keys.

Approach (no X API, careful browser scraping via CDP):
- X search is BLANK in headless mode (confirmed: 0 articles). So we scan the
  HOME timeline (For you + Following tabs) instead — that renders fine.
- Detect tweets containing key-sharing patterns (sk-, gsk_, AIza, Bearer, etc.)
- REDACT all keys before storing/displaying (security: never leak secrets)
- Output: structured findings (who, what service, redacted sample) for commentary

Safety: read-only, no posting, no login loops. Rate-limit friendly.
"""

import re
import json
import time
from datetime import datetime, timezone, timedelta

# Pattern deteksi key (di-redact nanti)
KEY_PATTERNS = [
    (r"sk-[A-Za-z0-9]{20,}", "openai-sk"),
    (r"gsk_[A-Za-z0-9]{20,}", "groq-gsk"),
    (r"AIza[A-Za-z0-9_\-]{35,}", "google-aiza"),
    (r"xai-[A-Za-z0-9]{20,}", "xai-xai"),
    (r"Bearer\s+[A-Za-z0-9_\-\.]{20,}", "bearer"),
    (r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}", "jwt"),
    (r"sk-ant-[A-Za-z0-9_\-]{20,}", "anthropic-sk"),
    (r"[a-f0-9]{32,64}", "hex-generic"),
]

# Kata kunci pembagi key gratis
SHARE_KEYWORDS = [
    r"api[_\s-]?key", r"free\s+(api|openai|gpt|key|groq|gemini)",
    r"gratis\s+(api|key|openai)", r"bagi\s+(api|key)", r"share\s+(api|key)",
    r"\$\d+.*(api|key|credit)", r"1000.*(api|key|credit)", r"credits.*free",
]

def _redact(match_text):
    """Redact: keep prefix + last 4 chars only."""
    if len(match_text) <= 8:
        return "[REDACTED]"
    return match_text[:6] + "…" + match_text[-4:]

def find_keys(text):
    """Return list of (type, redacted) found in text."""
    found = []
    for pat, label in KEY_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            raw = m.group(0)
            found.append((label, _redact(raw)))
    return found

def _has_share_intent(text):
    return any(re.search(p, text, re.IGNORECASE) for p in SHARE_KEYWORDS)

def _wib_now():
    return datetime.now(timezone(timedelta(hours=7)))

def scan_timeline(page, max_scrolls=8):
    """Scroll home timeline, return findings list."""
    findings = []
    seen_users = set()
    page.goto("https://x.com/home", timeout=25000, wait_until="domcontentloaded")
    time.sleep(6)
    for _ in range(max_scrolls):
        arts = page.locator("article").all()
        for art in arts:
            try:
                txt = art.inner_text()
            except Exception:
                continue
            if not _has_share_intent(txt):
                continue
            keys = find_keys(txt)
            if not keys:
                continue
            m = re.search(r"@([A-Za-z0-9_]+)", txt)
            user = "@" + m.group(1) if m else "unknown"
            if user in seen_users:
                continue
            seen_users.add(user)
            findings.append({
                "user": user,
                "keys": keys,
                "snippet": txt[:200].replace("\n", " "),
                "scanned_at": _wib_now().isoformat(),
            })
        page.mouse.wheel(0, 1500)
        time.sleep(2.5)
    return findings

def run_screen():
    """Run full screening via CDP Chrome. Returns JSON string."""
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            page = browser.contexts[0].pages[0]
            body = page.evaluate("() => document.body ? document.body.innerText : ''")
            if "For you" not in body and "Following" not in body:
                return json.dumps({"error": "SESSION_EXPIRED", "findings": []}, indent=2)
            print("[screen] scanning timeline (For you)...")
            findings = scan_timeline(page)
            browser.close()
        return json.dumps({"count": len(findings), "findings": findings}, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e), "findings": []}, indent=2)

if __name__ == "__main__":
    print(run_screen())
