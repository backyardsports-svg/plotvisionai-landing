# PlotVisionAI marketing site review

Static HTML/CSS/JS landing site for [landscapedesignsonline.com](https://www.landscapedesignsonline.com) (PlotVisionAI). Keep reviews light: logic and syntax only.

## SEO

- Canonicals should point at `https://www.landscapedesignsonline.com` (www, not apex, not vercel.app).
- `robots.txt` Host and Sitemap should stay on www. `sitemap.xml` should list www URLs only — never preview hosts.
- Production www stays indexable except `login.html` (`noindex, follow`).
- `*.vercel.app` aliases must remain `X-Robots-Tag: noindex` so preview hosts are not indexed.
- Do not drop GA4 `G-GVT2M7WT6J`.

## Links and titles

- Flag broken internal links, redirects that 404, and CTAs that no longer reach getplotvisionai.com.
- Visualizer pages (`patios.html`, `fencing.html`, `retaining-walls.html`, `backyard-sports-center.html`) must keep their visualizer search-intent titles.
