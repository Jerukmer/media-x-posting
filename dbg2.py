from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.goto("https://www.threads.com/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(6)
    labels = page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('[role="button"],button').forEach(el=>{
        out.push((el.getAttribute('aria-label')||el.innerText||'').slice(0,60));
      });
      return [...new Set(out)].slice(0,40);
    }""")
    for l in labels: print(repr(l))
    page.close()
