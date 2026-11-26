# Usage cards (dither-data-viz)

Read this before building any AI-agent usage card: tokens, quota or cost from
`omarchy-agent-usage`, a model-share card, or any of designs A–E. It adds to
`SKILL.md` and overrides it where they differ. Paths are relative to the skill
root (the folder holding `SKILL.md`), and bold section names such as
**Procedure** and **Engine Notes** refer to `SKILL.md`.

## Default design

**Default design = “Ledger First” model card (B).** When the user has not named
a design, ask first (see **Choose a design**). B is built when the user picks
it, says “default”, or declines to choose, and it is the ledger card: a ranked table (top 10 + “Lainnya”) is the hero (each row
carries its own `Dither.meter` bar), plus ONE small donut (`type: 'pie'`,
`inner: 0.62`, the only exported PNG). Top-N models plus a “Lainnya” bucket,
`model · agent` in every row, a KPI strip, a cost total, and a footnote —
1080×1920 dark, mobile 9:16. See **Default ledger card** below. The earlier
donut-led layout is option A in `design-options/` (reference set of 5 layouts,
each a standalone file over `file://`).

## Usage-data cards (Omarchy agent tokens / quota / cost)

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
- **Data dir:** `--data-dir` wins; otherwise `OMARCHY_USAGE_DATA` (env var,
  then `config.env`; folder holding `daily_by_model.csv`, `cost_by_model.csv`,
  `cost_daily.csv`); otherwise the Omarchy usage-history directory
  `${XDG_STATE_HOME:-~/.local/state}/omarchy/agents/usage-history`.
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

## Verification (usage cards)

In addition to the checklist in `SKILL.md`:

- [ ] For the default ledger card: slice values sum to the TOTAL row, displayed percentages
  sum to exactly 100.0% (the builder uses largest-remainder rounding), and every row carries its agent name.
- [ ] For a range with partial-cost days the card shows INCOMPLETE and names the days (check `cost_daily.csv`).
