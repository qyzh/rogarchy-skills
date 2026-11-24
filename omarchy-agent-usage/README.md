# omarchy-agent-usage

## What it is

A skill that reads the token usage of local AI agents on Omarchy (Hermes, Claude Code, Codex, OpenCode, grok, agy) and builds history and reports from it: tokens per day × per model, quota/limit percentage, pay-as-you-go cost simulation, metrics (cache hit, tokens per prompt, cost per task), and weekly summaries. All data is written to a data folder outside the skill folder. Prices come from Artificial Analysis (see Credits).

**Linux with Omarchy only.** The skill reads the `omarchy-agent-usage-*` wrappers and the agents' local stores; without Omarchy this skill is of no use.

## When to use / not use

Use it when you ask to:

- Check tokens used, whether a quota or limit is used up, which agent uses the most.
- Keep a per-day usage history, or get this week's report.
- Simulate the cost if usage were paid per token, cache hit ratio, tokens per prompt, cost per task.

Don't use it when:

- You want to build an Omarchy plugin that displays usage (use `omarchy-plugin-authoring`).
- You need a cloud provider billing dashboard. This skill only reads local stores.

The skill does not run `omarchy-agent-usage-update` unless asked, because that command can switch the account that is logged in.

## Requirements

| Requirement | Status | Purpose |
|---|---|---|
| Linux + Omarchy | **Required** | Provides the `omarchy-agent-usage-*` wrappers in `$OMARCHY_PATH/bin`. |
| Python 3 | **Required** | Runs the scripts in `scripts/`. Standard library only. |
| Internet access + `ARTIFICIAL_ANALYSIS_API_KEY` | Optional | Fetches prices from the free Artificial Analysis Data API. Without a key there are no network calls; the skill uses the cache/seed. |
| `omarchy-plugin-authoring` (outside this repo) | Route only | Handoff target for building a usage display plugin. |
| [`dither-data-viz`](../dither-data-viz/README.md) (this repo) | Optional | Makes cards/charts from this skill's output CSVs. |

## Configuration

| Variable | Meaning | Default |
|---|---|---|
| `OMARCHY_USAGE_DATA` | Data folder (snapshots, CSVs, reports) | `~/.local/state/omarchy/agents/usage-history` |
| `ARTIFICIAL_ANALYSIS_API_KEY` | Free Artificial Analysis Data API key ([get one here](https://artificialanalysis.ai/api-key-management-redirect)). Env var only, never write it to a file | (empty: no network calls) |
| `OMARCHY_USAGE_PRICING_CACHE` | Cache of prices fetched from the API (reused for 24 hours) | `~/.cache/omarchy-agent-usage/pricing.json` |
| `OMARCHY_USAGE_PRICING_SEED` | Optional read-only local price seed (not in the repo) | `references/pricing.json` (gitignored) |
| `OMARCHY_TASKS_FILE` | Task signal file (`tasks.jsonl`) | `~/.local/state/omarchy/agents/tasks.jsonl` |
| `OMARCHY_PATH` | Omarchy install location | `/usr/share/omarchy` |

For tests, point all of them at a temporary folder.

The values above can also be stored in the settings file `${XDG_CONFIG_HOME:-~/.config}/rogarchy-skills/config.env` (via [`rogarchy-setup`](../rogarchy-setup/README.md)), except `ARTIFICIAL_ANALYSIS_API_KEY`, which comes from the env var only; the env var still wins, then that file, then the default.

## Usage examples

```text
How many tokens did I use this week, and what would it cost if paid per token?
```

Running the pipeline by hand (from the repo folder):

```bash
S=omarchy-agent-usage/scripts
python3 $S/collect.py --all             # scan + snapshot + CSV + cost + metrics + weekly
python3 $S/collect.py --report --all --offline   # rebuild from snapshots, no scan and no network
python3 $S/cost.py 2026-01-01           # per-model cost breakdown for one date
python3 $S/weekly.py                    # summary of the current week
```

Running the tests (they don't touch real state; network is disabled):

```bash
cd omarchy-agent-usage && python3 -m unittest discover -s tests -v
```

For daily tracking, set up a scheduled job without an LLM that runs `collect.py --all`; the steps are in SKILL.md, section "Jadwal harian" (daily schedule).

## Folder contents

```
omarchy-agent-usage/
├── SKILL.md                       # instructions for the agent
├── references/
│   ├── collector-internals.md     # scanner signatures, per-agent scan composition
│   ├── pricing-sources.md         # AA price sources, model mapping, successors, proxies
│   ├── pricing.json               # optional local price seed (gitignored, not in the repo)
│   ├── task-signal.md             # tasks.jsonl schema, dedupe, generic hook examples
│   ├── task-signal.example.md     # template for this machine's hook notes (copy to task-signal.local.md)
│   ├── task-signal.local.md       # your machine's hook notes (optional, gitignored)
│   └── visual-preferences.md      # default style for usage cards/charts
├── scripts/
│   ├── common.py                  # paths, atomic IO, snapshot merge, task reader
│   ├── collect.py                 # collector: snapshot + CSV + report + parity check
│   ├── cost.py                    # pay-as-you-go cost simulation
│   ├── metrics.py                 # dashboard metrics
│   ├── weekly.py                  # weekly summary
│   └── tasklog.py                 # write/read tasks.jsonl
└── tests/                         # unittest tests + fixtures (including the config.env reader)
```

## Credits

A small part of the code in `scripts/collect.py` (the billing detection regexes and predicates) is copied from the `omarchy-agent-usage-*` wrappers of [Omarchy](https://github.com/omacom/omarchy) (MIT, © David Heinemeier Hansson); see [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). Not affiliated with or endorsed by Omarchy/Basecamp.

Source: [Artificial Analysis (artificialanalysis.ai)](https://artificialanalysis.ai/). Token prices are fetched through their free Data API with your own key (`ARTIFICIAL_ANALYSIS_API_KEY`), stored in a local cache, and not included in this repo. Every cost report includes "Source: Artificial Analysis (artificialanalysis.ai)" with a link, "Based on data from Artificial Analysis", and "Created by omarchy-agent-usage, not by Artificial Analysis. Artificial Analysis does not endorse this report/tool". Cards or charts shared publicly must also show the Artificial Analysis logo (a Data Platform Terms requirement; the logo is not included in the repo). Source details are in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md); API use is subject to Artificial Analysis's terms. This is not legal advice.

---

Version 0.3.0 · MIT License · [Repo README](../README.md)
