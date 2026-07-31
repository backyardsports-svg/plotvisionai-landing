/* ==========================================================================
   PlotVisionAI launch page — progressive enhancement only.
   Everything on this page is readable and usable with JS disabled.
   ========================================================================== */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* --------------------------- footer year ------------------------------ */
  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  /* --------------------------- sticky header ---------------------------- */
  var header = document.getElementById("site-header");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("is-stuck", window.scrollY > 12);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* --------------- drawn-into-reality before/after reveal ---------------
   * Replaces the old draggable seam and the plain wipe. Each featured pair
   * plays one restrained sequence when it scrolls into view:
   *   1. trace  — organic topographic contours, bed/patio/court edges, tree
   *               canopies and lighting cones draw themselves over the before
   *               photo in the brand's circuit-eye line language;
   *   2. resolve — colour blooms outward from those traced zones until the
   *               photorealistic concept has fully replaced the before photo;
   *   3. settle  — the lines fade out, leaving the concept and a faint glow.
   * It never loops, it pauses off-screen, and it can be replayed on demand.
   * Under prefers-reduced-motion nothing animates: the pair stays as a static
   * side-by-side before/after with an instant, motion-free toggle.
   * ------------------------------------------------------------------- */
  var DRAW_MS = 2900;
  var DRAW_TRACE_END = 0.46;   // fraction of the sequence spent tracing
  var DRAW_BLOOM_FROM = 0.34;  // colour starts resolving while lines finish
  var DRAW_FADE_FROM = 0.66;   // lines begin to dissolve
  var DRAW_DELAY = 240;

  /* Line vocabularies. Coordinates are in a 100x62 grid stretched over the
     frame, so the traced shapes read as a design overlay on the photograph
     rather than a claim of pixel-exact survey lines. */
  var DRAW_PLANS = {
    yard: {
      lines: [
        "M0 35 C 20 31, 40 37, 60 33 S 86 29, 100 33",
        "M0 41 C 18 37, 38 43, 58 39 S 86 35, 100 39",
        "M0 47 C 20 43, 40 49, 60 45 S 86 41, 100 45",
        "M0 53 C 18 49, 38 55, 58 51 S 86 47, 100 51",
        "M0 58 C 20 54, 40 60, 60 56 S 86 52, 100 56",
        "M0 63 C 18 59, 38 65, 58 61 S 86 57, 100 61",
        "M27 47 L57 44 L63 55 L25 59 Z",
        "M40 38 h15 a3 3 0 0 1 0 6 h-15 a3 3 0 0 1 0 -6 z",
        "M67 41 L89 38 L93 49 L69 52 Z",
        "M78 39.5 L81 50.5"
      ],
      nodes: [[27, 47], [57, 44], [67, 41], [93, 49], [40, 38]]
    },
    grade: {
      lines: [
        "M0 27 C 20 24, 40 29, 60 26 S 86 22, 100 26",
        "M0 34 C 18 31, 38 36, 58 33 S 86 29, 100 33",
        "M0 41 C 20 38, 40 43, 60 40 S 86 36, 100 40",
        "M4 48 L62 42 L96 46",
        "M4 54 L62 48 L96 52",
        "M30 45 L44 44 L44 50 L30 51 Z",
        "M32 51 L46 50 L46 56 L32 57 Z",
        "M34 57 L48 56 L48 62 L34 62",
        "M64 43 L96 47 L96 53 L64 49 Z",
        "M10 44 L28 43"
      ],
      nodes: [[62, 42], [44, 44], [96, 47], [34, 57], [10, 44]]
    },
    court: {
      lines: [
        "M0 28 C 20 24, 40 30, 60 26 S 86 22, 100 26",
        "M0 36 C 18 32, 38 38, 58 34 S 86 30, 100 34",
        "M0 44 C 20 40, 40 46, 60 42 S 86 38, 100 42",
        "M0 52 C 18 48, 38 54, 58 50 S 86 46, 100 50",
        "M0 60 C 20 56, 40 62, 60 58 S 86 54, 100 58",
        "M17 44 L81 40 L91 57 L11 61 Z",
        "M39 42 L61 41 L65 54 L35 55 Z",
        "M49 48 a6 3 0 1 0 0.1 0",
        "M22 51 L85 47",
        "M17 44 V37 M49 41 V34 M81 40 V33"
      ],
      nodes: [[17, 44], [81, 40], [91, 57], [11, 61], [49, 34]]
    },
    lighting: {
      lines: [
        "M0 30 C 20 26, 40 32, 60 28 S 86 24, 100 28",
        "M0 38 C 18 34, 38 40, 58 36 S 86 32, 100 36",
        "M0 46 C 20 42, 40 48, 60 44 S 86 40, 100 44",
        "M0 54 C 18 50, 38 56, 58 52 S 86 48, 100 52",
        "M0 62 C 20 58, 40 64, 60 60 S 86 56, 100 60",
        "M2 58 C 20 52, 40 53, 58 48 S 86 43, 100 46",
        "M20 47 L13 62 L29 62 Z",
        "M46 44 L39 62 L54 62 Z",
        "M71 41 L65 58 L79 58 Z",
        "M90 38 L85 54 L96 54 Z"
      ],
      nodes: [[20, 47], [46, 44], [71, 41], [90, 38], [58, 48]]
    }
  };

  /* ------------------- traced hardscape plans (Replay only) -----------------
     Keyed by the Before photograph's filename. Coordinates were measured on a
     grid rendered over each photo: x spans 0..100 across the image width, y uses
     the same unit, and `h` is the image's height in those units. The overlay is
     sliced (not stretched) so these lines stay on the same roof edge, coping
     line or court boundary at every responsive crop. Only the hero and the major
     featured comparisons have a traced plan; anything else keeps its generic
     topographic plan on replay. ------------------------------------------- */
  var DETAIL_PLANS = {
    // Homepage hero: raised deck, gable roof, patio under the deck, curved bed
    // edge, and the footprint of the proposed pool terrace in the open lawn.
    "before-yard": {
      h: 56.2,
      lines: [
        "M17.5,17.2 L30.2,9.6 L37.8,3.4 L44.2,0.6",           // main gable slope
        "M44.2,0.6 L52.6,6.4 L57.8,12.4 L60.6,16.8",          // opposite gable slope
        "M19.4,17.6 L46,18.6 L60.4,19.4 L74.6,20.6",          // eave line across the facade
        "M60.6,16.8 L69.4,15.4 L78.6,19.8 L80.4,24.6",        // right wing roof
        "M19.2,22.4 L34,22.9 L45.6,23.3 L52.4,23.6",          // deck rail
        "M19,26.4 L34.2,27 L46,27.5 L55.2,27.9",              // deck fascia
        "M21.4,27 L21.4,33.2 M31.6,27.4 L31.6,33.6 M42.2,27.8 L42.2,33.9",  // deck posts
        "M19.6,33.2 L33,33.6 L45.4,34 L55.6,34.3",            // patio slab under the deck
        "M60.2,20 L60.2,32 L72,32.4 L72,20.6",                // screened porch box
        "M43.8,44.6 C52.4,41.8 60.8,38.2 68.4,34.4 C72.4,32.4 75.6,31.2 78.4,30.6",  // bed edge
        "M25.2,30.4 C30.6,31.6 36,32.4 41.6,32.8",            // walk to the lawn
        // proposed pool terrace, in the lawn off the deck
        "M25.6,31.4 L55.8,35 L52.4,45.4 L23.2,41.6 Z",
        "M28.4,33.6 L52.6,36.6 L50.2,43.4 L26.4,40.2 Z",
        "M0,49.8 C14,47.6 30,46.4 46,46.6 C62,46.8 78,48 92,50.2"  // lawn grade contour
      ],
      nodes: [[19.4, 17.6], [44.2, 0.6], [60.6, 16.8], [25.6, 31.4], [55.8, 35], [78.4, 30.6]]
    },
    // Backyard Sports Center: the finished court's own boundary, the pool
    // perimeter, patio edge, boulder wall and the two roof ridges.
    "court1-before": {
      h: 75,
      lines: [
        "M20.6,17.4 L31.8,7.6 L41.6,2.4 L52.4,7.4 L57.2,13.6",   // main gable
        "M14.8,20.6 L22.4,11.2 L29.6,17.4",                      // left wing ridge
        "M28.6,20.4 L45.2,17.6 L54.4,16.2",                      // eave line
        "M40.4,22.6 L48.6,29.4 L57,28.2",                        // lower roof plane
        "M26.4,36.8 L52.4,40.8 L58.6,49.2 L28.2,47.4 Z",         // patio slab
        "M52.4,44.6 L69.2,42.4 L73,52.4 L52.6,55.6 Z",         // pool perimeter
        "M54.4,46.4 L67.6,44.6 L70.6,50.8 L54.6,53.4 Z",             // pool waterline
        "M0,47.6 C6.4,45.4 13.6,44.6 20.6,45.4 C24.4,45.8 26.6,46.6 28,47.4",  // boulder wall
        "M0,30.4 L11.6,30.8 L11.6,40.2 L0,39.4",                 // side fence panel
        // court boundary as built, in the lower-left lawn
        "M3.6,50.6 L38.4,52.4 L33.2,71.8 L1.2,68.4 Z",
        "M7.2,53.6 L34.6,55 L30.4,68.6 L5.4,66 Z",
        "M20.6,54.2 L17.4,67.4",                                 // court centre line
        "M0,60.4 C10,58.6 22,57.8 34,58.4 C44,58.9 52,60 60,61.8"  // grade contour
      ],
      nodes: [[41.6, 2.4], [52.4, 44.6], [69.2, 42.4], [3.6, 50.6], [38.4, 52.4], [26.4, 36.8]]
    },
    // Retaining walls: existing wall courses, the concrete step treads, the
    // walk-to-drive joint and the house corner.
    "wall-grade-before": {
      h: 75,
      lines: [
        "M41,52.4 C50,49 58.6,45.4 66.8,41.6 C70.6,40 72.8,39.4 74.6,38.8",  // wall top course
        "M41.2,56.6 C50.4,53.2 59,49.4 67.6,45.6 C70.8,44.2 72.8,43.6 74.4,43.2",  // second course
        "M41.6,60.6 C51,57.2 59.4,53.4 68,49.6 C70.8,48.4 72.6,47.8 74,47.4",    // base course
        "M19.6,41.4 L45,40.6",                                  // top landing edge
        "M21.4,47.4 L46.4,46.2",                                  // tread 1
        "M24.4,53.4 L50.4,51.6",                                    // tread 2
        "M26.6,60.4 L54.4,57.6",                                    // tread 3
        "M29.6,68 L58.6,64.4",                                  // tread 4
        "M62,42 L78.4,47 L92.6,53 L100,57",               // walk to driveway joint
        "M0,43 L14,41.4 L26.4,40.4",                          // sidewalk edge at the lawn
        "M20.6,8.4 L20.6,38.6",                                   // house corner
        "M0,4.6 L10.4,7.4 L20.6,9.8",                             // eave line
        "M74.6,24.6 L88.4,22.4 L100,23.8",                        // garage roofline
        "M0,66.4 C10,64.4 20,63.4 29.6,63.8",                     // lawn grade
        "M31.4,71.4 L64.6,67.4",                                  // walk control joint, lower
        "M46.6,74.6 L48.4,60.6",                                  // walk transverse joint
        "M69.4,63.4 L86.4,69.6"                                   // driveway expansion joint
      ],
      nodes: [[41, 52.4], [74.6, 38.8], [19.6, 41.4], [58.6, 64.4], [20.6, 38.6]]
    },
    // Night lighting: the walk edges the fixtures wash, bed lines and the
    // facade line the uplights graze.
    "lighting-off": {
      h: 56.2,
      lines: [
        "M0,52.4 C9.6,45.6 20.4,39.4 31.6,34.6 C36.6,32.4 40.6,31 44.4,30.2",   // walk left edge
        "M17.6,56 C25.6,49.6 33.6,44 41.6,39.4 C47.6,36 53.6,33.6 59.4,32.2",   // walk right edge
        "M0,41.4 C8.4,36.6 17.6,32.6 27.4,29.6 C33.4,27.8 39.4,26.8 44.6,26.4", // bed edge, left
        "M45.6,30.4 C52.6,29 60.6,28.2 68.6,28 C78.4,27.8 88.6,28.4 98,29.6",   // patio joint, right
        "M0,29.6 L14.6,29.2 L29.4,28.8 L44.2,28.4",                             // facade base line
        "M9.6,0.4 L9.6,14.6 M20.4,0.4 L20.4,14.2",                              // window jambs
        "M0,15.4 L20.6,15.2 L33.4,15.6",                                        // facade band
        "M42.8,24.6 L42.8,39.4 M47.4,21.6 L47.4,30.4",                          // path fixtures
        "M56.4,31.6 C66.4,32.6 76.4,34 86.4,36.2"                               // lawn edge
      ],
      nodes: [[42.8, 24.6], [47.4, 21.6], [44.4, 30.2], [59.4, 32.2], [0, 29.6]]
    },
    // Existing concrete pad: fence line, net posts and the pad's own control
    // joints, which are what a pickleball layout has to respect.
    "bsc-vinyl-before": {
      h: 133.3,
      lines: [
        "M0,56.4 L24.6,55.6 L48.4,54.8 L72.6,54.2",              // fence base
        "M0,40.6 L24.4,39.6 L48.6,38.8 L72.4,38.4",              // fence top rail
        "M4.4,55.6 L4.4,40.4 M36.6,54.8 L36.6,39 M68.4,54.2 L68.4,38.4",   // fence posts
        "M2.4,58.4 L34.6,57 L69.4,55.6",                          // net line
        "M34.4,57.4 L34.4,49.6 M69,55.8 L69,47.4",                // net posts
        "M0,63.4 L36.4,61.6 L74.6,60",                            // pad joint 1
        "M0,76.6 L38.4,74 L78.6,71.4",                            // pad joint 2
        "M0,92.4 L40.6,88.6 L82.4,84.6",                          // pad joint 3
        "M0,112.6 L42.4,107.4 L86.6,101.6",                       // pad joint 4
        "M14.6,60.4 L6.4,133",                                    // long joint, left
        "M52.4,58.6 L64.6,133"                                    // long joint, right
      ],
      nodes: [[4.4, 55.6], [34.4, 57.4], [69, 55.8], [0, 92.4], [82.4, 84.6]]
    },
    // Open lawn: the patio it starts from, walk edges and bed lines that set
    // where a court can actually sit.
    "court3-before": {
      h: 75,
      lines: [
        "M0,70.4 L14.6,58.6 L26.4,49.4 L21.6,47.6 L4.4,60.6 L0,64.4",   // patio slab, near left
        "M0,44.6 L10.4,41.6 L20.6,39.4 L27.4,38.4",                      // walk edge, left
        "M27.6,26.4 L44.6,25.4 L61.4,24.6 L74.6,25.4",                   // upper terrace line
        "M74.6,25.4 L80.4,30.6 L84.6,38.4 L88.4,46.6",                   // bed edge, right
        "M20.4,28.6 L40.6,26.6 L58.4,25.6",                              // far walk line
        "M39.6,21.4 L54.6,20.6 L54.6,25.4 L39.6,26.2 Z",                 // built feature, far
        "M0,31.6 L12.4,30.4 L21.6,29.4",                                 // side walk, left
        "M22.6,47.4 L58.6,45.6 L64.4,66.4 L18.4,69.4 Z",                 // proposed court footprint
        "M26.4,49.6 L55.4,48.2 L60.4,64.2 L22.6,66.6 Z",                 // inner boundary
        "M40.6,48.8 L41.4,65.4"                                          // centre line
      ],
      nodes: [[22.6, 47.4], [58.6, 45.6], [64.4, 66.4], [27.6, 26.4], [74.6, 25.4]]
    }
  };

  var SVGNS = "http://www.w3.org/2000/svg";

  // Measures a path in rendered pixels. The overlay strokes are non-scaling
  // inside a stretched viewBox, so Chromium applies the dash pattern in device
  // space while getTotalLength() reports viewBox units. We sample the path and
  // scale each sample by the SVG's rendered box.
  function pixelLength(el, sx, sy) {
    var user = 0;
    try { user = el.getTotalLength ? el.getTotalLength() : 0; } catch (e) { user = 0; }
    if (!user) return 0;
    var steps = 48;
    var total = 0;
    var prev = null;
    for (var i = 0; i <= steps; i++) {
      var pt = el.getPointAtLength((user * i) / steps);
      var x = pt.x * sx;
      var y = pt.y * sy;
      if (prev) total += Math.sqrt((x - prev[0]) * (x - prev[0]) + (y - prev[1]) * (y - prev[1]));
      prev = [x, y];
    }
    return total || user;
  }

  function primeStrokes(overlay) {
    var box = overlay.svg.getBoundingClientRect();
    var vh = overlay.vh || 62;
    var sx = box.width ? box.width / 100 : 1;
    var sy = box.height ? box.height / vh : 1;
    if (overlay.sliced) {
      // slice scales uniformly, using whichever axis has to cover
      var s = Math.max(sx, sy);
      sx = s;
      sy = s;
    }
    overlay.scale = sx + "x" + sy;
    overlay.strokes.forEach(function (el) {
      var len = pixelLength(el, sx, sy);
      if (!len) len = 60;
      el._len = len;
      el.style.strokeDasharray = len + " " + (len + 2);
    });
  }

  function buildDrawOverlay(planName, detailKey) {
    // A detail plan is measured against the photograph itself, so it is fitted
    // the way the photograph is fitted (slice = object-fit: cover). A generic
    // topographic plan is decorative and keeps stretching to the stage box.
    var detail = detailKey ? DETAIL_PLANS[detailKey] : null;
    var plan = detail || DRAW_PLANS[planName] || DRAW_PLANS.yard;
    var vh = detail ? detail.h : 62;
    var svg = document.createElementNS(SVGNS, "svg");
    svg.setAttribute("class", detail ? "drawplan drawplan--traced" : "drawplan");
    svg.setAttribute("viewBox", "0 0 100 " + vh);
    svg.setAttribute("preserveAspectRatio", detail ? "xMidYMid slice" : "none");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");

    // Plan-sheet veil: calms the photograph while the plan is drawn on it.
    var veil = document.createElementNS(SVGNS, "rect");
    veil.setAttribute("class", "drawplan__veil");
    veil.setAttribute("x", "0");
    veil.setAttribute("y", "0");
    veil.setAttribute("width", "100");
    veil.setAttribute("height", String(vh));
    svg.appendChild(veil);

    var ink = document.createElementNS(SVGNS, "g");
    ink.setAttribute("class", "drawplan__ink");
    svg.appendChild(ink);

    var strokes = [];
    var nodes = [];

    plan.lines.forEach(function (d) {
      var path = document.createElementNS(SVGNS, "path");
      path.setAttribute("d", d);
      path.setAttribute("class", "drawplan__line");
      path.setAttribute("vector-effect", "non-scaling-stroke");
      ink.appendChild(path);
      strokes.push(path);
    });

    plan.nodes.forEach(function (pt) {
      var c = document.createElementNS(SVGNS, "circle");
      c.setAttribute("cx", pt[0]);
      c.setAttribute("cy", pt[1]);
      c.setAttribute("r", String(detail ? Math.max(0.5, vh / 90) : 0.6));
      c.setAttribute("class", "drawplan__node");
      c.setAttribute("vector-effect", "non-scaling-stroke");
      ink.appendChild(c);
      nodes.push(c);
    });

    nodes.forEach(function (el) { el.style.opacity = "0"; });

    return { svg: svg, strokes: strokes, nodes: nodes, vh: vh, sliced: !!detail, detail: !!detail };
  }

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function clamp01(v) {
    return v < 0 ? 0 : v > 1 ? 1 : v;
  }

  var drawFigures = Array.prototype.slice.call(
    document.querySelectorAll("[data-reveal-wipe], [data-reveal-draw]")
  );

  drawFigures.forEach(function (fig) {
    var isHero = fig.classList.contains("hero");
    var stage = isHero
      ? fig.querySelector(".hero__stage")
      : fig.querySelector(".cmp__stage") || fig.querySelector(".xfade__stage");
    if (!stage) return;

    var btn = fig.querySelector("[data-reveal-replay]") || fig.querySelector("[data-xfade-toggle]");
    var label = fig.querySelector("[data-reveal-label]") || fig.querySelector("[data-xfade-toggle-label]");
    var live = fig.querySelector("[data-reveal-state]") || fig.querySelector("[data-xfade-state]");
    var plan = fig.getAttribute("data-reveal-plan") || "yard";

    // The traced plan is chosen from the Before photograph's own filename, and
    // is only ever used for a visitor-initiated replay.
    var beforeImg = stage.querySelector('[class*="--before"] img') || stage.querySelector("img");
    var detailKey = null;
    if (beforeImg) {
      var src = beforeImg.getAttribute("src") || "";
      var base = src.split("/").pop().replace(/\.(jpg|jpeg|png|webp)$/i, "");
      if (DETAIL_PLANS[base]) detailKey = base;
    }
    var overlayIsDetail = false;

    var raf = null;
    var startedAt = 0;
    var elapsed = 0;
    var played = false;
    var visible = !("IntersectionObserver" in window);
    var overlay = null;
    var showingAfter = false;

    function say(msg) {
      if (live) live.textContent = msg;
    }

    function stop() {
      if (raf) { window.cancelAnimationFrame(raf); raf = null; }
    }

    function ensureOverlay(wantDetail) {
      var useDetail = !!(wantDetail && detailKey);
      if (overlay && overlayIsDetail === useDetail) return overlay;
      if (overlay && overlay.svg.parentNode) overlay.svg.parentNode.removeChild(overlay.svg);
      overlay = buildDrawOverlay(plan, useDetail ? detailKey : null);
      overlayIsDetail = useDetail;
      stage.appendChild(overlay.svg);
      primeStrokes(overlay);
      return overlay;
    }

    function paint(p) {
      var trace = clamp01(p / DRAW_TRACE_END);
      var bloom = clamp01((p - DRAW_BLOOM_FROM) / (0.94 - DRAW_BLOOM_FROM));
      var fade = clamp01((p - DRAW_FADE_FROM) / (1 - DRAW_FADE_FROM));

      fig.style.setProperty("--bloom", easeInOutCubic(bloom).toFixed(4));
      fig.style.setProperty("--glow", (1 - fade).toFixed(4));
      fig.style.setProperty("--lines", (1 - fade).toFixed(4));

      if (overlay) {
        // Each stroke is drawn quickly and in turn, so the plan reads as a hand
        // working across the yard rather than a dozen half-finished dashes.
        var n = overlay.strokes.length;
        var span = 0.34;
        var slot = n > 1 ? (1 - span) / (n - 1) : 0;
        overlay.strokes.forEach(function (el, i) {
          var local = clamp01((trace - i * slot) / span);
          el.style.strokeDashoffset = String(el._len * (1 - easeOutCubic(local)));
        });
        // Circuit nodes pop in on the junctions once their neighbourhood exists.
        var m = overlay.nodes.length;
        overlay.nodes.forEach(function (el, i) {
          var start = 0.35 + (m > 1 ? (i / (m - 1)) * 0.5 : 0);
          el.style.opacity = clamp01((trace - start) / 0.18).toFixed(3);
        });
      }
    }

    function frame(now) {
      if (!startedAt) startedAt = now;
      var p = Math.min(1, (elapsed + (now - startedAt)) / DRAW_MS);
      paint(p);
      if (p >= 1) {
        raf = null;
        elapsed = DRAW_MS;
        fig.classList.remove("is-drawing");
        fig.classList.add("is-resolved");
        showingAfter = true;
        say("Concept visualization resolved over the before photo. Use Replay reveal to watch it drawn again.");
        if (label) label.textContent = "Replay reveal";
        return;
      }
      raf = window.requestAnimationFrame(frame);
    }

    function play(fromStart, traced) {
      if (reduceMotion) return;
      stop();
      ensureOverlay(traced);
      primeStrokes(overlay);
      if (fromStart) { elapsed = 0; paint(0); }
      startedAt = 0;
      played = true;
      fig.classList.add("is-drawn", "is-drawing");
      fig.classList.remove("is-resolved");
      say(overlayIsDetail
        ? "Tracing the property lines \u2014 roof, wall, patio and court edges \u2014 then resolving them into the concept visualization."
        : "Drawing the design lines over the before photo, then resolving them into the concept visualization.");
      if (label) label.textContent = "Drawing\u2026";
      raf = window.requestAnimationFrame(frame);
    }

    function pause() {
      if (!raf) return;
      elapsed = Math.min(DRAW_MS, elapsed + (window.performance.now() - startedAt));
      stop();
      fig.classList.remove("is-drawing");
    }

    window.addEventListener("resize", function () {
      if (!overlay) return;
      primeStrokes(overlay);
      if (!raf) paint(elapsed / DRAW_MS);
    });

    if (reduceMotion) {
      fig.classList.add("is-static");
      fig.style.setProperty("--bloom", "1");
      say("Before photo on the left, concept visualization on the right. Animation is off.");
      if (label) label.textContent = "Show the concept";
      if (btn) {
        btn.hidden = false;
        btn.addEventListener("click", function () {
          showingAfter = !showingAfter;
          fig.classList.toggle("is-shown-after", showingAfter);
          if (label) label.textContent = showingAfter ? "Show the before photo" : "Show the concept";
          say(showingAfter
            ? "Concept visualization shown."
            : "Before photo and concept visualization shown side by side.");
        });
      }
      return;
    }

    fig.style.setProperty("--bloom", "0");
    fig.style.setProperty("--lines", "1");
    say("Before photo shown. The concept is drawn in when this scrolls into view.");

    if (btn) {
      btn.hidden = false;
      btn.setAttribute("aria-pressed", "false");
      if (label) label.textContent = "Replay reveal";
      btn.addEventListener("click", function () { play(true, true); });
    }

    if ("IntersectionObserver" in window) {
      var dio = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (en) {
            visible = en.isIntersecting;
            if (visible) {
              if (!played) {
                window.setTimeout(function () { if (visible && !played) play(true); }, DRAW_DELAY);
              } else if (elapsed < DRAW_MS) {
                play(false);
              }
            } else {
              pause();
            }
          });
        },
        { threshold: 0.35 }
      );
      dio.observe(fig);
    } else {
      window.setTimeout(function () { play(true); }, DRAW_DELAY);
    }
  });

  /* ---------------- share + desktop view (mobile affordances) -------------- */
  /* Two things phone visitors could not do before: share the page, and see the
     desktop layout. Desktop view rewrites the viewport meta, which is the only
     mechanism that actually reflows a responsive site on a phone. The mode is
     transient: currentView holds it for this page, and the ?view=desktop
     parameter carries it across navigations. The parameter was always the
     durable half - it is written into the URL and into every internal link
     below - so nothing is persisted by the browser. */
  (function () {
    var DESKTOP_WIDTH = 1280;
    var currentView = "mobile";

    var params = new URLSearchParams(window.location.search);
    var wantDesktop = params.get("view") === "desktop";

    var meta = document.querySelector('meta[name="viewport"]');
    var MOBILE_VIEWPORT = "width=device-width, initial-scale=1";

    function applyView(desktop, updateUrl) {
      if (meta) {
        meta.setAttribute(
          "content",
          desktop
            ? "width=" + DESKTOP_WIDTH + ", initial-scale=" + (window.screen && window.screen.width
                ? Math.max(0.25, Math.round((window.screen.width / DESKTOP_WIDTH) * 100) / 100)
                : 0.3)
            : MOBILE_VIEWPORT
        );
      }
      currentView = desktop ? "desktop" : "mobile";
      document.documentElement.setAttribute("data-view", currentView);
      Array.prototype.forEach.call(document.querySelectorAll("[data-view-toggle]"), function (b) {
        b.setAttribute("aria-pressed", desktop ? "true" : "false");
        var lab = b.querySelector("[data-view-label]");
        if (lab) lab.textContent = desktop ? "Return to mobile view" : "Desktop view";
      });
      if (updateUrl && window.history && window.history.replaceState) {
        var u = new URL(window.location.href);
        if (desktop) u.searchParams.set("view", "desktop");
        else u.searchParams.delete("view");
        window.history.replaceState({}, "", u.pathname + (u.search || "") + u.hash);
      }
      // Internal links carry the mode so routing keeps working either way.
      // Match by pathname, not by suffix: once the parameter is appended the
      // href no longer ends in .html, and the mode could not be switched off.
      Array.prototype.forEach.call(document.querySelectorAll("a[href]"), function (a) {
        var href = a.getAttribute("href") || "";
        if (/^(https?:)?\/\//.test(href) || href.charAt(0) === "#") return;
        if (!/\.html(\?|#|$)/.test(href)) return;
        var clean = href.replace(/([?&])view=desktop(&|$)/, "$1").replace(/[?&]$/, "");
        a.setAttribute("href", desktop ? clean + (clean.indexOf("?") > -1 ? "&" : "?") + "view=desktop" : clean);
      });
    }

    applyView(wantDesktop, false);

    Array.prototype.forEach.call(document.querySelectorAll("[data-view-toggle]"), function (btn) {
      btn.addEventListener("click", function () {
        var nowDesktop = currentView !== "desktop";
        applyView(nowDesktop, true);
        var bar = document.querySelector("[data-view-bar]");
        if (bar) bar.hidden = !nowDesktop;
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });

    var bar = document.querySelector("[data-view-bar]");
    if (bar) bar.hidden = currentView !== "desktop";

    /* -------------------------------- share ------------------------------- */
    function shareState(msg) {
      Array.prototype.forEach.call(document.querySelectorAll("[data-share-state]"), function (el) {
        el.textContent = msg;
        el.hidden = !msg;
      });
      if (msg) {
        window.setTimeout(function () {
          Array.prototype.forEach.call(document.querySelectorAll("[data-share-state]"), function (el) {
            el.textContent = "";
            el.hidden = true;
          });
        }, 4000);
      }
    }

    function copyFallback(url) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(
          function () { shareState("Link copied to your clipboard."); },
          function () { manualFallback(url); }
        );
        return;
      }
      manualFallback(url);
    }

    function manualFallback(url) {
      // Last resort: put the link in a field, selected, so it can be copied by hand.
      var host = document.querySelector("[data-share-manual]");
      if (!host) { shareState("Copy this link: " + url); return; }
      host.hidden = false;
      var input = host.querySelector("input");
      if (input) {
        input.value = url;
        input.focus();
        input.select();
      }
      shareState("Copy the link below to share the site.");
    }

    Array.prototype.forEach.call(document.querySelectorAll("[data-share]"), function (btn) {
      btn.addEventListener("click", function () {
        var url = window.location.href.split("?")[0];
        var data = {
          title: "PlotVisionAI",
          text: "PlotVisionAI - AI landscape visualization and concept design tool.",
          url: url
        };
        if (navigator.share) {
          navigator.share(data).then(
            function () { shareState("Thanks for sharing."); },
            function (err) {
              if (err && err.name === "AbortError") { shareState(""); return; }
              copyFallback(url);
            }
          );
          return;
        }
        copyFallback(url);
      });
    });

    /* --------------------- 'Share This Page' (top header) ----------------- */
    /* Separate from the 'Share PlotVisionAI' site-level control: this one always
       shares the page the visitor is actually on, using its canonical URL. */
    var pageFlash = document.querySelector("[data-share-page-flash]");
    var pageMsg = document.querySelector("[data-share-page-state]");
    var pageManual = document.querySelector("[data-share-page-manual]");
    var pageFlashTimer = null;

    function pageState(msg, keepOpen) {
      if (!pageMsg || !pageFlash) return;
      pageMsg.textContent = msg;
      pageFlash.hidden = !msg;
      if (pageFlashTimer) window.clearTimeout(pageFlashTimer);
      if (msg && !keepOpen) {
        pageFlashTimer = window.setTimeout(function () {
          pageMsg.textContent = "";
          pageFlash.hidden = true;
          if (pageManual) pageManual.hidden = true;
        }, 5000);
      }
      if (!msg && pageManual) pageManual.hidden = true;
    }

    function pageUrl() {
      var link = document.querySelector('link[rel="canonical"]');
      if (link && link.href) return link.href;
      return window.location.href.split("?")[0].split("#")[0];
    }

    function pageManualFallback(url) {
      if (!pageManual) { pageState("Copy this link: " + url, true); return; }
      pageManual.hidden = false;
      var input = pageManual.querySelector("input");
      pageState("Copy the link below to share this page.", true);
      if (input) {
        input.value = url;
        input.focus();
        input.select();
      }
    }

    function pageCopy(url) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(
          function () { pageState("Link to this page copied to your clipboard."); },
          function () { pageManualFallback(url); }
        );
        return;
      }
      pageManualFallback(url);
    }

    Array.prototype.forEach.call(document.querySelectorAll("[data-share-page]"), function (btn) {
      btn.addEventListener("click", function () {
        var url = pageUrl();
        var title = (document.title || "PlotVisionAI").replace(/\s*\|\s*PlotVisionAI\s*$/, "");
        var desc = document.querySelector('meta[name="description"]');
        var data = {
          title: title,
          text: desc && desc.content ? desc.content : title,
          url: url
        };
        if (navigator.share) {
          btn.setAttribute("aria-busy", "true");
          navigator.share(data).then(
            function () {
              btn.removeAttribute("aria-busy");
              pageState("Thanks for sharing this page.");
            },
            function (err) {
              btn.removeAttribute("aria-busy");
              if (err && err.name === "AbortError") { pageState(""); return; }
              pageCopy(url);
            }
          );
          return;
        }
        pageCopy(url);
      });
    });
  })();

  /* ------------------------- reveal on scroll --------------------------- */
  var revealables = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window) || reduceMotion) {
    revealables.forEach(function (el) {
      el.classList.add("is-in");
    });
  } else {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.08 }
    );
    revealables.forEach(function (el) {
      io.observe(el);
    });
  }

  /* --------------------- shared roving-tab behaviour -------------------- */
  function wireTablist(tabs, onSelect, orientationVertical) {
    if (!tabs.length) return;

    function select(index, focus) {
      tabs.forEach(function (tab, i) {
        var on = i === index;
        tab.setAttribute("aria-selected", on ? "true" : "false");
        tab.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(tab.getAttribute("aria-controls"));
        if (panel) panel.hidden = !on;
      });
      if (focus) tabs[index].focus();
      onSelect(tabs[index], index);
    }

    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function () {
        select(i, false);
      });
      tab.addEventListener("keydown", function (event) {
        var next = null;
        var prevKey = orientationVertical ? "ArrowUp" : "ArrowLeft";
        var nextKey = orientationVertical ? "ArrowDown" : "ArrowRight";
        if (event.key === nextKey) next = (i + 1) % tabs.length;
        else if (event.key === prevKey) next = (i - 1 + tabs.length) % tabs.length;
        else if (event.key === "Home") next = 0;
        else if (event.key === "End") next = tabs.length - 1;
        if (next === null) return;
        event.preventDefault();
        select(next, true);
      });
    });

    // Normalise initial state from markup.
    var initial = 0;
    tabs.forEach(function (tab, i) {
      if (tab.getAttribute("aria-selected") === "true") initial = i;
    });
    select(initial, false);
  }

  /* --------------------------- editor preview -------------------------- */
  var stageTabs = Array.prototype.slice.call(document.querySelectorAll(".stage"));
  var segs = Array.prototype.slice.call(document.querySelectorAll(".seg"));
  var layers = Array.prototype.slice.call(document.querySelectorAll(".canvas__img"));
  var pins = document.getElementById("canvas-pins");
  var canvasTitle = document.getElementById("canvas-title");
  var canvasStamp = document.getElementById("canvas-stamp");

  var TITLES = {
    before: "Site photo — aerial frame, existing conditions",
    after: "Generated concept — evening lighting pass",
  };
  var STAMPS = { before: "Original · unedited", after: "Concept v3 · sample" };

  function showLayer(which) {
    layers.forEach(function (img) {
      img.classList.toggle("is-shown", img.dataset.layer === which);
    });
    segs.forEach(function (seg) {
      seg.setAttribute("aria-pressed", seg.dataset.compare === which ? "true" : "false");
    });
    if (canvasTitle) canvasTitle.textContent = TITLES[which];
    if (canvasStamp) canvasStamp.textContent = STAMPS[which];
    if (pins && which === "before") pins.hidden = true;
  }

  segs.forEach(function (seg) {
    seg.addEventListener("click", function () {
      showLayer(seg.dataset.compare);
    });
  });

  if (stageTabs.length) {
    wireTablist(
      stageTabs,
      function (tab) {
        showLayer(tab.dataset.view === "after" ? "after" : "before");
        if (pins) pins.hidden = tab.dataset.pins !== "on";
      },
      window.matchMedia("(min-width: 56rem)").matches
    );
  }

  // Pins: tap to toggle on touch, hover/focus handled in CSS.
  Array.prototype.forEach.call(document.querySelectorAll(".pin"), function (pin) {
    pin.addEventListener("click", function () {
      var open = pin.classList.contains("is-open");
      Array.prototype.forEach.call(document.querySelectorAll(".pin"), function (p) {
        p.classList.remove("is-open");
      });
      if (!open) pin.classList.add("is-open");
    });
  });

  /* ---------------------------- sports viewer -------------------------- */
  var sportTabs = Array.prototype.slice.call(document.querySelectorAll(".sport"));
  if (sportTabs.length) wireTablist(sportTabs, function () {}, false);

  /* --------------------------- concept editor -------------------------- */
  var layer = document.getElementById("ce-layer");
  var status = document.getElementById("ce-status");
  var selName = document.getElementById("ce-selname");
  var log = document.getElementById("ce-log");

  if (layer && status && selName && log) {
    var MATERIALS = {
      steps: ["stone", "poured concrete", "limestone slab"],
      plants: ["Japanese maple", "hydrangea mass", "ornamental grass"],
      patio: ["clay paver", "bluestone", "stamped concrete"],
      wall: ["limestone block", "wall block", "boulder"],
      lighting: ["warm uplight", "path light", "wash light"],
      court: ["forest green tile", "slate grey tile", "blue tile"],
    };
    var LABELS = {
      steps: "Steps",
      plants: "Plants",
      patio: "Patio",
      wall: "Wall",
      lighting: "Lighting",
      court: "Court",
    };

    var items = [];
    var selected = null;
    var history = [];
    var uid = 0;

    function announce(text) {
      status.textContent = text;
    }

    function record(text) {
      var empty = log.querySelector(".ce__logempty");
      if (empty) empty.remove();
      var li = document.createElement("li");
      var time = document.createElement("time");
      var now = new Date();
      time.textContent =
        String(now.getHours()).padStart(2, "0") + ":" + String(now.getMinutes()).padStart(2, "0");
      li.appendChild(time);
      li.appendChild(document.createTextNode(text));
      log.insertBefore(li, log.firstChild);
      while (log.children.length > 12) log.removeChild(log.lastChild);
    }

    function paint(item) {
      item.el.style.setProperty("--x", item.x + "%");
      item.el.style.setProperty("--y", item.y + "%");
      item.el.style.setProperty("--r", item.r + "deg");
      item.el.innerHTML = "";
      var strong = document.createElement("span");
      strong.textContent = LABELS[item.kind];
      var small = document.createElement("b");
      small.textContent = " · " + item.material;
      item.el.appendChild(strong);
      item.el.appendChild(small);
      item.el.setAttribute(
        "aria-label",
        LABELS[item.kind] + ", " + item.material + ", rotated " + item.r + " degrees. Select to edit."
      );
    }

    function describe(item) {
      return LABELS[item.kind] + " — " + item.material + ", " + item.r + "°";
    }

    function select(item) {
      selected = item;
      items.forEach(function (i) {
        i.el.classList.toggle("is-sel", i === item);
        i.el.setAttribute("aria-pressed", i === item ? "true" : "false");
      });
      selName.textContent = item ? describe(item) : "Nothing selected";
    }

    function add(kind, x, y, quiet) {
      uid += 1;
      var el = document.createElement("button");
      el.type = "button";
      el.className = "ce__el";
      el.id = "ce-el-" + uid;
      var item = { id: uid, kind: kind, x: x, y: y, r: 0, material: MATERIALS[kind][0], el: el };
      el.addEventListener("click", function () {
        select(item);
        announce(describe(item) + " selected.");
      });
      layer.appendChild(el);
      items.push(item);
      paint(item);
      select(item);
      if (!quiet) {
        announce("Added " + LABELS[kind].toLowerCase() + ".");
        record("Added " + LABELS[kind].toLowerCase() + " (" + item.material + ")");
        history.push({ type: "add", id: item.id });
      }
      return item;
    }

    function findIndex(id) {
      for (var i = 0; i < items.length; i += 1) if (items[i].id === id) return i;
      return -1;
    }

    function removeItem(item, quiet) {
      var idx = findIndex(item.id);
      if (idx < 0) return;
      items.splice(idx, 1);
      item.el.remove();
      if (selected === item) select(items[items.length - 1] || null);
      if (!quiet) {
        announce("Removed " + LABELS[item.kind].toLowerCase() + ".");
        record("Removed " + LABELS[item.kind].toLowerCase());
        history.push({ type: "remove", snapshot: item });
      }
    }

    function move(dir) {
      if (!selected) return;
      var step = 4;
      if (dir === "up") selected.y = Math.max(8, selected.y - step);
      if (dir === "down") selected.y = Math.min(92, selected.y + step);
      if (dir === "left") selected.x = Math.max(8, selected.x - step);
      if (dir === "right") selected.x = Math.min(92, selected.x + step);
      paint(selected);
      selName.textContent = describe(selected);
      announce("Moved " + LABELS[selected.kind].toLowerCase() + " " + dir + ".");
      record("Moved " + LABELS[selected.kind].toLowerCase() + " " + dir);
      history.push({ type: "move", id: selected.id, dir: dir });
    }

    function rotate() {
      if (!selected) return;
      selected.r = (selected.r + 90) % 360;
      paint(selected);
      selName.textContent = describe(selected);
      announce(LABELS[selected.kind] + " rotated to " + selected.r + " degrees.");
      record(LABELS[selected.kind] + " rotated to " + selected.r + "°");
      history.push({ type: "rotate", id: selected.id });
    }

    function replace() {
      if (!selected) return;
      var options = MATERIALS[selected.kind];
      var at = options.indexOf(selected.material);
      var previous = selected.material;
      selected.material = options[(at + 1) % options.length];
      paint(selected);
      selName.textContent = describe(selected);
      announce(LABELS[selected.kind] + " material changed to " + selected.material + ".");
      record(LABELS[selected.kind] + ": " + previous + " → " + selected.material);
      history.push({ type: "material", id: selected.id, previous: previous });
    }

    function undo() {
      var last = history.pop();
      if (!last) {
        announce("Nothing left to undo.");
        return;
      }
      var idx;
      if (last.type === "add") {
        idx = findIndex(last.id);
        if (idx > -1) removeItem(items[idx], true);
        announce("Undid the last addition.");
      } else if (last.type === "remove") {
        var s = last.snapshot;
        var restored = add(s.kind, s.x, s.y, true);
        restored.r = s.r;
        restored.material = s.material;
        paint(restored);
        selName.textContent = describe(restored);
        announce("Restored " + LABELS[s.kind].toLowerCase() + ".");
      } else if (last.type === "rotate") {
        idx = findIndex(last.id);
        if (idx > -1) {
          items[idx].r = (items[idx].r + 270) % 360;
          paint(items[idx]);
          select(items[idx]);
        }
        announce("Undid the rotation.");
      } else if (last.type === "material") {
        idx = findIndex(last.id);
        if (idx > -1) {
          items[idx].material = last.previous;
          paint(items[idx]);
          select(items[idx]);
        }
        announce("Undid the material change.");
      } else if (last.type === "move") {
        idx = findIndex(last.id);
        if (idx > -1) {
          var back = { up: "down", down: "up", left: "right", right: "left" }[last.dir];
          var item = items[idx];
          if (back === "up") item.y = Math.max(8, item.y - 4);
          if (back === "down") item.y = Math.min(92, item.y + 4);
          if (back === "left") item.x = Math.max(8, item.x - 4);
          if (back === "right") item.x = Math.min(92, item.x + 4);
          paint(item);
          select(item);
        }
        announce("Undid the move.");
      }
      record("Undo");
    }

    // Seed the demo with elements that match the concept render.
    add("steps", 44, 66, true);
    add("plants", 26, 58, true);
    add("lighting", 72, 48, true);
    select(items[0]);
    announce("Stone steps selected — nothing changed yet.");

    Array.prototype.forEach.call(document.querySelectorAll("[data-add]"), function (btn) {
      btn.addEventListener("click", function () {
        add(btn.dataset.add, 30 + Math.round(Math.random() * 40), 40 + Math.round(Math.random() * 30));
      });
    });

    Array.prototype.forEach.call(document.querySelectorAll("[data-move]"), function (btn) {
      btn.addEventListener("click", function () {
        move(btn.dataset.move);
      });
    });

    var rotateBtn = document.getElementById("ce-rotate");
    var replaceBtn = document.getElementById("ce-replace");
    var removeBtn = document.getElementById("ce-remove");
    var undoBtn = document.getElementById("ce-undo");
    if (rotateBtn) rotateBtn.addEventListener("click", rotate);
    if (replaceBtn) replaceBtn.addEventListener("click", replace);
    if (removeBtn)
      removeBtn.addEventListener("click", function () {
        if (selected) removeItem(selected);
      });
    if (undoBtn) undoBtn.addEventListener("click", undo);

    // Keyboard shortcuts only while focus is inside the demo.
    var demo = document.getElementById("concept");
    if (demo) {
      demo.addEventListener("keydown", function (event) {
        if (!selected) return;
        var tag = (event.target.tagName || "").toLowerCase();
        if (tag === "input" || tag === "textarea") return;
        var map = { ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right" };
        if (map[event.key] && event.target.closest(".ce__canvas, .ce__side")) {
          event.preventDefault();
          move(map[event.key]);
        } else if (event.key === "r" || event.key === "R") {
          rotate();
        }
      });
    }
  }

  /* ---------------------- Stripe checkout links ------------------------- */
  /* The three pricing buttons are ordinary same-window anchors with real
     hrefs, so they work with JS disabled and are never intercepted on a normal
     top-level visit. The one thing that breaks them is being inside an
     embedded preview frame: Stripe Checkout refuses to render in an iframe
     ("Stripe Checkout is not able to run in an iFrame"), the frame goes blank,
     and the click looks like it did nothing. When — and only when — the page is
     framed, checkout is sent to a new top-level tab and a direct fallback line
     is revealed. No script-opened popups: the browser handles the activation. */
  var checkoutLinks = document.querySelectorAll('.tier__cta a[href^="https://buy.stripe.com"]');

  var isEmbedded = false;
  try {
    isEmbedded = window.top !== window.self;
  } catch (e) {
    isEmbedded = true; // cross-origin embedder: the access itself threw
  }

  if (isEmbedded && checkoutLinks.length) {
    var embedNote = document.getElementById("pricing-embed-note");
    var embedLead = document.getElementById("pricing-embed-lead");
    var embedUrl = document.getElementById("pricing-embed-url");
    if (embedNote) embedNote.hidden = false;

    var announceBlocked = function (url) {
      if (!embedNote) return;
      embedNote.classList.add("is-blocked");
      if (embedLead) {
        embedLead.textContent =
          "This preview blocked the new tab. Copy the checkout link and open it in your browser:";
      }
      if (embedUrl) {
        embedUrl.hidden = false;
        embedUrl.textContent = url;
      }
    };

    Array.prototype.forEach.call(checkoutLinks, function (link) {
      // Native new-tab activation keeps keyboard Enter, middle-click and
      // long-press working exactly as users expect.
      link.target = "_blank";
      link.rel = "noopener";

      if (!link.querySelector(".sr-only")) {
        var hint = document.createElement("span");
        hint.className = "sr-only";
        hint.textContent = " (opens Stripe checkout in a new tab)";
        link.appendChild(hint);
      }

      link.addEventListener("click", function (event) {
        if (event.defaultPrevented) return;
        if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        var url = link.href;
        // If the new tab really opened, this document loses focus. If focus is
        // still here a moment later, the embedder blocked it — surface the URL.
        window.setTimeout(function () {
          if (document.hasFocus && document.hasFocus() && document.visibilityState === "visible") {
            announceBlocked(url);
          }
        }, 1500);
      });
    });
  }

  /* ------------------------- checkout targets ------------------------- */
  /* Every buy button names a key in checkout-links.js. A key with a Payment
     Link opens Stripe; a key without one falls back to the contact route with
     the plan pre-selected, and says it is requesting activation. The markup
     already carries a safe href, so this only has to keep it in step with the
     config and with the monthly/annual toggle. */
  var checkout = window.PV_CHECKOUT;

  if (checkout) {
    var contactRoute = checkout.CONTACT_ROUTE || "contact.html";
    var pageRef = (window.location.pathname.split("/").pop() || "index.html").replace(/\.html$/, "");

    var requestHref = function (key) {
      var req = (checkout.requests || {})[key] || {};
      var query = [];
      if (req.plan) query.push("plan=" + encodeURIComponent(req.plan));
      if (req.billing) query.push("billing=" + encodeURIComponent(req.billing));
      query.push("ref=" + encodeURIComponent(pageRef));
      return contactRoute + "?" + query.join("&");
    };

    var applyCheckout = function (el, key) {
      var url = (checkout.links || {})[key];
      if (url) {
        el.setAttribute("href", url);
        el.setAttribute("target", "_blank");
        el.setAttribute("rel", "noopener noreferrer");
        el.setAttribute("data-checkout-state", "live");
      } else {
        el.setAttribute("href", requestHref(key));
        el.removeAttribute("target");
        el.setAttribute("rel", "nofollow");
        el.setAttribute("data-checkout-state", "request");
      }
    };

    Array.prototype.forEach.call(document.querySelectorAll("[data-checkout]"), function (el) {
      applyCheckout(el, el.getAttribute("data-checkout"));
    });

    /* Monthly / annual. Each card carries both sets of copy, so switching is a
       swap of text plus the checkout key the button resolves against. */
    var billBar = document.querySelector("[data-billing-toggle]");
    var planCards = Array.prototype.slice.call(document.querySelectorAll("[data-plan-card]"));

    if (billBar && planCards.length) {
      var billState = document.querySelector("[data-billing-state]");
      var billOpts = Array.prototype.slice.call(billBar.querySelectorAll("[data-billing]"));

      var setBilling = function (period) {
        var annual = period === "annual";
        var prefix = annual ? "data-a-" : "data-m-";

        planCards.forEach(function (card) {
          var read = function (part) { return card.getAttribute(prefix + part) || ""; };
          var amount = card.querySelector("[data-price-amount]");
          var per = card.querySelector("[data-price-per]");
          var alt = card.querySelector("[data-price-alt]");
          var cta = card.querySelector("[data-checkout-plan]");
          var label = card.querySelector("[data-cta-label]");

          if (amount) amount.textContent = read("amount");
          if (per) per.textContent = read("per");
          if (alt) alt.textContent = read("alt");
          if (label) label.textContent = read("cta");
          if (cta) applyCheckout(cta, cta.getAttribute("data-checkout-plan") + "_" + period);
        });

        billOpts.forEach(function (opt) {
          var on = opt.getAttribute("data-billing") === period;
          opt.classList.toggle("is-on", on);
          opt.setAttribute("aria-pressed", on ? "true" : "false");
        });

        if (billState) {
          billState.textContent = annual
            ? "Showing annual prices — twelve months for the price of ten."
            : "Showing monthly prices.";
        }
      };

      billOpts.forEach(function (opt) {
        opt.addEventListener("click", function () {
          setBilling(opt.getAttribute("data-billing"));
        });
      });

      setBilling("monthly");
    }
  }

  /* ------------------- plan carried into the contact form ---------------- */
  /* An unreleased plan sends people here with ?plan= and ?billing=. Show what
     they asked for and seed the message, so the request arrives complete and
     nobody has to retype the plan name. */
  var planParams = new URLSearchParams(window.location.search);
  var wantedPlan = planParams.get("plan");
  var planSlot = document.querySelector("[data-plan-pick]");

  if (planSlot && wantedPlan) {
    var wantedBilling = planParams.get("billing") || "";
    var billingWord = { monthly: "billed monthly", annual: "billed annually", custom: "custom terms",
      "one-time": "a one-time payment" }[wantedBilling] || "";
    var planLine = wantedPlan + (billingWord ? ", " + billingWord : "");

    planSlot.innerHTML = "";
    var strong = document.createElement("strong");
    strong.textContent = "You are asking us to activate " + planLine + ".";
    planSlot.appendChild(strong);
    planSlot.appendChild(document.createTextNode(
      " Send this form and we will reply with the next step. Nothing has been charged and no seats exist yet."));
    planSlot.hidden = false;

    var msgField = document.getElementById("c-message");
    if (msgField && !msgField.value) {
      msgField.value = "Please activate " + planLine + " for us.\n\nHow many people will need a seat:\nCompany:\n";
    }
    var proRole = document.querySelector('input[name="role"][value="Landscape professional"]');
    if (proRole && !document.querySelector('input[name="role"]:checked')) proRole.checked = true;
  }

  /* --------------------------- contact form --------------------------- */
  /* No server and no third-party processor: the submit builds a structured
     message in the visitor's own mail client. It never claims to have sent. */
  var cForm = document.getElementById("contact-form");
  var cDone = document.getElementById("contact-done");
  var cDoneText = document.getElementById("contact-done-text");
  var MAILTO = "backyardsports@gmail.com";

  if (cForm && cDone && cDoneText) {
    var f = {
      name: document.getElementById("c-name"),
      email: document.getElementById("c-email"),
      interest: document.getElementById("c-interest"),
      message: document.getElementById("c-message")
    };
    var err = {
      name: document.getElementById("c-name-error"),
      email: document.getElementById("c-email-error"),
      role: document.getElementById("c-role-error"),
      interest: document.getElementById("c-interest-error")
    };

    function role() {
      var picked = cForm.querySelector('input[name="role"]:checked');
      return picked ? picked.value : "";
    }

    function flag(field, node, bad) {
      if (node) node.hidden = !bad;
      if (field) field.setAttribute("aria-invalid", bad ? "true" : "false");
      return !bad;
    }

    Object.keys(f).forEach(function (key) {
      if (!f[key] || !err[key]) return;
      var handler = function () {
        if (err[key] && !err[key].hidden) flag(f[key], err[key], false);
      };
      f[key].addEventListener("input", handler);
      f[key].addEventListener("change", handler);
    });

    Array.prototype.forEach.call(cForm.querySelectorAll('input[name="role"]'), function (radio) {
      radio.addEventListener("change", function () {
        if (err.role) err.role.hidden = true;
      });
    });

    cForm.addEventListener("submit", function (event) {
      event.preventDefault();

      var name = f.name.value.trim();
      var email = f.email.value.trim();
      var who = role();
      var interest = f.interest.value;
      var message = f.message.value.trim();

      var ok = true;
      var first = null;
      if (!flag(f.name, err.name, name.length < 2)) { ok = false; first = first || f.name; }
      if (!flag(f.email, err.email, !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email))) { ok = false; first = first || f.email; }
      if (err.role) {
        err.role.hidden = !!who;
        if (!who) { ok = false; first = first || cForm.querySelector('input[name="role"]'); }
      }
      if (!flag(f.interest, err.interest, !interest)) { ok = false; first = first || f.interest; }

      if (!ok) {
        if (first && first.focus) first.focus();
        return;
      }

      var link = cForm.querySelector("#c-link");
      var story = cForm.querySelector("#c-story");
      var testimonial = cForm.querySelector("#c-testimonial");
      var permission = cForm.querySelector("#c-permission");

      var lines = [
        "Name: " + name,
        "Email: " + email,
        "I am a: " + who,
        "Project interest: " + interest
      ];

      if (wantedPlan) {
        lines.push("Plan requested: " + wantedPlan +
          (planParams.get("billing") ? " (" + planParams.get("billing") + ")" : ""));
      }

      lines.push("", "Message:", message || "(none)");

      var linkVal = link && link.value.trim();
      var storyVal = story && story.value.trim();
      var quoteVal = testimonial && testimonial.value.trim();
      if (linkVal || storyVal || quoteVal || (permission && permission.checked)) {
        lines.push("", "— Project story —");
        if (linkVal) lines.push("Before / after link: " + linkVal);
        if (storyVal) lines.push("", "What happened:", storyVal);
        if (quoteVal) lines.push("", "Testimonial in their words:", quoteVal);
        lines.push(
          "",
          "Permission to publish: " + (permission && permission.checked ? "yes, with name and photos as supplied" : "not given"),
          "Photos: attach them to this email before sending — the form cannot upload files."
        );
      }

      lines.push("", "— Sent from the PlotVisionAI page");
      var href =
        "mailto:" + MAILTO +
        "?subject=" + encodeURIComponent("PlotVisionAI enquiry — " + name + " (" + who + ")") +
        "&body=" + encodeURIComponent(lines.join("\n"));

      cDoneText.textContent =
        "Your email app should now be opening with this message drafted to " + MAILTO +
        ". Nothing has been sent yet — press send in your email app to finish. If nothing opened, email " +
        MAILTO + " directly.";
      cDone.hidden = false;
      if (cDone.focus) cDone.focus();

      window.location.href = href;
    });
  }

  /* ---------------------------------------------------------------------
   * Automatic before / concept transitions (.xfade)
   * Directional reveal, restrained timing, pause control, pauses off-screen
   * and on hover/focus. Fully disabled under prefers-reduced-motion, where
   * the CSS shows both frames side by side instead.
   * ------------------------------------------------------------------- */
  var xfades = Array.prototype.slice.call(
    document.querySelectorAll("[data-xfade]:not([data-reveal-draw])")
  );
  xfades.forEach(function (fig) {
    var toggle = fig.querySelector("[data-xfade-toggle]");
    var live = fig.querySelector("[data-xfade-state]");
    var label = toggle ? toggle.querySelector("[data-xfade-toggle-label]") : null;
    var played = false;
    var timer = null;

    function setState(after) {
      fig.classList.toggle("is-after", after);
      if (live) {
        live.textContent = after
          ? "Showing the concept visualization"
          : "Showing the before photo";
      }
    }

    function reveal() {
      if (timer) { window.clearTimeout(timer); timer = null; }
      setState(false);
      timer = window.setTimeout(function () {
        setState(true);
        timer = null;
      }, 520);
    }

    if (reduceMotion) {
      fig.classList.add("is-static");
      if (toggle) toggle.hidden = true;
      if (live) live.textContent = "Before photo and concept visualization shown side by side";
      return;
    }

    setState(false);

    if (toggle) {
      toggle.hidden = false;
      toggle.setAttribute("aria-pressed", "false");
      if (label) label.textContent = "Replay reveal";
      toggle.addEventListener("click", function () { reveal(); });
    }

    if ("IntersectionObserver" in window) {
      var xio = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (en) {
            if (en.isIntersecting && !played) {
              played = true;
              reveal();
            }
          });
        },
        { threshold: 0.3 }
      );
      xio.observe(fig);
    } else {
      played = true;
      reveal();
    }
  });


  /* ── Filter sets: design type + role chips (Community Showcase, Gallery) ── */
  Array.prototype.forEach.call(document.querySelectorAll("[data-filterset]"), function (set) {
    var items = Array.prototype.slice.call(set.querySelectorAll("[data-type]"));
    if (!items.length) return;
    var typeChips = Array.prototype.slice.call(set.querySelectorAll("[data-filter]"));
    var roleChips = Array.prototype.slice.call(set.querySelectorAll("[data-role-filter]"));
    var count = set.querySelector("[data-filter-count]");
    var state = { type: "all", role: "all" };

    function norm(v) { return (v || "").replace(/\u2122|&trade;/g, "").trim().toLowerCase(); }

    function apply() {
      var shown = 0;
      items.forEach(function (item) {
        var okType = state.type === "all" || norm(item.getAttribute("data-type")) === norm(state.type);
        var okRole = state.role === "all" || (item.getAttribute("data-role") || "") === state.role;
        var ok = okType && okRole;
        item.hidden = !ok;
        if (ok) shown++;
      });
      if (count) {
        count.textContent = shown === items.length
          ? "Showing all " + items.length + " examples"
          : "Showing " + shown + " of " + items.length + " examples";
      }
    }

    function bind(chips, attr, key) {
      chips.forEach(function (chip) {
        chip.addEventListener("click", function () {
          chips.forEach(function (c) { c.classList.remove("is-on"); });
          chip.classList.add("is-on");
          state[key] = chip.getAttribute(attr);
          apply();
        });
      });
    }

    bind(typeChips, "data-filter", "type");
    bind(roleChips, "data-role-filter", "role");
    apply();
  });


  /* ─────────── Mobile menu sheet: height var, scroll lock, Escape ─────────── */
  (function () {
    var header = document.getElementById("site-header");
    var mnav = document.querySelector("[data-mnav]");
    if (!header) return;

    function setH() {
      document.documentElement.style.setProperty("--header-h", header.offsetHeight + "px");
    }
    setH();
    window.addEventListener("resize", setH);
    window.addEventListener("orientationchange", setH);

    if (!mnav) return;
    var root = document.documentElement;

    function close() {
      mnav.removeAttribute("open");
      root.classList.remove("mnav-open");
    }

    mnav.addEventListener("toggle", function () {
      setH();
      if (mnav.open) {
        root.classList.add("mnav-open");
        var first = mnav.querySelector(".mnav__close");
        if (first) first.focus({ preventScroll: true });
      } else {
        root.classList.remove("mnav-open");
      }
    });

    var closeBtn = mnav.querySelector("[data-mnav-close]");
    if (closeBtn) {
      closeBtn.addEventListener("click", function () {
        close();
        var btn = mnav.querySelector(".mnav__btn");
        if (btn) btn.focus({ preventScroll: true });
      });
    }

    Array.prototype.forEach.call(mnav.querySelectorAll(".mnav__panel a"), function (a) {
      a.addEventListener("click", close);
    });

    document.addEventListener("keydown", function (e) {
      if ((e.key === "Escape" || e.key === "Esc") && mnav.open) {
        close();
        var btn = mnav.querySelector(".mnav__btn");
        if (btn) btn.focus({ preventScroll: true });
      }
    });
  })();

})();

/* ------------------------------------------------------------------------- */
/* Free Preview optional signup                                               */
/* The preview link is public and is a plain anchor in the markup, so it works */
/* with JavaScript off and nothing here can block it. This form only records an */
/* address for launch news. With no endpoint configured it is switched off and  */
/* says so rather than faking a signup. The address is POSTed and then dropped: */
/* nothing is written to any browser-side store.                                */
(function () {
  var form = document.querySelector("[data-preview-gate]");
  if (!form) return;

  var cfg = window.PV_CONFIG || {};
  var submit = form.querySelector("[data-gate-submit]");
  var label = form.querySelector("[data-gate-label]");
  var email = form.querySelector("#gate-email");
  var emailErr = document.getElementById("gate-email-error");
  var optin = form.querySelector("#gate-updates");
  var pot = form.querySelector("#gate-company");
  var status = form.querySelector("[data-gate-status]");
  var alertBox = form.querySelector("[data-gate-alert]");
  var nocapture = form.querySelector("[data-gate-nocapture]");
  var sending = false;

  function say(node, msg) {
    if (!node) return;
    node.textContent = msg || "";
    node.hidden = !msg;
  }

  function fieldError(msg) {
    if (!emailErr) return;
    emailErr.textContent = msg || emailErr.textContent;
    emailErr.hidden = !msg;
    if (email) email.setAttribute("aria-invalid", msg ? "true" : "false");
  }

  function busy(on) {
    sending = on;
    if (!submit) return;
    submit.setAttribute("aria-busy", on ? "true" : "false");
    submit.disabled = on;
    if (label) label.textContent = on ? "Adding you\u2026" : "Notify me at launch";
  }

  /* No endpoint: do not pretend to save the address. Switch the form off and say
     so. The preview anchor above it is untouched. */
  if (!cfg.SIGNUP_ENDPOINT) {
    form.setAttribute("data-gate-state", "nocapture");
    if (nocapture) nocapture.hidden = false;
    if (submit) {
      submit.disabled = true;
      submit.setAttribute("aria-disabled", "true");
      submit.setAttribute("aria-describedby", "gate-nocapture");
      if (label) label.textContent = "Signup not connected yet";
    }
    if (email) {
      email.disabled = true;
      email.setAttribute("aria-describedby", "gate-nocapture");
    }
    if (optin) optin.disabled = true;
    form.addEventListener("submit", function (e) { e.preventDefault(); });
    return;
  }

  form.setAttribute("data-gate-state", "ready");

  function valid(v) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v);
  }

  /* Payload for the signup function. Both naming conventions are sent because the
     function accepts either; company is the honeypot and is always empty for a
     real person, so the server can reject bots as well. */
  function payload(value) {
    var optedIn = !!(optin && optin.checked);
    var consent = cfg.CONSENT_VERSION || "";
    return {
      email: value,
      source: cfg.SIGNUP_SOURCE || "free-preview",
      page: window.location.pathname,
      referrer: document.referrer || "",
      marketingOptIn: optedIn,
      marketing_opt_in: optedIn,
      consentVersion: consent,
      consent_version: consent,
      company: pot && pot.value ? pot.value : ""
    };
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (sending) return;
    say(alertBox, "");

    /* Honeypot: a real person never fills a field that is off screen and out of
       tab order, so stop without a request and without a false success. */
    if (pot && pot.value.trim() !== "") {
      say(alertBox, "That submission could not go through. If you are a real person, use the contact form and we will add you by hand.");
      return;
    }

    var value = (email && email.value ? email.value : "").trim();
    if (!valid(value)) {
      fieldError("Enter a valid email address, or skip this and use the preview link above.");
      if (email) email.focus();
      return;
    }
    fieldError("");

    busy(true);
    say(status, "Adding you\u2026");

    var headers = { "Content-Type": "application/json" };
    if (cfg.SIGNUP_ANON_KEY) {
      headers.apikey = cfg.SIGNUP_ANON_KEY;
      headers.Authorization = "Bearer " + cfg.SIGNUP_ANON_KEY;
    }

    fetch(cfg.SIGNUP_ENDPOINT, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(payload(value))
    })
      .then(function (res) {
        return res.json().catch(function () { return {}; }).then(function (data) {
          return { ok: res.ok, statusCode: res.status, data: data || {} };
        });
      })
      .then(function (r) {
        busy(false);
        /* Duplicate-safe: an address already on the list is a success, not an error. */
        var duplicate = r.statusCode === 409 || r.data.duplicate === true || r.data.status === "duplicate" ||
          r.data.status === "existing" || r.data.status === "already_registered";
        var created = r.data.status === "created" || r.statusCode === 201;
        if (r.ok || duplicate || created) {
          say(status, duplicate ? "Good news, you were already on the list." : "You are on the list \u2014 thank you.");
          if (label) label.textContent = "You are on the list";
          if (submit) submit.disabled = true;
          return;
        }
        say(status, "");
        var srvMsg = (r.data.error && r.data.error.message) || r.data.message || "";
        say(alertBox, srvMsg || "We could not save that address just now. Try again in a moment, or use the contact form. The preview link above is unaffected.");
      })
      .catch(function () {
        busy(false);
        say(status, "");
        say(alertBox, "That did not reach our server \u2014 check your connection and try again, or use the contact form. The preview link above is unaffected.");
      });
  });

  if (email) {
    email.addEventListener("input", function () {
      if (emailErr && !emailErr.hidden && valid(email.value.trim())) fieldError("");
    });
  }
})();
