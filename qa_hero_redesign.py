"""Visual + functional QA for the rebuilt landing header and hero.

Checks, at 320/360/390/430/1440:
  * no visible Before/After wording and no replay control anywhere in the page
  * one visually dominant app CTA in the first viewport
  * header controls >= 48px, no overlap between brand and controls
  * no horizontal overflow, no console errors
  * the automatic reveal runs (bloom rises) and returns to daylight on its cycle
  * the sticky header never covers the concept demo controls
"""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path('/home/user/workspace/plotvisionai-vercel')
URL = 'http://127.0.0.1:4321/index.html'
SHOTS = ROOT / 'qa_shots'
SHOTS.mkdir(exist_ok=True)
OUT = ROOT / 'qa_reports' / 'hero_redesign_qa.json'
OUT.parent.mkdir(exist_ok=True)

WIDTHS = [320, 360, 390, 430, 1440]
report = {}
failures = []


def expect(cond, label):
    if not cond:
        failures.append(label)


def rect(page, selector):
    loc = page.locator(selector)
    if loc.count() == 0:
        return None
    return loc.first.evaluate("""e => {
      const r = e.getBoundingClientRect(), s = getComputedStyle(e);
      return {x:r.x, y:r.y, w:r.width, h:r.height, right:r.right, bottom:r.bottom,
              display:s.display, visibility:s.visibility};
    }""")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for width in WIDTHS:
        height = 900 if width >= 1440 else 780
        page = browser.new_page(viewport={'width': width, 'height': height},
                               device_scale_factor=2 if width < 1440 else 1)
        errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(URL, wait_until='load')
        page.wait_for_timeout(900)

        entry = {}

        # 1. No Before/After wording, no replay control, no visible hint pill.
        entry['stamps'] = page.locator('.hero .stamp').count()
        entry['replay_controls'] = page.locator('[data-reveal-replay]').count()
        # Wording checks apply to the image area (where labels used to live) and
        # to standalone Before/After labels anywhere in the hero.
        stage_text = page.locator('.hero__stage').evaluate(
            """e => [...e.children]
                 .filter(c => !c.classList.contains('sr-only'))
                 .map(c => c.innerText.trim()).join(' ').trim()""")
        hero_text = page.locator('.hero').inner_text()
        import re
        entry['stage_text'] = stage_text
        entry['hero_has_before_word'] = bool(stage_text) or bool(
            re.search(r'(?m)^\s*(before|after)\b', hero_text, re.I))
        entry['hero_has_after_word'] = 'BEFORE' in hero_text or 'AFTER' in hero_text
        entry['hero_has_replay_word'] = 'replay' in hero_text.lower()
        expect(entry['stamps'] == 0, f'{width}: before/after stamps still in hero')
        expect(entry['replay_controls'] == 0, f'{width}: replay control still present')
        expect(not entry['hero_has_before_word'], f'{width}: visible "before" wording in hero')
        expect(not entry['hero_has_after_word'], f'{width}: visible "after" wording in hero')
        expect(not entry['hero_has_replay_word'], f'{width}: visible "replay" wording in hero')

        # 2. One dominant app CTA in the first viewport.
        dominant = page.evaluate("""() => {
          const vh = window.innerHeight;
          const out = [];
          document.querySelectorAll('a[href*="plotvisionai-preview.pplx.app"], .appbar__btn').forEach(a => {
            const r = a.getBoundingClientRect(), s = getComputedStyle(a);
            const visible = s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity) > 0.05;
            const inView = r.top < vh && r.bottom > 0 && r.width > 0;
            const filled = s.backgroundColor.replace(/[^0-9.,]/g, '').split(',');
            const alpha = filled.length > 3 ? parseFloat(filled[3]) : 1;
            if (visible && inView) out.push({
              text: a.textContent.trim().slice(0, 40),
              cls: a.className, area: Math.round(r.width * r.height), alpha,
              dominant: alpha > 0.6 && r.width * r.height > 8000
            });
          });
          return out;
        }""")
        entry['first_viewport_app_ctas'] = dominant
        entry['dominant_count'] = sum(1 for d in dominant if d['dominant'])
        expect(entry['dominant_count'] <= 1,
               f"{width}: {entry['dominant_count']} dominant app CTAs in first viewport")
        expect(len(dominant) <= 1,
               f"{width}: {len(dominant)} app CTAs visible in the first viewport")

        # 3. Touch targets in the header + hero.
        targets = page.evaluate("""() => {
          const sel = ['.mnav__btn', '.hshare', '.site-header__controls > .btn--primary',
                       '.hero__actions--single .btn--primary', '.hero__links a'];
          const out = [];
          sel.forEach(s => document.querySelectorAll(s).forEach(e => {
            const r = e.getBoundingClientRect(), st = getComputedStyle(e);
            if (st.display === 'none' || st.visibility === 'hidden' || r.width === 0) return;
            out.push({sel: s, w: Math.round(r.width), h: Math.round(r.height)});
          }));
          return out;
        }""")
        entry['touch_targets'] = targets
        for t in targets:
            expect(t['h'] >= 47.5, f"{width}: {t['sel']} height {t['h']}px < 48")
            expect(t['w'] >= 47.5, f"{width}: {t['sel']} width {t['w']}px < 48")

        # 4. Header geometry: single row, brand clear of controls, logo visible.
        brand = rect(page, '.brand')
        mark = rect(page, '.brand__mark')
        controls = rect(page, '.site-header__controls')
        header = rect(page, '.site-header__inner')
        entry['header'] = {'brand': brand, 'mark': mark, 'controls': controls, 'inner': header}
        if width < 1440:
            expect(header['h'] <= 76, f"{width}: header row {header['h']}px too tall")
            expect(mark['w'] >= 34, f"{width}: brand mark only {mark['w']}px wide")
            first_ctrl = page.evaluate("""() => {
              const items = [...document.querySelectorAll('.hshare, .mnav__btn, .site-header__controls > .btn--primary')]
                .filter(e => { const s = getComputedStyle(e), r = e.getBoundingClientRect();
                                return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 1; })
                .map(e => e.getBoundingClientRect().left);
              return items.length ? Math.min(...items) : null;
            }""")
            word = rect(page, '.brand__word')
            entry['brand_word_right'] = word['right']
            entry['brand_right'] = brand['right']
            entry['controls_left'] = first_ctrl
            expect(first_ctrl is None or brand['right'] <= first_ctrl + 0.5,
                   f'{width}: brand box overlaps header controls')
            expect(first_ctrl is None or word['right'] <= first_ctrl - 6,
                   f'{width}: wordmark runs into the header controls')

        # 5. Overflow + console.
        entry['overflow'] = page.evaluate(
            "() => document.documentElement.scrollWidth - window.innerWidth")
        expect(entry['overflow'] <= 1, f"{width}: horizontal overflow {entry['overflow']}px")
        entry['console_errors'] = errors
        expect(not errors, f'{width}: console errors {errors}')

        # 6. Above-the-fold content: kicker + h1 inside the first viewport.
        entry['h1_bottom'] = rect(page, '#hero-title')['bottom']
        entry['viewport_h'] = height
        expect(entry['h1_bottom'] <= height,
               f"{width}: h1 bottom {entry['h1_bottom']} below the fold ({height})")

        page.screenshot(path=str(SHOTS / f'redesign_home_{width}.png'))

        # 7. Reveal behaviour: bloom rises automatically, then returns to daylight.
        bloom0 = page.evaluate(
            "() => getComputedStyle(document.querySelector('.hero')).getPropertyValue('--bloom')")
        page.wait_for_timeout(3200)
        bloom1 = page.evaluate(
            "() => getComputedStyle(document.querySelector('.hero')).getPropertyValue('--bloom')")
        entry['bloom_start'] = bloom0.strip()
        entry['bloom_resolved'] = bloom1.strip()
        expect(float(bloom1 or 0) > 0.9, f'{width}: reveal did not resolve (bloom {bloom1})')
        entry['is_resolved'] = page.locator('.hero.is-resolved').count() == 1
        page.screenshot(path=str(SHOTS / f'redesign_home_{width}_resolved.png'))

        if width < 1440:
            # Scrolled state: the compact header CTA joins the row; the wordmark
            # must still fit beside it with no clipping or overlap.
            page.evaluate("() => window.scrollTo(0, 1600)")
            page.wait_for_timeout(700)
            fit = page.evaluate("""() => {
              const word = document.querySelector('.brand__word').getBoundingClientRect();
              const items = [...document.querySelectorAll('.hshare, .mnav__btn, .site-header__controls > .btn--primary')]
                .filter(e => { const s = getComputedStyle(e), r = e.getBoundingClientRect();
                               return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 1; });
              const left = items.length ? Math.min(...items.map(e => e.getBoundingClientRect().left)) : null;
              const small = items.filter(e => { const r = e.getBoundingClientRect();
                               return r.height < 47.5 || r.width < 47.5; }).length;
              return {wordRight: word.right, ctrlLeft: left, tooSmall: small,
                      overflow: document.documentElement.scrollWidth - window.innerWidth,
                      ctas: items.length};
            }""")
            entry['scrolled_header'] = fit
            expect(fit['ctrlLeft'] is None or fit['wordRight'] <= fit['ctrlLeft'] - 4,
                   f"{width}: scrolled header clips the wordmark")
            expect(fit['tooSmall'] == 0, f"{width}: scrolled header control under 48px")
            expect(fit['overflow'] <= 1, f"{width}: scrolled overflow {fit['overflow']}px")
            page.screenshot(path=str(SHOTS / f'redesign_header_scrolled_{width}.png'),
                            clip={'x': 0, 'y': 0, 'width': width, 'height': 90})
            page.evaluate("() => window.scrollTo(0, 0)")
            page.wait_for_timeout(400)

        if width == 390:
            # Full-page and daylight-return checks on one representative width.
            page.screenshot(path=str(SHOTS / f'redesign_home_{width}_full.png'), full_page=True)
            returned = page.evaluate("""() => new Promise(resolve => {
              const hero = document.querySelector('.hero');
              const t0 = performance.now();
              const tick = () => {
                const b = parseFloat(getComputedStyle(hero).getPropertyValue('--bloom')) || 0;
                if (b < 0.35) return resolve({returned: true, ms: Math.round(performance.now() - t0)});
                if (performance.now() - t0 > 20000) return resolve({returned: false, ms: null});
                requestAnimationFrame(tick);
              };
              tick();
            })""")
            entry['daylight_return'] = returned
            expect(returned['returned'], '390: hero never returned to daylight')
            if returned['returned']:
                expect(11000 <= returned['ms'] <= 19000,
                       f"390: daylight return at {returned['ms']}ms outside the 15s window")
            page.screenshot(path=str(SHOTS / f'redesign_home_{width}_daylight.png'))

            # Menu opens, is tappable, and closes.
            page.locator('.mnav__btn').click()
            page.wait_for_timeout(400)
            entry['menu_open'] = page.locator('.mnav[open]').count() == 1
            page.screenshot(path=str(SHOTS / f'redesign_menu_{width}.png'))
            expect(entry['menu_open'], '390: menu did not open')
            page.locator('[data-mnav-close]').click()
            page.wait_for_timeout(300)
            entry['menu_closed'] = page.locator('.mnav[open]').count() == 0
            expect(entry['menu_closed'], '390: menu did not close')

            # Scrolled state: header CTA hands off, share hides, no duplicate CTA.
            page.evaluate("() => window.scrollTo(0, 1400)")
            page.wait_for_timeout(600)
            entry['scrolled_dominant'] = page.evaluate("""() => {
              const vh = window.innerHeight; let n = 0;
              document.querySelectorAll('a[href*="plotvisionai-preview.pplx.app"], .appbar__btn').forEach(a => {
                const r = a.getBoundingClientRect(), s = getComputedStyle(a);
                const vis = s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity) > 0.05;
                if (vis && r.top < vh && r.bottom > 0) n++;
              });
              return n;
            }""")
            page.screenshot(path=str(SHOTS / f'redesign_home_{width}_scrolled.png'))

        if width == 1440:
            # Sticky header must never cover the concept demo controls.
            page.evaluate("""() => {
              document.documentElement.style.scrollBehavior = 'auto';
              const el = document.querySelector('#concept');
              window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 40);
            }""")
            page.wait_for_timeout(700)
            entry['appbar_over_demo'] = page.evaluate("""() => {
              const bar = document.querySelector('.appbar');
              if (!bar) return false;
              const s = getComputedStyle(bar);
              return !(s.visibility === 'hidden' || s.display === 'none' || parseFloat(s.opacity) < 0.05);
            }""")
            expect(not entry['appbar_over_demo'], '1440: app bar visible over the concept demo')
            page.screenshot(path=str(SHOTS / 'redesign_concept_1440.png'))

        report[str(width)] = entry
        page.close()

    browser.close()

report['failures'] = failures
report['passed'] = not failures
OUT.write_text(json.dumps(report, indent=2))
print(json.dumps({'passed': not failures, 'failures': failures}, indent=2))
