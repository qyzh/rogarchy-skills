---
name: dither-data-viz
description: Use for dithered charts; asks which of 5 card designs (A–E) when unspecified, default B Ledger First.
version: 0.4.0
author: qyzh, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [dither, bayer, chart, canvas, html, png, dataviz]
    related_skills: [web-design-guidelines, omarchy-agent-usage, graph-visualization, threejs-data-viz, baoyu-infographic, html-data-report]
---

# Dither Data Viz

Engine adapted from DeepanshuMishraa/dither-kit-rs (MIT OR Apache-2.0).

House charts: ordered Bayer dither on canvas, labels in real HTML. Deliver an
`index.html` that opens over `file://` plus one opaque PNG per chart canvas.
Engine: `./dither.js` in the output folder (`globalThis.Dither`); do not rewrite
it.

**Default design = “Ledger First” model card (B).** When the user has not named
a design, ask first (see **Choose a design**). B is built when the user picks
it, says “default”, or declines to choose, and it is the ledger card: a ranked table (top 10 + “Lainnya”) is the hero (each row
carries its own `Dither.meter` bar), plus ONE small donut (`type: 'pie'`,
`inner: 0.62`, the only exported PNG). Top-N models plus a “Lainnya” bucket,
`model · agent` in every row, a KPI strip, a cost total, and a footnote —
1080×1920 dark, mobile 9:16. See **Default ledger card** below. The earlier
donut-led layout is option A in `design-options/` (reference set of 5 layouts,
each a standalone file over `file://`).

## Hard Constraints

- Canvas marks only: Bayer `covers` / `t8`. No Chart.js, chart CDN, SVG
  `<pattern>`, or CSS noise as a dither substitute.
- Labels, legends, and captions stay HTML. Never bake text into the bitmap.
- Deliver both the HTML and the PNGs. Chart PNGs come from the canvas export,
  never image models or full-page screenshots — except usage-data cards
  (below), where the whole-card capture is the user's requested deliverable
  and canvas PNGs ship alongside it.
- Never invent values. Missing cells stay `null`; dummy data only when the user
  asks for a test.
- PNGs are composited onto `#0c0c0e`: opaque, non-blank, > 1 KB.

## When to Use

- User wants a dithered / Bayer / grainy canvas chart as HTML plus PNG.
- Parts of a whole / model share (default), time series, scores, inline trend,
  or 0–1 progress.
- Dark Geist chrome; labels, legend, and captions stay HTML.

**Don't use — route away:**

| Request | Load instead |
|---|---|
| Node–edge / network / wikilink graph | `graph-visualization` |
| 3D / three.js chart | `threejs-data-viz` |
| Infographic image / 信息图 | `baoyu-infographic` |
| Generic Chart.js HTML report | `html-data-report` |

### Usage-data cards (Omarchy agent tokens / quota / cost)

Load the `visual-preferences.md` reference of the
`omarchy-agent-usage` skill (same repo, `../omarchy-agent-usage/references/visual-preferences.md`)
and follow it: the standing preference overrides the canvas-only PNG default. Primary deliverable = full info card (title + chart + legend +
number table + footnote), 1080×1920 dark, costs taken from the cost CSVs
with `fetched_at` (INCOMPLETE when the range has partial-cost days). Capture the card-sized page whole
at DPR 2 and LANCZOS-downscale, AND export the per-canvas PNGs: canvas-only
output was explicitly rejected, while the canvas PNGs satisfy
this skill's contract. Delivering both resolves the conflict; picking one
violates a standing instruction. Cost figures obey the 2-decimal USD rule of
that skill (`$168.23`, `$0.00`).

**Which layout wins.** A usage card's layout is the design chosen in **Choose a
design** (default B); that choice overrides the reference's “agent, token and
prompt per day” layout. Use the per-day layout (agent × day, tokens and
prompts, `area` plateau bars via **Procedure**) only when the user explicitly
asks for a per-day or per-agent-over-time breakdown. Every other rule in the
reference — 9:16 dark, whole-card capture plus canvas PNGs, “token non-cache”,
cost from `cost_by_model.csv`, `fetched_at`, INCOMPLETE, 2-decimal USD —
applies to every layout.

## Choose a design

Applies to usage / model-share cards (the A–E set below). Other chart shapes
(time series — including an explicitly requested per-day agent breakdown —
radar, sparkline, meter) skip this and follow **Procedure**.

1. **Design named → build it, no question.** The user says A/B/C/D/E or
   describes one (“cost banner”, “per-agent panels”, “dense dashboard”).
2. **Design not named → ask before building.** Do not silently apply the
   default. Offer these five, B marked as recommended:

   | Option | Design |
   |---|---|
   | A · Donut Refined | huge donut, total in the hole, 2-col legend, table, cost banner |
   | **B · Ledger First (recommended, default)** | 11-row ledger/table as hero, per-row dither bars, small donut, mono/brutalist |
   | C · Cost Banner | giant total cost, cost-share ring, daily cost area, free-model list |
   | D · Split per Agent | hero donut + legend side by side, four per-agent panels |
   | E · Dense Dashboard | dense grid of 12 dither marks |

   Point to the visual gallery `design-options/index.html` (open or show it
   when offering the choice); each option's full preview is
   `design-options/option-a-donut-refined.html`, `option-b-ledger-first.html`,
   `option-c-cost-banner.html`, `option-d-split-agent.html`,
   `option-e-dense-dashboard.html`. Previews already exist; do not recreate them.
3. **“Default”, declines to choose, or no one can answer → B.** Do not ask
   again. In a non-interactive run (scheduled job, batch, a sub-task with no
   user channel) build B without asking and say in the delivery note that B was
   used by default.
4. B is built by `scripts/build_donut_card.py` (**Default ledger card**). A, C,
   D, E have no builder: copy the matching preview into the output folder as
   `index.html` next to `./dither.js` and `./scripts/export.mjs`
   (**Procedure** step 1), then replace its whole `const D = {…}` object with
   values aggregated from the user's CSVs for the requested range by the
   ledger-card rules (non-cache tokens, top 10 + “Lainnya”, largest-remainder
   shares, cost from `cost_by_model.csv`, `fetched_at`, INCOMPLETE for
   partial-cost days). Never ship a preview's own numbers — they are
   fake sample data (2026-01-01..06). Keep the preview's `canvas.chart` + `data-export`
   hooks and `__DITHER_COUNT__` so `export.mjs` finds the charts, make sure the
   footnote prints `fetched_at`, then run `export.mjs` and the full-card
   capture. Same contract: canvas-only Bayer, HTML labels, self-contained
   `file://`, opaque canvas PNGs, no invented values, 2-decimal USD.

## Default ledger card

Option B. Use this for usage/share requests once B is chosen or defaulted
(see **Choose a design**); it replaced the donut-led card (now option A in
`design-options/`) as the house default.

- **Data:** aggregate `inputTokens + outputTokens` (token non-cache) per model
  from `daily_by_model.csv`; aggregate USD per model from `cost_by_model.csv`.
  Never sum cache read into the plotted value.
- **Slices:** sort descending, keep top 10, fold the rest into one `Lainnya (N
  model)` slice (only when more than 10 models exist; no empty bucket). Cycle
  tones `green, blue, purple, orange, pink, red, grey`.
- **Layout:** header (kicker, title, date range) beside a 300px donut
  (`inner: 0.62`, `fill: 'gradient'`); KPI strip (tokens, total cost, count of
  models with usage — models folded into “Lainnya” included); ledger rows filling the remaining height. Each row: rank, swatch +
  `model` with `agent1, agent2 · share · cost` beneath, a dither meter bar
  (value = tokens ÷ largest row), tokens, share. A TOTAL row follows
  (`TOTAL · biaya $X`, total tokens, 100.0%). Displayed percentages sum to
  exactly 100.0% (largest-remainder rounding).
- **Attribution:** usage-card footers must keep "Source: Artificial Analysis (artificialanalysis.ai)" with the link, "Based on data from Artificial Analysis" and the non-endorsement line. A card/chart shared publicly must also show the AA logo (AA Data Platform Terms); tell the user, the repo ships no logo.
- **Footnote:** states that cache read is excluded, small models are folded
  into “Lainnya”, and cost is a historical revaluation (with `fetched_at`),
  not a subscription bill. When the range has partial-cost days
  (`cost_daily.csv` `partial=1`) the total cost and TOTAL row say INCOMPLETE
  and the footnote names those days; any cost from models with no non-cache
  tokens is disclosed in the footnote.
- **Data dir:** `--data-dir` wins; otherwise the env var `OMARCHY_USAGE_DATA`
  (folder holding `daily_by_model.csv`, `cost_by_model.csv`, `cost_daily.csv`);
  otherwise the Omarchy usage-history directory
  `~/.local/state/omarchy/agents/usage-history`.
- **Builder:** `python3 scripts/build_donut_card.py --data-dir <dir> --start
  YYYY-MM-DD --end YYYY-MM-DD --out <folder>` copies `dither.js` and
  `export.mjs` and writes a self-contained `index.html` (no template; own
  boot code, sets `__DITHER_READY__`, `__DITHER_ERROR__`, `__DITHER_COUNT__ = 1`).
  Only the donut canvas (`canvas.chart`, `data-export="model-donut"`) is
  exported by `export.mjs`; the row bars are decoration and carry no `.chart`
  class. Then run `export.mjs` and the full-card capture (see Engine Notes). It
  exits non-zero without writing anything when --start > --end, a CSV is
  missing, or the range has no non-cache usage.
- **Other layouts:** `design-options/` holds A (donut-led), C (cost banner),
  D (split per agent) and E (dense dashboard) built with synthetic sample data (`data contoh (fiktif)`) and the
  same contract; build one when the user picks it (**Choose a design**).
- **Font quirk:** the builder writes a zero-width space inside “non-cache”
  because some system mono fonts mask letter-spaced uppercase “NON-CACHE”.

## Procedure

Paths are relative to this skill root. The output folder receives `./dither.js`,
`./scripts/export.mjs`, and an `index.html` built from `./templates/page.html`.

1. **Copy engine, exporter, and chrome — then build from the copies.** Copy
   `./scripts/dither.js` → output `./dither.js`, `./scripts/export.mjs` →
   output `./scripts/export.mjs`, and `./templates/page.html` → a local
   template file in the output folder. Build `index.html` from that LOCAL
   template on every rebuild: the skill folder is shared state another
   session may rewrite mid-task, and re-reading it swaps chrome under your
   substitutions without warning. Keep `Dither.areaChart` / `pie` / `radar` /
   `sparkline` / `meter` intact.

2. **Shape the data.** Define `window.CHARTS = [ ... ]` (or `window.CHART = { ... }`
   for one chart) before the template boot script. Copy values exactly; missing
   cells are `null`. Each spec may set `name` (unique PNG filename), `title`
   (heading and canvas accessible name), and `type`.

3. **Choose the type from the data shape.**

   | Data shape | `type` | Engine call |
   |---|---|---|
   | time series | `area` | `Dither.areaChart` |
   | parts of a whole (DEFAULT) | `pie` | `Dither.pie` |
   | several axes / scores | `radar` | `Dither.radar` |
   | inline trend | `spark` | `Dither.sparkline` |
   | 0–1 progress | `meter` | `Dither.meter` |
   | categorical comparison | `area` + plateau | `Dither.areaChart` |

   Default to `pie` for share/composition data; other types only when the data
   shape demands it.

   `spark` is canonical; `sparkline` is a supported alias. Button, avatar, and
   background textures are optional decorations, never default chart types.

   **Bar/plateau encoding.** The engine has no bar type. For `k` categories and
   a plateau width of `m` slots, use `n = k * (m + 1) - 1` slots. Series `i`
   owns indices `[i*(m+1), i*(m+1)+m)`; every other index is `null`, so the one
   `null` slot between plateaus is the bar gap. Keep `type: 'area'` — this is
   data shaping, not extra JS. Example: 4 bars, `m = 8` → `n = 35`. Plateau
   labels in a narrow grid need `font-size: 9px; letter-spacing: 0` and
   `overflow: visible; text-overflow: clip` or they ellipsis-truncate.

4. **Write `index.html`.** Replace every `{{TITLE}}` (document title and
   heading) and every `{{SUB}}` occurrence. Insert the data script after
   `<script src="./dither.js"></script>` and before the boot script. The
   template renders one `.chart-card` per spec, fills `.legend` and `.xlabels`,
   and repaints on resize. Keep `name`, `title`, `series[].name`, and `labels`
   set; export filenames and accessible names come from them.

5. **Export the PNGs.** Run this from the output folder:

   ```sh
   node ./scripts/export.mjs index.html
   ```

   The script opens the page in headless Chromium at 540×960, DPR 2, forces
   `prefers-reduced-motion: reduce`, waits for paint, composites each chart
   canvas onto `#0c0c0e` (fill, then `drawImage`), and writes `<name>.png`
   beside `index.html`. Requires Node 22+; set `CHROME_BIN` if Chromium is not
   on `PATH`.

6. **Audit.** Load `web-design-guidelines` and audit the shipped HTML. Fix
   focus, contrast, reduced-motion, and accessible-name issues.

`window.CHARTS` shapes the template already understands:

```js
window.CHARTS = [
  // area
  { name: 'traffic', title: 'Weekly traffic', type: 'area',
    labels: ['Mon', 'Tue', 'Wed'], series: [{ name: 'Desktop', tone: 'green', fill: 'gradient', values: [/* user */] }] },
  // pie
  { name: 'share', title: 'Share by channel', type: 'pie',
    slices: [{ name: 'A', tone: 'blue', fill: 'gradient', value: 1 }], inner: 0.58 },
  // radar
  { name: 'scores', title: 'Scores', type: 'radar',
    labels: [/* axes */], series: [{ name: 'Score', tone: 'purple', fill: 'gradient', values: [/* per axis */] }] },
  // spark (sparkline is an alias)
  { name: 'trend', title: 'Trend', type: 'spark', values: [/* user */], tone: 'green' },
  // meter
  { name: 'progress', title: 'Progress', type: 'meter', value: 0.42, tone: 'green', fill: 'gradient' },
];
// Single-chart fallback: window.CHART = { ...one spec... };
```

Tones: `green` `blue` `purple` `orange` `pink` `red` `grey`. Fills: `gradient`
(default Bayer), `dotted`, `hatched`, `solid`.

## Engine Notes

- `niceScale` puts its top tick at `y = 0`; the grid line on the top edge is a
  tick, not a stray border.
- A `null` breaks the line and fill. It is a gap, never a zero-height column.
- `Dither.pie` ignores `opts.selected`; use `hover` (the template forwards
  `spec.hover` / `spec.selected`). Legend clicks on a donut only dim the other
  slices when `hover` is set.
- `Dither.fit(canvas, px)` sizes the bitmap from the CSS box before paint; a
  300×150 bitmap means the canvas has no layout box yet.
- `Dither.paint` clears to transparent. The export script owns opacity; do not
  ship a raw `toDataURL` frame.
- Canvas `height: 100%` inside a flex-derived parent can resolve to the
  intrinsic bitmap height instead of the box. Put the canvas
  `position: absolute; inset: 0` in a `position: relative` plot box.
- Fixed-size cards (e.g. 1080×1920): lay the page out as a column flex with
  the plot `flex: 1` so the chart absorbs leftover height — a fixed plot
  height leaves a band of dead space at the card bottom.
- `export.mjs` hardcodes a 540×960 viewport, so its canvas PNGs come from that
  layout; for the full-card PNG use a separate CDP capture at 1080×1920.
  `Emulation.setDeviceMetricsOverride(deviceScaleFactor: 2)` AND a clip with
  `scale: 2` multiply to 4× (4320×7680) — LANCZOS-downscale straight to
  1080×1920. Verify `scrollWidth/scrollHeight` equal the card box and that no
  text bounding box escapes the viewport before capturing.
- Plateau bars packed into many slots (e.g. 35 xlabels in a 2-column grid)
  ellipsis-truncate day numbers at the template's default 11px. Override
  `.xlabels` to `font-size: 9px; letter-spacing: 0` and spans to
  `overflow: visible; text-overflow: clip`.

## Verification

- [ ] Run these from the **output folder**, the one holding `index.html`.
  `node --check dither.js` and `node --check scripts/export.mjs` pass there;
  from the skill root the same files are `scripts/dither.js` and
  `scripts/export.mjs`.
- [ ] `index.html` exists, opens over `file://`, and loads `./dither.js` only (no
  external scripts, fonts, or stylesheets).
- [ ] PNG count equals chart count; each is opaque, non-blank, > 1 KB, and
  named from `spec.name` (slugified) or `chart` / `chart-1`, `chart-2`, ...
- [ ] Multi-chart PNGs are distinct, not copies of the same canvas;
  `export.mjs` exits non-zero before writing any PNG if two canvases are
  byte-identical.
- [ ] Plotted values match the source exactly; nulls are preserved as gaps.
- [ ] For the default ledger card: slice values sum to the TOTAL row, displayed percentages
  sum to exactly 100.0% (the builder uses largest-remainder rounding), and every row carries its agent name.
- [ ] For a range with partial-cost days the card shows INCOMPLETE and names the days (check `cost_daily.csv`).
- [ ] `grep -Ei 'chart\.js|new Chart\(|cdn\.jsdelivr|<pattern' index.html`
  finds nothing, and
  `grep -Ei 'https?://' index.html` shows no external `src`/`href`. The engine's own `Dither.areaChart(` is expected.
- [ ] `web-design-guidelines` audit ran and blocking issues are fixed.
- [ ] Render and layout proven programmatically, not by vision alone: bitmap
  ≠ 300×150, non-transparent pixels present, expected tone hues in the PNG
  (PIL hue buckets; if PIL is missing, `magick identify -format '%[opaque] %k'` for opacity and colour count, and `magick … -filter Lanczos -resize 1080x1920` for the downscale), page scroll size ≤ card size, and every text element's
  bounding box inside the viewport margins (no clipping). Vision rate-limits;
  these checks don't.
