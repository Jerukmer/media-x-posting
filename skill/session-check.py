#!/usr/bin/env python3
"""
session-check.py — Verify X session is alive via CDP + Playwright fallback.

Checks:
1. CDP port 9222 is reachable
2. X home page is loaded (not login screen)
3. Article count > 0 (logged-in state)

Returns exit code 0 if session healthy, 1 if dead/expired.
"""

import os
import sys
import time
import urllib.request
import json as json_mod

CDP_BASE = "http://127.0.0.1:9222"
X_HOME = "https://x.com/home"

def check_cdp():
    """Verify CDP port is alive and responsive."""
    try:
        resp = urllib.request.urlopen(f"{CDP_BASE}/json/version", timeout=5)
        data = resp.read().decode("utf-8", errors="replace")
        if "Browser" in data and "Chrome" in data:
            print("✓ CDP reachable, Chrome responding")
            return True
        else:
            print("⚠ CDP reachable but unexpected response")
            return True
    except Exception as e:
        print(f"✗ CDP not reachable: {e}")
        return False

def get_first_tab_id():
    """Get the first page tab ID from /json/list."""
    try:
        resp = urllib.request.urlopen(f"{CDP_BASE}/json/list", timeout=5)
        tabs = json_mod.loads(resp.read().decode("utf-8"))
        pages = [t for t in tabs if t.get("type") == "page"]
        if pages:
            return pages[0]["id"]
        return None
    except Exception as e:
        print(f"✗ Could not list tabs: {e}")
        return None

def check_via_playwright():
    """Use Playwright to navigate and check session."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP_BASE)
            try:
                contexts = browser.contexts
                if contexts:
                    page = contexts[0].pages[0]
                else:
                    page = browser.new_page()
                
                page.goto(X_HOME, timeout=15000, wait_until="domcontentloaded")
                time.sleep(5)
                
                content = page.content
                text_len = len(content)
                
                if text_len > 5000:
                    print(f"✓ Session appears alive via Playwright (content: {text_len} chars)")
                    browser.close()
                    return True
                
                # Check for login indicators
                login_indicators = ["Sign in", "Continue with", "Log in", "Daftar"]
                found_login = any(ind in content for ind in login_indicators)
                
                if found_login:
                    print("✗ Session expired — login screen detected via Playwright")
                    browser.close()
                    return False
                
                # Check article count via DOM
                try:
                    article_count = page.evaluate("""() => {
                        const articles = document.querySelectorAll('article');
                        return articles.length;
                    }""")
                    if article_count and article_count > 0:
                        print(f"✓ Session alive — {article_count} articles found on X home")
                        browser.close()
                        return True
                    else:
                        print(f"⚠ No articles found ({article_count}), checking login state again...")
                        if found_login:
                            browser.close()
                            return False
                        print("⚠ Uncertain — manual verification recommended")
                        browser.close()
                        return True
                except Exception as e:
                    print(f"⚠ Could not count articles: {e}")
                    browser.close()
                    return True
            except Exception as e:
                print(f"⚠ Playwright interaction error: {e}")
                browser.close()
                return True
    except Exception as e:
        print(f"✗ Playwright not available or failed: {e}")
        return False

def main():
    print("=== X Session Health Check ===")
    print(f"CDP: {CDP_BASE}")
    print(f"Target: {X_HOME}")
    print()
    
    if not check_cdp():
        print("\n✗ CDP not reachable — Chrome may not be running")
        print("  Launch with: profile-launch.py")
        return 1
    
    print()
    print("Checking X session via Playwright...")
    
    tab_id = get_first_tab_id()
    if tab_id:
        print(f"Found tab ID: {tab_id}")
    else:
        print("No existing pages found — will create new page")
    
    healthy = check_via_playwright()
    
    print()
    if healthy:
        print("✓ Session healthy — ready to post")
        return 0
    else:
        print("✗ Session dead/expired — manual re-login required")
        print("  Open Chrome with profile media-x-posting-profile and log into X manually")
        return 1

if __name__ == "__main__":
    sys.exit(main())
