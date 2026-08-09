import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path('/home/user/workspace/plotvisionai-vercel')
URL = 'http://127.0.0.1:4321/index.html'
OUT = ROOT / 'qa_reports' / 'production_audit_fixes_final.json'
SHOTS = ROOT / 'qa_shots'
SHOTS.mkdir(exist_ok=True)

results = {'desktop_demo': {}, 'mobile_home': {}, 'interior_mobile': {}, 'hero_replay': {}}
failures = []

def expect(condition, label):
    if not condition:
        failures.append(label)

def js_rect(page, selector):
    return page.locator(selector).evaluate("""e => {
      const r = e.getBoundingClientRect(), s = getComputedStyle(e);
      return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height,
        display:s.display,visibility:s.visibility,opacity:s.opacity,fontSize:parseFloat(s.fontSize)};
    }""")

def instant_scroll_to_control_overlap(page, selector):
    page.evaluate("""selector => {
      document.documentElement.style.scrollBehavior = 'auto';
      const e = document.querySelector(selector), r = e.getBoundingClientRect();
      const docY = r.top + window.scrollY;
      window.scrollTo(0, docY + r.height / 2 - (window.innerHeight - 50));
    }""", selector)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # App bar is present at ordinary desktop positions, then fully removed from
    # the hit-testing layer while the concept editor enters the viewport.
    for width in (1024, 1280, 1440, 1600):
        page = browser.new_page(viewport={'width': width, 'height': 900})
        errors, warnings = [], []
        page.on('pageerror', lambda e, arr=errors: arr.append(str(e)))
        page.on('console', lambda msg, arr=warnings: arr.append(msg.text) if msg.type == 'error' else None)
        page.goto(URL, wait_until='networkidle')
        initial = js_rect(page, '.appbar')
        expect(initial['visibility'] == 'visible', f'{width}: appbar is not restored outside concept demo')

        instant_scroll_to_control_overlap(page, '#ce-remove')
        page.wait_for_function("document.documentElement.classList.contains('concept-demo-in-view')")
        page.wait_for_timeout(30)
        appbar = js_rect(page, '.appbar')
        control_hits = {}
        for selector in ('#ce-remove', '#ce-undo'):
            hit = page.evaluate("""selector => {
                const e=document.querySelector(selector), r=e.getBoundingClientRect();
                const x=r.left+r.width/2, y=r.top+r.height/2, hit=document.elementFromPoint(x,y);
                return {x,y,hitId:hit && hit.id, hitText:(hit && hit.textContent || '').trim(), within:!!(hit && e.contains(hit))};
            }""", selector)
            control_hits[selector] = hit
            expect(hit['within'], f'{width}: elementFromPoint for {selector} is blocked by an overlay')
        expect(appbar['visibility'] == 'hidden', f'{width}: appbar remains visible over concept demo')
        if width == 1440:
            page.screenshot(path=str(SHOTS / 'production_audit_desktop_1440_concept.png'))

        # These are normal user clicks at an overlap-prone scroll position.
        page.locator('#ce-remove').click()
        expect('removed' in page.locator('#ce-status').inner_text().lower(), f'{width}: Remove did not execute')
        page.locator('#ce-undo').click()
        undo_status = page.locator('#ce-status').inner_text().lower()
        expect(('undid' in undo_status) or ('restored' in undo_status), f'{width}: Undo did not execute')

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_function("!document.documentElement.classList.contains('concept-demo-in-view')")
        restored = js_rect(page, '.appbar')
        expect(restored['visibility'] == 'visible', f'{width}: appbar did not restore after concept demo')
        results['desktop_demo'][str(width)] = {
            'initial_appbar': initial,
            'hidden_appbar': appbar,
            'control_hits': control_hits,
            'restored_appbar': restored,
            'errors': errors,
            'console_errors': warnings,
        }
        expect(not errors, f'{width}: page errors: {errors}')
        expect(not warnings, f'{width}: console errors: {warnings}')
        page.close()

    # Header CTA is only present when the hero CTA is not on screen. The mobile
    # appbar is tucked for this landing page, making the hero/header handoff the
    # sole prominent app action. The compact 320 brand keeps a 12px gap.
    for width in (320, 360, 430):
        page = browser.new_page(viewport={'width': width, 'height': 844}, is_mobile=True, has_touch=True)
        errors, warnings = [], []
        page.on('pageerror', lambda e, arr=errors: arr.append(str(e)))
        page.on('console', lambda msg, arr=warnings: arr.append(msg.text) if msg.type == 'error' else None)
        page.goto(URL, wait_until='networkidle')
        page.wait_for_function("document.documentElement.classList.contains('home-hero-primary-away')")
        initial = page.evaluate("""() => {
          const box = s => { const e=document.querySelector(s), r=e.getBoundingClientRect(), c=getComputedStyle(e); return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height,display:c.display,visibility:c.visibility,fontSize:parseFloat(c.fontSize)}; };
          const brand=box('.brand'), menu=box('.mnav__btn');
          return {header:box('#site-header'), brand, menu, gap:menu.x-brand.right, headerCta:box('.site-header__controls > .btn--primary'), heroCta:box('.hero__actions .btn--primary'), appbar:box('.appbar'), overflow:document.documentElement.scrollWidth-window.innerWidth};
        }""")
        expect(initial['headerCta']['display'] != 'none', f'{width}: header CTA did not appear when hero CTA was offscreen')
        expect(initial['headerCta']['height'] >= 52, f'{width}: header CTA shorter than 52px')
        expect(initial['menu']['height'] >= 56, f'{width}: Menu shorter than 56px')
        expect(initial['appbar']['visibility'] == 'hidden', f'{width}: home appbar competes with header CTA')
        expect(initial['overflow'] <= 0.5, f'{width}: initial horizontal overflow is {initial["overflow"]}')
        expect(initial['gap'] >= (12 if width == 320 else 8), f'{width}: brand/Menu gap is {initial["gap"]}')

        page.locator('.hero__actions .btn--primary').scroll_into_view_if_needed()
        page.wait_for_function("!document.documentElement.classList.contains('home-hero-primary-away')")
        visible_hero = page.evaluate("""() => {
          const box = s => { const e=document.querySelector(s), r=e.getBoundingClientRect(), c=getComputedStyle(e); return {top:r.top,bottom:r.bottom,height:r.height,display:c.display,visibility:c.visibility}; };
          return {header:box('#site-header'), headerCta:box('.site-header__controls > .btn--primary'), heroCta:box('.hero__actions .btn--primary'), appbar:box('.appbar'), overflow:document.documentElement.scrollWidth-window.innerWidth};
        }""")
        expect(visible_hero['headerCta']['display'] == 'none', f'{width}: header CTA remains visible with hero CTA')
        expect(visible_hero['heroCta']['height'] >= 52, f'{width}: hero CTA shorter than 52px')
        expect(visible_hero['appbar']['visibility'] == 'hidden', f'{width}: home appbar competes with hero CTA')
        expect(visible_hero['overflow'] <= 0.5, f'{width}: hero CTA state horizontal overflow')

        page.evaluate("""() => {
          document.documentElement.style.scrollBehavior='auto';
          const e=document.querySelector('.hero__actions .btn--primary'), r=e.getBoundingClientRect();
          window.scrollTo(0, r.bottom + window.scrollY + 8);
        }""")
        page.wait_for_function("document.documentElement.classList.contains('home-hero-primary-away')")
        after = page.evaluate("""() => {
          const box = s => { const e=document.querySelector(s), r=e.getBoundingClientRect(), c=getComputedStyle(e); return {height:r.height,display:c.display,visibility:c.visibility,fontSize:parseFloat(c.fontSize)}; };
          return {header:box('#site-header'), headerCta:box('.site-header__controls > .btn--primary'), appbar:box('.appbar'), overflow:document.documentElement.scrollWidth-window.innerWidth};
        }""")
        expect(after['headerCta']['display'] != 'none' and after['headerCta']['height'] >= 52, f'{width}: header CTA did not return after hero CTA')
        expect(after['appbar']['visibility'] == 'hidden', f'{width}: appbar competes after hero handoff')
        expect(after['overflow'] <= 0.5, f'{width}: after-handoff horizontal overflow')
        page.screenshot(path=str(SHOTS / f'production_audit_mobile_{width}.png'))
        results['mobile_home'][str(width)] = {'initial': initial, 'hero_visible': visible_hero, 'after_handoff': after, 'errors': errors, 'console_errors': warnings}
        expect(not errors, f'{width}: page errors: {errors}')
        expect(not warnings, f'{width}: console errors: {warnings}')
        page.close()

    # Interior routes retain a full-size header app CTA.
    for width in (320, 360, 430):
        page = browser.new_page(viewport={'width': width, 'height': 844}, is_mobile=True, has_touch=True)
        errors = []
        page.on('pageerror', lambda e, arr=errors: arr.append(str(e)))
        page.goto('http://127.0.0.1:4321/pricing.html', wait_until='networkidle')
        cta = js_rect(page, '.site-header__controls > .btn--primary')
        expect(cta['display'] != 'none' and cta['height'] >= 52, f'{width}: interior header CTA unavailable')
        results['interior_mobile'][str(width)] = {'header_cta': cta, 'overflow': page.evaluate('document.documentElement.scrollWidth-window.innerWidth'), 'errors': errors}
        expect(results['interior_mobile'][str(width)]['overflow'] <= 0.5, f'{width}: pricing horizontal overflow')
        expect(not errors, f'{width}: pricing page errors: {errors}')
        page.close()

    # Ensure the approved trace-free hero is still trace-free on both automatic
    # reveal and visitor replay; the reveal control itself remains usable.
    for width in (1440, 320):
        page = browser.new_page(viewport={'width': width, 'height': 900 if width == 1440 else 844}, is_mobile=width == 320, has_touch=width == 320)
        errors = []
        page.on('pageerror', lambda e, arr=errors: arr.append(str(e)))
        page.goto(URL, wait_until='networkidle')
        initial_count = page.locator('.hero .drawplan').count()
        page.locator('[data-reveal-replay]').click()
        page.wait_for_timeout(180)
        replay_count = page.locator('.hero .drawplan').count()
        label = page.locator('[data-reveal-label]').inner_text()
        expect(initial_count == 0 and replay_count == 0, f'{width}: landing tracing overlay returned')
        expect(label in ('Revealing…', 'Replay reveal'), f'{width}: replay control did not update')
        results['hero_replay'][str(width)] = {'initial_drawplans': initial_count, 'replay_drawplans': replay_count, 'label': label, 'errors': errors}
        expect(not errors, f'{width}: replay page errors: {errors}')
        page.close()

    browser.close()

results['failures'] = failures
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))
if failures:
    raise SystemExit('QA FAILED: ' + ' | '.join(failures))
