---
name: ytsum
description: "Use when given a YouTube URL to save as a summary file."
version: 3.1.0
author: qyzh, Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [YouTube, summary, markdown]
    related_skills: [youtube-content]
---

# ytsum

One YouTube URL becomes one faithful markdown summary in the output directory. Scratch files go to the scratch directory.

## Prerequisites / Config

Requires: commands `yt-dlp`, `python3`; skills `youtube-content` (its `fetch_transcript.py` helper).
Local files: none.

| Variable | Meaning | Default | Kind |
|---|---|---|---|
| `YTSUM_OUTPUT_DIR` | Where summary files are written | `$HOME/ytsum` | setting |
| `YTSUM_SCRATCH_DIR` | Temporary transcripts and block indexes | `${TMPDIR:-/tmp}/ytsum-scratch` | advanced |

Resolve each variable once, before the first step that needs it: the env var if set and non-empty; else its `KEY=value` line in `${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env` (written by `rogarchy-setup`; read it as data, never `source` it; the last matching line wins); else the default. A missing file or line means the default. Kind: `setting` = setup asks for it; `advanced` = setup keeps the default unless the user asks; `secret` = env var only, never in `config.env` or chat. In a shell, `rs_get` does the same lookup:

```bash
rs_get() { _rs_v=$(printenv "$1" || :); [ -n "$_rs_v" ] || _rs_v=$(sed -n "s/[[:space:]]*\$//; s/^$1=//p" "${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env" 2>/dev/null | tail -n 1 || :); printf '%s\n' "${_rs_v:-$2}"; }
OUT="$(rs_get YTSUM_OUTPUT_DIR "$HOME/ytsum")"; SCRATCH="$(rs_get YTSUM_SCRATCH_DIR "${TMPDIR:-/tmp}/ytsum-scratch")"
```

Below, `$OUT` means the resolved `YTSUM_OUTPUT_DIR` and `$SCRATCH` the resolved `YTSUM_SCRATCH_DIR`; use the resolved absolute paths in every later command. If the user names another output folder in the request, use that instead. `<skill-dir>` is the folder holding this `SKILL.md`; `<youtube-content-dir>` is the folder of the `youtube-content` skill.

## Steps

1. **Route.** Continue when the user wants the summary saved as a file. Hand a chat-only summary or a raw-transcript request to `youtube-content`. Done when the route is decided.
2. **Metadata.** Run:
   ```bash
   yt-dlp --no-playlist --skip-download --print '%(id)s|%(channel,uploader)s|%(release_date,upload_date)s|%(duration_string)s|%(title)s' "<URL>"
   ```
   The fields are video_id, creator, upload date (`YYYYMMDD`, write it as `YYYY-MM-DD`), runtime and title; the title is everything after the fourth `|`. Done when all five are filled. If yt-dlp errors, report the error and stop.
3. **Duplicate check.** Run `grep -l 'video_id: "<video_id>"' "$OUT"/*.md`, and check whether the target filename from step 6 already exists. If either matches, report the existing file and stop.
4. **Transcript.** Fetch with the `youtube-content` helper:
   ```bash
   mkdir -p "$SCRATCH" && python3 <youtube-content-dir>/scripts/fetch_transcript.py "<URL>" --text-only --timestamps --language <chain> > $SCRATCH/<video_id>.txt
   ```
   - **Language:** pick a chain that fits the video (`id,en,ms` for Indonesian).
   - **Done when** the file is non-empty, holds no `{"error": ...}` object and is in the video's language.
   - **Retries** follow `youtube-content` Error Handling, fetched plainly without proxies or cookies. If captions are disabled or retries run out, report and stop.
   - **Videos over 30 minutes:** build a block index of the transcript:
     ```bash
     python3 <skill-dir>/scripts/transcript_chapters.py "$SCRATCH/<video_id>.txt" --minutes 5 --index > "$SCRATCH/<video_id>.index.txt"
     ```
     Each index line is short and safe to read: `- 5:06–9:58  L54–111  first words…`, a 5-minute block with its time range and the lines it covers in `<video_id>.txt`. The ranges cover the whole file in order. Read the raw transcript block by block with those line ranges, several blocks per read call up to about 500 lines. Do not read the script's default output (one long line per block): file readers truncate long lines and silently lose the middle of each block.
5. **Summarize.** Read the whole transcript, block by block. Write the body in the video's language:
   - an opening paragraph with the exact title, channel, runtime, language and speakers;
   - term definitions, each as `What is **X** means?` followed by a tab and the explanation;
   - thematic `##` sections;
   - concise takeaways.

   Stay with what the speakers say, keep their claims apart from verified facts, and keep their stated uncertainty. You may delegate the draft to a subagent that reads the scratch transcript — for long videos, give it the `.index.txt` file and have it read `<video_id>.txt` by the index's line ranges. Review its draft before writing: subagent drafts can garble names, numbers, and term definitions, so spot-check the term lines and every quoted figure against the transcript before committing them to the file. Auto-captions garble proper names — a guest addressed by one name in the transcript may be billed as someone else — so confirm the speaker identities against the uploader's video description (`yt-dlp --no-playlist --skip-download --print '%(description)s' "<URL>"`) before writing the opening paragraph. Done when every part above is present and every block (every index line range, for a long video) is covered.
6. **Write.** Create `$OUT` if it is missing, then write one file named exactly `<creator> - <title>_<upload date>.md`, e.g. `Creator Name - Example Video Title_2026-03-02.md`. In creator and title, replace each of `/ \ : * ? " < > |` and control characters with `-`, collapse repeated spaces, and trim trailing dots and spaces. Start the file with this frontmatter, every value in double quotes with inner `"` and `\` backslash-escaped:
   ```yaml
   ---
   title: "<exact YouTube title>"
   creator: "<creator>"
   video_id: "<video_id>"
   upload_date: "YYYY-MM-DD"
   summary_date: "<today, local date>"
   source: "https://www.youtube.com/watch?v=<video_id>"
   language: "<summary language code, e.g. id>"
   ---
   ```
   Done when the file exists and its frontmatter parses. Before reporting done, verify the written file in place: the frontmatter parses with all seven required keys double-quoted; every `What is **...** means?` line contains a tab; the thematic `##` sections and takeaways are present; and no stray tokens from another writing system slipped into the target-language prose. Fix typos in place rather than rewriting the whole file.
7. **Clean up.** Delete this run's scratch files (`$SCRATCH/<video_id>*`). Report the file path.
