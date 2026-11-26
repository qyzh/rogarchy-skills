# note-to-quote

## What it is

A skill for finding the lines that hit in one note or summary. It returns 3–5 quotable lines, best first, in the note's own words, lightly tightened. Each one comes with a one-line reason, where it sits in the note, a source credit ("Diolah dari catatan …") and a short caption for posting. The output is text; image design and publishing are out of scope.

## When to use / not use

Use it when:

- You want quote card or Instagram Story text from a note or summary.
- You want a few strong lines to choose from instead of rereading the whole note.

Don't use it for:

- Making images or designing frames (use an image design skill in your agent).
- Publishing or posting.
- Finding a common thread across many notes; each note gets its own list, and multiple notes are processed only when asked.

## Requirements

- Runtime tools: none. This skill has no scripts.
- Skills outside this repo: none. `related_skills` is empty.

## Configuration

None. The default language is Indonesian and the default audience is general readers; both can be changed in the request. If you ask for the result to be saved, it follows the location you name. Personal vault rules can go in `references/vault-rules.local.md` (template: `vault-rules.example.md`; [`rogarchy-setup`](../rogarchy-setup/README.md) can create it).

## Usage examples

```text
/note-to-quote <path to note>
```

```text
jadikan quote dari note ini: <path to note>
```

("make quotes from this note: …")

Result: 3–5 quotes, best first. Each has **Kenapa** (why it hits), **Di note** (where it comes from), **Kredit** (source credit) and **Caption** (1–2 sentences for posting). Pick 1 is the recommended one. A thin note gives fewer picks, with a note on what is missing; the skill never invents a line.

Guardrails: every pick comes from the note, tightening keeps the meaning (negations, conditions and hedges stay), and a tightened line is credited "Diolah dari catatan …", never put in quotation marks under a speaker's name.

## Folder contents

```
note-to-quote/
├── SKILL.md                       # instructions for the agent
└── references/
    ├── examples.md                # examples: a full note, a third-party quote, a thin note
    ├── vault-rules.example.md     # vault rules template (copy to vault-rules.local.md)
    └── vault-rules.local.md       # your personal vault rules (optional, gitignored)
```

---

Version 2.0.0 · MIT License · [Repo README](../README.md) · 2.0.0: rebuilt as a hit-finder: 3–5 picks with reason, location, credit and caption; the verification flow, text types and score table are gone
