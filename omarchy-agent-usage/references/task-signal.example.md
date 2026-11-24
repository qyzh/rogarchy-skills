# Task signal notes template (this machine)

Copy this file to `task-signal.local.md` (gitignored) and fill it in for this
machine. When `task-signal.local.md` exists, the `omarchy-agent-usage` skill
reads it next to the generic `task-signal.md`. `rogarchy-setup` can create the
copy for you; it never overwrites an existing one.

Keep machine paths and profile names in the `.local.md` copy only, never in
this template.

## Hooks installed

| Agent | Hook event | Where the hook is configured | Command |
|---|---|---|---|
| `<agent>` | `<Stop / on_session_end / session.idle>` | `<settings file>` | `omarchy-tasklog record --agent <agent> --status ok --session <id>` |

## Not hooked

- `<agent>`: no hook yet; it has no task rows.

## Check

- `grep -c '"agent": "<agent>"' "$(rs_get OMARCHY_TASKS_FILE "${XDG_STATE_HOME:-$HOME/.local/state}/omarchy/agents/tasks.jsonl")"` > 0 after one session (`rs_get`: see the skill's Prerequisites / Config; it resolves env var, then config.env, then the default).
- Hook errors go to `tasklog-errors.log` next to `tasks.jsonl`.

## How to remove

- `<agent>`: delete the hook entry from `<settings file>`.
