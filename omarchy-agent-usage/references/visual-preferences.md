# Default visual style

The skill's default style for usage-data charts/video. Kept apart from SKILL.md because it is about appearance, not tool behavior. The user may ask for another style; an explicit request beats these defaults.

When a chart/video of usage data is requested:

- Mobile ratio **9:16** (1080×1920), dark theme.
- Show **only** the agent name, tokens, and prompts, split per day, without input/output/cache.
- Style: high-contrast bars on a dark background, typography readable on a phone screen. The same concept is reused for video variants.

**PNG = an informative card, not canvas-only.**
- Default: don't output the chart alone. The PNG must capture the whole card (title + chart + legend + number table + footnote) via `Page.captureScreenshot` clip 1080×1920 @ deviceScaleFactor 2, then be downscaled with LANCZOS to 1080×1920.
- Never write labels into the bitmap.

**Terminology:** use **non-cache tokens** (not "fresh tokens") (= non-cache input + output).

**Cost in charts (if requested):** take cost per agent from `cost_by_model.csv` (sum per agent over the chart's date range) in the data dir. Do **not** recompute "non-cache tokens × price per 1M": `cost.py` uses separate input, output, cache-hit and cache-write prices, so an inline number would differ from `cost_report.md`.
- Show a cost-per-agent column + a total banner under the chart.
- Include `fetched_at`, and mark `INCOMPLETE` if the cost report is.
- **All USD amounts on the card are written with exactly 2 decimals** (`$168.23`, `$0.00`). Don't show the 4–6 decimals of old CSVs; reformat when reading.
- `cost_by_model.csv` stores the cost **per model already rounded to 2 decimals**. Adding them up can differ by a few cents from `cost_daily.csv` / `cost_report.md` (cost.py adds the raw values, then rounds the total). For the card total, use the official `cost_daily.csv` figure; charge the difference to the highest-cost agent so the table rows still add up to the total.
