#!/usr/bin/env python3
"""
post_executor.py — Post ONE tweet via CDP Chrome (port 9222), carefully.

Safety rules baked in:
- Pre-check session alive BEFORE composing; abort if dead (no retry spam)
- Compose via clipboard paste (React-safe), validate text length before submit
- Verify success by checking composer cleared / toast appears
- On any failure: log + exit non-zero (caller decides next step)
- NEVER loop retries inside this script
"""

import sys
import time
import os

CDP_BASE = "http://127.0.0.1:9222"
COMPOSE_URL = "https://x.com/compose/post"

def post_tweet(text):
    """Post one tweet. Returns (success: bool, message: str)."""
    if not text or len(text.strip()) < 5:
        return False, "text kosong/terlalu pendek"
    if len(text) > 280:
        return False, f"text terlalu panjang ({len(text)} chars)"

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "playwright tidak tersedia"

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_BASE)
        try:
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            # --- PRE-CHECK: session alive ---
            # Guard: tutup modal nyangkut dulu (Escape), baru cek home
            try:
                page.keyboard.press("Escape")
                time.sleep(1)
            except Exception:
                pass
            if "/compose" in page.url:
                page.goto("https://x.com/home", timeout=20000, wait_until="domcontentloaded")
                time.sleep(3)
            else:
                page.goto("https://x.com/home", timeout=20000, wait_until="domcontentloaded")
                time.sleep(3)
            body = page.evaluate("() => document.body ? document.body.innerText : ''")
            if any(x in body for x in ["Continue with", "Email or username"]) and "For you" not in body:
                return False, "SESSION EXPIRED — login manual dulu"

            # --- OPEN COMPOSE MODAL ---
            # PENTING: SELALU klik Post button dari home. JANGAN goto /compose/post
            # — itu bikin modal dobel (mask nyangkut, 2 composer) dan wait_for race.
            post_btn = page.locator('[data-testid="SideNav_NewTweet_Button"]').first
            clicked = False
            for attempt in range(3):
                try:
                    post_btn.wait_for(state="visible", timeout=8000)
                    post_btn.click(timeout=5000)
                    clicked = True
                    break
                except Exception:
                    # button belum ada → pastikan di home + reload ringan
                    page.goto("https://x.com/home", timeout=20000, wait_until="domcontentloaded")
                    time.sleep(4)
            if not clicked:
                return False, "Post button tidak bisa diklik setelah 3 attempt"
            time.sleep(2)

            composer = page.locator('[data-testid="tweetTextarea_0"]').first
            try:
                composer.click(timeout=8000)
            except Exception:
                return False, "composer gak muncul setelah klik Post (modal issue)"

            # --- INPUT TEXT via keyboard.type (React-safe, proven) ---
            # NOTE: clipboard paste GAGAL dari Hermes SYSTEM context (Set-Clipboard
            # beda session). keyboard.type per-char delay 20ms = reliable.
            composer.click()
            time.sleep(0.5)
            page.keyboard.type(text, delay=20)
            time.sleep(1)

            # Validasi teks masuk
            typed = page.evaluate(
                "() => document.querySelector('[data-testid=\"tweetTextarea_0\"]')?.innerText || ''"
            )
            if len(typed.strip()) < max(5, len(text) // 2):
                return False, f"text gak masuk composer (hanya {len(typed)} chars)"

            # --- SUBMIT ---
            send = page.locator('[data-testid="tweetButton"]').last
            send.wait_for(state="attached", timeout=5000)
            for _ in range(12):
                if send.is_enabled():
                    break
                time.sleep(0.5)
            if not send.is_enabled():
                return False, "tombol Post tetap disabled — X mungkin nolak"
            send.click()
            time.sleep(3)

            # --- VERIFY: composer hilang / toast sukses ---
            after_body = page.evaluate("() => document.body.innerText")
            composer_gone = page.locator('[data-testid="tweetTextarea_0"]').count() == 0
            toast_sent = any(x in after_body for x in ["Your post was sent", "post was sent", "posted"])
            if composer_gone or toast_sent:
                return True, "POSTED OK"
            return False, "submit diklik tapi tidak ada konfirmasi — cek manual"

        except Exception as e:
            return False, f"EXCEPTION: {e}"
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # baca dari file
        txt_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "draft.txt")
        if os.path.exists(txt_file):
            text = open(txt_file, encoding="utf-8").read().strip()
        else:
            print("Usage: post_executor.py \"text\" atau taruh draft.txt")
            sys.exit(2)
    else:
        text = sys.argv[1]

    ok, msg = post_tweet(text)
    print(("OK: " if ok else "FAIL: ") + msg)
    sys.exit(0 if ok else 1)
