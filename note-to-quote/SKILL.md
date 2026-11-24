---
name: note-to-quote
description: Use to turn one note or summary into a short standalone quote (quote card, Instagram Story text, speaker quote). Separates editorial wording, candidate quotes and verified quotes. Output is text with context and attribution; output language is Indonesian by default. Indonesian triggers - "jadikan quote", "pilih kutipan", "quote dari note ini".
version: 1.0.1
author: qyzh, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [quote, note, editorial, indonesian]
    related_skills: []
---

# Note → Quote

Pick one strong idea from one note, then produce one main quote with a clear meaning and source. Each note may have a different topic. A quote's quality comes from how specific the insight is and how exact the meaning stays, not from sounding wise.

## Prerequisites / Config

Requires: none.
Local files: `references/vault-rules.local.md` (template `references/vault-rules.example.md`).

Variables: none.

## Usage and defaults

```text
Read skills/note-to-quote/SKILL.md and use it for my chosen note.
Pick the single strongest quote, explain why you chose it,
and include context and the source.
```

(Users may type this in Indonesian, e.g. "Baca skills/note-to-quote/SKILL.md dan gunakan untuk note pilihan saya.")

- **Output language: Indonesian** (natural Indonesian) unless the user says otherwise. Public labels stay in Indonesian: "Diolah dari catatan …", "Belum diverifikasi", "Terjemahan". The internal type and status values (`editorial`, `calon-kutipan`, `kutipan-terverifikasi`, `perlu-lengkapi`, `draft`, `belum-diverifikasi`, `diperiksa-pada-sumber`) are fixed identifiers; keep them as written. Default audience: lay readers who want ideas from something they read or watched. State your assumption or adjust to the user's choice.
- **Editorial quote** is the default when the material is a summary. The sentence is reworded from the note's content; write the public label "Diolah dari catatan …" (adapted from notes …). The speaker's name is credit for the inspiration, not the signature of whoever said the reworded sentence.
- If the user asks for an **original quotation**, use the verification flow below. If verification is not available yet, show the candidate quote with a clear status; do not quietly swap in an editorial wording.
- One note yields one main quote. Two or three different candidates may be compared internally, but not all of them need to be published.
- 12–30 words and at most two sentences usually suffice for an editorial wording. This is a writing guideline, not a rule: add context or drop the pick if shortening changes the meaning.
- A quote is text for one frame/card. Image design and publishing are outside this skill's output; for Story visuals, use an image-design skill available in your agent.
- This package is kept locally and can be used by asking the agent to read this file. Installing it into the agent's skill catalog is a separate step.

## 1. Read the note and map the context

Read the full content, frontmatter, source, speaker, and the parts before and after the candidate idea. Note the important distinctions, reasons, experiences or examples that explain the idea.

A short note can be enough for a definition quote if the concept is clear; it need not be enough for a carousel. But empty headings, a paper title, or a definition without results are not a basis for inventing research conclusions. If no idea is complete enough, output `perlu-lengkapi` and name the missing material.

Use `note/` as the main material. Links to concepts or MOCs are theme hints, not evidence of extra content. Process several notes only when asked; keep one separate output per note and do not force a common thread across sources.

## 2. Decide the text type and attribution

| Type | Basis | How to present |
|---|---|---|
| `editorial` | Idea supported by the note, sentence reworded | Text without quotation marks or speaker signature; label "Diolah dari catatan …" on the card/frame |
| `calon-kutipan` (candidate quote) | Sentence recorded in the note as spoken, original source not yet checked | Show for internal review, label "Belum diverifikasi"; not yet a ready-to-use quote in the speaker's name |
| `kutipan-terverifikasi` (verified quote) | Words, speaker and context checked against the original source | Quotation marks, speaker name, original source, and any location pointer available |

A third party's quote repeated by the speaker still belongs to the original speaker. If the note says the creator quoted James Clear, do not attribute that sentence to the creator. Record the source chain and verify the original source before making it a verified quote.

For an original quotation, use source material that is actually available: a recording with its location, a reliable transcript, or the original text with page/paragraph. An automatic transcript is a hint; check the relevant part of the recording when the wording or the speaker's identity is doubtful. Record what was checked; never invent timestamps. If access or evidence is insufficient, keep the candidate status and say what is missing.

An original quotation keeps the speaker's language and words; line breaks are fine. Mark cuts with an ellipsis and make sure the context stays intact. A polished sentence, or one stitched from separate parts, becomes editorial. For a translated quote, show the label "Terjemahan", keep the original text and its source in an internal note, and never call the translated wording a verbatim statement.

## 3. Find and choose the highlight

Look for 2–4 candidates if the content supports it; one candidate is enough for a narrow note. Candidates come from a useful distinction, a mechanism that explains something, a dilemma, a practical principle, or a concrete change in understanding.

Before scoring, a candidate must pass two conditions:

1. **Specific basis:** point to the heading/paragraph and the core idea that supports the sentence.
2. **Meaning stays intact:** shortening keeps who, context, uncertainty, and the limits of the claim that are needed. If it cannot fit without misleading, choose another idea or mark it a poor fit for the quote format.

Compare candidates with an editorial score of 0–2 per criterion: 0 weak, 1 partial, 2 strong.

| Criterion | Question |
|---|---|
| Specificity | Is there a real distinction or idea, not a slogan that fits any topic? |
| Relevance | Why does the target audience need to understand this? |
| Independence | Does the reader understand it without the video, other slides, or a "this/that" whose referent is missing? |
| Clarity | Is the sentence easy to read and free of unexplained jargon? |
| Memorability | Is the wording concise and memorable without overstating the meaning? |

Pick the highest total out of 10; on a tie, prefer the better source support and the least need for context. The score is not a virality prediction. Show a short comparison and the reason for choosing one candidate. Backups must carry a different idea, not many synonym versions of one sentence.

## 4. Write the card text and companion text

Use the [output template](references/output-template.md). For editorial, condense one insight, keep the distinguishing detail, then add the right public source label. Avoid turning "can" into "will", a personal experience into a general law, or a relationship into cause and effect.

If the meaning needs context or attribution, put it in the main text or in a context line on the same frame. The caption may add explanation but must not fix a quote that already misleads when standing alone. Opinions and experiences stay attributed. Medical, legal, financial, scientific or current statements that depend on factual accuracy must be checked before being claimed as fact; if not, use an accurate attributed form or pick another insight.

For a source in another language, the editorial wording may be in Indonesian with an adaptation credit. If the user chooses an original quotation, follow the language and translation rules in the text-type section.

Write a short caption that explains the context and the original source. If the original source was not checked, say the text is an adaptation based on the note. For Stories without a caption, provide companion text that can go on the source/link frame. If the URL/DOI or the speaker is unknown, state what is missing; never fill it in from a guess.

## 5. Final check and saving

Check by imagining only the card is shared again:

- The reader still understands the point, the attribution, and the important limits.
- Every idea maps to a note or an original source that was actually read.
- The public label distinguishes the reworded sentence from an original quotation.
- The sentence stays specific to the note's idea, with no added claims, motivation, or promised results.
- The quote does not lose negation, conditions, irony, or the host's question context.
- If a person is named, the spelling and who spoke match the source and the vault rules.

Send one main quote, the reason for the choice, brief context, public credit, caption/companion text, and an internal source map. If there is only a candidate quote or the note is not ready, state that result without claiming it is ready to publish.

If asked to save, follow the user's location and their vault/folder conventions if any. If `references/vault-rules.local.md` exists (gitignored), read and follow it: default location, index registration, and the vault's frontmatter format. If the source note lives in another vault or folder, ask for the save destination first — don't assume the note's vault is the vault this skill lives in. Keep the source note, brand, index, concept, MOC and carousel skill untouched. Create a new version if the user has edited the destination draft. Use a brand only if it has been specified; never fill in brand identity from assumptions.

Default format for the quote file: title `# Quote — <short title>`; sections A–D follow the [output template](references/output-template.md); add section **E. Aset produksi** (production assets) when there is an image. Frontmatter and index registration follow the user's vault conventions (or `references/vault-rules.local.md`). A source note that lives in another vault must not be referenced with a `[[note]]` wikilink — write its path.

Read the [worked examples](references/examples.md) (Indonesian example outputs) when you need an example of an editorial quote, handling a candidate quote, a chained quote, or rejecting incomplete material.
