from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.set_viewport_size({"width":1400,"height":900})
    page.goto("https://www.threads.com/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(6)
    # elementFromPoint di posisi tombol Create — siapa yg intercept?
    r = page.evaluate("""()=>{
      const svg=document.querySelector('svg[aria-label="Create"]');
      const rc=svg.getBoundingClientRect();
      const x=rc.x+rc.width/2, y=rc.y+rc.height/2;
      svg.dispatchEvent(new MouseEvent('mousedown',{bubbles:true}));
      svg.dispatchEvent(new MouseEvent('mouseup',{bubbles:true}));
      svg.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
      return [x,y];
    }""")
    print(r)
    time.sleep(4)
    ed = page.locator('div[contenteditable="true"]').count()
    print("editors(contenteditable any):", ed)
    # cek dialog/modal
    dlg = page.locator('div[role="dialog"]').count()
    print("dialogs:", dlg)
    body=page.evaluate("()=>document.body.innerText.slice(0,200)")
    print(body)
