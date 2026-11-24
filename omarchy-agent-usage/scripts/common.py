"""Shared helpers for the omarchy-agent-usage scripts (stdlib only).

Paths are resolved at CALL time (not import time) so env overrides work:
  OMARCHY_USAGE_DATA           data dir (default ${XDG_STATE_HOME:-~/.local/state}/omarchy/agents/usage-history)
  OMARCHY_USAGE_PRICING_CACHE  runtime price cache (default ${XDG_CACHE_HOME:-~/.cache}/omarchy-agent-usage/pricing.json)
  OMARCHY_USAGE_PRICING_SEED   read-only seed (default <skill>/references/pricing.json)
  OMARCHY_TASKS_FILE           task signal (default ${XDG_STATE_HOME:-~/.local/state}/omarchy/agents/tasks.jsonl)
  OMARCHY_PATH                 Omarchy install (default /usr/share/omarchy)
"""
from __future__ import annotations

import csv
import importlib.machinery
import importlib.util
import io
import json
import os
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent

VALID_AGENTS = frozenset({"hermes", "claude", "codex", "opencode", "agy", "grok"})
VALID_STATUSES = ("ok", "partial", "fail")
STATUS_WEIGHT = {"ok": 1.0, "partial": 0.5, "fail": 0.0}
BUCKET_FIELDS = ("tokens", "inputTokens", "outputTokens", "cacheReadInputTokens",
                 "cacheCreationInputTokens", "prompts")


def warn(msg: str) -> None:
    print(f"! {msg}", file=sys.stderr, flush=True)


# --- paths -------------------------------------------------------------------

def _env_path(var: str) -> Path | None:
    value = os.environ.get(var)
    return Path(value).expanduser() if value else None


def _xdg(var: str, fallback: str) -> Path:
    return _env_path(var) or (Path.home() / fallback)


def data_dir(create: bool = True) -> Path:
    path = _env_path("OMARCHY_USAGE_DATA") or (
        _xdg("XDG_STATE_HOME", ".local/state") / "omarchy" / "agents" / "usage-history")
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def snapshots_dir(create: bool = True) -> Path:
    path = data_dir(create) / "snapshots"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def pricing_cache_path() -> Path:
    return _env_path("OMARCHY_USAGE_PRICING_CACHE") or (
        _xdg("XDG_CACHE_HOME", ".cache") / "omarchy-agent-usage" / "pricing.json")


def pricing_seed_path() -> Path:
    return _env_path("OMARCHY_USAGE_PRICING_SEED") or (SKILL_DIR / "references" / "pricing.json")


def tasks_path() -> Path:
    return _env_path("OMARCHY_TASKS_FILE") or (
        _xdg("XDG_STATE_HOME", ".local/state") / "omarchy" / "agents" / "tasks.jsonl")


def omarchy_path() -> Path:
    return Path(os.environ.get("OMARCHY_PATH") or "/usr/share/omarchy")


def bin_dir() -> Path:
    return omarchy_path() / "bin"


def collectors_dir() -> Path:
    return omarchy_path() / "shell" / "plugins" / "agents"


def load_collector(path, name: str):
    """Load an extension-less Omarchy collector script as a module.

    spec_from_file_location() returns a spec whose loader is None for files
    without .py, so use SourceFileLoader + spec_from_loader. The wrappers
    have __main__ guards, so loading does not run them."""
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


# --- atomic IO -----------------------------------------------------------------

def atomic_write_text(path, text: str) -> None:
    """Write via temp file in the same dir + os.replace (no truncated files)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def atomic_write_json(path, obj, **kwargs) -> None:
    atomic_write_text(path, json.dumps(obj, **kwargs))


def write_csv(path, rows: list[dict], fields: list[str]) -> None:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    atomic_write_text(path, buf.getvalue())


def write_csv_rows(path, header: list[str], rows: list[list]) -> None:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerows(rows)
    atomic_write_text(path, buf.getvalue())


def fmt_int(n) -> str:
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n)


# --- snapshots -----------------------------------------------------------------

def load_all_snapshots(snap_dir=None) -> list[dict]:
    """All top-level snapshots/*.json (snapshots/archive/ is ignored), oldest
    first by (today, collectedAt). Unreadable files are skipped LOUDLY."""
    d = Path(snap_dir) if snap_dir else snapshots_dir(create=False)
    out = []
    if not d.is_dir():
        return out
    for path in sorted(d.glob("*.json")):
        try:
            with open(path, encoding="utf-8") as fh:
                snap = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            warn(f"snapshot dilewati (rusak/tak terbaca): {path} ({exc})")
            continue
        if not isinstance(snap, dict) or not isinstance(snap.get("agents"), dict):
            warn(f"snapshot dilewati (bukan format snapshot): {path}")
            continue
        out.append(snap)
    out.sort(key=lambda s: (str(s.get("today") or ""), str(s.get("collectedAt") or "")))
    return out


def day_sessions_from_rows(rows) -> dict[str, int]:
    """Distinct sessions per day from raw rows. The per-model `sessions`
    counts must NEVER be summed: one session spans several model rows."""
    seen: dict[str, set] = defaultdict(set)
    for r in rows or []:
        day, session = r.get("day"), r.get("session")
        if day and session:
            seen[day].add(session)
    return {day: len(s) for day, s in seen.items()}


def merge_snapshots(snapshots: list[dict]):
    """Merge snapshots (oldest -> newest).

    Returns (latest, record_latest, sessions_by_day, source_day):
      latest[day][agent]          = {model: bucket}   (byDayByModel)
      record_latest[day][agent]   = tokens from record.recentDays
      sessions_by_day[day][agent] = DISTINCT sessions that day
      source_day[day][agent]      = `today` of the snapshot that won

    Rule: the latest snapshot wins per (day, agent), EXCEPT an incomplete
    scan (agent["complete"] is False) never replaces a complete one.
    Snapshots without a `complete` flag (schema v1) count as complete.
    Distinct sessions come from `sessionsByDay` (schema v2) or are
    recomputed from the stored raw `rows` (schema v1)."""
    latest: dict = {}
    record_latest: dict = {}
    sessions: dict = {}
    source: dict = {}
    complete_of: dict = {}
    for snap in snapshots:
        for agent, data in (snap.get("agents") or {}).items():
            data = data or {}
            is_complete = data.get("complete", True) is not False
            spd = data.get("sessionsByDay")
            if not isinstance(spd, dict):
                spd = day_sessions_from_rows(data.get("rows"))
            for day, models in (data.get("byDayByModel") or {}).items():
                if complete_of.get((day, agent)) is True and not is_complete:
                    continue
                latest.setdefault(day, {})[agent] = models
                fallback = max((int(b.get("sessions", 0) or 0) for b in models.values()), default=0)
                sessions.setdefault(day, {})[agent] = int(spd.get(day, fallback))
                source.setdefault(day, {})[agent] = snap.get("today")
                complete_of[(day, agent)] = is_complete
            rec = data.get("record") or {}
            for entry in rec.get("recentDays") or []:
                day = entry.get("date")
                if day:
                    record_latest.setdefault(day, {})[agent] = int(entry.get("messageCount", 0) or 0)
    return latest, record_latest, sessions, source


def freshness_lines(ddir=None) -> list[str]:
    """Markdown bullet lines stamping which data a report was built from."""
    ddir = Path(ddir) if ddir else data_dir()
    lines = [f"- Data dir: `{ddir}`"]
    csv_path = ddir / "daily_by_model.csv"
    if csv_path.exists():
        mtime = datetime.fromtimestamp(csv_path.stat().st_mtime).astimezone()
        lines.append(f"- Sumber CSV: `daily_by_model.csv` (mtime {mtime.isoformat(timespec='seconds')})")
    snaps = sorted((ddir / "snapshots").glob("*.json")) if (ddir / "snapshots").is_dir() else []
    lines.append(f"- Snapshot terbaru: `{snaps[-1].stem if snaps else '—'}`")
    return lines


# --- task signal ---------------------------------------------------------------

def parse_ts(ts):
    """ISO 8601 -> aware LOCAL datetime (naive input is taken as local), or None."""
    if not isinstance(ts, str) or not ts.strip():
        return None
    try:
        parsed = datetime.fromisoformat(ts.strip().replace("Z", "+00:00"))
        return parsed.astimezone()
    except (ValueError, OverflowError, OSError):
        return None


def local_date_from_ts(ts):
    parsed = parse_ts(ts)
    return parsed.strftime("%Y-%m-%d") if parsed else None


def read_task_entries(path=None):
    """Validated rows of tasks.jsonl -> (entries, malformed).

    entries: dicts with extra keys `_line`, `_dt` (aware local), `_date` (local day).
    malformed: list of (line_no, reason). Malformed rows are counted, never silently dropped."""
    p = Path(path) if path else tasks_path()
    entries, malformed = [], []
    if not p.exists():
        return entries, malformed
    with open(p, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                malformed.append((i, f"JSON tidak valid: {exc}"))
                continue
            if not isinstance(obj, dict):
                malformed.append((i, "bukan objek JSON"))
                continue
            issues = []
            parsed = None
            if "ts" not in obj:
                issues.append("ts hilang")
            else:
                parsed = parse_ts(obj["ts"])
                if parsed is None:
                    issues.append(f"ts bukan ISO 8601: {obj['ts']!r}")
            if "agent" not in obj:
                issues.append("agent hilang")
            elif obj["agent"] not in VALID_AGENTS:
                issues.append(f"agent '{obj['agent']}' tidak dikenal")
            if "status" not in obj:
                issues.append("status hilang")
            elif obj["status"] not in VALID_STATUSES:
                issues.append(f"status '{obj['status']}' tidak valid")
            if "turns" in obj:
                t = obj["turns"]
                if isinstance(t, bool) or not isinstance(t, int) or t < 1:
                    issues.append(f"turns harus integer >= 1, dapat: {t}")
            if issues:
                malformed.append((i, "; ".join(issues)))
                continue
            entries.append(dict(obj, _line=i, _dt=parsed, _date=parsed.strftime("%Y-%m-%d")))
    return entries, malformed


def dedupe_by_session(entries):
    """One task per (agent, session).

    Hermes `on_session_end` and OpenCode `session.idle` fire once per TURN,
    so one session writes many rows. Winner = latest `_dt` (tie: later line);
    its status and date are used. Rows with an empty/missing session are
    each their own task. Returns (kept_in_file_order, duplicates_dropped)."""
    best: dict = {}
    loose = []
    for e in entries:
        session = str(e.get("session") or "").strip()
        if not session:
            loose.append(e)
            continue
        key = (e["agent"], session)
        cur = best.get(key)
        if cur is None or (e["_dt"], e["_line"]) >= (cur["_dt"], cur["_line"]):
            best[key] = e
    kept = sorted(loose + list(best.values()), key=lambda e: e["_line"])
    return kept, len(entries) - len(kept)


def read_tasks(path=None, dedupe: bool = True):
    """-> (agg, info).
    agg[(date, agent)] = {"ok", "partial", "fail", "weight"} (after dedupe);
    info = {"raw", "malformed", "duplicates", "tasks"}."""
    entries, malformed = read_task_entries(path)
    kept, dups = dedupe_by_session(entries) if dedupe else (entries, 0)
    agg: dict = defaultdict(lambda: {"ok": 0, "partial": 0, "fail": 0, "weight": 0.0})
    for e in kept:
        a = agg[(e["_date"], e["agent"])]
        a[e["status"]] += 1
        a["weight"] += STATUS_WEIGHT[e["status"]]
    info = {"raw": len(entries) + len(malformed), "malformed": len(malformed),
            "duplicates": dups, "tasks": len(kept)}
    return dict(agg), info
