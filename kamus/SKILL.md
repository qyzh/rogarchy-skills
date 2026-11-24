---
name: kamus
description: "Use when saving a term as one definition note in the user's kamus folder. Indonesian triggers - simpan kata, tambah istilah, definisi."
version: 1.0.1
author: qyzh, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kamus, obsidian, definisi]
    related_skills: [ytsum]
---

# Kamus

## Overview

One term = one definition note in the user's kamus (dictionary) folder (`KAMUS_DIR`). This skill keeps the format consistent and the meaning verified. It does not run a validator, graph, Index, or MOC unless the user asks. Output language: Indonesian (the note template, section titles and definitions are written in Indonesian).

## Prerequisites / Config

Requires: none.
Local files: `references/vault-rules.local.md` (template `references/vault-rules.example.md`).

| Variable | Meaning | Default | Kind |
|---|---|---|---|
| `KAMUS_DIR` | Folder where kamus notes are saved | `$HOME/kamus` | setting |

Resolve each variable once, before the first step that needs it: the env var if set and non-empty; else its `KEY=value` line in `${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env` (written by `rogarchy-setup`; read it as data, never `source` it; the last matching line wins); else the default. A missing file or line means the default. Kind: `setting` = setup asks for it; `advanced` = setup keeps the default unless the user asks; `secret` = env var only, never in `config.env` or chat. In a shell, `rs_get` does the same lookup:

```bash
rs_get() { _rs_v=$(printenv "$1" || :); [ -n "$_rs_v" ] || _rs_v=$(sed -n "s/[[:space:]]*\$//; s/^$1=//p" "${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env" 2>/dev/null | tail -n 1 || :); printf '%s\n' "${_rs_v:-$2}"; }
rs_get KAMUS_DIR "$HOME/kamus"
```

If the user names another folder in the request, use that. Create the folder on the first save if it does not exist.

If `references/vault-rules.local.md` exists in this skill's folder, read and follow it: it holds the user's vault-specific rules (a local file, not in the repo) that override the generic text here.

## When to Use

- The user asks "simpan kata X" (save the word X), "tambah istilah" (add a term), "definisi ..." (definition ...), or mentions the kamus.
- The user gives a foreign word/term to record as a kamus entry.

When NOT to use: a video summary → `ytsum`; a concept that spans sources → a concept note; a kamus in another folder → the user's explicit path wins.

## Workflow

1. **Resolve path.** Target: `<resolved KAMUS_DIR>/<Istilah>.md` (see Prerequisites / Config). File name = the term, first letter capitalized, spaces allowed. Do not create new subfolders.
2. **Check for duplicates.** List the kamus folder. If the file already exists, report its content and ask whether to update it — never overwrite silently.
3. **Verify the meaning.** Look the meaning up in KBBI (`kbbi.kemdikdasmen.go.id` or `kbbi.web.id`) for Indonesian words; for foreign words use Wiktionary or an official dictionary. Never invent a meaning from the word's shape. If no source is found, ask the user or state clearly in `## Catatan` that the definition is unverified.
4. **Write the file** using the template below, filling every section.
5. **Verify the result.** Read the file back: the frontmatter keys must be `type/status/topics`, all three `##` sections must exist, and every `[[Istilah]]` wikilink must point to a file that actually exists in the kamus folder.
6. **Report** the file's absolute path. Do not touch the graph or Index unless the user asks.

## Required template

The note itself is written in Indonesian; keep these section titles exactly.

```markdown
---
type: kamus
status: active
topics: [filsafat, waktu]
---

# <Istilah>

**<Istilah>** adalah ... (one-paragraph definition in Indonesian; name the source language if it is not Indonesian)

## Bedakan dengan kata mirip

- ...

## Contoh

> ...

## Catatan

Sumber: <URL KBBI/Wiktionary/official dictionary>. Ejaan alternatif: ...
```

Template rules: `status` = `active` or `verified`; `topics` has at least one lowercase kebab-case value; the section `## Bedakan dengan kata mirip` ("tell apart from similar words") is the core value of this kamus — fill it with words that are easily confused, and don't force it if there are none.

## Common mistakes

- Inventing frontmatter keys such as `istilah:`, `bahasa:`, `jenis:`, `kamus: true`, or `tags:` — use only `type/status/topics`.
- Renaming sections to `## Arti` or `## Etimologi` — use the three specified titles.
- Writing a definition without checking a source, then claiming it is verified.
- Adding the entry to an Index/MOC or running a validator/graph unless the user or a local rule asks.
