from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.goto("https://www.threads.com/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(6)
    print("URL:", page.url)
    body = page.evaluate("() => document.body ? document.body.innerText.slice(0,600) : ''")
    print(body)
    # jangan tutup tabnya dulu, biar keliatan state login
