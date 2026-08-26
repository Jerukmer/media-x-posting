#!/usr/bin/env python3
"""
threads_post.py — Post ONE thread via CDP Chrome port 9222 (threads.com).

Safety rules (same as post_executor.py):
- Pre-check session alive before composing; abort if dead (no login loops)
- Input via keyboard.type (React-safe), validate before submit
- Verify composer cleared after submit
- On failure: log + exit non-zero. NEVER loop retries.
"""

import sys, time, os

CDP_BASE = "http://127.0.0.1:9222"
COMPOSE_URL = "https://www.threads.com/intent/post?text="

def _open_composer(page):
    """Buka composer Threads via tombol New thread di sidebar (paling stabil)."""
    page.goto("https://www.threads.com/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(4)
    btn = page.locator('div[data-testid="app-top-bar"] svg').first
    # fallback umum: aria-label New thread / Post
    for sel in ['div[aria-label="New thread"]', 'div[aria-label="Buat utas"]',
                'svg[aria-label="New thread"]', '[role="button"]:has-text("New thread")']:
        loc = page.locator(sel).first
        try:
            loc.wait_for(state="visible", timeout=4000)
            loc.click(timeout=5000)
            time.sleep(2)
            return True
        except Exception:
            continue
    return False

def post_thread(text):
    if not text or len(text.strip()) < 5:
        return False, "text kosong/terlalu pendek"
    if len(text) > 490:
        return False, f"text terlalu panjang ({len(text)} chars, max 490)"
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "playwright tidak tersedia"

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_BASE)
        try:
            ctx = browser.contexts[0]
            page = ctx.new_page()
            page.set_viewport_size({"width": 1280, "height": 900})

            body = page.evaluate("() => document.body ? document.body.innerText : ''")
            if "Log in" in body and "Home" not in body:
                return False, "SESSION EXPIRED — login manual dulu"

            if not _open_composer(page):
                page.close()
                return False, "tombol New thread gak ketemu"

            editor = page.locator('div[contenteditable="true"][role="textbox"]').first
            try:
                editor.click(timeout=8000)
            except Exception:
                page.close()
                return False, "editor composer gak muncul"
            time.sleep(0.5)
            page.keyboard.type(text, delay=20)
            time.sleep(1)

            typed = page.evaluate(
                "() => { const e=document.querySelector('div[contenteditable=\'true\'][role=\'textbox\']');"
                " return e ? e.innerText : '' }")
            if len(typed.strip()) < max(5, len(text) // 2):
                page.close()
                return False, f"text gak masuk editor (hanya {len(typed)} chars)"

            send = page.locator('div[role="button"]:has-text("Post")').last
            send.wait_for(state="attached", timeout=5000)
            for _ in range(12):
                try:
                    if send.is_enabled():
                        break
                except Exception:
                    pass
                time.sleep(0.5)
            try:
                send.click(timeout=5000)
            except Exception:
                page.evaluate("(el)=>el.click()", send.element_handle())
            time.sleep(4)

            gone = page.locator('div[contenteditable="true"][role="textbox"]').count() == 0
            page.close()
            if gone:
                return True, "POSTED OK"
            return False, "submit diklik tapi konfirmasi tidak terdeteksi — cek manual"
        except Exception as e:
            try:
                page.close()
            except Exception:
                pass
            return False, f"EXCEPTION: {e}"
        finally:
            browser.close()

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else open("draft.txt", encoding="utf-8").read().strip()
    ok, msg = post_thread(text)
    print(("OK: " if ok else "FAIL: ") + msg)
    sys.exit(0 if ok else 1)
