#!/usr/bin/env python3
"""Dashboard metrik analitik Omarchy (Lapisan A — offline).

Sumber: daily_by_model.csv (data dir) + harga cost.py + tasks.jsonl.
  1. Cost per agent    — simulasi pay-as-you-go (cost.py); free = $0 DIKETAHUI
  2. Cache hit ratio   — cacheRead / (input + cacheRead + cacheWrite)
  3. Token per prompt  — non-cache = (input + output) / prompts; total = semua token / prompts.
                         prompts = SEMUA baris agent-hari, termasuk (unknown)
  4. Cost per task     — per agent: biaya / bobot task; agregat tanggal/periode =
                         Σ biaya ÷ Σ bobot HANYA atas agent-hari yang punya baris task
  5. Output token      — outputTokens + persentase terhadap total token
  6. Daily usage trend — delta vs hari KALENDER sebelumnya + avg7d kalender (hari nol ikut)

CLI:
  python3 scripts/metrics.py [YYYY-MM-DD] [--report] [--offline] [--strict]
"""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import cost as _cost  # noqa: E402

import argparse
import datetime as dt
from collections import defaultdict

NA_NO_TASKS = "n/a (no tasks)"
NA_ALL_FAILED = "n/a (all tasks failed, weight 0)"
NA_NO_USAGE = "n/a (no usage data)"
NA_UNPRICED = "n/a (unpriced tokens)"

COLUMNS = [  # (key, label) — dipakai CLI dan report.md
    ("costUSD", "Biaya USD"),
    ("costStatus", "Status biaya"),
    ("cacheHitRatio", "Cache hit"),
    ("nonCacheTokensPerPrompt", "Non-cache tok/prompt"),
    ("totalTokensPerPrompt", "Total tok/prompt"),
    ("prompts", "Prompt"),
    ("outputTokens", "Output tok"),
    ("outputShare", "Out%"),
    ("totalTokens", "Total tok"),
    ("deltaVsPrev", "Delta (kalender)"),
    ("avg7d", "Avg7d (kalender)"),
    ("tasks", "Tasks"),
    ("tasksWeight", "Bobot"),
    ("costPerTask", "Cost/task"),
]
CSV_FIELDS = ["date", "agent", "costUSD", "costStatus", "cacheHitRatio",
              "nonCacheTokensPerPrompt", "totalTokensPerPrompt", "prompts",
              "inputTokens", "outputTokens", "outputShare", "totalTokens",
              "deltaVsPrev", "avg7d", "tasksOk", "tasksPartial", "tasksFail",
              "tasksWeight", "costPerTask", "costPerTaskNote"]
SUM_FIELDS = ("costUSD", "unpricedTokens", "paidRows", "freeRows", "inputTokens",
              "outputTokens", "cacheRead", "cacheWrite", "tokens", "prompts",
              "tasksOk", "tasksPartial", "tasksFail", "tasksWeight")


# --------------------------------------------------------------------------- data

def read_model_rows(date_filter=None):
    rows = _cost.read_rows()
    return [r for r in rows if not date_filter or r["date"] == date_filter]


def cache_hit(cache_read, inp, cache_write):
    denom = inp + cache_read + cache_write
    return cache_read / denom if denom else None


def compute_cache_hit(row):
    return cache_hit(row["cacheReadInputTokens"], row["inputTokens"], row["cacheCreationInputTokens"])


def enrich_rows(rows, prices):
    """cost.build_recs (kind/cost/proxy/label) + cacheHitRatio per baris."""
    return [dict(r, cacheHitRatio=compute_cache_hit(r)) for r in _cost.build_recs(rows, prices)]


# ---------------------------------------------------------------------- aggregation

def _new_agg():
    return {"costUSD": 0.0, "unpricedTokens": 0, "paidRows": 0, "freeRows": 0,
            "inputTokens": 0, "outputTokens": 0, "cacheRead": 0, "cacheWrite": 0,
            "tokens": 0, "prompts": 0, "hasUsage": False,
            "tasksOk": 0, "tasksPartial": 0, "tasksFail": 0, "tasksWeight": 0.0}


def aggregate_by_day_agent(enriched, task_agg=None):
    """dict[(date, agent)] -> agregat. Entri yang hanya berisi task punya hasUsage=False."""
    agg = defaultdict(_new_agg)
    for r in enriched:
        a = agg[(r["date"], r["agent"])]
        a["hasUsage"] = True
        if r["kind"] == "unknown":
            a["unpricedTokens"] += r["tokens"]
        else:
            a["costUSD"] += r["cost"] or 0.0
        a["paidRows"] += r["kind"] == "paid"
        a["freeRows"] += r["kind"] == "free"
        a["inputTokens"] += r["inputTokens"]
        a["outputTokens"] += r["outputTokens"]
        a["cacheRead"] += r["cacheReadInputTokens"]
        a["cacheWrite"] += r["cacheCreationInputTokens"]
        a["tokens"] += r["tokens"]
        a["prompts"] += r["prompts"]            # SEMUA baris, termasuk (unknown) — M1
    for key, tv in (task_agg or {}).items():
        a = agg[key]
        a["tasksOk"], a["tasksPartial"] = tv["ok"], tv["partial"]
        a["tasksFail"], a["tasksWeight"] = tv["fail"], tv["weight"]
    return dict(agg)


def sum_agg(values):
    out = _new_agg()
    for v in values:
        for f in SUM_FIELDS:
            out[f] += v[f]
        out["hasUsage"] = out["hasUsage"] or v["hasUsage"]
    return out


def cost_status(v):
    if not v["hasUsage"]:
        return "no-usage"
    if v["unpricedTokens"] > 0:
        return "partial"
    if v["paidRows"] == 0:
        return "free"
    return "ok"


def tasks_count(v):
    return v["tasksOk"] + v["tasksPartial"] + v["tasksFail"]


def agent_cost_per_task(v):
    """-> (value | None, note)."""
    if tasks_count(v) == 0:
        return None, NA_NO_TASKS
    st = cost_status(v)
    if st == "no-usage":
        return None, NA_NO_USAGE
    if st == "partial":
        return None, NA_UNPRICED
    if v["tasksWeight"] <= 0:
        return None, NA_ALL_FAILED
    return v["costUSD"] / v["tasksWeight"], ("free: no paid usage" if st == "free" else "")


def pooled_cost_per_task(agg, keys):
    """Σ biaya ÷ Σ bobot atas (date, agent) yang PUNYA baris task.
    -> (value | None, note, agents_included, excluded[(key, reason)])."""
    cost = weight = 0.0
    agents, excluded = set(), []
    for k in sorted(keys):
        v = agg[k]
        if tasks_count(v) == 0:
            continue
        st = cost_status(v)
        if st in ("no-usage", "partial"):
            excluded.append((k, NA_NO_USAGE if st == "no-usage" else NA_UNPRICED))
            continue
        cost += v["costUSD"]
        weight += v["tasksWeight"]
        agents.add(k[1])
    if not agents:
        return None, (NA_NO_TASKS if not excluded else "n/a (semua agent-hari bertask dikecualikan)"), [], excluded
    if weight <= 0:
        return None, NA_ALL_FAILED, sorted(agents), excluded
    return cost / weight, "", sorted(agents), excluded


def compute_trends(agg):
    """Delta & avg7d atas hari KALENDER (hari tanpa pemakaian = 0), per agent.
    Hanya untuk entri dengan pemakaian; avg7d butuh 7 hari sejak pemakaian pertama agent."""
    series = defaultdict(dict)
    for (d, a), v in agg.items():
        if v["hasUsage"]:
            series[a][d] = v["tokens"]
    out = {}
    for a, s in series.items():
        first = dt.date.fromisoformat(min(s))
        for ds in s:
            day = dt.date.fromisoformat(ds)
            prev = day - dt.timedelta(days=1)
            delta = s[ds] - s.get(prev.isoformat(), 0) if prev >= first else None
            avg = None
            if (day - first).days >= 6:
                avg = sum(s.get((day - dt.timedelta(days=i)).isoformat(), 0) for i in range(7)) / 7
            out[(ds, a)] = {"deltaVsPrev": delta, "avg7d": avg}
    return out


# ------------------------------------------------------------------ metric builder

def metric_values(v, trend):
    """Satu sumber nilai metrik untuk CLI, CSV dan report (MINOR 12)."""
    tok, prm = v["tokens"], v["prompts"]
    noncache = v["inputTokens"] + v["outputTokens"]
    cpt, note = agent_cost_per_task(v)
    return {
        "costUSD": v["costUSD"] if v["hasUsage"] else None,
        "costStatus": cost_status(v),
        "cacheHitRatio": cache_hit(v["cacheRead"], v["inputTokens"], v["cacheWrite"]),
        "nonCacheTokensPerPrompt": noncache / prm if prm else None,
        "totalTokensPerPrompt": tok / prm if prm else None,
        "prompts": prm,
        "inputTokens": v["inputTokens"],
        "outputTokens": v["outputTokens"],
        "outputShare": v["outputTokens"] / tok if tok else None,
        "totalTokens": tok,
        "deltaVsPrev": (trend or {}).get("deltaVsPrev"),
        "avg7d": (trend or {}).get("avg7d"),
        "tasks": tasks_count(v),
        "tasksOk": v["tasksOk"], "tasksPartial": v["tasksPartial"], "tasksFail": v["tasksFail"],
        "tasksWeight": v["tasksWeight"],
        "costPerTask": cpt,
        "costPerTaskNote": note,
    }


def fmt_value(key, m, style):
    """style: 'cli' | 'md' | 'csv'."""
    val = m.get(key)
    csv_ = style == "csv"
    if key == "costPerTask":
        if val is None:
            return "" if csv_ else m["costPerTaskNote"]
        if csv_:
            return f"{val:.2f}"
        return f"{val:.2f}" + (" (free)" if m["costStatus"] == "free" else "")
    if key in ("costPerTaskNote", "costStatus"):
        return val or ""
    if val is None:
        return "" if csv_ else "n/a"
    if key == "costUSD":
        if csv_:
            return f"{val:.2f}"
        return f"{val:.2f}" + (" +?" if m["costStatus"] == "partial" else "")
    if key == "cacheHitRatio":
        return f"{val:.6f}" if csv_ else f"{val:.4f}"
    if key == "outputShare":
        return f"{val:.6f}" if csv_ else f"{val * 100:.1f}%"
    if key in ("nonCacheTokensPerPrompt", "totalTokensPerPrompt", "avg7d"):
        return f"{val:.2f}" if csv_ else f"{val:,.1f}"
    if key == "deltaVsPrev":
        return str(val) if csv_ else f"{val:+,}"
    if key == "tasksWeight":
        return f"{val:.2f}"
    return str(val) if csv_ else f"{val:,}"


# ----------------------------------------------------------------------------- CLI

def _print_table(header, rows, left=1):
    widths = [max(len(str(x)) for x in col) for col in zip(header, *rows)]

    def line(r):
        return "  ".join(str(c).ljust(w) if i < left else str(c).rjust(w)
                         for i, (c, w) in enumerate(zip(r, widths)))
    head = line(header)
    print(head)
    print("-" * len(head))
    for r in rows:
        print(line(r))
    print("-" * len(head))


def _agent_rows(keys, agg, trends, with_date, style):
    rows = []
    for k in keys:
        m = metric_values(agg[k], trends.get(k))
        rows.append(([k[0]] if with_date else []) + [k[1]] + [fmt_value(c, m, style) for c, _ in COLUMNS])
    return rows


def _pooled_lines(agg, keys, label, max_excluded=30):
    val, note, agents, excluded = pooled_cost_per_task(agg, keys)
    if val is None:
        out = [f"[#] {label} = {note}"]
    else:
        out = [f"[#] {label} = ${val:.2f} (Σ biaya ÷ Σ bobot; hanya agent dengan task signal: {', '.join(agents)})"]
    for (d, a), why in excluded[:max_excluded]:
        out.append(f"    dikecualikan: {d} {a} — {why}")
    if len(excluded) > max_excluded:
        out.append(f"    … +{len(excluded) - max_excluded} agent-hari lain dikecualikan")
    return out


def print_one_date(date, enriched, agg, trends):
    print(f"=== Metrik {date} ===\n")
    rows = []
    for r in sorted((x for x in enriched if x["date"] == date), key=lambda x: (x["agent"], -(x["cost"] or 0))):
        cost_s = (f"{r['cost']:.2f}" if r["kind"] == "paid" else
                  {"free": "$0 (free)", "tokenless": "(no tok)", "unknown": "TAK TERHARGA"}[r["kind"]])
        chr_ = f"{r['cacheHitRatio']:.4f}" if r["cacheHitRatio"] is not None else "n/a"
        tpp = f"{(r['inputTokens'] + r['outputTokens']) / r['prompts']:,.1f}" if r["prompts"] else "n/a"
        rows.append([r["agent"], r["model"], r["kind"], cost_s, chr_, tpp, f"{r['outputTokens']:,}"])
    _print_table(["agent", "model", "jenis", "biaya$", "cacheHit", "nonCache tok/prompt", "outTok"], rows, left=3)
    print("\n--- Ringkasan per agent (prompt = semua baris, termasuk (unknown)) ---\n")
    keys = sorted(k for k in agg if k[0] == date)
    _print_table(["agent"] + [label for _, label in COLUMNS], _agent_rows(keys, agg, trends, False, "cli"), left=1)
    print()
    print("\n".join(_pooled_lines(agg, keys, f"cost per task {date}")))


def print_all_dates(agg, trends):
    print("=== Rekap Semua Hari ===\n")
    keys = sorted(agg)
    _print_table(["tanggal", "agent"] + [label for _, label in COLUMNS],
                 _agent_rows(keys, agg, trends, True, "cli"), left=2)
    tot = sum_agg(v for v in agg.values() if v["hasUsage"])
    out_pct = tot["outputTokens"] / tot["tokens"] * 100 if tot["tokens"] else 0.0
    print(f"TOTAL biaya terharga ${tot['costUSD']:.2f} · token {tot['tokens']:,} · "
          f"output {tot['outputTokens']:,} ({out_pct:.1f}%) · token tak terharga {tot['unpricedTokens']:,}")
    print()
    print("\n".join(_pooled_lines(agg, keys, "cost per task periode")))


# ------------------------------------------------------------------------- reports

def write_metrics_daily_csv(agg, trends, path):
    rows = []
    for k in sorted(agg):
        m = metric_values(agg[k], trends.get(k))
        rows.append([k[0], k[1]] + [fmt_value(f, m, "csv") for f in CSV_FIELDS[2:]])
    common.write_csv_rows(path, CSV_FIELDS, rows)


def write_metrics_by_agent_csv(enriched, path):
    """Per date × agent × model. Token per prompt per model hanya bermakna bila baris itu punya prompt."""
    rows = []
    for r in sorted(enriched, key=lambda x: (x["date"], x["agent"], x["model"])):
        cost_s = f"{r['cost']:.2f}" if r["cost"] is not None else ""
        chr_s = f"{r['cacheHitRatio']:.6f}" if r["cacheHitRatio"] is not None else ""
        tpp = (r["inputTokens"] + r["outputTokens"]) / r["prompts"] if r["prompts"] else None
        rows.append([r["date"], r["agent"], r["model"], r["kind"], cost_s, chr_s,
                     f"{tpp:.2f}" if tpp is not None else "", r["prompts"], r["outputTokens"]])
    common.write_csv_rows(path, ["date", "agent", "model", "kind", "costUSD", "cacheHitRatio",
                                 "nonCacheTokensPerPrompt", "prompts", "outputTokens"], rows)


def write_metrics_report_md(agg, trends, summary, meta, generated_at, path):
    dates = sorted({k[0] for k in agg})
    agents = sorted({k[1] for k in agg})
    L = ["# Dashboard Metrik — Omarchy", "",
         f"- Dibuat: {generated_at}",
         f"- Rentang data: {dates[0] if dates else '—'} s/d {dates[-1] if dates else '—'} ({len(dates)} tanggal)",
         f"- Harga: {meta.get('mode')} · fetched_at {meta.get('fetched_at', '?')} · {_cost.ATTRIBUTION_MD}",
         f"- {_cost.DERIVED_NOTE}",
         *common.freshness_lines(path.parent),
         "- Sumber: `daily_by_model.csv` + `tasks.jsonl` (task signal, dedupe per sesi)", "",
         "> **Peringatan:** Token/biaya ≠ produktivitas. Agent harus dinilai dari",
         "> pekerjaan yang berhasil diselesaikan, bukan dari jumlah token atau biaya.", ""]
    if summary["incomplete"]:
        L += [f"> **INCOMPLETE:** {summary['ratio'] * 100:.2f}% token berbayar tidak terharga — "
              "biaya & cost per task di bawah TIDAK lengkap.", ""]
    L += ["## Metrik per hari × agent", "",
          "| Tanggal | Agent | " + " | ".join(label for _, label in COLUMNS) + " |",
          "|---|---|" + "---:|" * len(COLUMNS)]
    L += ["| " + " | ".join(r) + " |" for r in _agent_rows(sorted(agg), agg, trends, True, "md")]
    L += ["", "## Ringkasan per agent (semua waktu)", "",
          "| Agent | Biaya USD (terharga) | Status | Cache hit | Non-cache tok/prompt | Total tok/prompt | Prompt | Output tok | Total tok |",
          "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for a in agents:
        m = metric_values(sum_agg(v for k, v in agg.items() if k[1] == a), None)
        L.append(f"| {a} | " + " | ".join(fmt_value(c, m, "md") for c in (
            "costUSD", "costStatus", "cacheHitRatio", "nonCacheTokensPerPrompt",
            "totalTokensPerPrompt", "prompts", "outputTokens", "totalTokens")) + " |")
    m = metric_values(sum_agg(agg.values()), None)
    L.append("| **TOTAL** | " + " | ".join(fmt_value(c, m, "md") for c in (
        "costUSD", "costStatus", "cacheHitRatio", "nonCacheTokensPerPrompt",
        "totalTokensPerPrompt", "prompts", "outputTokens", "totalTokens")) + " |")
    L += ["", "## Cost per task (periode)", ""]
    L += [f"- {x.strip()}" for x in _pooled_lines(agg, list(agg), "cost per task periode")]
    L.append("")
    L += _cost.pricing_sections_md(summary)
    L += ["## Rumus & catatan", "",
          "1. **Model free** (`:free` / `-free`) → biaya $0 yang *diketahui* (status `free`). "
          "Estimasi \"seandainya berbayar\" ada di seksi *Model free — estimasi proxy*, bukan di total.",
          "2. **Cache hit ratio** = `cacheRead / (input + cacheRead + cacheWrite)` — porsi token input "
          "sisi-prompt yang dilayani dari cache. Output tidak ikut.",
          "3. **Token per prompt**: *non-cache* = `(input + output) / prompts`; *total* = "
          "`(input + output + cacheRead + cacheWrite) / prompts`. Penyebut = SEMUA prompt agent itu "
          "pada hari itu, termasuk baris `(unknown)`. Hermes mencatat seluruh prompt-nya di baris "
          "`(unknown)` tanpa token; Claude memakai `(unknown)` untuk prompt yang belum dibalas dan "
          "penanda sesi.",
          "4. **Cost per task** per agent = biaya agent ÷ bobot task (ok=1, partial=0.5, fail=0); "
          "task = sesi unik di `tasks.jsonl` (hook menulis per giliran, pembaca men-dedupe per sesi). "
          "Agregat tanggal/periode = Σ biaya ÷ Σ bobot **hanya** atas agent-hari yang punya baris task; "
          "agent-hari tanpa data usage atau dengan token tak terharga dikecualikan dan dicantumkan. "
          f"Catatan: `{NA_NO_TASKS}`, `{NA_ALL_FAILED}`, `{NA_NO_USAGE}`, `{NA_UNPRICED}`; "
          "`x.xxxx (free)` = semua pemakaian gratis.",
          "5. **Delta** = token hari ini − token hari kalender sebelumnya (0 bila tidak dipakai). "
          "**Avg7d** = rata-rata 7 hari kalender (hari nol ikut), baru muncul setelah 7 hari sejak "
          "pemakaian pertama agent.",
          "6. **Biaya** = revaluasi pemakaian historis ke harga AA saat `fetched_at` (AA tidak punya harga historis).",
          "7. **Token/cost ≠ produktivitas.**", "", "---",
          f"*Dibuat otomatis oleh `scripts/metrics.py` pada {generated_at}.*"]
    common.atomic_write_text(path, "\n".join(L) + "\n")


# ---------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Dashboard metrik analitik Omarchy (Lapisan A)")
    ap.add_argument("date", nargs="?", help="YYYY-MM-DD; kosong = rekap semua hari")
    ap.add_argument("--report", action="store_true",
                    help="tulis metrics_daily.csv, metrics_by_agent.csv, metrics_report.md ke data dir")
    ap.add_argument("--offline", action="store_true", help="pakai cache/seed harga, jangan fetch live")
    ap.add_argument("--strict", action="store_true", help="exit 3 bila INCOMPLETE")
    a = ap.parse_args()
    if a.date:
        try:
            dt.date.fromisoformat(a.date)
        except ValueError:
            ap.error(f"tanggal tidak valid: {a.date}")

    prices, meta = _cost.load_prices(offline=a.offline)
    print(f"# harga: {meta.get('mode')} · {meta.get('fetched_at', '?')} · {_cost.ATTRIBUTION} {_cost.AA_URL} · {_cost.DERIVED_NOTE}")
    rows = read_model_rows()                     # SELALU semua baris; filter hanya untuk tampilan (M12)
    if not rows:
        sys.exit("! daily_by_model.csv kosong")
    if a.date and not any(r["date"] == a.date for r in rows):
        sys.exit(f"! tidak ada data untuk {a.date}")
    enriched = enrich_rows(rows, prices)
    summary = _cost.pricing_summary(enriched, prices)
    task_agg, tinfo = common.read_tasks()
    if tinfo["malformed"]:
        print(f"! {tinfo['malformed']} baris tasks.jsonl cacat dilewati", file=sys.stderr)
    if tinfo["duplicates"]:
        print(f"# tasks: {tinfo['raw']} baris → {tinfo['tasks']} task "
              f"(dedupe per sesi: {tinfo['duplicates']} baris duplikat)", file=sys.stderr)
    agg = aggregate_by_day_agent(enriched, task_agg)
    trends = compute_trends(agg)
    if summary["incomplete"]:
        print(f"!!! INCOMPLETE: {summary['ratio'] * 100:.2f}% token berbayar tak terharga — biaya TIDAK lengkap")

    if a.date:
        print_one_date(a.date, enriched, agg, trends)
    else:
        print_all_dates(agg, trends)

    if a.report:
        out = common.data_dir()
        generated_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        write_metrics_daily_csv(agg, trends, out / "metrics_daily.csv")
        write_metrics_by_agent_csv(enriched, out / "metrics_by_agent.csv")
        write_metrics_report_md(agg, trends, summary, meta, generated_at, out / "metrics_report.md")
        for n in ("metrics_daily.csv", "metrics_by_agent.csv", "metrics_report.md"):
            print(f"-> {out / n}")

    if summary["unpriced"]:
        print("\n! model berbayar tanpa harga (DI LUAR biaya):", file=sys.stderr)
        for (agent, m), (t, n) in sorted(summary["unpriced"].items(), key=lambda z: -z[1][0]):
            print(f"   {agent:9s} {m:34s} {t:>12,} token  ({n} baris)", file=sys.stderr)
    return 3 if (a.strict and summary["incomplete"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
