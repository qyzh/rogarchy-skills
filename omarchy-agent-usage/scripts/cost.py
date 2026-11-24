#!/usr/bin/env python3
"""Simulasi biaya token (pay-as-you-go) dari daily_by_model.csv di data dir.

Harga: seed lokal opsional (OMARCHY_USAGE_PRICING_SEED) <- cache runtime
(~/.cache/omarchy-agent-usage/pricing.json) <- Artificial Analysis Data API
(hanya bila ARTIFICIAL_ANALYSIS_API_KEY di-set, cache < 24 jam tidak memanggil
API, dan bukan --offline). Tanpa kunci: tanpa panggilan jaringan.
Atribusi wajib: "Source: Artificial Analysis (artificialanalysis.ai)" + tautan; angka turunan: "Based on data from Artificial Analysis" + pernyataan non-endorsement. Slug yang hilang dari fetch terbaru TIDAK dibuang: harga
terakhirnya dipakai dan ditandai stale (last_seen). Ini murni simulasi:
Claude Code / Codex / OpenCode sebenarnya langganan.

Aturan:
  - model :free / -free -> $0 (dicek SEBELUM MODEL_MAP); padanan berbayar = footnote proxy
  - cacheReadInputTokens dikenai cacheHitPrice; cache write dikenai cacheWritePrice
    (tak tersedia di AA -> cacheHit = harga input, cacheWrite = 1.25 x input, dicatat)
  - model berbayar tanpa harga -> di luar total, DICANTUMKAN di tabel "Tidak terhitung";
    hari dengan token tak terharga = partial; >1% token berbayar tak terharga = INCOMPLETE
  - baris tanpa token (prompt saja) = "tokenless", bukan "tak terharga"
"""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

import argparse  # noqa: E402
import csv  # noqa: E402
import datetime as dt  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402
from collections import defaultdict  # noqa: E402

API_URL = "https://artificialanalysis.ai/api/v2/language/models/free"
KEY_ENV = "ARTIFICIAL_ANALYSIS_API_KEY"
KEY_URL = "https://artificialanalysis.ai/api-key-management-redirect"
AA_URL = "https://artificialanalysis.ai/"
ATTRIBUTION = "Source: Artificial Analysis (artificialanalysis.ai)"                       # plain text
ATTRIBUTION_MD = f"[{ATTRIBUTION}]({AA_URL})"                                           # markdown / HTML output
DERIVED_NOTE = ("Based on data from Artificial Analysis. "
                "Created by omarchy-agent-usage, not by Artificial Analysis. "
                "Artificial Analysis does not endorse this report/tool.")
MAX_PAGES = 10                   # batas halaman per fetch (tier gratis: 100 request / 24 jam)
CACHE_TTL_HOURS = 24             # cache API lebih muda dari ini -> API tidak dipanggil

# model lokal -> slug Artificial Analysis. Slug = field `slug` di Data API AA.
MODEL_MAP = {
    "claude-opus-5-5": "claude-opus-5-5",
    "claude-sonnet-5-5": "claude-sonnet-5-5",
    "claude-fable-5-2": "claude-fable-5-2",
    "claude-haiku-5-5": "claude-haiku-5-5",
    "gpt-6-luna": "gpt-6-luna",
    "gpt-6.1-sol": "gpt-6-2-sol",      # SUCCESSOR: slug asli gpt-6-1-sol hilang dari AA (2026-11-19)
    "gpt-6.1-terra": "gpt-6-1-terra",
    "gpt-6-astra": "gpt-6-2-astra",    # SUCCESSOR: slug asli gpt-6-astra hilang dari AA (2026-11-19)
    # model free TIDAK dimasukkan ke sini: harga mereka $0, padanannya
    # (bila ada) dipakai sebagai footnote proxy lihat PROXY di bawah.
}

# model lokal yang dipatok ke slug SUCCESSOR -> slug asli (sudah hilang dari AA).
# Dicantumkan di laporan supaya revaluasi ini tidak tersembunyi.
SUCCESSOR_OF = {"gpt-6.1-sol": "gpt-6-1-sol", "gpt-6-astra": "gpt-6-astra"}

INCOMPLETE_THRESHOLD = 0.01      # >1% token berbayar tak terharga -> INCOMPLETE
CACHE_WRITE_FALLBACK = 1.25      # x harga input bila cacheWritePrice tak tersedia

# model free yang TIDAK ditampilkan proxy-nya (tak ada padanan di AA)
FREE_NO_PROXY = {
    "stepfun/step-3.7-flash:free", "stepfun/step-5-preview:free",
    "poolside/laguna-s-2.1:free", "stealth/space-bunny-alpha",
    "stealth/missingno", "stealth/crouton-alpha",
    "muse-spark-1.2-contributor-free", "muse-spark-1.3-contributor-free",
    "glm-4.5-flash",  # Z.AI free-tier model; AA free API has no glm-4-5-flash slug
    "beam-free", "big-pickle", "nemotron-3.5-super-vl-free",
}

# model free -> padanan berbayar untuk footnote
PROXY = {
    "meituan/longcat-2.5:free": "longcat-2-0",
    "meituan/longcat-2.5-preview:free": "longcat-2-0",
    "meituan/longcat-2.0:free": "longcat-2-0",
    "tencent/hy4-flash:free": "tencent-hy4",
    "GLM-5.3-flash-free": "glm-5-3-flash",
    "deepseek-v4.1-flash-free": "deepseek-v4-1-flash-1017",
    "minimax-m3.1-flash-free": "minimax-m3-1-flash",
    "upstage/solar-pro4:free": "solar-pro4",
    "upstage/solar-mini4:free": "solar-mini4",
    "reflection/beam-1.0-501b-a23b:free": "reflection-beam",
}


def api_key():
    """Kunci API HANYA dari env var; tidak pernah ditulis ke file/log."""
    return os.environ.get(KEY_ENV, "").strip()


def parse_api_models(models):
    """Peta daftar model Data API AA -> {slug: {input, output, cacheHit, cacheWrite}}.

    Satuan USD per 1 juta token. Harga cache yang tidak ada tetap None
    (nanti dipakai asumsi di effective_prices). Model tanpa harga input
    DAN output dilewati."""
    prices = {}
    for m in models:
        slug = m.get("slug")
        pr = m.get("pricing") or {}
        i, o = pr.get("price_1m_input_tokens"), pr.get("price_1m_output_tokens")
        if not slug or slug in prices or (i is None and o is None):
            continue
        prices[slug] = {
            "input": i or 0, "output": o or 0,
            "cacheHit": pr.get("price_1m_cache_hit_tokens"),
            "cacheWrite": pr.get("price_1m_cache_write_tokens"),
        }
    return prices


def fetch_prices(key):
    """Ambil harga dari Artificial Analysis Data API (tier gratis). Tanpa scraping."""
    models, page = [], 1
    while page <= MAX_PAGES:
        req = urllib.request.Request(f"{API_URL}?page={page}",
                                     headers={"x-api-key": key, "Accept": "application/json",
                                              "User-Agent": "omarchy-agent-usage"})
        try:
            body = json.loads(urllib.request.urlopen(req, timeout=45).read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code}" + (f" (Retry-After {e.headers.get('Retry-After')}s)"
                                                    if e.code == 429 else "")) from None
        models += body.get("data") or []
        if not (body.get("pagination") or {}).get("has_more"):
            break
        page += 1
    prices = parse_api_models(models)
    if not prices:
        raise RuntimeError("tidak ada harga terparse")
    return prices


def required_slugs():
    return set(MODEL_MAP.values()) | set(PROXY.values())


def _now_iso():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _read_price_file(path):
    try:
        d = json.loads(Path(path).read_text())
    except FileNotFoundError:
        return {}, {}
    except (OSError, json.JSONDecodeError) as e:
        print(f"! file harga rusak {path}: {e}", file=sys.stderr)
        return {}, {}
    return d.get("prices") or {}, d.get("meta") or {}


def _warn_slugs(prices):
    for s in sorted(required_slugs()):
        p = prices.get(s)
        if p is None:
            print(f"! slug AA '{s}' tidak ada di harga (live/cache/seed): model terkait TIDAK terharga",
                  file=sys.stderr)
        elif p.get("stale"):
            print(f"! slug AA '{s}' tidak ada di fetch terakhir; dipakai harga terakhir "
                  f"(last_seen {p.get('last_seen')}, stale)", file=sys.stderr)


def _cache_fresh(cache_meta, cache_p):
    """True bila cache berasal dari API dan umurnya < CACHE_TTL_HOURS."""
    if not cache_p or cache_meta.get("source") != API_URL:
        return False
    try:
        age = dt.datetime.now().astimezone() - dt.datetime.fromisoformat(cache_meta["fetched_at"])
    except (KeyError, ValueError):
        return False
    return dt.timedelta(0) <= age < dt.timedelta(hours=CACHE_TTL_HOURS)


def load_prices(offline=False):
    """Return (prices, meta). Urutan: seed <- cache <- live (bila tidak offline).

    API MENIMPA per slug, tidak MENGGANTI seluruh tabel: slug yang tak ada di
    fetch terbaru tetap dengan harga terakhir, stale=True, last_seen dipertahankan.
    Seed tidak pernah ditulis."""
    seed_p, seed_meta = _read_price_file(common.pricing_seed_path())
    base = {s: dict(v, last_seen=v.get("last_seen") or seed_meta.get("fetched_at"),
                    stale=bool(v.get("stale", False)))
            for s, v in seed_p.items()}
    cache_path = common.pricing_cache_path()
    cache_p, cache_meta = _read_price_file(cache_path)
    base.update(cache_p)
    meta = dict(cache_meta if cache_p else seed_meta)
    meta["mode"] = "cache" if cache_p else "seed"
    if not offline:
        key = api_key()
        if not key:
            print(f"! {KEY_ENV} belum di-set: tidak ada panggilan jaringan; pakai {meta['mode']}. "
                  f"Kunci gratis: {KEY_URL} lalu `export {KEY_ENV}=...`", file=sys.stderr)
        elif _cache_fresh(cache_meta, cache_p):
            meta["mode"] = "cache (segar)"
        else:
            try:
                live = fetch_prices(key)
            except Exception as e:
                print(f"! fetch API gagal ({e}); pakai {meta['mode']}", file=sys.stderr)
            else:
                now = _now_iso()
                merged = {s: dict(v, stale=True) for s, v in base.items()}
                for s, v in live.items():
                    merged[s] = dict(v, last_seen=now, stale=False)
                meta = {"fetched_at": now, "source": API_URL, "mode": "live", "schema": 2}
                common.atomic_write_json(cache_path, {"meta": meta, "prices": merged}, indent=1, sort_keys=True)
                _warn_slugs(merged)
                return merged, meta
    if not base:
        sys.exit("! tidak ada harga: cache + seed kosong dan API tidak dipakai/gagal (set ARTIFICIAL_ANALYSIS_API_KEY)")
    _warn_slugs(base)
    return base, meta


def is_free(model):
    return (model.endswith(":free") or model.endswith("-free")
            or model in FREE_NO_PROXY)


def prices_for(model, prices):
    """-> (kind, prices_dict, label). kind: paid | free | unknown"""
    # free dulu: model :free/-free SELALU $0, walaupun AA punya padanannya.
    # Padanan itu dipakai sebagai footnote proxy, bukan harga tagihan.
    if is_free(model):
        return "free", None, None
    slug = MODEL_MAP.get(model)
    if slug and slug in prices:
        return "paid", prices[slug], slug
    return "unknown", None, None


def effective_prices(p):
    """-> (input, output, cacheHit, cacheWrite, assumed). Fallback bila AA tak punya harga cache."""
    assumed = []
    ch = p.get("cacheHit")
    if ch is None:
        ch = p["input"]
        assumed.append("cacheHit=input")
    cw = p.get("cacheWrite")
    if cw is None:
        cw = p["input"] * CACHE_WRITE_FALLBACK
        assumed.append("cacheWrite=1.25×input")
    return p["input"], p["output"], ch, cw, assumed


def cost_of(row, p):
    i, o, ch, cw, _ = effective_prices(p)
    return (row["inputTokens"] * i + row["outputTokens"] * o
            + row["cacheReadInputTokens"] * ch
            + row["cacheCreationInputTokens"] * cw) / 1e6


def classify(row, prices):
    """-> (kind, price_dict, slug). kind: paid | free | unknown | tokenless.
    Free DULU (lewat prices_for), lalu MODEL_MAP. Baris tanpa token yang tak
    terharga = tokenless (prompt/sesi saja), bukan unknown."""
    kind, p, slug = prices_for(row["model"], prices)
    if kind == "unknown" and row["tokens"] == 0:
        return "tokenless", None, None
    return kind, p, slug


def build_recs(rows, prices):
    """Tiap baris + kind, cost (paid: USD; free/tokenless: 0.0; unknown: None), proxy, label."""
    recs = []
    for r in rows:
        kind, p, slug = classify(r, prices)
        cost = cost_of(r, p) if kind == "paid" else (None if kind == "unknown" else 0.0)
        proxy = None
        if kind == "free" and r["model"] in PROXY and PROXY[r["model"]] in prices:
            proxy = cost_of(r, prices[PROXY[r["model"]]])
        recs.append(dict(r, kind=kind, cost=cost, proxy=proxy, label=slug))
    return recs


def pricing_summary(recs, prices):
    unpriced = defaultdict(lambda: [0, 0])     # (agent, model) -> [tokens, rows]
    proxies = defaultdict(lambda: [0, 0.0])    # model -> [tokens, usd]
    partial_days, successors, stale, assumed = set(), set(), {}, set()
    paid_tokens = unpriced_tokens = 0
    for x in recs:
        k = x["kind"]
        if k == "paid":
            paid_tokens += x["tokens"]
            if x["model"] in SUCCESSOR_OF:
                successors.add(x["model"])
            p = prices[x["label"]]
            if p.get("stale"):
                stale[x["label"]] = p.get("last_seen")
            if effective_prices(p)[4]:
                assumed.add(x["label"])
        elif k == "unknown":
            unpriced_tokens += x["tokens"]
            unpriced[(x["agent"], x["model"])][0] += x["tokens"]
            unpriced[(x["agent"], x["model"])][1] += 1
            partial_days.add(x["date"])
        elif k == "free" and x["proxy"] is not None:
            proxies[x["model"]][0] += x["tokens"]
            proxies[x["model"]][1] += x["proxy"]
    denom = paid_tokens + unpriced_tokens
    ratio = unpriced_tokens / denom if denom else 0.0
    return {"unpriced": dict(unpriced), "proxies": dict(proxies),
            "partial_days": sorted(partial_days), "paid_tokens": paid_tokens,
            "unpriced_tokens": unpriced_tokens, "ratio": ratio,
            "incomplete": ratio > INCOMPLETE_THRESHOLD, "successors": sorted(successors),
            "stale": stale, "assumed": sorted(assumed)}


def pricing_sections_md(s):
    """Markdown sections reused by cost_report.md AND metrics_report.md."""
    pct = s["ratio"] * 100
    thr = INCOMPLETE_THRESHOLD * 100
    status = (f"**INCOMPLETE** — {pct:.2f}% token berbayar tidak terharga (ambang {thr:.0f}%). "
              f"Total BUKAN biaya lengkap." if s["incomplete"]
              else f"LENGKAP — token tak terharga {pct:.4f}% (≤ ambang {thr:.0f}%)")
    L = ["## Kelengkapan harga", "", f"- Status: {status}",
         f"- Token berbayar terharga: {s['paid_tokens']:,} · token tak terharga: {s['unpriced_tokens']:,}",
         f"- Hari partial (ada token tak terharga): {', '.join(s['partial_days']) or '—'}", "",
         "### Tidak terhitung (di luar total)", ""]
    if s["unpriced"]:
        L += ["| Agent | Model | Token | Baris | Alasan |", "|---|---|---:|---:|---|"]
        for (agent, model), (tok, n) in sorted(s["unpriced"].items(), key=lambda z: -z[1][0]):
            slug = MODEL_MAP.get(model)
            reason = "tidak ada di MODEL_MAP" if not slug else f"slug `{slug}` tidak ada di harga"
            L.append(f"| {agent} | {model} | {tok:,} | {n} | {reason} |")
    else:
        L.append("Tidak ada.")
    L.append("")
    if s["successors"]:
        L += ["### Dipatok ke harga slug successor", "",
              "| Model lokal | Slug dipakai | Slug asli (hilang dari AA) |", "|---|---|---|"]
        L += [f"| {m} | {MODEL_MAP[m]} | {SUCCESSOR_OF[m]} |" for m in s["successors"]]
        L.append("")
    if s["stale"]:
        L += ["### Harga stale (slug tak ada di fetch terakhir)", "", "| Slug | last_seen |", "|---|---|"]
        L += [f"| {k} | {v or '?'} |" for k, v in sorted(s["stale"].items())]
        L.append("")
    if s["assumed"]:
        L += ["### Asumsi harga cache", "",
              f"- Slug tanpa cacheHitPrice/cacheWritePrice dari AA: {', '.join(s['assumed'])} → "
              "cacheHit = harga input, cacheWrite = 1.25 × harga input.", ""]
    L += ["### Model free ($0) — estimasi proxy (TIDAK masuk total)", ""]
    if s["proxies"]:
        L += ["| Model free | Proxy AA | Token | Seandainya USD |", "|---|---|---:|---:|"]
        for m, (tok, usd) in sorted(s["proxies"].items(), key=lambda z: -z[1][1]):
            L.append(f"| {m} | {PROXY[m]} | {tok:,} | {usd:.2f} |")
    else:
        L.append("Tidak ada.")
    L.append("")
    return L


def read_rows(path=None):
    p = Path(path) if path else common.data_dir() / "daily_by_model.csv"
    if not p.exists():
        sys.exit(f"! {p} belum ada — jalankan collect.py dulu")
    with open(p, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k in ("tokens", "inputTokens", "outputTokens",
                  "cacheReadInputTokens", "cacheCreationInputTokens",
                  "prompts", "sessions"):
            r[k] = int(r[k])
    return rows


def fmt(x):
    return f"{x:,.2f}"


def write_report(recs, prices, meta, summary, out_dir=None):
    out = Path(out_dir) if out_dir else common.data_dir()
    daily, bymodel, byagent = defaultdict(float), defaultdict(float), defaultdict(float)
    for x in recs:
        if x["kind"] == "paid":
            daily[x["date"]] += x["cost"]
            bymodel[(x["date"], x["agent"], x["model"])] += x["cost"]
            byagent[x["agent"]] += x["cost"]
    partial = set(summary["partial_days"])
    days = sorted(set(daily) | partial)
    common.write_csv_rows(out / "cost_daily.csv", ["date", "costUSD", "partial"],
                          [[d, f"{daily.get(d, 0.0):.2f}", int(d in partial)] for d in days])
    common.write_csv_rows(out / "cost_by_model.csv", ["date", "agent", "model", "costUSD"],
                          [[*k, f"{bymodel[k]:.2f}"] for k in sorted(bymodel)])
    lines = ["# Simulasi Biaya Token (pay-as-you-go)", "",
             f"- Dibuat: {_now_iso()}",
             f"- Harga: {meta.get('mode')} · fetched_at {meta.get('fetched_at', '?')}",
             f"- {ATTRIBUTION_MD} · {DERIVED_NOTE}",
             f"- API: {API_URL} (AA hanya punya harga SAAT INI: ini revaluasi pemakaian historis)",
             *common.freshness_lines(out), ""]
    if summary["incomplete"]:
        lines += [f"> **INCOMPLETE:** {summary['ratio'] * 100:.2f}% token berbayar tidak terharga — "
                  "total di bawah lebih rendah dari biaya sebenarnya.", ""]
    lines += ["## Total per agent", "", "| Agent | Biaya USD |", "|---|---:|"]
    lines += [f"| {a} | {byagent[a]:.2f} |" for a in sorted(byagent)]
    lines += ["", "## Total per hari", "", "| Tanggal | Biaya USD | Partial |", "|---|---:|:---:|"]
    lines += [f"| {d} | {daily.get(d, 0.0):.4f} | {'ya' if d in partial else ''} |" for d in days]
    lines += ["", f"**Total (hanya token terharga): ${fmt(sum(daily.values()))}**", ""]
    lines += pricing_sections_md(summary)
    lines += ["## Per hari × model", "", "| Tanggal | Agent | Model | Biaya USD |", "|---|---|---|---:|"]
    lines += [f"| {k[0]} | {k[1]} | {k[2]} | {bymodel[k]:.4f} |" for k in sorted(bymodel)]
    common.atomic_write_text(out / "cost_report.md", "\n".join(lines) + "\n")
    for n in ("cost_daily.csv", "cost_by_model.csv", "cost_report.md"):
        print(f"-> {out / n}")


def main():
    ap = argparse.ArgumentParser(description="Simulasi biaya token (pay-as-you-go)")
    ap.add_argument("date", nargs="?", help="YYYY-MM-DD; kosong = rekap per hari")
    ap.add_argument("--report", action="store_true", help="tulis cost_*.csv + cost_report.md ke data dir")
    ap.add_argument("--offline", action="store_true", help="pakai cache/seed, jangan panggil API")
    ap.add_argument("--strict", action="store_true", help="exit 3 bila INCOMPLETE")
    a = ap.parse_args()

    prices, meta = load_prices(offline=a.offline)
    recs = build_recs(read_rows(), prices)
    summary = pricing_summary(recs, prices)
    print(f"# harga: {meta.get('mode')} · {meta.get('fetched_at', '?')} · {ATTRIBUTION} {AA_URL} · {DERIVED_NOTE}")
    if summary["incomplete"]:
        print(f"!!! INCOMPLETE: {summary['ratio'] * 100:.2f}% token berbayar tak terharga — total TIDAK lengkap")

    if a.date:
        sel = [x for x in recs if x["date"] == a.date]
        if not sel:
            sys.exit(f"! tidak ada data untuk {a.date}")
        print(f"=== {a.date} ===")
        print(f"{'agent':9s} {'model':34s} {'input':>10s} {'output':>9s} "
              f"{'cacheR':>12s} {'cacheW':>10s} {'biaya$':>14s}")
        tot = 0.0
        for x in sorted(sel, key=lambda z: -(z["cost"] or 0)):
            if x["kind"] == "paid":
                cs = f"{x['cost']:.2f}"
                tot += x["cost"]
            else:
                cs = {"free": "$0 (free)", "tokenless": "(no tok)", "unknown": "TAK TERHARGA"}[x["kind"]]
            print(f"{x['agent']:9s} {x['model']:34s} {x['inputTokens']:10,} "
                  f"{x['outputTokens']:9,} {x['cacheReadInputTokens']:12,} "
                  f"{x['cacheCreationInputTokens']:10,} {cs:>14s}")
        print(f"{'TOTAL':9s} {'':34s} {'':>10s} {'':>9s} {'':>12s} {'':>10s} {fmt(tot):>14s}")
        if a.date in summary["partial_days"]:
            print("  (partial: ada token tak terharga pada tanggal ini)")
        foot = [x for x in sel if x["proxy"] is not None]
        if foot:
            print("\nfootnote (seandainya model free dipatok harga padanannya):")
            for x in foot:
                print(f"  {x['model']:34s} proxy {PROXY[x['model']]:24s} ${fmt(x['proxy'])}")
    else:
        days = defaultdict(float)
        for x in recs:
            if x["kind"] == "paid":
                days[x["date"]] += x["cost"]
        partial = set(summary["partial_days"])
        for d in sorted(set(days) | partial):
            print(f"{d}  ${fmt(days.get(d, 0.0)):>10s}{'  (partial)' if d in partial else ''}")
        print(f"TOTAL  ${fmt(sum(days.values())):>10s}")

    if summary["unpriced"]:
        print("\n! model berbayar tanpa harga (DI LUAR total; lihat 'Tidak terhitung' di laporan):", file=sys.stderr)
        for (agent, m), (t, n) in sorted(summary["unpriced"].items(), key=lambda z: -z[1][0]):
            print(f"   {agent:9s} {m:34s} {t:>12,} token  ({n} baris)", file=sys.stderr)

    if a.report:
        write_report(recs, prices, meta, summary)
    return 3 if (a.strict and summary["incomplete"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
