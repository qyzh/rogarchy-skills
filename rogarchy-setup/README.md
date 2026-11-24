# rogarchy-setup

## What it is

A skill that sets up the other skills in this repo, or checks how they are set up. The agent follows it step by step: it looks around, shows you a draft of every change, and writes only after you say yes.

- **setup** links skills into your agents' skill folders (symlinks, never copies), writes one settings file, and can create your personal `.local.md` files from their templates.
- **check** is read-only. It reports:
  - each setting's value and where it came from (env var, settings file or default)
  - missing commands and supporting skills
  - link status per agent
  - which `.local.md` files exist
  - whether secrets are set (never their values)

## When to use / not use

Use it when:

- You run `/rogarchy-setup`, or ask the agent to set up, install, configure or check rogarchy-skills.
- You added an agent or a profile and want the skills there too.
- A skill can't find its folder, tool or supporting skill, and you want to know why.

Don't use it for:

- Installing system packages (`yt-dlp`, Node, Chromium) or third-party skills. Setup only reports what is missing.
- Setting API keys. Keys stay in your environment; setup only tells you whether they are set.
- Removing skills. This version has no uninstall: delete the symlink yourself.

The skill is meant to run only when you ask for it. Claude Code honors `disable-model-invocation: true` in its frontmatter. Hermes Agent has no such key and ignores it, so the description also says to load it only on request.

## Requirements

- Linux or macOS with a POSIX shell (`ln`, `sed`, `diff`, `realpath`).
- An agent that reads `SKILL.md` folders, with terminal access. Tested targets:
  - Hermes Agent (`~/.hermes/skills`, `~/.hermes/profiles/<profile>/skills`)
  - Claude Code (`~/.claude/skills`)
  - the shared `~/.agents/skills` folder
  - any custom folder
- No supporting skills.

## Configuration

Setup writes the settings file `${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env`. Every skill resolves each setting in this order:

1. the environment variable, if it is set and not empty
2. its `KEY=value` line in `config.env`
3. the skill's default

A missing file or line means the default, so skills work without setup and existing environment variables keep working.

```bash
# rogarchy-skills config v1
# Written by rogarchy-setup. Env vars override these values. Read as data, never sourced.

# ytsum
YTSUM_OUTPUT_DIR=/home/<you>/Documents/ytsum
```

The file format:

- One `KEY=value` per line, with no quotes and no `export`.
- Values are literal: `$HOME` and `~` are not expanded, so setup writes absolute paths.
- `#` lines are comments. If a key appears twice, the last line wins.

Safety rules:

- Setup shows a diff before writing.
- It keeps a `config.env.bak` copy and sets the file to mode `600`.
- It keeps any lines you added yourself.
- It never puts secrets in the file.

Secrets such as `ARTIFICIAL_ANALYSIS_API_KEY` belong in your agent's env file (for Hermes: `~/.hermes/.env`, or `~/.hermes/profiles/<profile>/.env`) or in your shell profile. You add them yourself; setup never edits those files.

Each skill's `SKILL.md` declares what setup needs in a `## Prerequisites / Config` section, with the same shape in every skill:

- a `Requires:` line
- a `Local files:` line
- a table with the columns `Variable | Meaning | Default | Kind`

Kind is one of:

- `setting`: setup asks for it.
- `advanced`: setup keeps the default unless you ask.
- `secret`: env only.

A new skill plugs in by adding that section.

## Usage examples

```text
/rogarchy-setup
```

The agent detects your agent folders and asks which ones to use and which skills to link. It asks for each setting (default shown) and whether to create missing `.local.md` files. Then it shows the draft:

```text
Symlinks
  ~/.hermes/profiles/<profile>/skills/ytsum   link  -> <repo>/ytsum
  ~/.hermes/profiles/<profile>/skills/kamus   ok    (already linked)
  ~/.claude/skills/kamus                      skip  (not ours: real folder)

config.env (new file)
  + # rogarchy-skills config v1
  + KAMUS_DIR=/home/<you>/notes/kamus
  + YTSUM_OUTPUT_DIR=/home/<you>/ytsum

Apply these changes? (yes / no / change something)
```

```text
/rogarchy-setup check
```

This gives a read-only report: settings with their source, missing commands and skills, link status per agent, local files, secrets set or not set.

Running setup again is safe:

- Existing links and your own values stay.
- Existing `.local.md` files are never touched.
- An unchanged draft writes nothing.

## Folder contents

```
rogarchy-setup/
├── SKILL.md    # instructions for the agent
└── README.md   # this document
```

## Credits

Inspired by the setup skills of [mattpocock/skills](https://github.com/mattpocock/skills) (`setup-matt-pocock-skills`) and [cursor/plugins pstack](https://github.com/cursor/plugins/tree/main/pstack) (`setup-pstack`): a user-invoked skill that explores, shows a draft, confirms and then writes, and one config file whose missing lines fall back to defaults. No text or code was copied.

---

Version 0.1.0 · MIT License · [Repo README](../README.md)
