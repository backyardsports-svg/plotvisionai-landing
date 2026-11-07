#!/usr/bin/env python3
"""Public phone regression check.

Every shipped HTML page must publish one Caroline OsmO number:
visible (949) 876-8913, tel:+19498768913, and schema telephone
+1-949-876-8913. The retired public line and the personal line must
not appear in shipped text. Active tracking-vendor script, pixel, or
form hooks must not appear. The existing Supabase email intake and
preview signup endpoints must stay in place.

    python3 qa_public_phone.py
"""
import base64
import glob
import json
import os
import re
import sys

DISPLAY = "(949) 876-8913"
TEL = "tel:+19498768913"
SCHEMA_TEL = "+1-949-876-8913"
CONTACT_ENDPOINT = "https://dtryhdykdbncxxwgqmta.supabase.co/functions/v1/submit-contact-intake"
SIGNUP_ENDPOINT = "https://dtryhdykdbncxxwgqmta.supabase.co/functions/v1/register-preview-signup"

# Decoded at runtime so this file does not store retired or personal lines.
RETIRED_PUBLIC = base64.b64decode("MzE5NDIyNzA2MA==").decode("ascii")
PERSONAL = base64.b64decode("MzE5ODk5NDMyMg==").decode("ascii")
VENDOR = base64.b64decode("Y2FsbHNjYWxlcg==").decode("ascii")

TEXT_EXTS = {
    ".html", ".js", ".css", ".json", ".xml", ".txt", ".md", ".py",
    ".svg", ".webmanifest", ".vtt",
}
SKIP_DIRS = {".git", "qa_shots", ".vercel", "node_modules"}


def phone_pattern(ten_digits):
    area, prefix, line = ten_digits[:3], ten_digits[3:6], ten_digits[6:]
    sep = r"[\s.\-]*"
    return re.compile(
        rf"(?<!\d)(?:\+?1{sep})?\(?{area}\)?{sep}{prefix}{sep}{line}(?!\d)"
    )


RETIRED_RE = phone_pattern(RETIRED_PUBLIC)
PERSONAL_RE = phone_pattern(PERSONAL)
VENDOR_RE = re.compile(VENDOR[:4] + r"[\s_\-]?" + VENDOR[4:], re.I)
TEL_RE = re.compile(r'href="(tel:[^"]+)"', re.I)
LDJSON_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>', re.I | re.S
)
FORM_RE = re.compile(r"<form\b([^>]*)>", re.I)


def iter_text_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if ext not in TEXT_EXTS:
                continue
            yield os.path.join(dirpath, name)


def walk_nodes(node, found):
    if isinstance(node, dict):
        if "telephone" in node:
            found.append(node.get("telephone"))
        for value in node.values():
            walk_nodes(value, found)
    elif isinstance(node, list):
        for item in node:
            walk_nodes(item, found)


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    failures = []

    for path in iter_text_files(root):
        rel = os.path.relpath(path, root)
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for lineno, line in enumerate(text.splitlines(), 1):
            if RETIRED_RE.search(line):
                failures.append(f"{rel}:{lineno}: retired public number")
            if PERSONAL_RE.search(line):
                failures.append(f"{rel}:{lineno}: personal number")
            if VENDOR_RE.search(line):
                failures.append(f"{rel}:{lineno}: {VENDOR} dependency")

    html_paths = sorted(glob.glob(os.path.join(root, "*.html")))
    if not html_paths:
        failures.append("no HTML files found")

    for path in html_paths:
        rel = os.path.basename(path)
        html = open(path, encoding="utf-8").read()
        if html.count(DISPLAY) != 1:
            failures.append(f"{rel}: expected one visible {DISPLAY}")
        tels = TEL_RE.findall(html)
        if tels != [TEL]:
            failures.append(f"{rel}: tel links {tels!r}")
        blocks = LDJSON_RE.findall(html)
        telephones = []
        if not blocks:
            failures.append(f"{rel}: missing schema")
        for index, block in enumerate(blocks, 1):
            try:
                data = json.loads(block)
            except json.JSONDecodeError as exc:
                failures.append(f"{rel}: schema block {index} is invalid JSON ({exc})")
                continue
            walk_nodes(data, telephones)
        if telephones != [SCHEMA_TEL]:
            failures.append(f"{rel}: schema telephone {telephones!r}")
        for form in FORM_RE.findall(html):
            action = re.search(r'\baction="([^"]*)"', form, re.I)
            if action and action.group(1).strip():
                failures.append(f"{rel}: form action {action.group(1)!r}")

    config = open(os.path.join(root, "config.js"), encoding="utf-8").read()
    script = open(os.path.join(root, "script.js"), encoding="utf-8").read()
    if f'CONTACT_ENDPOINT: "{CONTACT_ENDPOINT}"' not in config:
        failures.append("config.js: contact intake endpoint changed")
    if f'SIGNUP_ENDPOINT: "{SIGNUP_ENDPOINT}"' not in config:
        failures.append("config.js: preview signup endpoint changed")
    if "fetch(contactCfg.CONTACT_ENDPOINT" not in script:
        failures.append("script.js: contact form no longer posts to CONTACT_ENDPOINT")
    if "fetch(cfg.SIGNUP_ENDPOINT" not in script:
        failures.append("script.js: preview signup no longer posts to SIGNUP_ENDPOINT")
    for page in ("contact.html", "index.html"):
        page_html = open(os.path.join(root, page), encoding="utf-8").read()
        if 'id="contact-form"' not in page_html:
            failures.append(f"{page}: contact form removed")
    preview = open(os.path.join(root, "free-preview.html"), encoding="utf-8").read()
    if 'id="preview-gate"' not in preview:
        failures.append("free-preview.html: preview signup form removed")

    print(f"checked {len(html_paths)} html page(s)")
    if failures:
        print("PUBLIC PHONE FAILURES:")
        for item in failures:
            print("  " + item)
        return 1
    print("OK: Caroline OsmO number only; no retired line, personal line, or tracking-vendor hook")
    return 0


if __name__ == "__main__":
    sys.exit(main())
