# Token price sources

Used by `scripts/cost.py`.

## Price files

| File | Role |
|---|---|
| `references/pricing.json` | **Optional local seed**, gitignored (not in the repo), never written by code. Can be created from the runtime cache. Skipped if absent. |
| `~/.cache/omarchy-agent-usage/pricing.json` (`OMARCHY_USAGE_PRICING_CACHE`) | Runtime cache. The merge of seed ← old cache ← API fetch. |

Load order:
1. the seed (if present);
2. overwritten by the cache;
3. overwritten by the API fetch (only if there is a key, not `--offline`, and the API cache is > 24 hours old).

A fetch **overwrites per slug**: a slug missing from the latest fetch keeps its last price with `stale: true` and `last_seen`.

## Source: Artificial Analysis Data API (free tier)

- Documentation: https://artificialanalysis.ai/data-api/docs · https://artificialanalysis.ai/api-reference
- Endpoint: `GET https://artificialanalysis.ai/api/v2/language/models/free` (query `page`, starting at 1; response `pagination.has_more`). The `/api/v2/language/models` path is Pro+ only.
- Auth: the `x-api-key` header, its value from the env var `ARTIFICIAL_ANALYSIS_API_KEY`.
- Free-tier rate limit: 100 requests per 24-hour window (starting from the first request); a 429 carries `Retry-After`. The 24-hour cache keeps usage far below that.
- Required attribution: "Source: Artificial Analysis (artificialanalysis.ai)" with a link to https://artificialanalysis.ai/. Derived numbers (computed costs): "Based on data from Artificial Analysis" + "Artificial Analysis does not endorse this report/tool". Cards/charts shared publicly must carry the AA logo.
- Unit: USD per **1 million tokens**. Model fields: `slug`, `name`, `pricing.price_1m_input_tokens`, `pricing.price_1m_output_tokens`, `pricing.price_1m_cache_hit_tokens`, `pricing.price_1m_cache_write_tokens` (the cache prices can be `null`/absent, not guaranteed on the free tier).
- `cost.parse_api_models()` maps them to the internal format `{input, output, cacheHit, cacheWrite}`; `slug` is the key (`MODEL_MAP` maps local models to that slug).
- Without a key: no network calls. No scraping fallback.

Unavailable cache prices: cacheHit = the input price, cacheWrite = 1.25 × the input price. This assumption is stated in the report.

## Local model → AA slug mapping (`MODEL_MAP`)

| Local model | AA slug | Note |
|---|---|---|
| `claude-opus-5-5` | `claude-opus-5-5` | |
| `claude-sonnet-5-5` | `claude-sonnet-5-5` | |
| `claude-fable-5-2` | `claude-fable-5-2` | |
| `claude-haiku-5-5` | `claude-haiku-5-5` | |
| `gpt-6-luna` | `gpt-6-luna` | |
| `gpt-6.1-sol` | `gpt-6-2-sol` | **successor**; the original slug `gpt-6-1-sol` vanished from AA (fetch 2026-11-19) |
| `gpt-6.1-terra` | `gpt-6-1-terra` | |
| `gpt-6-astra` | `gpt-6-2-astra` | **successor**; the original slug `gpt-6-astra` vanished from AA (fetch 2026-11-19) |

Successor models are listed in `SUCCESSOR_OF` in `cost.py` and in every report (the report line "Dipatok ke harga slug successor", i.e. pinned to the successor slug's price).

**`:free`/`-free` models must NOT be in this table.** Their rule is $0; their equivalent is used as a proxy (the table below). `cost.py` checks `is_free` before `MODEL_MAP`. If the order were reversed, a free model that has an equivalent would be billed by mistake.

## Models without a price

A paid model that is not in `MODEL_MAP`, or whose slug is not in the prices:
- is left out of the total, but **listed** in the "Tidak terhitung" section (not counted; `cost_report.md`, `metrics_report.md`) with its token count and the reason;
- the day that contains it is marked `partial`;
- more than 1% of paid tokens unpriced → an `INCOMPLETE` banner (`--strict` → exit 3).

A row without tokens (`(unknown)`, prompts only) does not count as "unpriced".

**If a slug drifts:** find the replacement slug in the price cache, then update `MODEL_MAP` (+ `SUCCESSOR_OF`) and this table.

## Proxy footnote for free models

A free model = $0. To stay informative, the report has a section "Model free — estimasi proxy" (free models, proxy estimate: as if pinned to the equivalent's price), only when AA has a similar model:

| Free model | Proxy |
|---|---|
| `meituan/longcat-2.5:free`, `meituan/longcat-2.5-preview:free`, `meituan/longcat-2.0:free` | `longcat-2-0` |
| `tencent/hy4-flash:free` | `tencent-hy4` |
| `GLM-5.3-flash-free` | `glm-5-3-flash` |
| `deepseek-v4.1-flash-free` | `deepseek-v4-1-flash-1017` |
| `minimax-m3.1-flash-free` | `minimax-m3-1-flash` |
| `upstage/solar-pro4:free` | `solar-pro4` |
| `upstage/solar-mini4:free` | `solar-mini4` |
| `reflection/beam-1.0-501b-a23b:free` | `reflection-beam` |

No proxy (no equivalent): `stepfun/*`, `poolside/*`, `stealth/*`, `muse-spark-*`, `beam-free`, `big-pickle`, `nemotron-*`.

## Important: prices can go up or down

- AA shows **current** prices, not historical ones. This simulation means "as if historical usage were priced at today's prices".
- Every report states `fetched_at` + `mode` (live/cache/seed).
- **AA does not provide history.** To compare prices between weeks, use Wayback Machine snapshots of the provider's own price page (not Artificial Analysis) or the provider's newsroom.
