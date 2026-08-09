from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    page=b.new_page(viewport={'width':1440,'height':900})
    page.goto('http://127.0.0.1:4321/index.html',wait_until='networkidle')
    page.evaluate("""() => {let e=document.querySelector('#ce-remove'), r=e.getBoundingClientRect(); window.scrollTo(0, r.top + scrollY + r.height/2 - 850)}""")
    page.wait_for_timeout(100)
    print(page.evaluate("""() => {let e=document.querySelector('#ce-remove'),r=e.getBoundingClientRect(),a=document.querySelector('.appbar').getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y);return {scrollY,docH:document.documentElement.scrollHeight,remove:{x:r.x,y:r.y,right:r.right,bottom:r.bottom},appbar:{x:a.x,y:a.y,right:a.right,bottom:a.bottom},point:{x,y,hit:h&&h.id,tag:h&&h.tagName,text:(h&&h.textContent||'').trim()}}}"""))
    b.close()
