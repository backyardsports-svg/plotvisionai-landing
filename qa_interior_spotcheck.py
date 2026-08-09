#!/usr/bin/env python3
"""Spot-check interior pages after the site-wide header CSS change (section 40).

The rebuilt header rules are appended to the shared stylesheet, so pages other
than the landing page must keep a single-row header, 48px controls, the header
app CTA visible (only the landing page hides it behind the hero CTA), and no
horizontal overflow.
"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
BASE = "http://127.0.0.1:%s" % (sys.argv[1] if len(sys.argv) > 1 else "4321")
PAGES = ["pricing.html", "corporate-pricing.html", "how-it-works.html", "contact.html"]
VIEWPORTS = [(390, 780, True), (1440, 900, False)]

def main():
    report, failures = {}, []
    shots = ROOT / "qa_shots"; shots.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for width, height, mobile in VIEWPORTS:
            for path in PAGES:
                page = b.new_page(viewport={"width": width, "height": height},
                                  is_mobile=mobile, has_touch=mobile,
                                  device_scale_factor=2 if mobile else 1)
                errs = []
                page.on("pageerror", lambda e, errs=errs: errs.append(str(e)))
                page.on("console", lambda m, errs=errs: errs.append(m.text) if m.type == "error" else None)
                page.goto(f"{BASE}/{path}", wait_until="load")
                page.wait_for_selector(".site-header")
                page.wait_for_timeout(350)
                state = page.evaluate("""() => {
                  const vis = e => { if (!e) return false; const s = getComputedStyle(e), r = e.getBoundingClientRect();
                    return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 1 && r.height > 1; };
                  const box = s => { const e = document.querySelector(s); if (!vis(e)) return null;
                    const r = e.getBoundingClientRect();
                    return {w: Math.round(r.width), h: Math.round(r.height), t: Math.round(r.top), l: Math.round(r.left), r: Math.round(r.right)}; };
                  const hdr = document.querySelector('.site-header').getBoundingClientRect();
                  return {
                    header: {h: Math.round(hdr.height)},
                    cta: box('.site-header__controls > .btn--primary'),
                    menu: box('.mnav__btn'),
                    share: box('.hshare'),
                    word: box('.brand__word'),
                    overflow: document.documentElement.scrollWidth - window.innerWidth,
                  };
                }""")
                state["errors"] = errs
                report[f"{width}:{path}"] = state
                if state["header"]["h"] > 96:
                    failures.append(f"{width} {path}: header is {state['header']['h']}px tall")
                if not state["cta"]:
                    failures.append(f"{width} {path}: header app CTA is not visible")
                for key in ("cta", "menu", "share"):
                    v = state[key]
                    if v and min(v["w"], v["h"]) < 47.5:
                        failures.append(f"{width} {path}: {key} is {v['w']}x{v['h']}")
                controls = [state[k] for k in ("share", "menu", "cta") if state[k]]
                if state["word"] and controls:
                    left = min(c["l"] for c in controls)
                    if state["word"]["r"] > left - 4:
                        failures.append(f"{width} {path}: wordmark collides with the header controls")
                if state["overflow"] > 1:
                    failures.append(f"{width} {path}: horizontal overflow {state['overflow']}px")
                if errs:
                    failures.append(f"{width} {path}: console errors {errs[:2]}")
                page.screenshot(path=str(shots / f"interior_{Path(path).stem}_{width}.png"),
                                clip={"x": 0, "y": 0, "width": width, "height": min(height, 900)})
                page.close()
        b.close()
    out = ROOT / "qa_reports"; out.mkdir(exist_ok=True)
    payload = {"passed": not failures, "failures": failures, "pages": report}
    (out / "interior_spotcheck.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"passed": payload["passed"], "failures": failures}, indent=2))
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
