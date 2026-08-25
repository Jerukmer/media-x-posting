#!/usr/bin/env python3
"""
watchdog_cdp.py — Self-heal watchdog for media-x-posting Chrome profile.

Checks every 10 min: is CDP port 9222 alive AND X session still logged in?
- CDP dead → relaunch via scheduled task "MediaXChromeLaunch" (user session)
- Session expired → report to Telegram, do NOT auto-login
Stdlib only. Designed to run as a background loop or scheduled task.
"""

import time
import subprocess
import urllib.request

CDP = "http://127.0.0.1:9222"
CHECK_INTERVAL = 600  # 10 min
TASK_NAME = "MediaXChromeLaunch"

def cdp_alive():
    try:
        with urllib.request.urlopen(f"{CDP}/json/version", timeout=5) as r:
            return b"Browser" in r.read()
    except Exception:
        return False

def session_alive():
    """True kalau x.com/home masih logged in."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP)
            page = browser.contexts[0].pages[0]
            page.goto("https://x.com/home", timeout=20000, wait_until="domcontentloaded")
            time.sleep(3)
            body = page.evaluate("() => document.body ? document.body.innerText : ''")
            browser.close()
            return "For you" in body or "Following" in body
    except Exception as e:
        print(f"[watchdog] session check error: {e}")
        return False

def relaunch_chrome():
    print("[watchdog] relaunching Chrome via scheduled task...")
    subprocess.run(["schtasks", "/Run", "/TN", TASK_NAME], capture_output=True)

def notify(text):
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from notifier import send_report
        send_report(f"[watchdog] {text}")
    except Exception as e:
        print(f"[watchdog] notify failed: {e}")

def check_once():
    if not cdp_alive():
        print("[watchdog] CDP DEAD — relaunch")
        relaunch_chrome()
        time.sleep(8)
        if cdp_alive():
            notify("Chrome mati, udah direlaunch otomatis. CDP hidup lagi.")
            return
        notify("Chrome mati dan relaunch GAGAL — perlu cek manual.")
        return

    # CDP hidup; cek session tiap cycle (murah: 1x goto)
    if not session_alive():
        # double-check sekali lagi sebelum alarm
        time.sleep(5)
        if not session_alive():
            notify("Session X @txtguru EXPIRED — perlu login manual di Chrome profile media-x-posting-profile.")
        else:
            print("[watchdog] false alarm, session ok")

if __name__ == "__main__":
    print("[watchdog] started, interval 600s")
    while True:
        try:
            check_once()
        except Exception as e:
            print(f"[watchdog] loop error: {e}")
        time.sleep(CHECK_INTERVAL)
