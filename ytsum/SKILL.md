---
name: ytsum
description: "Use when given a YouTube URL to save as a summary file."
version: 3.0.2
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
| `YTSUM_SCRATCH_DIR` | Temporary transcripts and chunks | `${TMPDIR:-/tmp}/ytsum-scratch` | advanced |

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
   Pick a language chain that fits the video (`id,en,ms` for Indonesian). Done when the file is non-empty, holds no `{"error": ...}` object and is in the video's language. Retries follow `youtube-content` Error Handling, fetched plainly without proxies or cookies. If captions are disabled or retries run out, report and stop. For a video over 30 minutes, split it into 5-minute chunks with real time ranges, redirecting to a scratch file because `transcript_chapters.py` writes its `## start–end` chunks to stdout: `python3 <skill-dir>/scripts/transcript_chapters.py $SCRATCH/<video_id>.txt --minutes 5 > $SCRATCH/<video_id>.chunks.txt`. Always redirect, even when you intend to read the chunks yourself, so a long transcript does not flood the main context. Pitfall: `transcript_chapters.py` collapses each segment into ONE very long line, and `read_file` truncates long lines — reading `.chunks.txt` silently loses the middle of every chunk. Use the chunks file only as a timestamp map; read the raw timestamped `<video_id>.txt` in line ranges (roughly 400–500 lines per call) for full-fidelity coverage.
5. **Summarize.** Read the whole transcript, chunk by chunk. Write the body in the video's language:
   - an opening paragraph with the exact title, channel, runtime, language and speakers;
   - term definitions, each as `What is **X** means?` followed by a tab and the explanation;
   - thematic `##` sections;
   - concise takeaways.

   Stay with what the speakers say, keep their claims apart from verified facts, and keep their stated uncertainty. You may delegate the draft to a subagent that reads the scratch transcript — for long videos, point it at the raw timestamped transcript in line ranges, not the `.chunks.txt` file, whose single-line segments get truncated on read. Review its draft before writing: subagent drafts can garble names, numbers, and term definitions, so spot-check the term lines and every quoted figure against the transcript before committing them to the file. Auto-captions garble proper names — a guest addressed by one name in the transcript may be billed as someone else — so confirm the speaker identities against the uploader's video description (`yt-dlp --no-playlist --skip-download --print '%(description)s' "<URL>"`) before writing the opening paragraph. Done when every part above is present and every chunk is covered.
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
