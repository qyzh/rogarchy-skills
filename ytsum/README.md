# ytsum

## What it is

A skill that turns one YouTube URL into one Markdown summary file that stays faithful to the video. Metadata comes from `yt-dlp`, the transcript from the `youtube-content` skill, and the summary is written in the video's language with YAML frontmatter. Long videos are split into 5-minute blocks by a helper script.

## When to use / not use

Use it when:

- You give a YouTube URL and want its summary **saved as a file**.

Don't use it (hand off to `youtube-content`) when:

- You only want a summary in chat.
- You ask for the raw transcript.

The agent also stops if the video was already summarized (the `video_id` or filename already exists), `yt-dlp` fails, or captions are disabled.

## Requirements

| Requirement | Status | Purpose |
|---|---|---|
| `yt-dlp` | **Required** | Video metadata (id, creator, upload date, duration, title). |
| Python 3 | **Required** | Runs `fetch_transcript.py` and `scripts/transcript_chapters.py`. |
| `youtube-content` skill (outside this repo) | **Required** | Provides `scripts/fetch_transcript.py` to fetch the transcript. Also the handoff target for chat-only or raw transcript requests. |

Platforms: Linux and macOS (per the frontmatter).

## Configuration

| Variable | Meaning | Default |
|---|---|---|
| `YTSUM_OUTPUT_DIR` | Folder where summaries are written | `$HOME/ytsum` |
| `YTSUM_SCRATCH_DIR` | Temporary folder for transcripts and chunks | `${TMPDIR:-/tmp}/ytsum-scratch` |

An output folder named in the request takes priority. Temporary files are deleted at the end of the run.

The values above can also be stored in the settings file `${XDG_CONFIG_HOME:-~/.config}/rogarchy-skills/config.env` (via [`rogarchy-setup`](../rogarchy-setup/README.md)); the env var still wins, then that file, then the default.

## Usage examples

```text
/ytsum https://www.youtube.com/watch?v=<video_id>
```

Result: one file `<creator> - <title>_<upload date>.md` in the output folder, with frontmatter (`title`, `creator`, `video_id`, `upload_date`, `summary_date`, `source`, `language`), an opening paragraph, term definitions, thematic `##` sections, and key points. The agent reports the file path.

Checking a long video's transcript by hand (optional):

```bash
python3 ytsum/scripts/transcript_chapters.py transcript.txt --minutes 5 > chunks.txt
```

The script reads a timestamped transcript (`M:SS` or `H:MM:SS` per line) and prints `## start–end` blocks. The `--index` and `--json` options are available. Always redirect its output to a file.

## Folder contents

```
ytsum/
├── SKILL.md                       # instructions for the agent
└── scripts/
    └── transcript_chapters.py     # splits a timestamped transcript into N-minute blocks
```

---

Version 3.0.0 · MIT License · [Repo README](../README.md)
