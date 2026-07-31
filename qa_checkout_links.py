#!/usr/bin/env python3
"""Check every buy button against checkout-links.js.

Markup keeps its own href so the site works without JavaScript, which means a
URL can drift out of step with the config. This fails if that happens, if a
button names a key the config does not define, or if an unreleased plan points
somewhere that would dead-end.

    python3 qa_checkout_links.py
"""
import glob
import json
import re
import sys

CONTACT_ROUTE = "contact.html"


def load_config():
    src = open("checkout-links.js", encoding="utf-8").read()
    body = src[src.index("{", src.index("window.PV_CHECKOUT")):src.rindex("}") + 1]
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    body = re.sub(r"(?m)^\s*//.*$", "", body)
    body = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', body)
    body = re.sub(r",(\s*[}\]])", r"\1", body)
    return json.loads(body)


def main():
    cfg = load_config()
    links = cfg["links"]
    failures = []
    seen = set()

    tag = re.compile(r"<a\b[^>]*>", re.I)
    for path in sorted(glob.glob("*.html")):
        html = open(path, encoding="utf-8").read()
        for m in tag.finditer(html):
            el = m.group(0)
            key = re.search(r'data-checkout="([^"]+)"', el)
            plan = re.search(r'data-checkout-plan="([^"]+)"', el)
            href = re.search(r'href="([^"]*)"', el)
            if not (key or plan) or not href:
                continue
            href = href.group(1)

            # A toggled card starts on monthly; that is the state in the markup.
            name = key.group(1) if key else plan.group(1) + "_monthly"
            seen.add(name)
            if name not in links:
                failures.append("%s: data-checkout %r is not in checkout-links.js" % (path, name))
                continue

            url = links[name]
            if url and href != url:
                failures.append("%s: %s href is %s but the config says %s" % (path, name, href, url))
            if not url and not href.startswith(CONTACT_ROUTE + "?"):
                failures.append(
                    "%s: %s has no Payment Link, so its href must be a pre-filled %s request, not %r"
                    % (path, name, CONTACT_ROUTE, href))
            if not url and "plan=" not in href:
                failures.append("%s: %s fallback does not pre-select a plan" % (path, name))

    for name, url in sorted(links.items()):
        state = "live" if url else "request"
        print("  %-16s %-8s %s" % (name, state, url or CONTACT_ROUTE + " fallback"))
    print("keys referenced by the pages: %d of %d" % (len(seen), len(links)))

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nPASS: every buy button matches checkout-links.js")
    return 0


if __name__ == "__main__":
    sys.exit(main())
