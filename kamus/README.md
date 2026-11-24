# kamus

## What it is

A skill for saving one term as one definition note in your kamus (dictionary) folder. The note format is fixed (frontmatter `type/status/topics`, and the sections "Bedakan dengan kata mirip" (distinguish from similar words), "Contoh" (example), "Catatan" (notes)), and the meaning is verified against a source such as KBBI or Wiktionary, not invented from the shape of the word.

## When to use / not use

Use it when:

- The user asks to "simpan kata X" (save word X), "tambah istilah" (add a term), or "definisi ..." (definition ...), or mentions the kamus.
- The user gives a foreign word or term they want recorded as a kamus entry.

Don't use it for:

- Video summaries (`ytsum`).
- Concepts across sources (use a concept note).
- A kamus in another folder: the path the user names takes priority.

## Requirements

- Runtime tools: no scripts. The agent uses file read/write access and web access to check meanings.
- Skills outside this repo: none required. `ytsum` (in this repo) is only named as a handoff target and listed in `related_skills`. The note format suits an Obsidian vault (wikilinks `[[Istilah]]`), but Obsidian is not required.

## Configuration

| Variable | Meaning | Default |
|---|---|---|
| `KAMUS_DIR` | Folder where kamus notes are saved | `$HOME/kamus` |

The folder is created on the first save. A folder the user names in the request takes priority. If the default folder is not where your kamus lives, set `KAMUS_DIR`.

Rules specific to your vault (for example "don't touch the Index/MOC") can go in `kamus/references/vault-rules.local.md` (template: `vault-rules.example.md`). The agent reads it if it exists; `*.local.md` files are ignored by git, so they are not published.

The values above can also be stored in the settings file `${XDG_CONFIG_HOME:-~/.config}/rogarchy-skills/config.env` (via [`rogarchy-setup`](../rogarchy-setup/README.md)); the env var still wins, then that file, then the default.

## Usage examples

The skill targets Indonesian terms and writes Indonesian notes, so the example prompt and note stay in Indonesian.

```text
simpan kata "hakikat" ke kamus
```

("save the word "hakikat" to the kamus")

The agent checks for duplicates, verifies the meaning, then writes `$KAMUS_DIR/Hakikat.md`:

```markdown
---
type: kamus
status: active
topics: [filsafat]
---

# Hakikat

**Hakikat** adalah ... (definisi satu paragraf)

## Bedakan dengan kata mirip

- ...

## Contoh

> ...

## Catatan

Sumber: <URL KBBI>. Ejaan alternatif: ...
```

If the file already exists, the agent reports its contents and asks before overwriting. After writing, the agent rereads the file and makes sure every wikilink points to a file that exists.

## Folder contents

```
kamus/
├── SKILL.md                         # instructions for the agent
├── README.md                        # this document
└── references/
    ├── vault-rules.example.md       # vault rules template (copy to vault-rules.local.md)
    └── vault-rules.local.md         # optional, local, not in git
```

---

Version 1.0.0 · MIT License · [Repo README](../README.md)
