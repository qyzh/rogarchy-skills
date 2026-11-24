# dither-data-viz

## What it is

A skill for making dithered (Bayer pattern) charts on canvas, with labels, legends, and captions as real HTML. The output is an `index.html` that opens over `file://` plus one opaque PNG per chart canvas. For usage / model-share cards there are 5 designs (A–E); if none is named, the agent asks first, and the default is B "Ledger First".

## When to use / not use

Use it when:

- You want dither/Bayer/grainy charts on canvas as HTML and PNG.
- The data is parts of a whole (default, donut), a time series, scores (radar), a mini trend, or 0–1 progress.
- You ask for an agent token usage / quota / cost card (designs A–E).

Don't use it (hand off) for:

| Request | Skill |
|---|---|
| Node–edge graphs / networks / wikilinks | `graph-visualization` |
| 3D charts / three.js | `threejs-data-viz` |
| Infographic images | `baoyu-infographic` |
| Plain Chart.js HTML reports | `html-data-report` |

The hard rules: only Bayer marks on canvas (no Chart.js, CDN, SVG `<pattern>`), text is never baked into the bitmap, and values are never invented (empty cells stay `null`).

## Requirements

| Requirement | Status | Purpose |
|---|---|---|
| Node.js 22+ | **Required** | Runs `scripts/export.mjs`. |
| Chrome/Chromium | **Required** | Headless PNG export. Set `CHROME_BIN` if it is not on `PATH`. |
| Python 3 | Required for card B | Runs `scripts/build_donut_card.py`. |
| `web-design-guidelines` (outside this repo) | Called during the audit | Audits focus, contrast, reduced motion, and accessible names. |
| [`omarchy-agent-usage`](../omarchy-agent-usage/README.md) (this repo) | Only for usage cards | Provides `visual-preferences.md` (the cards' default style) and the cost CSVs. Linux/Omarchy only. |
| `graph-visualization`, `threejs-data-viz`, `baoyu-infographic`, `html-data-report` | Route only | Handoff targets for out-of-scope requests. |

Usage cards need `daily_by_model.csv` and `cost_by_model.csv` (and `cost_daily.csv` to flag days with partial cost).

## Configuration

| Variable | Meaning | Default |
|---|---|---|
| `CHROME_BIN` | Chrome/Chromium path for `export.mjs` | looked up on `PATH` |
| `OMARCHY_USAGE_DATA` | Usage CSV data folder for `build_donut_card.py`; the `--data-dir` option takes priority | the Omarchy usage history directory, `${XDG_STATE_HOME:-~/.local/state}/omarchy/agents/usage-history` |

The values above can also be stored in the settings file `${XDG_CONFIG_HOME:-~/.config}/rogarchy-skills/config.env` (via [`rogarchy-setup`](../rogarchy-setup/README.md)); the env var still wins, then that file, then the default.

## Usage examples

```text
Make a dithered area chart from this weekly traffic data: Mon 120, Tue 98, Wed 143.
```

Result: a folder with `index.html`, `dither.js`, `scripts/export.mjs`, and one PNG named after `spec.name`. Run `node ./scripts/export.mjs index.html` from the output folder to export the PNGs.

```text
Make a token share per model card for 2026-01-01 to 2026-01-06.
```

Because no design was named, the agent offers options A–E (B recommended; the gallery is in `design-options/index.html`). For B:

```bash
python3 scripts/build_donut_card.py --data-dir <csv-folder> --start 2026-01-01 --end 2026-01-06 --out <output-folder>
```

The result is a dark 1080×1920 card: a ledger table of the top 10 plus "Lainnya" (Other), one small donut (the only exported PNG), a KPI strip, the total cost, and a footnote. The agent also captures the full card as a PNG.

## Folder contents

```
dither-data-viz/
├── SKILL.md                          # instructions for the agent
├── scripts/
│   ├── dither.js                     # dither engine (globalThis.Dither): area, pie, radar, spark, meter
│   ├── export.mjs                    # exports each canvas as PNG via headless Chromium
│   └── build_donut_card.py           # builds the "Ledger First" (B) card from usage CSVs
├── templates/
│   └── page.html                     # page skeleton for general charts (window.CHARTS / window.CHART)
└── design-options/
    ├── index.html                    # gallery of the 5 designs
    ├── dither.js                     # engine copy for standalone previews
    ├── option-a-donut-refined.html   # A: large donut, 2-column legend, cost banner
    ├── option-b-ledger-first.html    # B: ledger table as the hero (default)
    ├── option-c-cost-banner.html     # C: giant total cost, cost share ring
    ├── option-d-split-agent.html     # D: donut + legend, per-agent panel
    └── option-e-dense-dashboard.html # E: dense grid of 12 dither marks
```

The numbers in the preview files are sample data (fictional, range 2026-01-01..06); don't reuse them for your data.

## Credits

Usage cards carry prices derived from [Artificial Analysis](https://artificialanalysis.ai/) ("Source: Artificial Analysis (artificialanalysis.ai)" is in the card footer). Cards or charts shared publicly must also show the Artificial Analysis logo (a Data Platform Terms requirement; the logo is not included in the repo).

The dither engine (`scripts/dither.js`, `design-options/dither.js`) is adapted from [DeepanshuMishraa/dither-kit-rs](https://github.com/DeepanshuMishraa/dither-kit-rs) (MIT OR Apache-2.0; MIT is used here), rewritten in JavaScript. The original license text and copyright are in [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

---

Version 0.4.0 · MIT License · [Repo README](../README.md)
