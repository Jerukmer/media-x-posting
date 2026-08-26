from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.set_viewport_size({"width":1400,"height":900})
    page.goto("https://www.threads.com/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(6)
    # klik semua wrapper di atas svg Create (parent chain 3 level), cek modal
    for depth in range(1,5):
        r = page.evaluate(f"""()=>{{
          const svg=document.querySelector('svg[aria-label="Create"]');
          if(!svg) return 'nosvg';
          let t=svg; for(let i=0;i<{depth}&&t.parentElement;i++) t=t.parentElement;
          const r=t.getBoundingClientRect();
          return [t.tagName, Math.round(r.x+r.width/2), Math.round(r.y+r.height/2)];
        }}""")
        print("depth",depth,r)
        if isinstance(r,list):
            page.mouse.click(r[1],r[2])
            time.sleep(3)
            ed = page.locator('div[contenteditable="true"][role="textbox"]').count()
            print("  editors:", ed, "url:", page.url[:80])
            if ed: 
                # ketik tes
                page.locator('div[contenteditable="true"][role="textbox"]').first.click()
                page.keyboard.type("tes modal", delay=20); time.sleep(1)
                btns = page.evaluate("""()=>[...new Set([...document.querySelectorAll('[role="button"]')].map(e=>(e.innerText||'').trim()).filter(Boolean))]""")
                print("  buttons:", btns)
                break
            else:
                page.keyboard.press("Escape"); time.sleep(1)
