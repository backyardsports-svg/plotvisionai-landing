#!/usr/bin/env python3
"""Static forbidden-browser-API scan, mirroring the deploy gate.

The gate is a token match, not a parse, so a mention inside a comment or a
string fails it just as a real call does. Run before deploying:

    python3 scan_forbidden_apis.py
"""
import os
import re
import sys

FORBIDDEN = [
    "localStorage", "sessionStorage", "indexedDB", "openDatabase", "webkitStorageInfo",
    "requestPointerLock", "exitPointerLock", "pointerLockElement",
    "requestFullscreen", "exitFullscreen", "fullscreenElement",
    "webkitRequestFullscreen", "webkitRequestFullScreen", "mozRequestFullScreen",
    "msRequestFullscreen", "webkitFullscreenElement", "mozFullScreenElement",
    "msFullscreenElement", "webkitExitFullscreen", "mozCancelFullScreen",
]
SKIP_DIRS = {".git", "qa_shots", ".vercel", "node_modules"}
EXTS = (".js", ".html", ".json", ".xml", ".webmanifest", ".css", ".svg")

pattern = re.compile("|".join(re.escape(t) for t in FORBIDDEN), re.I)


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    hits = []
    scanned = 0
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            if not name.endswith(EXTS):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, root_dir)
            scanned += 1
            with open(path, encoding="utf-8", errors="replace") as fh:
                for lineno, line in enumerate(fh, 1):
                    for m in pattern.finditer(line):
                        hits.append(f"{rel}:{lineno}: {m.group(0)}  |  {line.strip()[:90]}")

    print(f"scanned {scanned} shipped file(s)")
    if hits:
        print("FORBIDDEN API HITS:")
        for h in hits:
            print("  " + h)
        return 1
    print("OK: no forbidden browser API access in shipped files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
