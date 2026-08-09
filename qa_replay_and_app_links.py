#!/usr/bin/env python3
"""Focused QA for the no-trace landing reveal and canonical app CTA targets."""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
BASE = "http://127.0.0.1:%s" % (sys.argv[1] if len(sys.argv) > 1 else "4321")
CANONICAL = "https://plotvisionai-preview.pplx.app"
VIEWPORTS = [
    ("desktop", 1440, 900, False),
    ("mobile-320", 320, 740, True),
    ("mobile-360", 360, 740, True),
    ("mobile-430", 430, 740, True),
]
PREVIEW_LABELS = {
    "Try PlotVisionAI Free",
    "Try Free",
    "Try the New Mobile App",
    "Try the free preview",
    "Open the preview",
}
MOBILE_INFO_LABELS = {"Mobile app", "Get the app"}


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.current = dict(attrs)
            self.current["_text"] = ""

    def handle_data(self, data):
        if self.current is not None:
            self.current["_text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.anchors.append(self.current)
            self.current = None


def compact(text):
    return re.sub(r"\s+", " ", text or "").strip()


def source_link_audit():
    failures = []
    totals = {"preview": 0, "mobile_info": 0, "persistent_app_cta": 0, "header_app_cta": 0, "menu_app_cta": 0}
    for path in sorted(ROOT.glob("*.html")):
        parser = AnchorParser()
        parser.feed(path.read_text())
        for anchor in parser.anchors:
            text = compact(anchor.get("_text", ""))
            href = anchor.get("href")
            classes = set((anchor.get("class") or "").split())
            is_persistent_app_cta = "appbar__btn" in classes
            is_header_app_cta = "btn--sm" in classes and "btn--primary" in classes
            is_menu_app_cta = "mnav__cta" in classes

            if is_persistent_app_cta or is_header_app_cta or is_menu_app_cta:
                if is_persistent_app_cta:
                    totals["persistent_app_cta"] += 1
                if is_header_app_cta:
                    totals["header_app_cta"] += 1
                if is_menu_app_cta:
                    totals["menu_app_cta"] += 1
                if href != CANONICAL:
                    failures.append(
                        f"{path.name}: app CTA classes {sorted(classes)!r} point to {href!r}, not {CANONICAL!r}"
                    )
            elif text in PREVIEW_LABELS:
                totals["preview"] += 1
                if href != CANONICAL:
                    failures.append(f"{path.name}: {text!r} points to {href!r}, not {CANONICAL!r}")
            elif text in MOBILE_INFO_LABELS:
                totals["mobile_info"] += 1
                if href != "download.html":
                    failures.append(f"{path.name}: intentionally labeled {text!r} points to {href!r}, not 'download.html'")
    return totals, failures


def hero_state(page):
    return page.evaluate(
        """() => {
          const hero = document.querySelector('.hero');
          const stage = document.querySelector('.hero__stage');
          const before = document.querySelector('.hero__half--before img');
          const after = document.querySelector('.hero__half--after img');
          const replay = document.querySelector('[data-reveal-replay]');
          const b = stage && stage.getBoundingClientRect();
          return {
            heroClasses: hero && hero.className,
            traceNodes: hero ? hero.querySelectorAll('.drawplan').length : -1,
            stage: b && { width: Math.round(b.width), height: Math.round(b.height) },
            beforeLoaded: !!(before && before.complete && before.naturalWidth),
            afterLoaded: !!(after && after.complete && after.naturalWidth),
            replayVisible: !!(replay && !replay.hidden),
            replayLabel: replay && replay.innerText.replace(/\\s+/g, " ").trim(),
            overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
          };
        }"""
    )


def popup_url(page, selector):
    with page.expect_popup(timeout=10000) as popup_info:
        page.locator(selector).click()
    popup = popup_info.value
    try:
        return popup.url
    finally:
        popup.close()


def main():
    report = {"source_link_audit": {}, "viewports": {}, "pricing": {}}
    failures = []
    totals, source_failures = source_link_audit()
    report["source_link_audit"] = totals
    failures.extend(source_failures)

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
            page.wait_for_selector(".hero__stage")
            # Inspect while the initial animation is active, then after it settles.
            page.wait_for_timeout(400)
            initial = hero_state(page)
            try:
                page.wait_for_function("() => document.querySelector('.hero').classList.contains('is-resolved')", timeout=7000)
            except Exception:
                failures.append(f"{name}: initial hero never reached its resolved state")
            settled = hero_state(page)

            page.locator("[data-reveal-replay]").click()
            try:
                page.wait_for_function("() => document.querySelector('.hero').classList.contains('is-drawing')", timeout=1500)
            except Exception:
                failures.append(f"{name}: replay did not start after a normal click")
            replaying = hero_state(page)
            try:
                page.wait_for_function("() => document.querySelector('.hero').classList.contains('is-resolved')", timeout=7000)
            except Exception:
                failures.append(f"{name}: replay never returned to its resolved state")
            replay_settled = hero_state(page)

            # The landing page intentionally tucks the persistent app bar on
            # phones so it cannot compete with the hero/header CTA handoff.
            # The source audit above still verifies every appbar href; this
            # interaction check uses the visible header action at every size.
            selector = ".site-header__controls > .btn--primary"
            target_url = popup_url(page, selector)
            data = {
                "initial": initial,
                "settled": settled,
                "replaying": replaying,
                "replay_settled": replay_settled,
                "clicked_app_link": target_url,
                "errors": errors,
            }
            report["viewports"][name] = data

            for point, state in (("initial", initial), ("settled", settled), ("replay", replaying), ("replay settled", replay_settled)):
                if state["traceNodes"] != 0:
                    failures.append(f"{name} {point}: found {state['traceNodes']} tracing overlay node(s)")
                if not state["stage"] or state["stage"]["width"] < 1 or state["stage"]["height"] < 1:
                    failures.append(f"{name} {point}: hero stage is blank or has no size")
                if state["overflow"]:
                    failures.append(f"{name} {point}: horizontal overflow")
            if not settled["beforeLoaded"] or not settled["afterLoaded"]:
                failures.append(f"{name}: a hero image did not load")
            if not settled["replayVisible"] or settled["replayLabel"] != "Replay reveal":
                failures.append(f"{name}: replay control is missing or has the wrong settled label")
            if target_url.rstrip("/") != CANONICAL.rstrip("/"):
                failures.append(f"{name}: clicked app CTA opened {target_url!r}, not {CANONICAL!r}")
            if errors:
                failures.append(f"{name}: console/page errors: {errors[:3]}")
            page.close()

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
            page.goto(BASE + "/corporate-pricing.html", wait_until="load")
            page.wait_for_timeout(300)
            state = page.evaluate(
                """() => ({
                  prices: [...document.querySelectorAll('.tier__price')].map(x => x.innerText.replace(/\\s+/g, ' ').trim()),
                  activationNotes: [...document.querySelectorAll('.tier__note')].map(x => x.innerText.replace(/\\s+/g, ' ').trim()),
                  qrCaption: document.querySelector('.appqr__cap').innerText.replace(/\\s+/g, ' ').trim(),
                  overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
                })"""
            )
            report["pricing"][name] = {**state, "errors": errors}
            for expected in ("$299 one-time", "$249 one-time", "$999 one-time"):
                if expected not in state["prices"]:
                    failures.append(f"{name} corporate pricing: missing spaced price {expected!r}: {state['prices']}")
            if not any(note.lower().startswith("activation request opens") for note in state["activationNotes"]):
                failures.append(f"{name} corporate pricing: activation-note space is missing")
            if state["qrCaption"] != "Scan for the mobile app Opens the PlotVisionAI app page on your phone":
                failures.append(f"{name} corporate pricing: QR caption is {state['qrCaption']!r}")
            if state["overflow"]:
                failures.append(f"{name} corporate pricing: horizontal overflow")
            if errors:
                failures.append(f"{name} corporate pricing: console/page errors: {errors[:3]}")
            page.close()
        browser.close()

    out = ROOT / "qa_reports"
    out.mkdir(exist_ok=True)
    (out / "replay_app_links_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print(" - " + failure)
        return 1
    print("\nPASS: landing reveal has no trace overlay; replay, responsive layout, corporate copy, and app CTA destinations hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
