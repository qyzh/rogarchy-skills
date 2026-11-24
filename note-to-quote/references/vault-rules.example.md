# Vault rules template (note-to-quote)

Copy this file to `vault-rules.local.md` (gitignored) and fill it in with the
rules of your own vault. When `vault-rules.local.md` exists and the user asks
to save a quote, the `note-to-quote` skill reads it and follows it.
`rogarchy-setup` can create the copy for you; it never overwrites an existing
one.

Keep personal paths and vault names in the `.local.md` copy only, never in this
template.

## Default location

- Folder for saved quote files: `<path inside your vault>`.
- File naming (e.g. `Quote - <short title>.md`).

## Index registration

Pick one and delete the other:

- No index: save the file only.
- After saving, add `[[<file name>]]` to `<index note name>` under the heading
  `<heading>`.

## Frontmatter

```yaml
---
type: quote
status: draft
source: "<source note path>"
---
```

Replace with the keys your vault uses.

## Links

- Source notes in another vault: write the path, never a `[[wikilink]]`.
