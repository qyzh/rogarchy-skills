---
name: omarchy-agent-usage
description: "Token usage, quota/limit %, per-day x per-model breakdowns, pay-as-you-go cost simulation (Artificial Analysis prices), cache-hit / token-per-prompt / cost-per-task metrics and weekly reports for local AI agents on Omarchy (Hermes, Claude Code, Codex, OpenCode, grok, agy). Triggers: cek penggunaan token, berapa token terpakai, kuota atau limit habis, agent mana paling boros, simulasi biaya, biaya pay-as-you-go, cache hit ratio, token per prompt, cost per task, laporan mingguan, track usage per hari."
version: 0.3.1
author: qyzh, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [omarchy, token-usage, metrics, agents, quota, cost]
    related_skills: [omarchy-plugin-authoring]
---

# Omarchy Agent Usage Skill

Read this before answering questions about AI agent token usage, quota, or cost on this machine, or before building a usage history.

## When to Use

Indonesian trigger phrases are kept because users type them; the English equivalents work too.

- "cek penggunaan token", "berapa token yang sudah dipakai", "kuota habis?" (check token usage, how many tokens used, quota exhausted?)
- "simpan data penggunaan token selama N hari", "track usage per hari" (keep token usage data for N days, track usage per day)
- "agent mana yang paling boros", "kenapa limit cepat habis" (which agent is the most wasteful, why does the limit run out fast)
- "simulasi biaya token", "kalau dibayar per token berapa", "biaya pay-as-you-go" (token cost simulation, what would it cost per token, pay-as-you-go cost)
- "metrik dashboard", "cache hit ratio", "token per prompt", "cost per task"
- "laporan minggu ini" (this week's report), a per-day × per-model breakdown.

**Don't use for:** building an Omarchy plugin that shows usage (see `omarchy-plugin-authoring`), or a cloud provider billing dashboard. This skill reads the agents' LOCAL stores and Omarchy records.

## Prerequisites / Config

Requires: commands `python3`; Omarchy wrappers `<OMARCHY_PATH>/bin/omarchy-agent-usage-*` (Linux + Omarchy only).
Local files: `references/task-signal.local.md` (template `references/task-signal.example.md`).

| Variable | Meaning | Default | Kind |
|---|---|---|---|
| `OMARCHY_USAGE_DATA` | Data dir (snapshots, CSV, reports) | `${XDG_STATE_HOME:-$HOME/.local/state}/omarchy/agents/usage-history` | setting |
| `OMARCHY_USAGE_PRICING_CACHE` | Runtime price cache | `${XDG_CACHE_HOME:-$HOME/.cache}/omarchy-agent-usage/pricing.json` | advanced |
| `OMARCHY_USAGE_PRICING_SEED` | Optional read-only local price seed | `<skill-dir>/references/pricing.json` | advanced |
| `OMARCHY_TASKS_FILE` | Task signal file | `${XDG_STATE_HOME:-$HOME/.local/state}/omarchy/agents/tasks.jsonl` | advanced |
| `OMARCHY_PATH` | Omarchy install | `/usr/share/omarchy` | advanced |
| `ARTIFICIAL_ANALYSIS_API_KEY` | Free Artificial Analysis Data API key (prices) | none: no network calls | secret |

Resolve each variable once, before the first step that needs it: the env var if set and non-empty; else its `KEY=value` line in `${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env` (written by `rogarchy-setup`; read it as data, never `source` it; the last matching line wins); else the default. A missing file or line means the default. Kind: `setting` = setup asks for it; `advanced` = setup keeps the default unless the user asks; `secret` = env var only, never in `config.env` or chat. In a shell, `rs_get` does the same lookup:

```bash
rs_get() { _rs_v=$(printenv "$1" || :); [ -n "$_rs_v" ] || _rs_v=$(sed -n "s/[[:space:]]*\$//; s/^$1=//p" "${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env" 2>/dev/null | tail -n 1 || :); printf '%s\n' "${_rs_v:-$2}"; }
rs_get OMARCHY_PATH /usr/share/omarchy
```

The scripts resolve these themselves in the same order (`scripts/common.py`); the API key is read from the env var only (`scripts/cost.py`).

## Quick snapshot (one agent)

```bash
omarchy-agent-usage-claude      # or hermes, codex, opencode, grok, ... -> one JSON record on stdout
ls "$(rs_get OMARCHY_PATH /usr/share/omarchy)"/bin/omarchy-agent-usage-* | grep -v -- '-update$'   # list of agents
```

- A per-agent wrapper does not change state, but some call the provider's limit API (network).
- **DO NOT run `omarchy-agent-usage-update`** unless the user explicitly asks. It is not a "read-only refresh":
  - it rewrites every `~/.local/state/omarchy/agents/usage/<agent>.json`;
  - it refreshes the account registry;
  - it runs `omarchy-agent-account-state autoswitch` for claude/codex/grok, which **can switch the account that is logged in**;
  - its stdout is empty (not JSON).

  If the user asks for it, warn them about the auto-switch first.

### Record fields

| Field | Meaning |
|---|---|
| `todayTotalTokens` | Total tokens today. |
| `todayTokensByModel` | `{model: tokens}` for today. |
| `todayPrompts` / `todaySessions` | Number of prompts and sessions today. |
| `recentDays` | Last 7 days: `{date, messageCount}`. **`messageCount` HOLDS TOKENS**, not a message count. |
| `modelUsage` | Lifetime total per model (`inputTokens`, `outputTokens`, `cacheReadInputTokens`, `cacheCreationInputTokens`). |
| `limits[]` | `{label, percent, resetsAt}`. **`percent` = a 0–1 fraction** (0.95 = 95% used, NOT 0.95%). `resetsAt` = ISO UTC time and may already be past; compare it with now before saying "resets later". |
| `totalPrompts` / `totalSessions` / `activeDays` | Lifetime totals. |

### Rules for reading the numbers

- **`cacheReadInputTokens` are not new tokens.** Total tokens can be 10–100x the fresh input. When reporting, separate them and use **non-cache tokens** (input + output) as the actual usage. Don't say "wasted 600 million tokens" if the 600 million is cache read.
- **`recentDays` covers only 7 days, totals only.** For a per-day × per-model breakdown, use the pipeline below.
- **Agents without local rows** (agy, grok, copilot, openrouter, ...) only have per-day totals from `recentDays`. Never invent a model breakdown.
- **The `(unknown)` row** = a row with no tokens and no model name; it holds only prompts/sessions:
  - **Hermes:** ALL Hermes prompts are here. The wrapper records prompts separately from tokens, so Hermes model rows always have `prompts=0`.
  - **Claude:** prompts not yet answered + the marker row of the active session.
  - **Codex / OpenCode:** rare; prompts without tokens.

  That is why tokens per prompt is computed per **agent** (Σ tokens ÷ Σ prompts over ALL rows, including `(unknown)`). Tokens per prompt per Hermes model is meaningless.
- **`sessions` in `daily_by_model.csv` = unique sessions per model — do not add them up** (one session uses several models). Unique sessions per day are in `daily.csv`.

## Data dir & pipeline

All output lives in the **data dir**, not in the skill folder (the skill folder may be synced/overwritten; the data must not go with it):

```
<OMARCHY_USAGE_DATA>/            (resolved; see Prerequisites / Config)
  snapshots/<date>.json        snapshots/archive/ (not read)   archive/ (old data)
  daily.csv  daily_by_model.csv  report.md
  cost_daily.csv  cost_by_model.csv  cost_report.md
  metrics_daily.csv  metrics_by_agent.csv  metrics_report.md
  weekly.csv  report_week.md  cron.log
```

Env (values and defaults: the table in Prerequisites / Config):
- `OMARCHY_USAGE_DATA` — data dir.
- `OMARCHY_USAGE_PRICING_CACHE` — runtime price cache.
- `OMARCHY_USAGE_PRICING_SEED` — optional read-only local price seed (default `references/pricing.json`, gitignored; may be absent).
- `ARTIFICIAL_ANALYSIS_API_KEY` — free Artificial Analysis Data API key. **From the env var only**; never write it to a file, never ask the user to paste it in chat. Without a key: no network calls (cache/seed are used) and one hint line is printed. Free key: https://artificialanalysis.ai/api-key-management-redirect
- `OMARCHY_TASKS_FILE` — task signal file.
- `OMARCHY_PATH` — Omarchy install.

**For tests: point everything at a temp dir.**

Pipeline order (each stage reads the output of the previous one):

```bash
S=<skill-folder>/scripts     # e.g. $HOME/.hermes/skills/omarchy-agent-usage/scripts
python3 $S/collect.py                       # 1. scan + today's snapshot + daily*.csv + report.md
python3 $S/cost.py --report                 # 2. cost (fetches live prices; --offline = cache/seed)
python3 $S/metrics.py --report --offline    # 3. metrics (uses prices from stage 2)
python3 $S/weekly.py                        # 4. weekly summary
python3 $S/collect.py --all                 # 1->4 in one go (add --offline: no price fetch)
python3 $S/collect.py --report --all --offline   # rebuild everything from snapshots: no scan, no network
```

**Before quoting numbers**, check the stamps at the head of the report: `Snapshot terbaru` (latest snapshot), the mtime of `daily_by_model.csv`, and the price `fetched_at`.
- If the latest snapshot is older than yesterday, or the report is older than `daily_by_model.csv`, re-run the pipeline or state the date.
- If the report is marked `INCOMPLETE`, do not present its total as a complete cost.

## Building the history (`collect.py`)

1. **Daily snapshot.** Runs all `$OMARCHY_PATH/bin/omarchy-agent-usage-*` wrappers in parallel (agent list from that folder, without `update`), then the internal scanner for Hermes/Claude/Codex/OpenCode, and writes `snapshots/<today>.json`.
   - **Network side effect:** some wrappers call the provider's limit API.
   - There is no price fetch in this stage.
2. **Backfill depth depends on the source.**
   - Hermes/Claude/OpenCode: all the local history that still exists.
   - **Codex: only the last 30 days** (the upstream rollout window).
   - Old snapshots keep the days that are no longer visible. **Do not delete old snapshots.**
3. **Merging.** The newest snapshot wins per (day, agent), except that an incomplete scan (`complete: false`) never overwrites a complete one.
4. **Parity check.**
   - The row total of each local agent is compared with the `recentDays` of its record (7 days). Differences are logged (`! parity …`) and written to `report.md`.
   - A difference outside the current day = the skill's scan composition has drifted from the upstream wrapper. Report it, and don't trust the per-model breakdown for that day.
5. **Idempotent.** Running twice on the same day overwrites the same snapshot.
6. **Options.** `--report` rebuilds the CSVs + report from snapshots without scanning. `--days N` changes the `report.md` range (default 7).

## Daily schedule (optional)

The history only fills on days the skill runs, so for daily tracking install a scheduled job **without an LLM** that runs `collect.py --all` (e.g. every day at 23:45). The skill does not create the job itself; ask the user first.

- Job command: `python3 <skill-folder>/scripts/collect.py --all`. It may be wrapped in a small shell script that sends stdout/stderr to `<data dir>/cron.log`.
- Trigger: cron, a systemd timer, or the agent's scheduler (e.g. `hermes cron`) in a no-agent/no-LLM mode. Stdout is empty on success.
- **Do not limit the number of repeats** (e.g. `--repeat N`): some schedulers stop silently after N runs, leaving holes in the daily history.
- After installing, check `<data dir>/cron.log` and the `Snapshot terbaru` stamp in `report.md` the next day.

### Cost simulation (`cost.py`)

Turns `daily_by_model.csv` into a cost estimate using **Artificial Analysis** prices (free Data API). The report must carry the attribution "Source: Artificial Analysis (artificialanalysis.ai)" with a link to <https://artificialanalysis.ai/>, plus "Based on data from Artificial Analysis" and "Created by omarchy-agent-usage, not by Artificial Analysis. Artificial Analysis does not endorse this report/tool" for derived numbers (already automatic in `cost`/`metrics`; include them too if you present price figures elsewhere). **Cards/charts shared publicly must also show the Artificial Analysis logo** (a Data Platform Terms requirement); the logo is not included in this repo, take it from their site. This is only a simulation: Claude Code / Codex / OpenCode are actually subscriptions, not metered.

**Cost format = exactly 2 decimal places** (`$168.23`, `$0.00`, `$1.70`), not 4 or 6 decimals, and don't drop trailing zeros. This applies to `cost_report.md`, `cost_daily.csv`, `cost_by_model.csv`, CLI stdout, and the cost columns in `metrics.py` (`costUSD`, `costPerTask`, totals, proxy). Use `cost.fmt()` for USD amounts. Ratios (cache-hit, output share) and tokens do **not** follow this rule.

```bash
python3 scripts/cost.py 2026-01-01          # per-model breakdown for one date
python3 scripts/cost.py                     # per-day summary (partial days flagged)
python3 scripts/cost.py --report            # write cost_daily.csv + cost_by_model.csv + cost_report.md
python3 scripts/cost.py --offline           # no API (cache, then seed)
python3 scripts/cost.py --report --strict   # exit 3 if INCOMPLETE
```

- **Price order:** optional local seed (`OMARCHY_USAGE_PRICING_SEED`) ← cache `~/.cache/omarchy-agent-usage/pricing.json` ← AA Data API.
  - The API is called only if `ARTIFICIAL_ANALYSIS_API_KEY` is set, not `--offline`, and the API cache is older than 24 hours (free tier: 100 requests per 24 hours; 1 fetch = 1-2 requests).
  - A fetch only overwrites slugs present in the fetch result.
  - Slugs that disappear keep their last price, marked `stale` + `last_seen`.
  - The seed file is never written.
- `cacheReadInputTokens` → **cacheHitPrice**; cache write → cacheWritePrice. If AA has no cache price: cacheHit = input, cacheWrite = 1.25 × input (noted in the report).
- `:free`/`-free` models → `$0`, checked BEFORE `MODEL_MAP`. Their paid equivalent appears in the section **"Model free — estimasi proxy"** (free models — proxy estimate), not in the total.
- **Paid models without a price** → left out of the total, but **listed** in the section **"Tidak terhitung"** (not counted: tokens + reason), and the day that contains them is marked `partial`.
  - If > 1% of paid tokens are unpriced → an **`INCOMPLETE`** banner (stdout + report).
  - A row without tokens (prompts only) is not "unpriced".
- Models pinned to a **successor** slug (their original slug vanished from AA) are listed in the report. Currently: `gpt-6.1-sol → gpt-6-2-sol` (same price) and `gpt-6-astra → gpt-6-2-astra` (the successor is cheaper than the old price; see `references/pricing-sources.md`).
- Do not mix cache read into "actual tokens"; report it separately.
- **AA only has current prices, not historical ones.** A cost report = a revaluation of historical usage at the prices of the fetch date. Always state `fetched_at`.
  - The question "is model X cheaper this week than last week?" cannot be answered from AA; it needs a Wayback snapshot of the provider's own price page (not Artificial Analysis) / the provider's newsroom.

## Dashboard metrics (`metrics.py`, Layer A)

Offline analytics from `daily_by_model.csv` + prices + `tasks.jsonl`. The separate `omarchy-ai-usage` QML plugin's contract is quota only.

```bash
python3 scripts/metrics.py [YYYY-MM-DD] [--report] [--offline] [--strict]
```

| Metric | Formula | Notes |
|---|---|---|
| Cost per agent | Σ cost per agent per day | free = $0 *known*; `partial` (+?) if some tokens are unpriced |
| Cache hit ratio | `cacheRead / (input + cacheRead + cacheWrite)` | the share of prompt-side input served from cache; output is not included |
| Token per prompt | non-cache: `(input + output) / prompts`; total: all tokens / prompts | prompts = ALL agent-day rows, including `(unknown)` |
| Cost per task | agent cost ÷ the agent's task weight (`ok`=1, `partial`=0.5, `fail`=0) | task = unique session in `tasks.jsonl`; a date/period aggregate = Σ cost ÷ Σ weight **only** over agent-days that have task rows |
| Output token | `outputTokens` + % of total | |
| Daily trend | delta vs the previous **calendar** day; calendar avg7d (zero days count) | avg7d appears 7 days after the agent's first usage |

Output: `metrics_daily.csv`, `metrics_by_agent.csv`, `metrics_report.md`.

- `costPerTask` notes:
  - `n/a (no tasks)`
  - `n/a (all tasks failed, weight 0)`
  - `n/a (no usage data)`: tasks exist but the snapshot does not yet cover that day
  - `n/a (unpriced tokens)`
  - `x.xxxx (free)`: all usage is free
- **Only agents with a writer hook have task rows** (e.g. OpenCode after the plugin was fixed). Claude/Codex cost per task = `n/a (no tasks)`. Never quote a single "cost per task for all agents" number.
- **Tokens/cost ≠ productivity.** The report must say this: agents are judged by the work they complete successfully, not by tokens or cost.
- **Do not replace cost per task with "cost per prompt"** without a clear label.

## Task signal

`OMARCHY_TASKS_FILE` (default `~/.local/state/omarchy/agents/tasks.jsonl`; append-only). Write with `omarchy-tasklog record --agent <a> --status ok|partial|fail [--session ID]` (a shim in `~/.local/bin` that calls `scripts/tasklog.py`). `tasklog.py summary` shows the number of tasks per day after session dedupe; it does not compute cost.

Hook status: every machine differs. A generic example is in `references/task-signal.md`. **If `references/task-signal.local.md` exists, read it too**: it holds this machine's hook notes (gitignored). What applies generally:
- An end-of-turn hook (e.g. `on_session_end`, `Stop`, `session.idle`) fires **per turn**, so one session can write dozens of rows; the reader dedupes per (agent, session).
- Make sure a row with `"agent": "<name>"` exists in `tasks.jsonl` before relying on that agent's task rows. Without a hook, that agent has no task rows.

Schema & semantics detail: `references/task-signal.md`. When testing, set `OMARCHY_TASKS_FILE` to a temp file.

## Weekly report (`weekly.py`)

`python3 scripts/weekly.py [--week-start YYYY-MM-DD]`. Reads snapshots only (no re-scan).
- Window = 7 calendar days starting at `--week-start` (default: the Monday of the week of the latest snapshot), clipped at the latest snapshot date. The current week → fewer than 7 days, and the title marks it "belum lengkap" (incomplete).
- A start after the latest snapshot → exit 2.

## Charts / video

The default style for cards/charts is in `references/visual-preferences.md`. Cost per agent for charts is **always taken from `cost_by_model.csv` / `cost_daily.csv`** (the result of `cost.py`, with separate input/output/cache prices). Never recompute "tokens × price" in chart code, because the numbers would differ from the report.

## Pitfalls

- **`spec_from_file_location` fails for the `omarchy-agent-usage-*` wrappers.** The files have no `.py` extension, so `spec.loader` is `None`. Use `importlib.machinery.SourceFileLoader` + `spec_from_loader` (`common.load_collector`).
- **`scan_codex_routed("codex")` returns 0 rows** when `codex_provider_urls()` is empty. Native rollouts are read via `codex_rollouts(..., native=True)` and then filtered by provider/owner like the wrapper does.
- **Rows are bucketed by local date** (`local_day`), so a session that crosses midnight is split across two days.
- **Scan cache.** `collect.py` calls the scanners directly; `cached_scan` (a per-day cache) is used only by the wrappers. But `claude_code_usage` and `codex_rollouts` write a shared index/cache in `~/.cache/omarchy/agent-usage/`, so a second run is still faster.
- **One day's numbers change after the collector re-runs.** Don't treat a day's cost/tokens as final before that day has passed; state the snapshot date when reporting.
- **AA slug drift.** If a model shows up in "Tidak terhitung" with the reason "slug … tidak ada di harga" (slug … not in the prices), or there is a `! slug AA … stale` warning, the AA slug has changed.
  - Find the replacement slug in the price cache, then update `MODEL_MAP` (+ `SUCCESSOR_OF` for a successor) and the table in `references/pricing-sources.md`.
  - **Don't report the total as complete before that.**
- **API fetch fails / no key.** `cost.py` uses the cache (then the seed) and prints a warning. Don't guess prices, and don't scrape AA pages.
- **`:free`/`-free` models must be checked BEFORE `MODEL_MAP`.** Never put a free model in `MODEL_MAP`; put its equivalent in `PROXY`.
- **Adding a metric:** add it to `aggregate_by_day_agent` → `metric_values` → `COLUMNS`/`CSV_FIELDS` in `metrics.py`. All presenters (CLI, CSV, report) use the same builder.
- **`cost per task` = cost per session, not per semantic task.**
- **Never write data into the skill folder.** All scripts write to the data dir; the price seed (`references/pricing.json`, local) is never written.

## Support files

- `references/collector-internals.md`: scanner signatures, how to load the collector, scan composition per agent, owner resolution.
- `references/pricing-sources.md`: the AA Data API, price mapping, successors, proxy footnotes, the price cache.
- `references/task-signal.md`: the `tasks.jsonl` schema, dedupe, semantics, a generic hook example. `references/task-signal.local.md` (gitignored, if present): this machine's hooks.
- `references/visual-preferences.md`: default style for usage charts/video (9:16 cards, cost number rules).
- `scripts/common.py`: paths, atomic IO, snapshot merge, task reader.
- `scripts/collect.py`: the collector (snapshot + CSV + report + parity check; `--all`).
- `scripts/cost.py`: pay-as-you-go cost simulation.
- `scripts/metrics.py`: dashboard metrics (Layer A).
- `scripts/weekly.py`: weekly summary from snapshots.
- `scripts/tasklog.py`: write/read `tasks.jsonl` (`record`, `summary`, `validate`).
- `tests/`: fixture tests (`python3 -m unittest discover -s tests -v`).
