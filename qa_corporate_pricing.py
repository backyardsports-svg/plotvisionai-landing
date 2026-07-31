#!/usr/bin/env python3
"""UI QA for the corporate pricing page.

Checks the things that would quietly break: a toggle that moves the price but
not the checkout target, a request button that dead-ends, a tap target too
small for a thumb, and the contact route failing to pick the plan up.

    python3 -m http.server 4321 &
    python3 qa_corporate_pricing.py [label] [port]
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

LABEL = sys.argv[1] if len(sys.argv) > 1 else "corp"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 4321
WIDTHS = [320, 360, 430]
OUT = Path(__file__).parent / "qa_shots"
MIN_TAP = 48
PILOT_URL = "https://buy.stripe.com/eVqeVd4V3awi2tU3G2cMM09"

EXPECTED = {
    "team5": {"monthly": ("$299", "/month"), "annual": ("$2,990", "/year")},
    "team10": {"monthly": ("$499", "/month"), "annual": ("$4,990", "/year")},
    "team15": {"monthly": ("$699", "/month"), "annual": ("$6,990", "/year")},
    "team25": {"monthly": ("$999", "/month"), "annual": ("$9,990", "/year")},
}


def read_cards(page):
    return page.evaluate("""() => {
      return [...document.querySelectorAll('[data-plan-card]')].map(c => {
        const cta = c.querySelector('[data-checkout-plan]');
        return {
          key: c.getAttribute('data-plan-key'),
          amount: c.querySelector('[data-price-amount]').textContent.trim(),
          per: c.querySelector('[data-price-per]').textContent.trim(),
          alt: c.querySelector('[data-price-alt]').textContent.trim(),
          label: c.querySelector('[data-cta-label]').textContent.trim(),
          href: cta.getAttribute('href'),
          state: cta.getAttribute('data-checkout-state'),
          target: cta.getAttribute('target'),
          h: Math.round(cta.getBoundingClientRect().height),
        };
      });
    }""")


def check_period(cards, period, failures, where):
    for c in cards:
        amount, per = EXPECTED[c["key"]][period]
        if c["amount"] != amount or c["per"] != per:
            failures.append("%s %s: %s shows %s%s, expected %s%s"
                            % (where, period, c["key"], c["amount"], c["per"], amount, per))
        if c["state"] != "request":
            failures.append("%s %s: %s is %r, expected an activation request"
                            % (where, period, c["key"], c["state"]))
        if "billing=" + period not in c["href"] or "plan=" not in c["href"]:
            failures.append("%s %s: %s falls back to %r without the plan and period"
                            % (where, period, c["key"], c["href"]))
        if not c["href"].startswith("contact.html?"):
            failures.append("%s %s: %s dead-ends at %r" % (where, period, c["key"], c["href"]))
        if c["target"]:
            failures.append("%s %s: %s opens a new tab for an in-site request" % (where, period, c["key"]))
        if c["h"] < MIN_TAP:
            failures.append("%s %s: %s button is %dpx tall" % (where, period, c["key"], c["h"]))


def main():
    OUT.mkdir(exist_ok=True)
    report = {}
    failures = []
    base = "http://localhost:%d" % PORT

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for w in WIDTHS + [1440]:
            mobile = w in WIDTHS
            page = browser.new_page(viewport={"width": w, "height": 740 if mobile else 900},
                                    device_scale_factor=2 if mobile else 1,
                                    is_mobile=mobile, has_touch=mobile)
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.goto(base + "/corporate-pricing.html", wait_until="load")
            page.wait_for_timeout(900)

            entry = {"errors": errors}
            where = "%dpx" % w

            monthly = read_cards(page)
            if len(monthly) != 4:
                failures.append("%s: found %d team cards, expected 4" % (where, len(monthly)))
            check_period(monthly, "monthly", failures, where)

            page.click('[data-testid="billing-annual"]')
            page.wait_for_timeout(250)
            annual = read_cards(page)
            check_period(annual, "annual", failures, where)
            entry["billing_state_annual"] = page.text_content("[data-billing-state]").strip()

            page.click('[data-testid="billing-monthly"]')
            page.wait_for_timeout(250)
            check_period(read_cards(page), "monthly", failures, where + " (back)")

            pilot = page.evaluate("""() => {
              const a = document.querySelector('[data-testid="cta-pilot"]');
              const e = document.querySelector('[data-testid="cta-enterprise"]');
              return {
                pilotHref: a.getAttribute('href'), pilotTarget: a.getAttribute('target'),
                pilotState: a.getAttribute('data-checkout-state'),
                pilotH: Math.round(a.getBoundingClientRect().height),
                entHref: e.getAttribute('href'), entState: e.getAttribute('data-checkout-state'),
                entText: e.textContent.trim(), entH: Math.round(e.getBoundingClientRect().height),
              };
            }""")
            entry.update(pilot)
            if pilot["pilotHref"] != PILOT_URL:
                failures.append("%s: pilot CTA points at %r" % (where, pilot["pilotHref"]))
            if pilot["pilotState"] != "live" or pilot["pilotTarget"] != "_blank":
                failures.append("%s: pilot CTA is not a live new-tab checkout" % where)
            if pilot["entText"] != "Request Corporate Pricing":
                failures.append("%s: enterprise CTA reads %r" % (where, pilot["entText"]))
            if not pilot["entHref"].startswith("contact.html?plan=Enterprise"):
                failures.append("%s: enterprise CTA dead-ends at %r" % (where, pilot["entHref"]))
            for name in ("pilotH", "entH"):
                if pilot[name] < MIN_TAP:
                    failures.append("%s: %s is %dpx tall" % (where, name, pilot[name]))

            toggle_h = page.evaluate(
                """() => [...document.querySelectorAll('[data-billing]')]
                     .map(b => Math.round(b.getBoundingClientRect().height))""")
            entry["toggle_heights"] = toggle_h
            if min(toggle_h) < MIN_TAP:
                failures.append("%s: billing toggle is %dpx tall" % (where, min(toggle_h)))

            entry["h_overflow"] = page.evaluate(
                "() => document.documentElement.scrollWidth > window.innerWidth + 1")
            if entry["h_overflow"]:
                failures.append("%s: horizontal overflow" % where)

            appbar = page.evaluate("""() => {
              const a = document.querySelector('.appbar__btn');
              return a && { href: a.getAttribute('href'),
                            label: a.querySelector('.appbar__label').textContent.trim() };
            }""")
            entry["appbar"] = appbar
            if not appbar or appbar["label"] != "Try the New Mobile App":
                failures.append("%s: the persistent app CTA is missing or reworded" % where)

            if errors:
                failures.append("%s: console/page errors: %s" % (where, errors[:3]))

            page.screenshot(path=str(OUT / ("%s_corporate_%d.png" % (LABEL, w))))
            page.evaluate("() => document.querySelector('#team-plans').scrollIntoView()")
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUT / ("%s_corporate_%d_plans.png" % (LABEL, w))))
            report[where] = entry
            page.close()

        # The fallback has to arrive somewhere that knows what was asked for.
        page = browser.new_page(viewport={"width": 360, "height": 740},
                                device_scale_factor=2, is_mobile=True, has_touch=True)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base + "/contact.html?plan=Team+10&billing=annual&ref=corporate-pricing",
                  wait_until="load")
        page.wait_for_timeout(600)
        pick = page.evaluate("""() => {
          const n = document.querySelector('[data-plan-pick]');
          const r = document.querySelector('input[name="role"]:checked');
          return { hidden: n.hidden, text: n.textContent.trim(),
                   message: document.getElementById('c-message').value,
                   role: r && r.value };
        }""")
        report["contact_fallback"] = pick
        if pick["hidden"]:
            failures.append("contact fallback: the plan notice stayed hidden")
        if "Team 10" not in pick["text"] or "billed annually" not in pick["text"]:
            failures.append("contact fallback: notice reads %r" % pick["text"])
        if "Team 10" not in pick["message"]:
            failures.append("contact fallback: the message was not seeded with the plan")
        if errors:
            failures.append("contact fallback: %s" % errors[:3])
        page.screenshot(path=str(OUT / ("%s_contact_prefill.png" % LABEL)))
        page.close()
        browser.close()

    print(json.dumps(report, indent=2))
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nPASS: prices, targets, tap targets and the contact fallback all hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
