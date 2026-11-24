# note-to-quote

## What it is

A skill for picking one idea from a single note or summary and turning it into one short quote that can stand on its own, with context and attribution. The skill distinguishes three kinds of text: an editorial rewording, a candidate quote, and a quote checked against the original source. The output is text; image design and publishing are out of scope.

## When to use / not use

Use it when:

- You want a quote card, Instagram Stories text, or a choice of speaker quotes from a note or summary.
- You need to know whether a sentence is an editorial rewording, a candidate quote, or a verified quote.

Don't use it for:

- Making images or designing frames (use an image design skill in your agent).
- Publishing or posting.
- Finding a common thread across many notes; one note produces one separate output, and multiple notes are processed only when asked.

## Requirements

- Runtime tools: none. This skill has no scripts.
- Skills outside this repo: none. `related_skills` is empty. For Story visuals, SKILL.md only suggests your agent's own image design skill (not required).
- For an original quote, the agent needs source material that is actually available (a recording with its location, a reliable transcript, or the original text with page/paragraph). Without it, the result stays a candidate quote.

## Configuration

None. The default language is Indonesian and the default audience is general readers; both can be changed in the request. If you ask for the result to be saved, it follows the location you name. Personal vault rules can go in `references/vault-rules.local.md` (template: `vault-rules.example.md`; [`rogarchy-setup`](../rogarchy-setup/README.md) can create it).

## Usage examples

The skill targets Indonesian content, so the example prompts below stay in Indonesian (an English gloss follows each one).

```text
Baca note-to-quote/SKILL.md dan gunakan untuk note ini.
Pilih satu quote terkuat, jelaskan alasan pemilihannya,
dan sertakan konteks serta sumbernya.
```

("Read note-to-quote/SKILL.md and use it for this note. Pick the single strongest quote, explain why you chose it, and include its context and source.")

Result: one main quote (editorial by default, labeled "Diolah dari catatan …", "Adapted from notes …"), a short comparison of candidates scored 0–2 per criterion, the reason for the choice, context, public credit, a caption or companion text, and an internal source map. If the note is not complete enough, the result is `perlu-lengkapi` ("needs completing") with the missing material listed.

```text
Saya mau kutipan asli pembicaranya, bukan rumusan ulang.
```

("I want the speaker's original quote, not a rewording.")

The agent uses the verification flow against the original source. If it can't be verified yet, the sentence is shown as a candidate quote labeled "Belum diverifikasi" ("Not yet verified"), not silently replaced with an editorial rewording.

## Folder contents

```
note-to-quote/
├── SKILL.md                       # instructions for the agent
└── references/
    ├── output-template.md         # output template (sections A–D: selection, card text, caption, source map)
    ├── vault-rules.example.md     # vault rules template (copy to vault-rules.local.md)
    ├── vault-rules.local.md       # your personal vault rules (optional, gitignored)
    └── examples.md                # examples: editorial quote, candidate quote, chained quote, rejecting incomplete material
```

---

Version 1.0.0 · MIT License · [Repo README](../README.md)
