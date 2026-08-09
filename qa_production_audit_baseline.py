import json
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:4321/index.html'

def rect(page, selector):
    return page.locator(selector).evaluate("e => { const r=e.getBoundingClientRect(); const s=getComputedStyle(e); return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom,display:s.display,visibility:s.visibility,opacity:s.opacity}; }")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    results = {}
    for width in [1024, 1280, 1440, 1600]:
        page = browser.new_page(viewport={"width": width, "height": 900})
        errors=[]
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE, wait_until='networkidle')
        page.locator('#ce-remove').scroll_into_view_if_needed()
        page.wait_for_timeout(150)
        vals = page.evaluate("""() => {
          const qs = s => document.querySelector(s);
          const out = {};
          for (const s of ['#concept','#ce-remove','#ce-undo','.appbar','.appbar__btn']) {
            const e=qs(s); if (!e) continue; const r=e.getBoundingClientRect(); const cs=getComputedStyle(e);
            out[s]={x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height,display:cs.display,visibility:cs.visibility,opacity:cs.opacity};
          }
          for (const s of ['#ce-remove','#ce-undo']) {
            const e=qs(s), r=e.getBoundingClientRect();
            const x=Math.max(0,Math.min(innerWidth-1,r.left+r.width/2)); const y=Math.max(0,Math.min(innerHeight-1,r.top+r.height/2));
            const hit=document.elementFromPoint(x,y);
            out[s+'_hit']={x,y,tag:hit&&hit.tagName,id:hit&&hit.id,cls:hit&&hit.className,text:(hit&&hit.textContent||'').trim().slice(0,80),within:!!(hit&&e.contains(hit))};
          }
          return out;
        }""")
        results[str(width)]={'values':vals,'errors':errors}
        page.close()
    for width in [320, 360, 430]:
        page=browser.new_page(viewport={'width':width,'height':844},is_mobile=True,has_touch=True)
        errors=[]
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE,wait_until='networkidle')
        page.wait_for_timeout(100)
        vals=page.evaluate("""() => {
          const get = s => {const e=document.querySelector(s);if(!e)return null; const r=e.getBoundingClientRect(), c=getComputedStyle(e);return{x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height,display:c.display,visibility:c.visibility,opacity:c.opacity,fontSize:c.fontSize};};
          const brand=get('.brand'), menu=get('.mnav__btn'), headerCta=get('.site-header__controls > .btn--primary'), heroCta=get('.hero__actions .btn--primary'), app=get('.appbar');
          return {brand,menu,headerCta,heroCta,app, gap:menu&&brand?menu.x-brand.right:null, overflow:document.documentElement.scrollWidth-innerWidth, headerH:document.querySelector('#site-header').getBoundingClientRect().height, classes:document.documentElement.className};
        }""")
        results[str(width)]={'values':vals,'errors':errors}
        page.close()
    browser.close()
print(json.dumps(results,indent=2))
Path('/home/user/workspace/plotvisionai-vercel/qa_reports').mkdir(exist_ok=True)
Path('/home/user/workspace/plotvisionai-vercel/qa_reports/production_audit_baseline.json').write_text(json.dumps(results,indent=2)+'\n')
