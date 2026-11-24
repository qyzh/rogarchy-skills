# Vault rules template (kamus)

Copy this file to `vault-rules.local.md` (gitignored) and fill it in with the
rules of your own vault. When `vault-rules.local.md` exists, the `kamus` skill
reads it and its rules win over the generic text in `SKILL.md`. `rogarchy-setup`
can create the copy for you; it never overwrites an existing one.

Keep personal paths and vault names in the `.local.md` copy only, never in this
template.

## Location

- Kamus folder: set `KAMUS_DIR` (env var or `rogarchy-setup`) instead of
  writing the path here.
- Folder naming exceptions, if any (e.g. "terms in English go to the same
  folder").

## Index and maps

Pick one and delete the other:

- This vault has no Index, MOC, validator or graph step. Never add entries to
  them.
- After writing a note, add `[[<Istilah>]]` to `<index note name>` under the
  heading `<heading>`.

## Frontmatter

- Extra keys this vault requires beyond `type/status/topics`, if any.
- Allowed `topics` values, if the vault keeps a fixed list.

## Links

- Wikilink style (e.g. `[[Istilah]]` or `[[Istilah|alias]]`).
- Notes in other vaults: write the path, never a wikilink.
