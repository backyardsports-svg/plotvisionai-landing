#!/usr/bin/env python3
"""Capture visual evidence for the trace-free replay and shared navigation."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
BASE = "http://127.0.0.1:%s" % (sys.argv[1] if len(sys.argv) > 1 else "4321")
VIEWPORTS = [
    ("desktop", 1440, 900, False),
    ("mobile-320", 320, 740, True),
    ("mobile-360", 360, 740, True),
    ("mobile-430", 430, 740, True),
]


def hero_state(page):
    return page.evaluate("""() => {
      const hero = document.querySelector('.hero');
      const stage = document.querySelector('.hero__stage');
      const r = stage.getBoundingClientRect();
      return {
        classes: hero.className,
        traceNodes: hero.querySelectorAll('.drawplan').length,
        replayText: document.querySelector('[data-reveal-label]').textContent.trim(),
        stage: { x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height) },
        overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
      };
    }""")


def main():
    reports = ROOT / "qa_reports"
    reports.mkdir(exist_ok=True)
    shots = ROOT / "qa_shots"
    shots.mkdir(exist_ok=True)
    report, failures = {"viewports": {}, "navigation": {}}, []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, width, height, mobile in VIEWPORTS:
            page = browser.new_page(
                viewport={"width": width, "height": height},
                is_mobile=mobile,
                has_touch=mobile,
                device_scale_factor=2 if mobile else 1,
            )
            errors = []
            page.on("pageerror", lambda err, errors=errors: errors.append(str(err)))
            page.on("console", lambda msg, errors=errors: errors.append(msg.text) if msg.type == "error" else None)
            page.goto(BASE + "/index.html", wait_until="load")
            page.wait_for_selector(".hero.is-drawing")
            page.wait_for_timeout(350)
            during_initial = hero_state(page)
            page.screenshot(path=str(shots / f"final_tracefree_initial_{name}.png"))
            if during_initial["traceNodes"] != 0:
                failures.append(f"{name}: initial visual state has tracing nodes")
            try:
                page.wait_for_selector(".hero.is-resolved", timeout=7000)
            except Exception:
                failures.append(f"{name}: hero did not settle before replay")
            page.locator("[data-reveal-replay]").click()
            page.wait_for_selector(".hero.is-drawing")
            page.wait_for_timeout(350)
            during_replay = hero_state(page)
            page.screenshot(path=str(shots / f"final_tracefree_replay_{name}.png"))
            if during_replay["traceNodes"] != 0:
                failures.append(f"{name}: replay visual state has tracing nodes")
            if during_replay["overflow"]:
                failures.append(f"{name}: horizontal overflow during replay")
            if errors:
                failures.append(f"{name}: console/page errors: {errors[:3]}")
            report["viewports"][name] = {
                "initial_animation": during_initial,
                "replay_animation": during_replay,
                "errors": errors,
            }
            page.close()

        # Real navigation uses visible controls, not direct URL assignment.
        desktop = browser.new_page(viewport={"width": 1440, "height": 900})
        desktop.goto(BASE + "/index.html", wait_until="load")
        desktop.locator('.section-nav a[href="how-it-works.html"]').click()
        desktop.wait_for_url("**/how-it-works.html")
        report["navigation"]["desktop_header_link"] = {
            "url": desktop.url,
            "header": desktop.locator(".site-header").count(),
        }
        if not desktop.url.endswith("/how-it-works.html"):
            failures.append("desktop: header navigation reached the wrong page")
        desktop.close()

        for width in (320, 360, 430):
            mobile = browser.new_page(viewport={"width": width, "height": 740}, is_mobile=True, has_touch=True, device_scale_factor=2)
            errors = []
            mobile.on("pageerror", lambda err, errors=errors: errors.append(str(err)))
            mobile.goto(BASE + "/index.html", wait_until="load")
            mobile.locator(".mnav__btn").click()
            mobile.wait_for_selector(".mnav__panel", state="visible")
            mobile.locator('.mnav__panel a[href="how-it-works.html"]').click()
            mobile.wait_for_url("**/how-it-works.html")
            record = {
                "url": mobile.url,
                "header": mobile.locator(".site-header").count(),
                "overflow": mobile.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1"),
                "errors": errors,
            }
            report["navigation"][f"mobile_{width}_menu_link"] = record
            if not mobile.url.endswith("/how-it-works.html"):
                failures.append(f"mobile {width}: menu navigation reached the wrong page")
            if record["overflow"]:
                failures.append(f"mobile {width}: overflow after menu navigation")
            if errors:
                failures.append(f"mobile {width}: navigation errors: {errors[:3]}")
            mobile.close()
        browser.close()

    (reports / "visual_animation_navigation_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print(" - " + failure)
        return 1
    print("\nPASS: trace-free initial/replay visual states and desktop/mobile navigation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
