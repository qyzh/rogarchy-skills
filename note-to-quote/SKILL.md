---
name: note-to-quote
description: Use to pull the 3–5 strongest quotable lines from one note or summary, best first, each lightly tightened and given a credit, its place in the note, a caption and a one-line reason. Output is Indonesian by default. Indonesian triggers - "jadikan quote", "pilih kutipan", "quote dari note ini".
version: 2.0.0
author: qyzh, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [quote, note, editorial, indonesian]
    related_skills: []
---

# Note → Quote

Find the lines in one note that hit: the ones worth putting on a quote card or an Instagram Story. Return 3–5 of them, best first, in the note's own words, lightly tightened. A good pick is specific to the note, makes sense on its own, and sticks; sounding wise is not enough.

## Prerequisites / Config

Requires: none.
Local files: `references/vault-rules.local.md` (template `references/vault-rules.example.md`).

Variables: none.

## When to Use

- `/note-to-quote <path to note>`, or "jadikan quote dari note ini", "pilih kutipan", "quote dari note ini".
- One note or summary in, a short ranked list of quotable lines out.

Do not use for: designing the card image (use an image-design skill in your agent), publishing or posting, or finding a common thread across many notes. Several notes are handled only when asked, with one separate list per note.

Defaults: output in Indonesian unless the user asks otherwise; audience is lay readers who want ideas from something they read or watched. Follow the user's choice when they give one.

## Procedure

1. **Read the note.** The whole note: frontmatter, source, speaker, and the text around each idea. Use the note's own text as the material. Links to concepts or MOCs are theme hints, not extra content.
2. **Collect candidates.** Look for lines that carry a real distinction, a mechanism that explains something, a practical principle, a dilemma, or a concrete change in understanding. Skip slogans that fit any topic and lines that need the video or a missing "this/that" to make sense.
3. **Tighten lightly.** Start from the note's wording. Trim filler, fix flow, and make the line stand alone; keep it recognizable as the note's line. Aim for 12–30 words and at most two sentences, but keep context the meaning needs.
4. **Rank and keep 3–5.** Best first: most specific, clearest on its own, most memorable. Each pick carries a different idea, not a synonym of another pick. A thin note may give fewer; if nothing works, say what the note is missing instead of inventing a line.
5. **Output** in the format below.
6. **Save only when asked** (see Saving).

## Guardrails

- Every pick and every caption comes from the note. No added claims, superlatives, metaphors, numbers, motivation, or promised results; a caption that says "kata <speaker>" must match what the note says they said.
- Tightening keeps the meaning: keep negations, conditions and hedges ("bisa" stays "bisa"), keep irony and the question a host asked, and do not turn one person's experience into a general rule or a correlation into cause and effect.
- A tightened line never goes in quotation marks under a speaker's name. Credit it as "Diolah dari catatan …". If the note records the speaker quoting someone else, credit that original person, not the speaker.
- Medical, legal, financial, scientific or current claims stay attributed ("menurut …") or are skipped.
- Spell names as the note and the vault rules spell them. If the source URL or the speaker is unknown, leave it out of the credit; never guess it.

## Output format

Write it in the output language. Keep these labels.

```markdown
## Quote dari: <note title>

### 1. <the quote line>
- **Kenapa:** <one line: why this one hits>
- **Di note:** <heading › paragraph or idea it comes from>
- **Kredit:** Diolah dari catatan <note/source title> (<speaker or channel, if known>)
- **Caption:** <1–2 sentences of context for posting; name the source>

### 2. <the quote line>
…
```

Pick 1 is the recommended one. End with one line when the note has more material worth a second pass, or when fewer than 3 picks were possible and why.

Worked examples (Indonesian): [references/examples.md](references/examples.md).

## Saving

Only when the user asks. Follow the location they name. If `references/vault-rules.local.md` exists (gitignored), read and follow it: default folder, file naming, frontmatter, and index registration. If the source note lives in another vault or folder, ask where to save first. Save the output above under the title `# Quote — <short title>`. A source note in another vault is referenced by its path, never a `[[wikilink]]`. Never edit the source note, its index, concept notes or MOCs.
