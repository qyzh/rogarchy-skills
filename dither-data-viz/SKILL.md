---
name: dither-data-viz
description: "Use for dithered / Bayer / grainy canvas charts delivered as HTML plus PNG: area, pie/donut, radar, sparkline, meter, bars. For AI-agent usage cards (tokens, quota, cost) it offers 5 designs (A–E, default B Ledger First)."
version: 0.5.0
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

**Usage cards** (AI-agent tokens, quota or cost from `omarchy-agent-usage`,
model-share cards, designs A–E): read `references/usage-cards.md` first; it
overrides this file where they differ. Every other chart follows this file
alone and never asks for a design.

## Hard Constraints

- Canvas marks only: Bayer `covers` / `t8`. No Chart.js, chart CDN, SVG
  `<pattern>`, or CSS noise as a dither substitute.
- Labels, legends, and captions stay HTML. Never bake text into the bitmap.
- Deliver both the HTML and the PNGs. Chart PNGs come from the canvas export,
  never image models or full-page screenshots — except usage cards (see
  `references/usage-cards.md`), where the whole-card capture is the user's
  requested deliverable and canvas PNGs ship alongside it.
- Never invent values. Missing cells stay `null`; dummy data only when the user
  asks for a test.
- PNGs are composited onto `#0c0c0e`: opaque, non-blank, > 1 KB.

## Prerequisites / Config

Requires: commands `node` (22+), `python3`, and Chrome/Chromium (`chromium`, `google-chrome`, or `CHROME_BIN`).
Local files: none.

| Variable | Meaning | Default | Kind |
|---|---|---|---|
| `CHROME_BIN` | Chrome/Chromium executable for the PNG export | auto-detect (common install paths, then `PATH`) | advanced |
| `OMARCHY_USAGE_DATA` | Usage data dir for usage-data cards (shared with `omarchy-agent-usage`) | `${XDG_STATE_HOME:-$HOME/.local/state}/omarchy/agents/usage-history` | setting |

Resolve each variable once, before the first step that needs it: the env var if set and non-empty; else its `KEY=value` line in `${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env` (written by `rogarchy-setup`; read it as data, never `source` it; the last matching line wins); else the default. A missing file or line means the default. Kind: `setting` = setup asks for it; `advanced` = setup keeps the default unless the user asks; `secret` = env var only, never in `config.env` or chat. In a shell, `rs_get` does the same lookup:

```bash
rs_get() { _rs_v=$(printenv "$1" || :); [ -n "$_rs_v" ] || _rs_v=$(sed -n "s/[[:space:]]*\$//; s/^$1=//p" "${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env" 2>/dev/null | tail -n 1 || :); printf '%s\n' "${_rs_v:-$2}"; }
rs_get CHROME_BIN ""
```

The scripts resolve these themselves in the same order (`scripts/export.mjs`, `scripts/build_donut_card.py`).

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

**Usage cards** (Omarchy agent tokens / quota / cost, model share, designs
A–E): read `references/usage-cards.md` before choosing a layout.

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
   beside `index.html`. Requires Node 22+; set `CHROME_BIN` (env var or
   `config.env`) if Chromium is not found.

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
- [ ] Usage cards: the checks in `references/usage-cards.md` pass too.
- [ ] `grep -Ei 'chart\.js|new Chart\(|cdn\.jsdelivr|<pattern' index.html`
  finds nothing, and
  `grep -Ei 'https?://' index.html` shows no external `src`/`href`. The engine's own `Dither.areaChart(` is expected.
- [ ] `web-design-guidelines` audit ran and blocking issues are fixed.
- [ ] Render and layout proven programmatically, not by vision alone: bitmap
  ≠ 300×150, non-transparent pixels present, expected tone hues in the PNG
  (PIL hue buckets; if PIL is missing, `magick identify -format '%[opaque] %k'` for opacity and colour count, and `magick … -filter Lanczos -resize 1080x1920` for the downscale), page scroll size ≤ card size, and every text element's
  bounding box inside the viewport margins (no clipping). Vision rate-limits;
  these checks don't.
