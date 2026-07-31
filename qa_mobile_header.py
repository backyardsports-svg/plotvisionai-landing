#!/usr/bin/env python3
"""Mobile header/hero QA for the PlotVisionAI landing page.

Measures the things the rebalance is meant to fix — how far down the fold the
primary actions sit, and whether any of them is too small to hit — then writes
one screenshot per width. Run against a local static server:

    python3 -m http.server 4321 &
    python3 qa_mobile_header.py [label] [port]
"""
import json
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

LABEL = sys.argv[1] if len(sys.argv) > 1 else "shot"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 4321
WIDTHS = [320, 360, 430]
OUT = Path(__file__).parent / "qa_shots"

# Every control a thumb is meant to hit in the header region.
TARGETS = {
    "Menu": ".mnav__btn",
    # Direct child only — the menu sheet contains its own primary CTA.
    "Try Free": ".site-header__controls > .btn--primary",
    "Share This Page": ".hshare",
    "App CTA": ".appbar__btn",
    "brand": ".brand",
}
MIN_TAP = 48
PREVIEW_URL = "https://plotvisionai-preview.pplx.app"
# Routes spot-checked for the persistent app CTA and an ungated primary CTA.
PAGES = ["index.html", "pricing.html", "free-preview.html", "gallery.html", "contact.html"]


def rect(page, sel):
    el = page.query_selector(sel)
    return el.bounding_box() if el else None


def main():
    OUT.mkdir(exist_ok=True)
    report = {}
    failures = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for w in WIDTHS:
            page = browser.new_page(viewport={"width": w, "height": 740},
                                    device_scale_factor=2, is_mobile=True,
                                    has_touch=True)
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.goto(f"http://localhost:{PORT}/index.html", wait_until="load")
            page.wait_for_timeout(1200)

            entry = {"targets": {}, "errors": errors}

            for name, sel in TARGETS.items():
                box = rect(page, sel)
                if box is None:
                    entry["targets"][name] = "MISSING"
                    failures.append(f"{w}px: {name} missing ({sel})")
                    continue
                entry["targets"][name] = {
                    "w": round(box["width"], 1), "h": round(box["height"], 1),
                    "top": round(box["y"], 1), "bottom": round(box["y"] + box["height"], 1),
                }
                if name != "brand" and (box["width"] < MIN_TAP or box["height"] < MIN_TAP):
                    failures.append(
                        f"{w}px: {name} is {box['width']:.0f}x{box['height']:.0f}, under {MIN_TAP}")

            # Overlap between the three action controls.
            boxes = {n: rect(page, s) for n, s in TARGETS.items() if n != "brand"}
            names = [n for n, b in boxes.items() if b]
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    a, b = boxes[names[i]], boxes[names[j]]
                    if (a["x"] < b["x"] + b["width"] and b["x"] < a["x"] + a["width"]
                            and a["y"] < b["y"] + b["height"] and b["y"] < a["y"] + a["height"]):
                        failures.append(f"{w}px: {names[i]} overlaps {names[j]}")

            # How much of the first screen the hero photo eats, and whether the
            # CTA is reachable without scrolling.
            stage = rect(page, ".hero__stage")
            if stage:
                entry["hero_stage_h"] = round(stage["height"], 1)
                entry["hero_pct_of_fold"] = round(100 * stage["height"] / 740, 1)
            cta = boxes.get("Try Free")
            if cta:
                entry["cta_fully_above_fold"] = (cta["y"] + cta["height"]) <= 740
                if not entry["cta_fully_above_fold"]:
                    failures.append(f"{w}px: Try Free is below the fold")

            entry["hero_title_top"] = (rect(page, "#hero-title") or {}).get("y")
            if entry["hero_title_top"] is not None:
                entry["hero_title_top"] = round(entry["hero_title_top"], 1)

            # The sticky app bar must reserve its own height, not sit on the
            # footer. Body padding-bottom is what buys that space.
            bar = rect(page, ".appbar")
            if bar:
                pad = page.evaluate(
                    "() => parseFloat(getComputedStyle(document.body).paddingBottom)")
                entry["appbar_h"] = round(bar["height"], 1)
                entry["body_pad_bottom"] = round(pad, 1)
                if pad < bar["height"]:
                    failures.append(
                        f"{w}px: app bar is {bar['height']:.0f}px but body reserves only {pad:.0f}px")

            entry["h_overflow"] = page.evaluate(
                "() => document.documentElement.scrollWidth > window.innerWidth + 1")
            if entry["h_overflow"]:
                failures.append(f"{w}px: horizontal overflow")
            if errors:
                failures.append(f"{w}px: console/page errors: {errors[:3]}")

            page.screenshot(path=str(OUT / f"{LABEL}_home_{w}.png"))

            # Scrolled state: the sticky bar collapses, but Menu and the CTA
            # must stay hittable while floating over the content.
            page.evaluate("() => window.scrollTo(0, 900)")
            page.wait_for_timeout(500)
            hdr = rect(page, ".site-header")
            entry["stuck_header_h"] = round(hdr["height"], 1) if hdr else None
            for name in ("Menu", "Try Free"):
                box = rect(page, TARGETS[name])
                if not box or box["height"] < MIN_TAP:
                    failures.append(f"{w}px scrolled: {name} is under {MIN_TAP}")
            if hdr and hdr["height"] > 0.25 * 740:
                failures.append(
                    f"{w}px scrolled: sticky header is {hdr['height']:.0f}px, over 25% of the fold")
            page.screenshot(path=str(OUT / f"{LABEL}_home_{w}_scrolled.png"))

            report[w] = entry
            page.close()

        # Every route: the app CTA is present with the exact approved wording and
        # the direct preview destination, and no primary CTA still routes to the
        # old email gate.
        routes = {}
        page = browser.new_page(viewport={"width": 360, "height": 740},
                                device_scale_factor=2, is_mobile=True, has_touch=True)
        for name in PAGES:
            page.goto(f"http://localhost:{PORT}/{name}", wait_until="load")
            page.wait_for_timeout(400)
            info = page.evaluate("""() => {
              const a = document.querySelector('.appbar__btn');
              const gated = [...document.querySelectorAll('a.btn--primary, a.btn--ghost')]
                .filter(x => x.getAttribute('href') === 'free-preview.html').length;
              return {
                href: a && a.getAttribute('href'),
                label: a && a.querySelector('.appbar__label').textContent.trim(),
                sub: a && a.querySelector('.appbar__sub').textContent.trim(),
                h: a ? Math.round(a.getBoundingClientRect().height) : 0,
                gatedCtas: gated,
                gateRequiredEmail: document.querySelectorAll('[data-preview-gate] input[type=email][required]').length,
              };
            }""")
            routes[name] = info
            if info["href"] != PREVIEW_URL:
                failures.append(f"{name}: app CTA points at {info['href']!r}")
            if info["label"] != "Try the New Mobile App":
                failures.append(f"{name}: app CTA label is {info['label']!r}")
            if info["sub"] != "Coming soon to the App Store":
                failures.append(f"{name}: app CTA sub is {info['sub']!r}")
            if info["h"] < MIN_TAP:
                failures.append(f"{name}: app CTA is {info['h']}px tall")
            if info["gatedCtas"]:
                failures.append(f"{name}: {info['gatedCtas']} CTA(s) still route to the email gate")
            if info["gateRequiredEmail"]:
                failures.append(f"{name}: the preview form still requires an email address")
        report["routes"] = routes
        page.close()

        # Desktop must be untouched by the phone rules.
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"http://localhost:{PORT}/index.html", wait_until="load")
        page.wait_for_timeout(1200)
        inner = page.evaluate(
            "() => getComputedStyle(document.querySelector('.site-header__inner')).display")
        nav = page.evaluate(
            "() => getComputedStyle(document.querySelector('.section-nav')).display")
        desktop = {"header_display": inner, "section_nav_display": nav,
                   "h_overflow": page.evaluate(
                       "() => document.documentElement.scrollWidth > window.innerWidth + 1")}
        if inner != "flex":
            failures.append(f"desktop: header is '{inner}', expected the original flex row")
        if nav == "none":
            failures.append("desktop: section nav disappeared")
        if desktop["h_overflow"]:
            failures.append("desktop: horizontal overflow")
        page.screenshot(path=str(OUT / f"{LABEL}_home_1440.png"))
        report["1440"] = desktop
        page.close()
        browser.close()

    print(json.dumps(report, indent=2))
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nPASS: all header targets >= 48px, no overlap, no overflow, CTA above the fold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
