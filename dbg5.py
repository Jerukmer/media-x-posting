from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.set_viewport_size({"width":1400,"height":900})
    page.goto("https://www.threads.com/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(6)
    page.locator('svg[aria-label="Create"]').first.click()
    time.sleep(3)
    print("URL:", page.url)
    ed = page.locator('div[contenteditable="true"][role="textbox"]')
    print("editors:", ed.count())
    if ed.count():
        ed.first.click(); time.sleep(0.5)
        page.keyboard.type("test posting otomatis via CDP - abis ini dihapus", delay=20)
        time.sleep(1)
        typed = page.evaluate("()=>{const e=document.querySelector('div[contenteditable=\'true\']');return e?e.innerText:''}")
        print("typed:", len(typed), "chars")
        # cari tombol Post
        btns = page.evaluate("""()=>{const o=[];document.querySelectorAll('[role="button"],button').forEach(el=>o.push((el.innerText||'').slice(0,20)));return [...new Set(o)]}""")
        print(btns)
