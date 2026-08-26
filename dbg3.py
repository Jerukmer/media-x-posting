from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.goto("https://www.threads.com/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(6)
    # sidebar kiri: cari svg pertama di nav + semua elemen dengan aria di nav
    nav = page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('nav div[role="button"], nav a, header div, div[data-testid]').forEach(el=>{
        out.push(el.tagName+'|'+(el.getAttribute('aria-label')||'')+'|'+(el.getAttribute('data-testid')||'')+'|'+(el.innerText||'').slice(0,30));
      });
      return out.slice(0,40);
    }""")
    for n in nav: print(repr(n))
