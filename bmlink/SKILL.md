---
name: bmlink
description: "Save a URL as a row in the bookmark links table."
version: 1.0.1
author: qyzh, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [bookmark, link, table, save]
    related_skills: [bookmark-link, discord-link-save, web-article-to-vault]
---

# bmlink

Save links to the user's single Markdown bookmark table. Keep each save compact and record when it was saved. Do not fetch full article text or create separate per-link notes.

## Prerequisites / Config

Requires: none.
Local files: none.

| Variable | Meaning | Default | Kind |
|---|---|---|---|
| `BMLINK_FILE` | Path of the single Markdown bookmark table | `$HOME/bookmarks/linksaved.md` | setting |
| `BMLINK_TZ` | Timezone used for the save date | system timezone | advanced |

Resolve each variable once, before the first step that needs it: the env var if set and non-empty; else its `KEY=value` line in `${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env` (written by `rogarchy-setup`; read it as data, never `source` it; the last matching line wins); else the default. A missing file or line means the default. Kind: `setting` = setup asks for it; `advanced` = setup keeps the default unless the user asks; `secret` = env var only, never in `config.env` or chat. In a shell, `rs_get` does the same lookup:

```bash
rs_get() { _rs_v=$(printenv "$1" || :); [ -n "$_rs_v" ] || _rs_v=$(sed -n "s/[[:space:]]*\$//; s/^$1=//p" "${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env" 2>/dev/null | tail -n 1 || :); printf '%s\n' "${_rs_v:-$2}"; }
rs_get BMLINK_FILE "$HOME/bookmarks/linksaved.md"
```

If the user names another file in the request, use that. Create the file and its parent directory on first save.

## When to Use

- User invokes `/bmlink` or asks to bookmark/save a link into their bookmark list.
- If no URL is included, ask them to send the link.
- Optional extras after the URL: `#tags` and a note after `--`, e.g. `/bmlink <url> #ai #tools -- read later`.

Do not use for: per-link bookmark notes (use `bookmark-link`), saving a link with its content or categorized routing (use `discord-link-save`), or full article archiving (use `web-article-to-vault`). `bmlink` only appends a row to the single table.

## Procedure

1. Use the destination: the resolved `BMLINK_FILE` (see Prerequisites / Config). Do not substitute another file or location unless the user says so.
2. Capture the URL exactly as provided. Use its hostname as the domain; use a supplied title if available, otherwise a concise readable label from the URL. Do not open suspicious links or shorteners just to identify them. Take tags (`#word`, space-separated) and the note (text after `--`) only from what the user supplied; leave those cells empty otherwise. Never infer them.
3. Get the save date with `date +%F` (or `TZ="<resolved BMLINK_TZ>" date +%F` when `BMLINK_TZ` resolves to a value); do not guess it from context. Check for duplicates by comparing normalized URLs against the Link column: lowercase the host, drop `www.`, the fragment, a trailing slash, and tracking params (`utm_*`, `fbclid`, `gclid`). If a match exists, do not add a row; tell the user it is already saved. Store the original URL as provided, not the normalized form.
4. Create the parent directory and file if missing. Use this table format:

```markdown
# Saved Links

| Title | Link | Domain | Tags | Note | Saved on |
|---|---|---|---|---|---|
| Example | https://example.com/page | example.com | #ai #tools | read later | 2026-10-29 |
```

If the existing header is the old 4-column one (`Title | Link | Domain | Saved on`), upgrade it to this format and rewrite each existing row with empty `Tags` and `Note` cells before the `Saved on` value.

5. Append one row, preserving existing content and table formatting. Escape `|` in cell values (including the note) as `\\|`; keep each row on one line. Use an append-only write (e.g. a terminal Python append or a patch matching a unique anchor) — never rewrite the whole file from memory, and never match a non-unique last row as the patch anchor.
6. Read the file back and verify the new row cell-by-cell before reporting: Title, Link exactly as provided, Domain equal to the hostname verbatim (no abbreviation or truncation), Tags/Note empty unless supplied, and Saved on equal to the date command output. If any cell is garbled or truncated, fix that row in place first — a truncated Domain breaks duplicate normalization on the next save.

## Pitfalls

- Do not use a router/proxy tool, web extraction, or article archiving for a basic bookmark.
- Do not fabricate a title or description; a domain/path-derived label is acceptable.
- Do not overwrite the existing file when appending. Read it first and preserve every existing row.
- Never abbreviate the hostname in the Domain cell — copy it verbatim and verify the read-back row character-for-character before reporting success.
- Set `BMLINK_FILE` (or tell the agent the file) if the default location is not where the bookmark table lives; otherwise a new table is created at the default path.
