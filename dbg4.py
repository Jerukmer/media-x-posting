from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.set_viewport_size({"width":1400,"height":900})
    page.goto("https://www.threads.com/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(6)
    print("URL:", page.url)
    # semua svg dengan aria-label di seluruh dokumen
    res = page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('svg[aria-label], [aria-label]').forEach(el=>{
        const r=el.getBoundingClientRect();
        out.push(el.tagName+'|'+el.getAttribute('aria-label')+'|x='+Math.round(r.x)+',y='+Math.round(r.y));
      });
      return out.slice(0,40);
    }""")
    for n in res: print(n)
