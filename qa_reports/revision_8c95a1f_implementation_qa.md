# Revision after 8c95a1f — implementation and QA

## Scope preserved
- The landing hero aerial media, sizing, crop, reveal, lighting transition, replay timing, CTA layout, and trace-removal implementation were not changed.
- The canonical app destination remains `https://plotvisionai-preview.pplx.app`.
- Corporate-pricing spacing fixes remain in place.

## Revision implementation
1. `index.html`
   - Adds a home-only `data-home-hero-cta` marker to drive contextual mobile CTA behavior without affecting interior routes.
2. `script.js`
   - Adds two `IntersectionObserver`-based state classes:
     - `concept-demo-in-view` while `#concept` is visible.
     - `home-hero-primary-away` when the landing hero primary CTA is no longer visible.
   - Includes a viewport/scroll fallback for browsers without `IntersectionObserver`.
3. `styles.css`
   - At desktop/tablet widths (48rem+), the persistent `.appbar` becomes `visibility:hidden`, opacity `0`, translated down, and non-interactive while `#concept` is in view. This removes the underlying click surface rather than relying on z-index.
   - On the mobile landing page only, the header CTA is initially hidden while the hero CTA is visible and appears after it leaves. The header retains its two-row height during the handoff; interior-page header CTAs remain unchanged.
   - The mobile landing `.appbar` is tucked so it never becomes a second app CTA in the same viewport.
   - At <=335px, the organic logo mark is 30px, wordmark is 15px, gap is 6.4px, trademark is suppressed, and header column gap is 12px. Menu remains a 56px, 16px-label control.

## Focused measurements
- Desktop 1024, 1280, 1440, and 1600: `.appbar` was visible outside `#concept`, hidden with `pointer-events:none` in `#concept`, then restored after leaving it.
- At the overlap-prone in-demo position, `elementFromPoint` returned `#ce-remove` and `#ce-undo` at every desktop width. Normal clicks removed and restored the selected element.
- Mobile home widths 320/360/430:
  - Menu height: 56px at every width; label 16px.
  - Header Try Free height: 52px and label 16px after the hero CTA leaves.
  - Hero Try PlotVisionAI Free height: 58.28px while visible.
  - Header height stays about 131.4px during the CTA handoff (no vertical layout jump).
  - Home appbar is hidden, eliminating a competing third app CTA.
  - Horizontal overflow: 0px in tested states.
  - Brand-to-Menu gutter: 12px at 320px; 8px at 360px and 430px.
- Interior `pricing.html` widths 320/360/430: header Try Free remains visible and 52px high; no horizontal overflow.

## Regression QA passed
- `python qa_production_audit_fixes.py`
  - concept controls hit-testing, click behavior, appbar restoration, mobile CTA handoff, interior header availability, no-trace replay checks, no page/console errors.
- `python qa_replay_and_app_links.py`
  - all 25 header, 25 menu, and 25 persistent app CTA sources resolve to canonical destination; intentional Mobile app/Get the app links still resolve to `download.html`; no tracing overlay on initial/replay; corporate spacing holds.
- `python qa_touch_targets.py`
  - mobile controls, pricing/request buttons, forms, replay controls, and menu controls meet requested dimensions at 320/360/430; no overflow/errors.
- `python qa_visual_and_navigation.py`
  - desktop/mobile initial/replay visual states and navigation passed.
- `python qa_corporate_pricing.py` and `python qa_checkout_links.py`
  - corporate text/spacing, tap targets, fallback behavior, and checkout link configuration passed.
- `node --check script.js`, `python -m py_compile ...`, and `git diff --check` passed.

## Visual artifacts
- `qa_shots/production_audit_desktop_1440_concept.png`
- `qa_shots/production_audit_mobile_320.png`
- `qa_shots/production_audit_mobile_360.png`
- `qa_shots/production_audit_mobile_430.png`
