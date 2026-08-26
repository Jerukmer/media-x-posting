from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = ctx.new_page()
    page.set_viewport_size({"width":1400,"height":900})
    page.goto("https://www.threads.com/", timeout=30000, wait_until="domcontentloaded")
    time.sleep(6)
    # klik parent div yang punya aria-label Create (bukan svg-nya) via JS
    ok = page.evaluate("""()=>{
      const els=[...document.querySelectorAll('[aria-label="Create"]')];
      for(const el of els){
        let t=el;
        while(t && t.getAttribute && !t.getAttribute('role')) t=t.parentElement;
        if(t){ (t.getAttribute('role')==='button'?t:el).dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}
      }
      // fallback: click svg langsung
      const svg=document.querySelector('svg[aria-label="Create"]');
      if(svg){svg.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));return 'svg';}
      return false;
    }""")
    print("clicked:", ok)
    time.sleep(4)
    print("URL:", page.url)
    ed = page.locator('div[contenteditable="true"][role="textbox"]')
    print("editors:", ed.count())
    body = page.evaluate("()=>document.body.innerText.slice(0,300)")
    print(body)
