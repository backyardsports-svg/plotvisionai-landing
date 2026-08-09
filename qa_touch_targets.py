#!/usr/bin/env python3
"""Targeted mobile touch, layout, and control QA for the PlotVisionAI site."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
BASE = "http://127.0.0.1:%s" % (sys.argv[1] if len(sys.argv) > 1 else "4321")
VIEWPORTS = [(320, 740), (360, 740), (430, 740)]
MIN_PRIMARY = 52
MIN_SECONDARY = 48
MIN_FONT = 16

# Representative pages cover each shared header/footer template plus the unique
# replay, pricing, form, and comparison controls requested for this pass.
PAGES = {
    "home": {
        "path": "index.html",
        "controls": [
            ("Header Try Free", ".site-header__controls > .btn--primary", MIN_PRIMARY, MIN_FONT),
            ("Share This Page", ".hshare", MIN_PRIMARY, MIN_FONT),
            ("Menu", ".mnav__btn", MIN_PRIMARY, MIN_FONT),
            ("Sticky app CTA", ".appbar__btn", MIN_PRIMARY, MIN_FONT),
            ("Hero replay", ".hero__replay", MIN_PRIMARY, MIN_FONT),
        ],
    },
    "consumer_pricing": {
        "path": "pricing.html",
        "controls": [
            ("Pricing purchase", ".tier__cta .btn", MIN_PRIMARY, MIN_FONT),
        ],
    },
    "corporate_pricing": {
        "path": "corporate-pricing.html",
        "controls": [
            ("Corporate activation request", ".tier__cta .btn", MIN_PRIMARY, MIN_FONT),
            ("Billing choice", ".billtoggle__opt", MIN_PRIMARY, MIN_FONT),
        ],
    },
    "contact": {
        "path": "contact.html",
        "controls": [
            ("Contact form submit", "#contact-form button[type=submit]", MIN_PRIMARY, MIN_FONT),
        ],
    },
    "preview": {
        "path": "free-preview.html",
        "controls": [
            ("Preview form submit", "#preview-gate button[type=submit]", MIN_PRIMARY, MIN_FONT),
        ],
    },
    "comparison": {
        "path": "backyard-sports-center.html",
        "controls": [
            ("Comparison replay", ".cmp__replay", MIN_PRIMARY, MIN_FONT),
            ("Crossfade replay", ".xfade__toggle", MIN_PRIMARY, MIN_FONT),
        ],
    },
}


def rect_and_font(page, selector):
    return page.locator(selector).first.evaluate(
        """el => {
          const r = el.getBoundingClientRect();
          const c = getComputedStyle(el);
          return {
            x: Math.round(r.x * 10) / 10,
            y: Math.round(r.y * 10) / 10,
            width: Math.round(r.width * 10) / 10,
            height: Math.round(r.height * 10) / 10,
            font_size: Math.round(parseFloat(c.fontSize) * 10) / 10,
            color: c.color,
            background: c.backgroundColor,
            visible: !!(r.width && r.height && c.visibility !== 'hidden' && c.display !== 'none'),
          };
        }"""
    )


def overlaps(a, b):
    return (
        a["x"] < b["x"] + b["width"]
        and b["x"] < a["x"] + a["width"]
        and a["y"] < b["y"] + b["height"]
        and b["y"] < a["y"] + a["height"]
    )


def check_menu(page, width, report, failures):
    page.locator(".mnav__btn").click()
    page.wait_for_selector(".mnav__panel", state="visible")
    menu = {}
    for name, selector, minimum, font_minimum in (
        ("Close menu", ".mnav__close", MIN_PRIMARY, MIN_FONT),
        ("Menu app CTA", ".mnav__cta", MIN_PRIMARY, MIN_FONT),
        ("Menu share", ".mnav__tools .toolbtn", MIN_PRIMARY, MIN_FONT),
    ):
        measure = rect_and_font(page, selector)
        menu[name] = measure
        if not measure["visible"] or min(measure["width"], measure["height"]) < minimum:
            failures.append(f"{width}px menu: {name} is not a {minimum}px target: {measure}")
        if measure["font_size"] < font_minimum:
            failures.append(f"{width}px menu: {name} font is {measure['font_size']}px, under {font_minimum}px")
    page.locator(".mnav__close").click()
    page.wait_for_function("() => !document.querySelector('.mnav').open")
    report["menu"] = menu


def main():
    out = ROOT / "qa_reports"
    out.mkdir(exist_ok=True)
    shots = ROOT / "qa_shots"
    shots.mkdir(exist_ok=True)
    report = {"minimums": {"primary": MIN_PRIMARY, "secondary": MIN_SECONDARY, "font": MIN_FONT}, "viewports": {}}
    failures = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width, height in VIEWPORTS:
            viewport_report = {}
            for key, spec in PAGES.items():
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    is_mobile=True,
                    has_touch=True,
                    device_scale_factor=2,
                )
                errors = []
                page.on("pageerror", lambda err, errors=errors: errors.append(str(err)))
                page.on("console", lambda msg, errors=errors: errors.append(msg.text) if msg.type == "error" else None)
                page.goto(f"{BASE}/{spec['path']}", wait_until="load")
                page.wait_for_selector(".site-header")
                page.wait_for_timeout(250)
                item = {"path": spec["path"], "controls": {}, "errors": errors}
                for name, selector, minimum, font_minimum in spec["controls"]:
                    if not page.locator(selector).count():
                        failures.append(f"{width}px {key}: {name} is missing ({selector})")
                        item["controls"][name] = "MISSING"
                        continue
                    measure = rect_and_font(page, selector)
                    item["controls"][name] = measure
                    if not measure["visible"]:
                        failures.append(f"{width}px {key}: {name} is not visible")
                    if min(measure["width"], measure["height"]) < minimum:
                        failures.append(f"{width}px {key}: {name} is not a {minimum}px target: {measure}")
                    if measure["font_size"] < font_minimum:
                        failures.append(f"{width}px {key}: {name} font is {measure['font_size']}px, under {font_minimum}px")

                item["horizontal_overflow"] = page.evaluate(
                    "() => document.documentElement.scrollWidth > window.innerWidth + 1"
                )
                if item["horizontal_overflow"]:
                    failures.append(f"{width}px {key}: horizontal overflow")

                if key == "home":
                    header_controls = {
                        name: item["controls"][name]
                        for name in ("Header Try Free", "Share This Page", "Menu")
                        if isinstance(item["controls"].get(name), dict)
                    }
                    names = list(header_controls)
                    for i, first in enumerate(names):
                        for second in names[i + 1 :]:
                            if overlaps(header_controls[first], header_controls[second]):
                                failures.append(f"{width}px home: {first} overlaps {second}")
                    appbar = item["controls"].get("Sticky app CTA")
                    if isinstance(appbar, dict) and appbar["height"] > 88:
                        failures.append(f"{width}px home: sticky app bar button is too tall at {appbar['height']}px")
                    check_menu(page, width, item, failures)
                    page.screenshot(path=str(shots / f"final_touch_home_{width}.png"))
                    page.evaluate("() => window.scrollTo(0, 1000)")
                    page.wait_for_timeout(150)
                    stuck_header = page.locator(".site-header").bounding_box()
                    item["stuck_header_height"] = round(stuck_header["height"], 1) if stuck_header else None
                    if stuck_header and stuck_header["height"] > 190:
                        failures.append(f"{width}px home: sticky header occupies {stuck_header['height']:.1f}px")
                    page.screenshot(path=str(shots / f"final_touch_home_{width}_stuck.png"))
                if key == "corporate_pricing":
                    page.screenshot(path=str(shots / f"final_touch_corporate_{width}.png"))
                viewport_report[key] = item
                if errors:
                    failures.append(f"{width}px {key}: console/page errors: {errors[:3]}")
                page.close()
            report["viewports"][str(width)] = viewport_report
        browser.close()

    (out / "touch_targets_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print(" - " + failure)
        return 1
    print("\nPASS: shared mobile controls, replay controls, pricing CTAs, and form submits meet the requested touch-target pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
