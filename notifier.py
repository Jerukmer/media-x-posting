#!/usr/bin/env python3
"""
notifier.py — Send post report to Boss's Telegram thread via direct Bot API.
Token from Hermes .env. Stdlib only.
"""

import json
import os
import urllib.request
import urllib.parse

ENV_PATH = r"C:\Users\EMIS-07\AppData\Local\hermes\.env"
CHAT_ID = "7084085287"
THREAD_ID = "28465"

def _get_token():
    for line in open(ENV_PATH, encoding="utf-8"):
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            return line.strip().split("=", 1)[1]
    return None

def send_report(text):
    """Send message to thread. Returns bool."""
    token = _get_token()
    if not token:
        print("[notifier] no TELEGRAM_BOT_TOKEN in .env")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "message_thread_id": THREAD_ID,
        "text": text,
        "parse_mode": "",
        "disable_web_page_preview": "true",
    }).encode()
    try:
        with urllib.request.urlopen(url, data=payload, timeout=15) as resp:
            data = json.loads(resp.read())
        return data.get("ok", False)
    except Exception as e:
        print(f"[notifier] FAILED: {e}")
        return False

def report_post(ok, tweet_text, source_link, method, msg):
    """Format + send a posting report."""
    status = "POSTED" if ok else "GAGAL"
    icon = "[OK]" if ok else "[X]"
    text = (
        f"{icon} media-x-posting | {status}\n"
        f"Metode: {method}\n\n"
        f"{tweet_text[:250]}\n\n"
        f"Sumber: {source_link[:80]}\n"
        f"Note: {msg}"
    )
    # Telegram caption max 4096; aman
    ok_sent = send_report(text)
    print(f"[notifier] report sent: {ok_sent}")
    return ok_sent

if __name__ == "__main__":
    print(send_report("Test report dari media-x-posting notifier"))
