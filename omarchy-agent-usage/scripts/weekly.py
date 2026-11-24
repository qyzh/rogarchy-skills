#!/usr/bin/env python3
"""Ringkasan pemakaian token per MINGGU (7 hari kalender) dari snapshot, tanpa scan ulang.

Jendela: start = --week-start (default: Senin dari tanggal snapshot terbaru);
end = min(start + 6 hari, tanggal snapshot terbaru). Minggu berjalan -> < 7 hari
(judul menandai "belum lengkap"). Start setelah snapshot terbaru -> exit 2.

Output (data dir): weekly.csv, report_week.md

Pakai:
  python3 weekly.py
  python3 weekly.py --week-start 2026-11-09
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

import argparse
from datetime import date, datetime, timedelta

FIELDS = list(common.BUCKET_FIELDS)
fmt = common.fmt_int


def week_window(snapshots, week_start):
    """-> (start, end, [YYYY-MM-DD ...]); ValueError bila start setelah snapshot terbaru."""
    if not snapshots:
        raise ValueError("tidak ada snapshot")
    last = date.fromisoformat(snapshots[-1]["today"])
    start = week_start or last - timedelta(days=last.weekday())
    if start > last:
        raise ValueError(f"--week-start {start} setelah snapshot terbaru {last}")
    end = min(start + timedelta(days=6), last)
    days = [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]
    return start, end, days


def totals(day, agent, latest, record_latest, sessions_by_day):
    models = latest.get(day, {}).get(agent)
    if models:
        out = {k: sum(int(b.get(k, 0) or 0) for b in models.values()) for k in FIELDS}
        out["sessions"] = sessions_by_day.get(day, {}).get(agent, 0)
        out["source"] = "model-rows"
        return out
    out = {k: 0 for k in FIELDS}
    out.update(tokens=record_latest.get(day, {}).get(agent, 0), sessions=0, source="usage-record")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Ringkasan token per minggu (7 hari kalender)")
    ap.add_argument("--week-start", type=date.fromisoformat,
                    help="YYYY-MM-DD (default: Senin minggu snapshot terbaru)")
    args = ap.parse_args()

    snapshots = common.load_all_snapshots()
    if not snapshots:
        print("[weekly] tidak ada snapshot", file=sys.stderr)
        return 1
    try:
        start, end, days = week_window(snapshots, args.week_start)
    except ValueError as exc:
        print(f"! {exc}", file=sys.stderr)
        return 2
    latest, record_latest, sessions_by_day, _ = common.merge_snapshots(snapshots)

    row_agents = sorted({a for d in days for a in latest.get(d, {})})
    other_agents = sorted({a for d in days for a in record_latest.get(d, {})
                           if a not in row_agents and record_latest[d][a]})
    rows = []
    for d in days:
        for a in row_agents + other_agents:
            t = totals(d, a, latest, record_latest, sessions_by_day)
            if t["tokens"] or t["prompts"]:
                rows.append({"date": d, "agent": a, **t})

    out = common.data_dir()
    common.write_csv(out / "weekly.csv", rows, ["date", "agent", "source", *FIELDS, "sessions"])

    n = len(days)
    title = f"# Pemakaian Token — Minggu {start} s/d {end} ({n} hari{'' if n == 7 else ', belum lengkap'})"
    L = [title, "",
         f"- Dibuat: {datetime.now().astimezone().isoformat(timespec='seconds')}",
         *common.freshness_lines(out),
         f"- Agent lokal (pecahan per model): {', '.join(row_agents) or '-'}",
         f"- Agent lain (total/hari dari recentDays): {', '.join(other_agents) or '-'}", "",
         "## Total minggu per agent", "",
         "| Agent | Sumber | Total token | Input | Output | Cache read | Cache write | Non-cache (in+out) | Prompt |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    tot = {k: 0 for k in FIELDS}
    other_total = 0
    for a in row_agents:
        s = {k: sum(r[k] for r in rows if r["agent"] == a) for k in FIELDS}
        for k in FIELDS:
            tot[k] += s[k]
        L.append(f"| {a} | model-rows | {fmt(s['tokens'])} | {fmt(s['inputTokens'])} | {fmt(s['outputTokens'])} | "
                 f"{fmt(s['cacheReadInputTokens'])} | {fmt(s['cacheCreationInputTokens'])} | "
                 f"{fmt(s['inputTokens'] + s['outputTokens'])} | {fmt(s['prompts'])} |")
    for a in other_agents:
        t = sum(r["tokens"] for r in rows if r["agent"] == a)
        other_total += t
        L.append(f"| {a} | usage-record | {fmt(t)} | — | — | — | — | — | — |")
    L.append(f"| **Total model-rows** | | **{fmt(tot['tokens'])}** | {fmt(tot['inputTokens'])} | "
             f"{fmt(tot['outputTokens'])} | {fmt(tot['cacheReadInputTokens'])} | "
             f"{fmt(tot['cacheCreationInputTokens'])} | {fmt(tot['inputTokens'] + tot['outputTokens'])} | "
             f"{fmt(tot['prompts'])} |")
    L.append(f"| **Total semua agent** | | **{fmt(tot['tokens'] + other_total)}** | | | | | | |")
    L += ["", "> Input + Output + Cache read + Cache write = Total (model-rows). Agent `usage-record` hanya "
          "punya total harian dari `recentDays`. Pemakaian aktual = **non-cache**; cache read bukan token baru.", ""]

    L += ["## Harian (total token)", "",
          "| Tanggal | " + " | ".join(row_agents + other_agents) + " | Total |",
          "|---|" + "---:|" * (len(row_agents + other_agents) + 1)]
    for d in days:
        cells, s = [], 0
        for a in row_agents + other_agents:
            t = totals(d, a, latest, record_latest, sessions_by_day)["tokens"]
            s += t
            cells.append(fmt(t) if t else "—")
        L.append(f"| {d} | " + " | ".join(cells) + f" | {fmt(s)} |")
    L.append("")

    for a in row_agents:
        models = sorted({m for d in days for m in latest.get(d, {}).get(a, {})})
        if not models:
            continue
        L += [f"## {a} — per hari × model", "",
              "| Tanggal | Model | Tokens | Input | Output | Cache read | Cache write | Prompt |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
        for d in days:
            for m in models:
                b = latest.get(d, {}).get(a, {}).get(m)
                if not b or not (b.get("tokens") or b.get("prompts")):
                    continue
                L.append(f"| {d} | {m} | {fmt(b.get('tokens', 0))} | {fmt(b.get('inputTokens', 0))} | "
                         f"{fmt(b.get('outputTokens', 0))} | {fmt(b.get('cacheReadInputTokens', 0))} | "
                         f"{fmt(b.get('cacheCreationInputTokens', 0))} | {fmt(b.get('prompts', 0))} |")
        L.append("")
    L += ["> `sessions` di weekly.csv = sesi UNIK per hari; jangan dijumlahkan antar hari "
          "(sesi yang melewati tengah malam terhitung di dua hari).", ""]

    common.atomic_write_text(out / "report_week.md", "\n".join(L))
    print(f"[weekly] {out / 'weekly.csv'} ({len(rows)} baris)")
    print(f"[weekly] {out / 'report_week.md'} ({len(L)} baris)")
    print(f"[weekly] rentang {start} s/d {end} ({n} hari)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
