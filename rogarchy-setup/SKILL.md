---
name: rogarchy-setup
description: "Only when the user asks: set up or check rogarchy-skills. Links skills into agent skill folders, writes their settings file, reports what is missing. Never load it on your own; wait for /rogarchy-setup or an explicit request to set up, install, configure or check rogarchy-skills."
version: 0.1.0
author: qyzh, Hermes Agent
license: MIT
platforms: [linux, macos]
disable-model-invocation: true
metadata:
  hermes:
    tags: [setup, install, config, check]
    related_skills: []
---

# rogarchy-setup

Set up the skills of this repo, or check how they are set up. You do the work yourself with ordinary shell commands, in a fixed order: look around first, show the user every planned change, and change nothing until they say "yes". Talk to the user in English.

Two modes:

- **setup** (default): link skills into agent skill folders, write the settings file, optionally create personal `.local.md` files.
- **check**: the same discovery, read-only. Use it when the user says "check", "doctor", "status" or "what's missing".

## Hard rules

- Write only these: symlinks inside the agent skill folders the user picked (and `mkdir -p` of those folders), the settings file `config.env` (with `mkdir -p` of its folder, a timestamped backup `config.env.bak.<time>` and a `mktemp` temp file beside it), and `.local.md` copies the user confirmed. Nothing else.
- Never overwrite. A target that already exists and is not a symlink into this repo is reported, never replaced. No `ln -f`, no `rm`, no `cp` without `-n`; backups get a new timestamped name each time. The only file replaced is `config.env` itself, by `mv` of a confirmed temp file; if `config.env` is a symlink, the link stays and its target file is replaced.
- Never edit shell profiles (`~/.bashrc`, `~/.zshrc`, ...) or agent env files (`~/.hermes/.env`, ...). Print the line for the user to add instead.
- Secrets (Kind `secret`) are env-only. Never ask for them, never write them anywhere, never print their values: report only `set` or `not set`. If the user pastes a key into chat, do not repeat or store it, and suggest they rotate it.
- Never write inside the repo except confirmed `.local.md` copies (gitignored). `config.env` must live outside the repo; refuse a path inside it.
- Never write before the user confirms the draft (step 4).

## Terms

- `<skill-dir>`: the folder holding this `SKILL.md`. `<repo>`: the real parent of it, `realpath "<skill-dir>/.."` (the skill folder is usually a symlink).
- **Skill**: a top-level folder of `<repo>` that holds a `SKILL.md`. This skill (`rogarchy-setup`) is one of them.
- **Settings file**: `${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env`. Plain `KEY=value` lines, read as data and never sourced. First line `# rogarchy-skills config v1`. Each skill resolves a variable as: env var if set and non-empty, else the last `KEY=value` line here, else the skill's default.
- **Install targets** (skill folders of agents):

  | Agent | Folder | Offer it when |
  |---|---|---|
  | Hermes Agent, default profile | `~/.hermes/skills` | `~/.hermes` exists |
  | Hermes Agent, profile `<p>` | `~/.hermes/profiles/<p>/skills` | `~/.hermes/profiles/<p>/` holds `config.yaml`, `.env`, `SOUL.md`, `profile.yaml`, `auth.json` or `state.db` |
  | Claude Code | `~/.claude/skills` | `~/.claude` exists |
  | Shared agents folder | `~/.agents/skills` | `~/.agents` exists |
  | Custom | a folder the user names | always offered |

## How a skill declares its setup

Each skill's `SKILL.md` has a `## Prerequisites / Config` section in this shape. Read it from every skill; do not hard-code any skill's values here.

```markdown
## Prerequisites / Config

Requires: commands `yt-dlp`, `python3`; skills `youtube-content`.
Local files: `references/x.local.md` (template `references/x.example.md`).

| Variable | Meaning | Default | Kind |
|---|---|---|---|
| `SOME_DIR` | What it controls | `$HOME/some-dir` | setting |
```

- `Requires:` names commands (check with `command -v`) and skills (look for `<target>/<name>/SKILL.md` in the install targets). Other text on the line (platform notes, "or" alternatives) is informational; report it as written. `none` means nothing.
- `Local files:` lists personal files, each with its template. `none` means nothing.
- A variable declared by several skills (e.g. `OMARCHY_USAGE_DATA`) is one setting: ask it once and write it once, in the block of the first of those skills in alphabetical order.
- The table lists variables, or the section says `Variables: none.` Kind is `setting` (ask), `advanced` (keep the default unless the user wants to change it) or `secret` (env only, see Hard rules). Defaults are shell expressions; expand them in the user's shell to show the effective value.
- A skill with no such section: report `no config section` and skip its config.
- A skill whose frontmatter `platforms:` excludes this OS (`uname -s`: Linux → `linux`, Darwin → `macos`) is not offered for install and is marked `skipped (platform)`.

## Look up a value without printing secrets

Resolve a variable and its source (never use this for `secret` variables):

```bash
rs_src() { _rs_v=$(printenv "$1" || :); if [ -n "$_rs_v" ]; then printf 'env\t%s\n' "$_rs_v"; return 0; fi
  _rs_v=$(sed -n "s/[[:space:]]*\$//; s/^$1=//p" "${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env" 2>/dev/null | tail -n 1 || :)
  if [ -n "$_rs_v" ]; then printf 'config\t%s\n' "$_rs_v"; else printf 'default\t%s\n' "$2"; fi; }
rs_src YTSUM_OUTPUT_DIR "$HOME/ytsum"
```

For a secret, print only whether it is set: `[ -n "$(printenv NAME)" ] && echo set || echo "not set"`. Note in the report that this is the env of the agent's own shell; a skill run by another agent or service may see a different env.

## check mode (read-only)

Run the discovery below and report it as compact tables. Write nothing.

1. **Skills**: every skill in `<repo>` with its version (frontmatter `version`).
2. **Settings**: per variable: skill, value, source (`env` / `config` / `default`). Secrets: `set` / `not set` only. Flag values that point to a missing folder or file only when the Meaning says it must exist (an output folder that will be created is fine).
3. **Requirements**: each command found or missing; each required skill found or missing per install target that holds rogarchy skills.
4. **Install status**: per target × skill, one of:
   - `linked`: a symlink whose `realpath` is `<repo>/<skill>`
   - `missing`: nothing there
   - `foreign link`: a symlink to somewhere else
   - `broken link`: a symlink to nothing
   - `not ours`: a real folder or file
5. **Local files**: per declared `.local.md`, `present` or `missing` (and whether its template exists).
6. **Settings file**:
   - whether it exists and has the `# rogarchy-skills config v1` line
   - its mode (expect `600`)
   - keys no skill declares (`unknown`)
   - keys that look secret (`*_KEY`, `*_TOKEN`, `*_SECRET`, `*PASSWORD*`), reported by name only, with a warning to move them to the env

End with a short "To fix" list.

## setup mode

### 1. Explore (no writes)

Do everything check mode does. Also list the candidate install targets from the Terms table, with the rogarchy skills each one already links.

### 2. Ask

Ask one group at a time, in English. Use the agent's multiple-choice question tool if it has one. Show a default for every question.

1. **Targets**: "Which agent skill folders should these skills be linked into?" Multi-select from the detected targets plus "Custom path". Default: the targets that already link rogarchy skills; if none, ask with no preselection.
2. **Skills**: "Link all skills that support this OS, or pick some?" Default: all. `rogarchy-setup` itself is included, so it can be run again from the agent.
3. **Settings**: for each `setting` variable, show the Meaning, the default and the current value with its source.
   - Ask: "Keep `<current>` or enter a new value?"
   - If the env var is set, say that the env value wins over anything written to `config.env`.
4. **Advanced**: one question: "Change any advanced settings? (default: no)". Only on "yes", list them and ask per variable.
5. **Local files**: for each missing `.local.md`, ask: "Create `<skill>/<local>` from its template now? (default: no)".
   - Explain that the skill follows this file as soon as it exists, so the placeholders must be replaced before the next use.
6. **Secrets**: do not ask for values. For each secret that is not set, say where the user can set it:
   - Hermes: `~/.hermes/.env`, or `~/.hermes/profiles/<p>/.env` for a profile.
   - Other agents: their own env/secret setting, or the user's shell profile.

   Then show the line to add, `NAME=<your key>`, and the skill's link for getting a key if it has one.

### 3. Build the draft

- **Symlink plan**: per target × skill, one line:
  - `link`: will run `ln -s "<repo>/<skill>" "<target>/<skill>"`
  - `ok`: already linked, nothing to do
  - `skip`: `foreign link`, `broken link` or `not ours`; report it and leave it alone
  - `skip (platform)`
- **Settings file**: the full proposed file and a unified diff against the current one (`diff -u`; "new file" if absent). Build it like this:
  - First line `# rogarchy-skills config v1`, then a comment saying env vars override these values and the file is read as data.
  - One block per skill (`# <skill>` comment), with a line for each `setting` variable and each `advanced` variable the user changed. A shared key goes only in the block of the first skill (alphabetical) that declares it. Write values as literal absolute paths: expand `$HOME`, `~` and `${...}` before writing, because nothing expands them later.
  - Keep every existing line the user wrote, including unknown keys and comments, unless the user asked to change that key. Replace a key in place; never write the same key twice.
  - Never write a `secret` variable.
  - If `config.env` is a symlink, say so in the draft: "config.env is a link to `<realpath>`; that file will be updated, the link stays." If the link is broken or its target is inside `<repo>`, stop and report instead.
- **Local files**: each `cp -n "<template>" "<local>"` the user agreed to.

### 4. Confirm

Show the whole draft and ask: "Apply these changes? (yes / no / change something)". On "change something", go back to the matching question. If the draft changes nothing (all symlinks `ok`, empty diff, no copies), say "Already set up, nothing to write" and stop.

### 5. Write

Apply only what the confirmed draft lists:

1. **Symlinks**: `mkdir -p "<target>"`, then for each `link` line, `[ -e "<target>/<skill>" ] || [ -L "<target>/<skill>" ] || ln -s "<repo>/<skill>" "<target>/<skill>"`.
2. **Settings file**, only if the diff is not empty:
   - `mkdir -p` its folder. Let `F` be the file to update: `config.env`, or its `realpath` if it is a symlink (as shown in the draft).
   - If `F` exists, back it up without overwriting an older backup: `cp -p -n "$F" "$F.bak.$(date +%Y%m%d-%H%M%S)"`.
   - `tmp=$(mktemp "$(dirname "$F")/config.env.XXXXXX")` (created with mode 600), write the new content to `"$tmp"`, then `mv "$tmp" "$F"`. Never write through a fixed temp name.
3. **Local files**: `cp -n "<template>" "<local>"`.

### 6. Verify and report

Run check mode again and show its tables. Then list what was written: the symlinks made, the settings file path (and its `.bak.<time>` backup), the local files created. Also list what was skipped and why, the secrets still not set, and the missing requirements, with the command or skill to install. Setup never installs packages or third-party skills.

## Re-running

Re-running is safe:

- Existing links stay.
- Your values and extra lines in `config.env` are kept.
- Existing `.local.md` files are never touched.
- An unchanged draft writes nothing.

To remove a skill from an agent, delete its symlink (`rm <target>/<skill>` removes only the link, not the repo folder). This version has no uninstall mode.
