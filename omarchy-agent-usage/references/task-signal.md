# Task Signal — `tasks.jsonl`

The task-completed signal for the **cost per task** metric.

## File location

```
~/.local/state/omarchy/agents/tasks.jsonl
```

Append-only, one JSON object per line. Override via the env var `OMARCHY_TASKS_FILE` (required in tests).

## Schema

```json
{"ts":"2026-11-17T16:20:00+07:00","agent":"hermes","session":"local-9b07…","label":"hermes session","status":"ok"}
```

| Field     | Required | Type    | Rule |
|-----------|----------|---------|------|
| `ts`      | yes      | string  | ISO 8601 (a time zone is recommended; without one it is local time). `Z` is accepted |
| `agent`   | yes      | string  | `hermes` \| `claude` \| `codex` \| `opencode` \| `agy` \| `grok` |
| `session` | —        | string  | session id; **used for dedupe** |
| `label`   | —        | string  | free text |
| `status`  | yes      | string  | `ok` \| `partial` \| `fail` |
| `turns`   | —        | integer | ≥ 1 |

### Rules

- Append-only. A row already written must not be deleted or edited.
- A malformed row is skipped **and counted** (never silently ignored).
- **Dedupe when reading** (`common.read_tasks`):
  - one task = one (agent, session);
  - the winner is the row with the latest `ts` (its status and date are used);
  - a row without `session` = a task of its own.

  Dedupe is needed because installed hooks fire **per turn**, not per session.
- The date = the LOCAL day of `ts` (`ts` is converted to the local zone first), consistent with the `local_day` bucket in `collect.py`.

## Semantics

| Status    | Weight |
|-----------|-------:|
| `ok`      |    1.0 |
| `partial` |    0.5 |
| `fail`    |    0.0 |

- **Cost per task (per agent-day)** = the agent's cost on that day ÷ that agent's task weight. The cost of a failed task still counts (its weight is 0 in the denominator).
- **Date / period aggregate** = Σ cost ÷ Σ weight **only over agent-days that have task rows**. Agents without a task signal (currently Claude, Codex) are left out. An agent-day with no usage data or with unpriced tokens is excluded, and listed in the report.
- Usage that is entirely free models = a *known* cost of $0 → `0.0000 (free)`.
- `n/a` always comes with a reason:
  - `n/a (no tasks)`
  - `n/a (all tasks failed, weight 0)`
  - `n/a (no usage data)`
  - `n/a (unpriced tokens)`
- Granularity: because task = session, "cost per task" = **cost per session**, not per semantic task.

## CLI

```bash
omarchy-tasklog record --agent hermes --label "fix tests" --status ok --session S1   # shim in ~/.local/bin
python3 scripts/tasklog.py record --agent hermes --status ok                         # same, directly
python3 scripts/tasklog.py summary [--days 7] [--agent hermes]
python3 scripts/tasklog.py validate
```

- `record`: appends one row (default `status=ok`, `ts=now`); `--ts` is validated as ISO 8601.
- `summary`: the number of tasks per agent/day + weight, **after session dedupe** (it prints how many duplicate rows there were). It does **not** compute cost; cost per task is in `metrics.py`.
- `validate`: checks all raw rows (without dedupe) and reports malformed rows (line number + reason).
- Stdlib only.

## Hook writers (generic example)

Each agent has its own hook mechanism; check your agent's documentation. The usual pattern is the same:

1. An "end of turn/session" hook calls `omarchy-tasklog record --agent <a> --status ok --session <session ID from the hook payload>`.
2. The hook must not block the agent (`|| true`) and must not read credentials.
3. Many agents send this event **per turn**, not per session. One session can write dozens of rows; the reader dedupes per (agent, session).
4. Check the result: `grep -c '"agent": "<a>"' "$OMARCHY_TASKS_FILE"` > 0 after one session. Hook failures should preferably be logged to `tasklog-errors.log` in the same folder as `tasks.jsonl`.

Hook notes specific to your machine (paths, allowlist, how to revoke) go in `references/task-signal.local.md`. That file is in `.gitignore`; the agent is asked to read it if present.

## Untested templates

Examples only. Match them against the real agent's hook system first. All templates call the shim, don't read credentials, and don't block the agent if they fail.

### Claude Code (`~/.claude/settings.json`, `Stop` hook)

Claude Code sends a JSON payload on stdin that contains `session_id`. `Stop` fires per turn; the reader's dedupe handles it.

```jsonc
{
  "hooks": {
    "Stop": [
      { "matcher": "", "hooks": [ { "type": "command",
        "command": "sid=$(jq -r '.session_id // empty' 2>/dev/null); omarchy-tasklog record --agent claude --status ok --label 'claude stop' --session \"$sid\" >/dev/null 2>&1 || true" } ] }
    ]
  }
}
```

Codex and agy: there is no verified hook mechanism yet. Record manually with `omarchy-tasklog record --agent codex …` if needed.
