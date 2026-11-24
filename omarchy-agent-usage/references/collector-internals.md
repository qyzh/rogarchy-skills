# Omarchy collectors.py — internals

`$OMARCHY_PATH/shell/plugins/agents/collectors.py` is the shared plumbing every
`$OMARCHY_PATH/bin/omarchy-agent-usage-*` script imports, and the only source
of per-day × per-model rows.

**It is importable, but not side-effect free:**
- `claude_code_usage` writes a Claude scan index;
- `codex_rollouts` writes a shared rollout file cache;
- both live under `${XDG_CACHE_HOME:-~/.cache}/omarchy/agent-usage/`.

Reading through it is safe for usage data, but it does touch those caches.

## Loading the per-agent collector scripts

The wrappers are Python without a `.py` extension.
`importlib.util.spec_from_file_location` returns a spec whose `loader` is
`None`, so load them with an explicit source loader. Resolve them under
`$OMARCHY_PATH/bin`, not `/usr/bin`, so `omarchy dev link` setups load the same
version the update script runs:

```python
import importlib.machinery, importlib.util, os, sys
OMARCHY = os.environ.setdefault("OMARCHY_PATH", "/usr/share/omarchy")
sys.path.insert(0, f"{OMARCHY}/shell/plugins/agents")


def load_collector(path, name):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


hermes = load_collector(f"{OMARCHY}/bin/omarchy-agent-usage-hermes", "hermes_usage")
opencode = load_collector(f"{OMARCHY}/bin/omarchy-agent-usage-opencode", "opencode_usage")
```

The wrappers have `__main__` guards, so loading does not run them. Do **not**
load the codex wrapper as a module: it builds module-level state
(`ENV = runtime_env()`, `STATS = Stats()`). `scripts/collect.py` copies its
predicates instead.

## UsageRow

Every shared reader returns
`UsageRow(day, session, provider, model, input_tokens, output_tokens,
cache_read, cache_write, prompts=1)`.

`day` is the LOCAL date (`YYYY-MM-DD`). A row with no tokens carries prompts
only (Hermes books every prompt this way; its model rows have `prompts=0`).

## Scan composition per agent (what each wrapper bills)

`scripts/collect.py` mirrors these exactly. Its parity check compares the
result with the wrapper's `recentDays` to catch future drift.

| Agent | Sources | Filter / model name |
| --- | --- | --- |
| Hermes | `hermes.harness_rows(hermes.AGENT_ID)` (every `state.db`) | owner resolved inside; tokenless rows = prompts |
| Claude Code | `C.claude_code_usage("claude")` + `C.scan_pi_sessions(r'"provider"\s*:\s*"anthropic"', accept)` + `C.scan_opencode(['anthropic"'], accept)` | `accept = provider == "anthropic"`; pi model `row.model or "claude"`; opencode model = last path segment of the id |
| Codex | `C.codex_rollouts(C.codex_rollout_cache(), reuse=True, native=True)` + `C.scan_pi_sessions(PI_PATTERN, pi_billed_here)` + `C.scan_opencode(['openai"'], provider == "openai")` | rollouts only with `record["provider"] in ("", C.CODEX_NATIVE_PROVIDER)` **and** `C.codex_route_owner(native, model, C.codex_provider_urls()) == "codex"`; pi accepts provider `openai-codex` or `api` starting `openai-codex`. Rollouts are read back **30 days** (`CODEX_WINDOW_DAYS`) |
| OpenCode | `C.scan_pi_sessions(r'"provider"\s*:\s*"opencode(-go)?"', opencode.billed_here)` + `C.scan_opencode(opencode.PROVIDERS, opencode.billed_here)` | model `opencode.model_name(row.model)` |

Other agents (agy, grok, copilot, openrouter, cursor, ...) are read from their
own records / remote APIs and have no local row source, so only `recentDays`
totals are available. Do not invent a per-model breakdown for them.

## Owner resolution

- `claude_code_usage(owner)` keeps replies where
  `claude_code_owner(model, base_url) == owner`.
- `scan_codex_routed(owner)` only covers ROUTED providers; it returns `[]`
  when `codex_provider_urls()` is empty. Native rollouts are separate (above).
- `scan_opencode(providers, accept)` takes provider ids as LIKE prefixes and
  an `accept(provider, model, entry)` predicate.

## Stats aggregation

`Stats` aggregates rows into the record shape (`today*`, `recentDays`,
`modelUsage`, `activeDates`). `Stats.recent` keeps 7-day totals only, so there
is no built-in per-day × per-model export; that is why the raw rows are needed.
`recentDays[].messageCount` holds **tokens**.

`Stats.add_row(row, model)` books a row; a row with no tokens books its
prompts alone.

## Snapshot layout

`collect.py` snapshots nest the wrapper record under `agents.<name>.record`
(`today*`, `recentDays`, `modelUsage`, `limits[]`); scanned per-day rows live
in `agents.<name>.byDayByModel`. For quota questions read `limits[]` from
every agent's record in the latest snapshot — `report.md`'s limit table can
omit agents whose records carry limits.

## Cache behaviour

- `cached_scan` (used by the **wrappers**, not by `collect.py`) caches the
  wrapper's whole scan keyed by the scan date. `read_cached_scan` rejects a
  cache whose `scanDate != today()`. A scan that could not read every source is
  not cached (`complete=False`).
- `collect.py` calls the scanners directly every time. Repeat runs are still
  fast because the Claude index and the Codex file cache (above) are reused.
