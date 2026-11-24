#!/usr/bin/env python3
"""
Token usage collector for Omarchy.

Menyimpan pemakaian token semua AI agent di mesin ini, per hari, dengan
pecahan per model. Data diambil dari dua sumber:

  1. `omarchy-agent-usage-<agent>`  -> record lengkap (limit, prompt, sesi,
     todayTokensByModel, recentDays).
  2. Scanner internal Omarchy        -> baris mentah per (hari, model) untuk
     agent lokal: Hermes, Claude Code, Codex, OpenCode.

Output (di sisi direktori script):
  snapshots/<tanggal>.json   - semua data mentah per agent
  daily.csv                  - total per (tanggal, agent)
  daily_by_model.csv         - total per (tanggal, agent, model)
  report.md                  - laporan manusia

Pakai:
  python3 collect.py            # kumpulkan snapshot hari ini
  python3 collect.py --report   # bangun ulang CSV + report dari snapshots
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

import argparse  # noqa: E402
import os  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
from concurrent.futures import ThreadPoolExecutor  # noqa: E402
from collections import defaultdict  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

# --- konfigurasi -------------------------------------------------------------

ROW_AGENTS = ("hermes", "claude", "codex", "opencode")

KNOWN_AGENTS = (
    "agy", "claude", "codex", "copilot", "cursor", "deepseek", "devin",
    "fireworks", "grok", "grokbot", "hermes", "kimchi", "kimi", "local",
    "minimax", "muse", "ollama", "opencode", "openrouter", "qwen",
    "synthetic", "vibe", "zai",
)

SCHEMA_VERSION = 2


def log(msg: str) -> None:
    print(f"[collect] {msg}", flush=True)


CLAUDE_PI_PATTERN = r'"provider"\s*:\s*"anthropic"'
OPENCODE_PI_PATTERN = r'"provider"\s*:\s*"opencode(-go)?"'
CODEX_PI_PATTERN = r'"provider"\s*:\s*"openai-codex"|"api"\s*:\s*"openai-codex'
# Disalin dari wrapper upstream (omarchy-agent-usage-claude/-codex), bagian dari Omarchy
# (https://github.com/omacom/omarchy, MIT, Copyright (c) David Heinemeier Hansson;
# lihat THIRD_PARTY_NOTICES.md). Wrapper codex
# tidak di-import karena punya state level-modul (ENV = runtime_env(), STATS = Stats()).
# Drift berikutnya tertangkap oleh parity_check().


def claude_billed(provider, model, entry):
    return provider == "anthropic"


def claude_opencode_model(model):
    return str(model or "claude").rstrip("/").split("/")[-1] or "claude"


def codex_pi_billed(provider, model, entry):
    return provider == "openai-codex" or str(entry.get("api") or "").startswith("openai-codex")


def codex_opencode_billed(provider, model, entry):
    return provider == "openai"


def codex_model_name(raw):
    return str(raw or "codex") or "codex"


def wrapper_path(agent: str) -> Path:
    if agent == "update":
        raise ValueError("omarchy-agent-usage-update tidak boleh dijalankan skill ini "
                         "(menulis ulang semua record + bisa auto-switch akun)")
    return common.bin_dir() / f"omarchy-agent-usage-{agent}"


def discover_agents() -> list[str]:
    prefix = "omarchy-agent-usage-"
    found = sorted(p.name[len(prefix):] for p in common.bin_dir().glob(prefix + "*")
                   if p.is_file() and os.access(p, os.X_OK) and p.name != prefix + "update")
    if not found:
        log(f"tidak ada wrapper di {common.bin_dir()}; pakai daftar bawaan")
        return list(KNOWN_AGENTS)
    new = sorted(set(found) - set(KNOWN_AGENTS))
    if new:
        log(f"agent baru terdeteksi: {', '.join(new)}")
    return found


def _tokens(r) -> int:
    return r.input_tokens + r.output_tokens + r.cache_read + r.cache_write


def _row(r, model: str) -> dict:
    return {"day": r.day, "model": model,
            "input": r.input_tokens, "output": r.output_tokens,
            "cacheRead": r.cache_read, "cacheWrite": r.cache_write,
            "prompts": r.prompts, "session": r.session}


def _name(r, fn, default: str) -> str:
    """Nama model seperti yang ditampilkan wrapper; baris tanpa token & tanpa model = (unknown)."""
    if not r.model and _tokens(r) == 0:
        return "(unknown)"
    return fn(r.model) if r.model else default


load_collector = common.load_collector


def empty_bucket() -> dict:
    return {
        "tokens": 0,
        "inputTokens": 0,
        "outputTokens": 0,
        "cacheReadInputTokens": 0,
        "cacheCreationInputTokens": 0,
        "prompts": 0,
        "sessions": set(),
    }


def usage_record(agent: str) -> dict | None:
    """Jalankan $OMARCHY_PATH/bin/omarchy-agent-usage-<agent>; JSON record atau None.
    Wrapper bisa memanggil API limit provider (network). Tidak pernah menjalankan `update`."""
    path = wrapper_path(agent)
    try:
        proc = subprocess.run([str(path)], capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        log(f"{agent}: record gagal ({exc})")
        return None
    out = (proc.stdout or "").strip()
    rec = None
    if out:
        try:
            rec = json.loads(out)
        except json.JSONDecodeError:
            rec = None
    if proc.returncode != 0:
        tail = " | ".join((proc.stderr or "").strip().splitlines()[-2:])
        if isinstance(rec, dict):
            log(f"{agent}: exit {proc.returncode} tapi stdout JSON valid — dipakai ({tail})")
            return rec
        log(f"{agent}: exit {proc.returncode}, record diabaikan ({tail})")
        return None
    if not isinstance(rec, dict):
        if out:
            log(f"{agent}: record bukan JSON objek")
        return None
    return rec


def usage_records(agents: list[str]) -> dict:
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = dict(zip(agents, ex.map(usage_record, agents)))
    return {a: r for a, r in results.items() if r is not None}


def collect_rows(collectors) -> tuple[dict, dict]:
    """-> (rows_by_agent, complete_by_agent). Komposisi scan = sama dengan wrapper upstream."""
    rows: dict[str, list[dict]] = {}
    complete: dict[str, bool] = {}

    try:  # Hermes: state.db (lewat wrapper)
        hermes = common.load_collector(wrapper_path("hermes"), "hermes_usage")
        hrows, ok = hermes.harness_rows(hermes.AGENT_ID)
        rows["hermes"] = [_row(r, r.model or "(unknown)") for r in hrows]
        complete["hermes"] = bool(ok)
    except Exception as exc:
        log(f"hermes: baris gagal ({exc})")
        rows["hermes"], complete["hermes"] = [], False

    try:  # Claude: transcript + pi/omp (provider anthropic) + opencode DB (provider == anthropic)
        crows, c1 = collectors.claude_code_usage("claude")
        pi_rows, c2 = collectors.scan_pi_sessions(CLAUDE_PI_PATTERN, claude_billed)
        db_rows, c3 = collectors.scan_opencode(['anthropic"'], claude_billed)
        rows["claude"] = ([_row(r, r.model or "(unknown)") for r in crows]
                          + [_row(r, _name(r, str, "claude")) for r in pi_rows]
                          + [_row(r, _name(r, claude_opencode_model, "claude")) for r in db_rows])
        complete["claude"] = bool(c1 and c2 and c3)
    except Exception as exc:
        log(f"claude: baris gagal ({exc})")
        rows["claude"], complete["claude"] = [], False

    try:  # Codex: rollout native (provider bawaan + owner) + pi openai-codex + opencode openai
        urls = collectors.codex_provider_urls()
        native = collectors.CODEX_NATIVE_PROVIDER
        records, c1 = collectors.codex_rollouts(collectors.codex_rollout_cache(), reuse=True, native=True)
        owners, out, skipped = {}, [], 0
        for rec in records.values():
            if rec.get("provider", "") not in ("", native):
                skipped += 1
                continue
            for day, models in rec["days"].items():
                for model, (i, o, cr, cw, p) in models.items():
                    if model not in owners:
                        owners[model] = collectors.codex_route_owner(native, model, urls) == "codex"
                    if not owners[model]:
                        continue
                    out.append({"day": day, "model": codex_model_name(model), "input": i, "output": o,
                                "cacheRead": cr, "cacheWrite": cw, "prompts": p, "session": rec["session"]})
        pi_rows, c2 = collectors.scan_pi_sessions(CODEX_PI_PATTERN, codex_pi_billed)
        db_rows, c3 = collectors.scan_opencode(['openai"'], codex_opencode_billed)
        out += [_row(r, _name(r, codex_model_name, "codex")) for r in pi_rows]
        out += [_row(r, _name(r, lambda m: codex_model_name(str(m or "").rstrip("/").split("/")[-1]), "codex"))
                for r in db_rows]
        rows["codex"] = out
        complete["codex"] = bool(c1 and c2 and c3)
        if skipped:
            log(f"codex: {skipped} rollout provider non-bawaan dilewati (bukan langganan ini)")
    except Exception as exc:
        log(f"codex: baris gagal ({exc})")
        rows["codex"], complete["codex"] = [], False

    try:  # OpenCode: pi/omp (opencode, opencode-go) + DB
        oc = common.load_collector(wrapper_path("opencode"), "opencode_usage")
        pi_rows, c1 = collectors.scan_pi_sessions(OPENCODE_PI_PATTERN, oc.billed_here)
        db_rows, c2 = collectors.scan_opencode(oc.PROVIDERS, oc.billed_here)
        rows["opencode"] = [_row(r, _name(r, oc.model_name, "opencode")) for r in list(pi_rows) + list(db_rows)]
        complete["opencode"] = bool(c1 and c2)
    except Exception as exc:
        log(f"opencode: baris gagal ({exc})")
        rows["opencode"], complete["opencode"] = [], False

    for agent in ROW_AGENTS:
        log(f"{agent}: {len(rows.get(agent, []))} baris (complete={complete.get(agent)})")
    return rows, complete


def aggregate(rows: list[dict]) -> dict:
    """{day: {model: bucket}} dari baris mentah."""
    by_day: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(empty_bucket))
    for r in rows:
        day = r.get("day")
        if not day:
            continue
        model = r.get("model") or "(unknown)"
        b = by_day[day][model]
        b["tokens"] += r["input"] + r["output"] + r["cacheRead"] + r["cacheWrite"]
        b["inputTokens"] += r["input"]
        b["outputTokens"] += r["output"]
        b["cacheReadInputTokens"] += r["cacheRead"]
        b["cacheCreationInputTokens"] += r["cacheWrite"]
        b["prompts"] += r.get("prompts", 0)
        if r.get("session"):
            b["sessions"].add(r["session"])
    for day in by_day:
        for model in by_day[day]:
            by_day[day][model]["sessions"] = len(by_day[day][model]["sessions"])
    return dict(by_day)


def parity_check(rows: list[dict], record: dict, today: str) -> dict:
    """Bandingkan total token baris per hari dengan record.recentDays (7 hari).
    Selisih di luar hari berjalan = komposisi scan skill drift dari wrapper upstream."""
    recent = {e.get("date"): int(e.get("messageCount", 0) or 0)
              for e in (record or {}).get("recentDays") or [] if e.get("date")}
    if not recent:
        return {"checked": False, "ok": None, "mismatches": []}
    by_day = defaultdict(int)
    for r in rows:
        if r.get("day") in recent:
            by_day[r["day"]] += r["input"] + r["output"] + r["cacheRead"] + r["cacheWrite"]
    mism = [{"day": d, "rows": by_day.get(d, 0), "record": t, "today": d == today}
            for d, t in sorted(recent.items()) if by_day.get(d, 0) != t]
    return {"checked": True, "ok": not any(not m["today"] for m in mism), "mismatches": mism}


def build_snapshot() -> dict:
    sys.path.insert(0, str(common.collectors_dir()))
    import collectors  # noqa: E402

    now = datetime.now(timezone.utc).astimezone()
    today = now.strftime("%Y-%m-%d")
    agents_list = discover_agents()
    log(f"mengambil record usage {len(agents_list)} agent (paralel; sebagian memanggil API limit)...")
    records = usage_records(agents_list)
    log("mengambil baris mentah agent lokal...")
    raw_rows, complete = collect_rows(collectors)

    agents = {}
    for agent in sorted(set(agents_list) | set(ROW_AGENTS)):
        rec = records.get(agent) or {}
        rows = raw_rows.get(agent, []) if agent in ROW_AGENTS else []
        entry = {"name": rec.get("name") or agent, "record": rec, "rows": rows,
                 "byDayByModel": aggregate(rows) if rows else {}}
        if agent in ROW_AGENTS:
            entry["complete"] = bool(complete.get(agent, False))
            entry["sessionsByDay"] = common.day_sessions_from_rows(rows)
            entry["parity"] = parity_check(rows, rec, today)
            for m in entry["parity"]["mismatches"]:
                log(f"! parity {agent} {m['day']}: baris={m['rows']:,} record={m['record']:,}"
                    + (" (hari berjalan)" if m["today"] else " — DRIFT komposisi scan?"))
        agents[agent] = entry
    return {"schemaVersion": SCHEMA_VERSION, "collectedAt": now.isoformat(), "today": today, "agents": agents}


def save_snapshot(snapshot: dict) -> Path:
    path = common.snapshots_dir() / f"{snapshot['today']}.json"
    common.atomic_write_json(path, snapshot, indent=2, sort_keys=True)
    log(f"snapshot -> {path}")
    return path


def load_all_snapshots() -> list[dict]:
    return common.load_all_snapshots()


def build_csvs(snapshots: list[dict], out_dir=None) -> None:
    """daily.csv + daily_by_model.csv from all snapshots.

    Latest snapshot wins per (day, agent); an incomplete scan never replaces
    a complete one (common.merge_snapshots). Sources:
      - `model-rows`   : agents with raw per-day x per-model rows.
      - `usage-record` : other agents, daily total from recentDays only.
    daily.csv `sessions` = DISTINCT sessions that day. daily_by_model.csv
    `sessions` = distinct sessions of that model only; never sum it."""
    out = Path(out_dir) if out_dir else common.data_dir()
    latest, record_latest, sessions_by_day, _ = common.merge_snapshots(snapshots)
    daily_rows, model_rows = [], []
    for day in sorted(set(latest) | set(record_latest)):
        for agent in sorted(latest.get(day, {})):
            models = latest[day][agent]
            tot = {k: 0 for k in common.BUCKET_FIELDS}
            for model, b in sorted(models.items()):
                for k in tot:
                    tot[k] += int(b.get(k, 0) or 0)
                model_rows.append({"date": day, "agent": agent, "model": model,
                                   **{k: int(b.get(k, 0) or 0) for k in common.BUCKET_FIELDS},
                                   "sessions": int(b.get("sessions", 0) or 0)})
            daily_rows.append({"date": day, "agent": agent, "source": "model-rows", **tot,
                               "sessions": sessions_by_day.get(day, {}).get(agent, 0)})
        for agent in sorted(record_latest.get(day, {})):
            if agent in latest.get(day, {}):
                continue
            tok = record_latest[day].get(agent) or 0
            if not tok:
                continue
            daily_rows.append({"date": day, "agent": agent, "source": "usage-record",
                               "tokens": tok, "inputTokens": 0, "outputTokens": 0,
                               "cacheReadInputTokens": 0, "cacheCreationInputTokens": 0,
                               "prompts": 0, "sessions": 0})
    fields_daily = ["date", "agent", "source", *common.BUCKET_FIELDS, "sessions"]
    fields_model = ["date", "agent", "model", *common.BUCKET_FIELDS, "sessions"]
    common.write_csv(out / "daily.csv", daily_rows, fields_daily)
    common.write_csv(out / "daily_by_model.csv", model_rows, fields_model)
    log(f"{out / 'daily.csv'}: {len(daily_rows)} baris")
    log(f"{out / 'daily_by_model.csv'}: {len(model_rows)} baris")


def fmt(n) -> str:
    return common.fmt_int(n)


def build_report(snapshots: list[dict], days: int = 7, out_dir=None) -> None:
    if not snapshots:
        return
    snap = snapshots[-1]
    generated = snap.get("collectedAt", "")

    report_dir = Path(out_dir) if out_dir else common.data_dir()
    latest, record_latest, _, _ = common.merge_snapshots(snapshots)

    all_days = sorted(set(latest) | set(record_latest))
    window = all_days[-days:] if days else all_days
    row_agents = sorted({a for d in window for a in latest.get(d, {})})
    other_agents = sorted({
        a for d in window for a in record_latest.get(d, {})
        if a not in row_agents
        and any(record_latest.get(dd, {}).get(a, 0) for dd in window)
    })

    def day_total(day: str, agent: str) -> int:
        models = latest.get(day, {}).get(agent)
        if models:
            return sum(b.get("tokens", 0) for b in models.values())
        return record_latest.get(day, {}).get(agent, 0)

    lines = []
    lines.append("# Pemakaian Token — Omarchy")
    lines.append("")
    lines.append(f"- Dibuat: {generated}")
    lines.append(f"- Rentang: {window[0] if window else '-'} s/d {window[-1] if window else '-'} ({len(window)} hari)")
    lines.append("- Sumber: `omarchy-agent-usage-*` + scanner internal Omarchy")
    lines.extend(common.freshness_lines(report_dir))
    lines.append("")

    # --- ringkasan periode ---
    lines.append("## Ringkasan periode")
    lines.append("")
    lines.append("| Agent | Sumber | Total token | Input | Output | Cache read | Cache write | Non-cache (in+out) | Prompt |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    keys = ("tokens", "inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens", "prompts")
    tot_rows = {k: 0 for k in keys}
    for agent in row_agents:
        s = {k: sum(int(b.get(k, 0) or 0) for d in window for b in latest.get(d, {}).get(agent, {}).values())
             for k in keys}
        for k in keys:
            tot_rows[k] += s[k]
        lines.append(f"| {agent} | model-rows | {fmt(s['tokens'])} | {fmt(s['inputTokens'])} | "
                     f"{fmt(s['outputTokens'])} | {fmt(s['cacheReadInputTokens'])} | "
                     f"{fmt(s['cacheCreationInputTokens'])} | {fmt(s['inputTokens'] + s['outputTokens'])} | "
                     f"{fmt(s['prompts'])} |")
    other_total = 0
    for agent in other_agents:
        tot = sum(record_latest.get(d, {}).get(agent, 0) for d in window)
        other_total += tot
        lines.append(f"| {agent} | usage-record | {fmt(tot)} | — | — | — | — | — | — |")
    t = tot_rows
    lines.append(f"| **Total model-rows** | | **{fmt(t['tokens'])}** | {fmt(t['inputTokens'])} | "
                 f"{fmt(t['outputTokens'])} | {fmt(t['cacheReadInputTokens'])} | "
                 f"{fmt(t['cacheCreationInputTokens'])} | {fmt(t['inputTokens'] + t['outputTokens'])} | "
                 f"{fmt(t['prompts'])} |")
    lines.append(f"| **Total semua agent** | | **{fmt(t['tokens'] + other_total)}** | | | | | | |")
    lines.append("")
    lines.append("> Input + Output + Cache read + Cache write = Total (model-rows). Agent `usage-record` "
                 "hanya punya total harian dari `recentDays`. Pemakaian aktual = **non-cache**.")
    lines.append("")

    # --- total per hari ---
    lines.append("## Total per hari")
    lines.append("")
    all_agents = row_agents + other_agents
    lines.append("| Tanggal | " + " | ".join(all_agents) + " | Total |")
    lines.append("|---|" + "---:|" * (len(all_agents) + 1))
    for day in window:
        cells = []
        day_total_sum = 0
        for a in all_agents:
            tot = day_total(day, a)
            day_total_sum += tot
            cells.append(fmt(tot) if tot else "—")
        lines.append(f"| {day} | " + " | ".join(cells) + f" | {fmt(day_total_sum)} |")
    lines.append("")

    # --- per agent: per hari x per model ---
    for agent in row_agents:
        lines.append(f"## {agent}")
        lines.append("")
        model_names = set()
        for day in window:
            model_names.update(latest.get(day, {}).get(agent, {}).keys())
        if not model_names:
            continue
        model_names = sorted(model_names)
        lines.append("| Tanggal | Model | Tokens | Input | Output | Cache Read | Cache Write | Prompt |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
        for day in window:
            models = latest.get(day, {}).get(agent, {})
            for model in model_names:
                b = models.get(model)
                if not b or not b.get("tokens"):
                    continue
                lines.append(
                    f"| {day} | {model} | {fmt(b.get('tokens'))} | "
                    f"{fmt(b.get('inputTokens'))} | {fmt(b.get('outputTokens'))} | "
                    f"{fmt(b.get('cacheReadInputTokens'))} | {fmt(b.get('cacheCreationInputTokens'))} | "
                    f"{fmt(b.get('prompts'))} |"
                )
        lines.append("")

    # --- agent lain: total per hari ---
    if other_agents:
        lines.append("## Agent lain (total per hari)")
        lines.append("")
        lines.append("| Tanggal | " + " | ".join(other_agents) + " |")
        lines.append("|---|" + "---:|" * len(other_agents))
        for day in window:
            cells = []
            for a in other_agents:
                tot = record_latest.get(day, {}).get(a, 0)
                cells.append(fmt(tot) if tot else "—")
            lines.append(f"| {day} | " + " | ".join(cells) + " |")
        lines.append("")

    # --- limit ---
    lines.append("## Limit / Kuota")
    lines.append("")
    lines.append("> `percent` di record = **pecahan 0–1** (0.95 = 95% terpakai); kolom ini = percent × 100. "
                 "`resetsAt` = ISO UTC.")
    lines.append("")
    lines.append("| Agent | Label | Terpakai | Reset | Catatan |")
    lines.append("|---|---|---:|---|---|")
    collected = common.parse_ts(snap.get("collectedAt"))
    for agent in all_agents:
        rec = snap.get("agents", {}).get(agent, {}).get("record") or {}
        for lim in rec.get("limits") or []:
            reset = lim.get("resetsAt", "") or ""
            reset_dt = common.parse_ts(reset)
            note = "reset sudah lewat saat snapshot" if (reset_dt and collected and reset_dt < collected) else ""
            try:
                pct = f"{float(lim.get('percent', 0)) * 100:.0f}%"
            except (TypeError, ValueError):
                pct = "?"
            lines.append(f"| {agent} | {lim.get('label', '')} | {pct} | {reset} | {note} |")
    lines.append("")

    lines.append("## Cek paritas scan (baris vs recentDays wrapper)")
    lines.append("")
    any_p = False
    for agent in ROW_AGENTS:
        p = (snap.get("agents", {}).get(agent) or {}).get("parity")
        if not p:
            continue
        any_p = True
        if not p.get("checked"):
            lines.append(f"- {agent}: tidak dicek (record tanpa recentDays)")
        elif not p["mismatches"]:
            lines.append(f"- {agent}: OK (7 hari cocok)")
        else:
            bad = ", ".join(f"{m['day']} baris {fmt(m['rows'])} vs record {fmt(m['record'])}"
                            + (" (hari berjalan)" if m["today"] else "") for m in p["mismatches"])
            lines.append(f"- {agent}: {'OK kecuali hari berjalan' if p['ok'] else '**SELISIH**'} — {bad}")
    if not any_p:
        lines.append("- (snapshot lama tanpa data paritas)")
    lines.append("")

    common.atomic_write_text(report_dir / "report.md", "\n".join(lines))
    log(f"{report_dir / 'report.md'} ({len(lines)} baris)")


def run_chain(offline: bool) -> int:
    """collect -> cost --report -> metrics --report --offline -> weekly (M11)."""
    here = Path(__file__).resolve().parent
    steps = [["cost.py", "--report"] + (["--offline"] if offline else []),
             ["metrics.py", "--report", "--offline"],   # pakai harga yang baru diambil cost.py
             ["weekly.py"]]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    worst = 0
    for step in steps:
        log("menjalankan " + " ".join(step))
        sys.stdout.flush()
        rc = subprocess.run([sys.executable, str(here / step[0]), *step[1:]], env=env).returncode
        if rc:
            log(f"{step[0]} gagal (exit {rc})")
            worst = worst or rc
    return worst


def main() -> int:
    parser = argparse.ArgumentParser(description="Kolektor pemakaian token Omarchy")
    parser.add_argument("--report", action="store_true",
                        help="bangun ulang CSV + report dari snapshot (tanpa scan, tanpa network)")
    parser.add_argument("--days", type=int, default=7, help="jumlah hari di report.md (default 7)")
    parser.add_argument("--all", action="store_true",
                        help="lanjutkan pipeline: cost.py --report, metrics.py --report, weekly.py")
    parser.add_argument("--offline", action="store_true",
                        help="dengan --all: cost.py tanpa fetch harga (pakai cache/seed)")
    args = parser.parse_args()

    if not args.report:
        save_snapshot(build_snapshot())
    snapshots = common.load_all_snapshots()
    if not snapshots:
        log("tidak ada snapshot")
        return 1
    build_csvs(snapshots)
    build_report(snapshots, days=args.days)
    return run_chain(args.offline) if args.all else 0


if __name__ == "__main__":
    raise SystemExit(main())
