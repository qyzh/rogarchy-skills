# bmlink

## What it is

A skill for saving one URL as one row in a single Markdown bookmark table. Each row holds the title, link, domain, tags, note, and save date. The skill does not fetch article content and does not create per-link notes.

## When to use / not use

Use it when:

- The user runs `/bmlink` or asks to save a link to their bookmark list.
- There is no URL in the message: the agent asks the user to send the link.

Don't use it for:

- Per-link bookmark notes, or saving a link together with its content or with categorized routing (out of scope; the agent says so).
- Archiving full articles (`web-article-to-vault`).

## Requirements

- Runtime tools: no scripts. The agent uses `date` and write access to files.
- Skills outside this repo: none required. `web-article-to-vault` is only named as a handoff target (route only) and listed in `related_skills`.

## Configuration

| Variable | Meaning | Default |
|---|---|---|
| `BMLINK_FILE` | Path of the bookmark table | `$HOME/bookmarks/linksaved.md` |
| `BMLINK_TZ` | Timezone for the save date | system timezone |

The file and its parent folder are created on the first save. A file the user names in the request takes priority. If the default location is not where your table lives, set `BMLINK_FILE`; otherwise a new table is created at the default location.

The values above can also be stored in the settings file `${XDG_CONFIG_HOME:-~/.config}/rogarchy-skills/config.env` (via [`rogarchy-setup`](../rogarchy-setup/README.md)); the env var still wins, then that file, then the default.

## Usage examples

```text
/bmlink https://example.com/artikel #ai #tools -- read later
```

One row is added to the table:

```markdown
| Title | Link | Domain | Tags | Note | Saved on |
|---|---|---|---|---|---|
| Artikel | https://example.com/artikel | example.com | #ai #tools | read later | 2026-10-29 |
```

Tags and notes are filled only from what you write; they are never guessed. The agent rereads the row to make sure each cell is right.

```text
/bmlink https://www.example.com/artikel/?utm_source=x
```

If that URL is already saved (compared after normalization: lowercase, without `www.`, the fragment, a trailing slash, and tracking parameters), no row is added and the agent says the link is already saved.

## Folder contents

```
bmlink/
└── SKILL.md    # instructions for the agent
```

---

Version 1.0.3 · MIT License · [Repo README](../README.md) · 1.0.3: drops references to the renamed `bookmark-link` and the deleted `discord-link-save`
