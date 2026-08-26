from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.goto("https://www.threads.com/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(6)
    # cari elemen klikable yg mengandung 'thread'/'post' di aria/label
    info = page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('div[role="button"],a,svg,div[data-testid]').forEach(el=>{
        const lab=(el.getAttribute('aria-label')||'')+'|'+(el.getAttribute('data-testid')||'');
        if(/thread|post|buat|utas/i.test(lab)) out.push(el.tagName+' '+lab.slice(0,80));
      });
      return out.slice(0,30);
    }""")
    for i in info: print(i)
    # juga cek URL intent approach
    page.goto("https://www.threads.com/intent/post?text=hello%20test", timeout=30000, wait_until="domcontentloaded")
    time.sleep(5)
    print("---INTENT URL:", page.url)
    ed = page.locator('div[contenteditable="true"][role="textbox"]').count()
    print("editors:", ed)
    body = page.evaluate("() => document.body.innerText.slice(0,400)")
    print(body)
    page.close()
