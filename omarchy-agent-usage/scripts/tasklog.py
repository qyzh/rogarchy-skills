#!/usr/bin/env python3
"""Task logger CLI — tulis dan baca tasks.jsonl.

Menyediakan tiga subcommand:
  record   – append satu baris tugas ke tasks.jsonl
  summary  – ringkasan jumlah tugas per agent/hari + bobot
  validate – cek semua baris, laporkan baris cacat

Data disimpan di ~/.local/state/omarchy/agents/tasks.jsonl (append-only).
Override lokasi via env OMARCHY_TASKS_FILE (untuk tes).

Skema per baris (JSON):
  ts      (wajib) ISO 8601 ber-timezone, kapan tugas selesai
  agent   (wajib) hermes | claude | codex | opencode | agy | grok
  session         id sesi/agent, string bebas
  label           nama tugas, string bebas
  status  (wajib) ok | partial | fail
  turns           integer >= 1

Bobot penyelesaian: ok = 1, partial = 0.5, fail = 0.
"""

import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

import argparse  # noqa: E402
import json  # noqa: E402
from collections import defaultdict  # noqa: E402
from datetime import datetime, timezone  # noqa: E402


# ---------------------------------------------------------------------------
# record
# ---------------------------------------------------------------------------

def cmd_record(args):
    """Append satu baris tugas."""
    ts = args.ts or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    agent = args.agent
    if args.ts and common.parse_ts(args.ts) is None:
        print("! --ts bukan ISO 8601", file=sys.stderr)
        return 1
    if agent not in common.VALID_AGENTS:
        print(f"! agent '{agent}' tidak dikenal (valid: {', '.join(sorted(common.VALID_AGENTS))})",
              file=sys.stderr)
        return 1
    status = args.status
    if status not in common.VALID_STATUSES:
        print(f"! status '{status}' tidak valid (valid: {', '.join(sorted(common.VALID_STATUSES))})",
              file=sys.stderr)
        return 1
    if args.turns is not None and args.turns < 1:
        print("! turns harus >= 1", file=sys.stderr)
        return 1

    entry = {"ts": ts, "agent": agent, "status": status}
    if args.session:
        entry["session"] = args.session
    if args.label:
        entry["label"] = args.label
    if args.turns is not None:
        entry["turns"] = args.turns

    p = common.tasks_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"+ {p}: {json.dumps(entry, ensure_ascii=False)}")
    return 0


# ---------------------------------------------------------------------------
# read helpers
# ---------------------------------------------------------------------------

def read_tasks(path=None):
    entries, malformed = common.read_task_entries(path)
    clean = [{k: v for k, v in e.items() if not k.startswith("_")} for e in entries]
    return clean, len(malformed), malformed


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def cmd_summary(args):
    """Ringkasan tugas per agent/hari + bobot (satu task = satu sesi)."""
    entries, malformed = common.read_task_entries()
    malformed_count = len(malformed)
    if not entries and malformed_count == 0:
        p = common.tasks_path()
        print(f"! tidak ada data (file: {p})")
        return 0

    kept, dups = common.dedupe_by_session(entries)
    if args.agent:
        kept = [e for e in kept if e["agent"] == args.agent]

    # Kelompokkan per (date, agent)
    by_date_agent = defaultdict(lambda: {"ok": 0, "partial": 0, "fail": 0, "total": 0})
    for e in kept:
        key = (e["_date"], e["agent"])
        by_date_agent[key][e["status"]] += 1
        by_date_agent[key]["total"] += 1

    # Sort dan filter --days
    all_dates = sorted({k[0] for k in by_date_agent})
    if args.days:
        all_dates = all_dates[-args.days:]

    print(f"{'tanggal':12s} {'agent':10s} {'ok':>4s} {'partial':>7s} {'fail':>4s} "
          f"{'total':>5s} {'bobot':>6s}")
    print("-" * 55)

    grand_weight = 0.0
    grand_total = 0
    for date in all_dates:
        for key in sorted(k for k in by_date_agent if k[0] == date):
            d, agent = key
            v = by_date_agent[key]
            weight = (v["ok"] * common.STATUS_WEIGHT["ok"]
                      + v["partial"] * common.STATUS_WEIGHT["partial"]
                      + v["fail"] * common.STATUS_WEIGHT["fail"])
            grand_weight += weight
            grand_total += v["total"]
            print(f"{d:12s} {agent:10s} {v['ok']:4d} {v['partial']:7d} {v['fail']:4d} "
                  f"{v['total']:5d} {weight:6.1f}")

    print("-" * 55)
    print(f"{'TOTAL':12s} {'':10s} {'':>4s} {'':>7s} {'':>4s} "
          f"{grand_total:5d} {grand_weight:6.1f}")
    print(f"# {len(entries)} baris valid → {len(kept)} task (dedupe per sesi; {dups} baris duplikat)")

    if malformed_count > 0:
        print(f"\n! {malformed_count} baris cacat diabaikan (jalankan validate untuk detail)")
    return 0


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

def cmd_validate(args):
    """Cek semua baris tasks.jsonl, laporkan baris cacat."""
    p = common.tasks_path()
    if not p.exists():
        print(f"! file tidak ditemukan: {p}")
        return 1

    entries, malformed_details = common.read_task_entries(p)
    malformed_count = len(malformed_details)
    total_lines = len(entries) + malformed_count

    if malformed_count == 0:
        print(f"OK: {total_lines} baris valid, 0 cacat ({p})")
        return 0

    print(f"! {malformed_count} baris cacat dari {total_lines} baris ({p}):\n")
    for lineno, reason in malformed_details:
        print(f"  baris {lineno}: {reason}")
    print(f"\n{len(entries)} baris valid, {malformed_count} baris cacat")
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Task logger CLI — tulis dan baca tasks.jsonl")
    sub = ap.add_subparsers(dest="cmd")

    # record
    p_rec = sub.add_parser("record", help="append satu baris tugas")
    p_rec.add_argument("--agent", required=True,
                       help=f"nama agent ({', '.join(sorted(common.VALID_AGENTS))})")
    p_rec.add_argument("--label", default="", help="nama tugas")
    p_rec.add_argument("--status", default="ok",
                       help=f"status ({', '.join(sorted(common.VALID_STATUSES))}) [default: ok]")
    p_rec.add_argument("--turns", type=int, default=None, help="jumlah turns (>= 1)")
    p_rec.add_argument("--session", default="", help="id sesi")
    p_rec.add_argument("--ts", default="", help="timestamp ISO 8601 (default: now)")

    # summary
    p_sum = sub.add_parser("summary", help="ringkasan per agent/hari")
    p_sum.add_argument("--days", type=int, default=None, help="tampilkan N hari terakhir")
    p_sum.add_argument("--agent", default=None, help="filter agent")

    # validate
    sub.add_parser("validate", help="cek semua baris, laporkan cacat")

    a = ap.parse_args()
    if not a.cmd:
        ap.print_help()
        return 1
    if a.cmd == "record":
        return cmd_record(a)
    if a.cmd == "summary":
        return cmd_summary(a)
    if a.cmd == "validate":
        return cmd_validate(a)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
