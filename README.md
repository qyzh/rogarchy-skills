# rogarchy-skills

A personal collection of agent skills in `SKILL.md` format. One repo, one folder per skill.

> The skills in this repo are **tested only on Hermes Agent**. Other agents that read
> `SKILL.md` skill folders should be able to use them, but this is untested.

## Skills

| Skill | Description | Version | Extra folders |
|---|---|---|---|
| [`blog-post`](blog-post/README.md) | Writes one cited blog post: research first, draft second, score third. | 0.2.2 | `references/`, `templates/` |
| [`bmlink`](bmlink/README.md) | Saves a URL as one row in a Markdown bookmark table. No per-link notes. | 1.0.1 | - |
| [`dither-data-viz`](dither-data-viz/README.md) | Makes dithered (Bayer) charts on canvas with real HTML labels. Outputs `index.html` and one PNG per canvas. 5 card designs (A–E), default B. | 0.4.1 | `scripts/`, `templates/`, `design-options/` |
| [`kamus`](kamus/README.md) | Saves one term as one definition note in a kamus (dictionary) folder, with the meaning verified against KBBI/Wiktionary. | 1.0.1 | `references/` (optional, local) |
| [`note-to-quote`](note-to-quote/README.md) | Picks one idea from a note or summary and turns it into a short quote, with context and attribution. | 1.0.1 | `references/` |
| [`omarchy-agent-usage`](omarchy-agent-usage/README.md) | History and reports of local AI agent token usage on Omarchy: per day × per model, quota, cost simulation, metrics. Linux/Omarchy only. | 0.3.1 | `references/`, `scripts/`, `tests/` |
| [`rogarchy-setup`](rogarchy-setup/README.md) | Sets up or checks the skills in this repo: symlinks into agents, the `config.env` settings file, a report of missing requirements. Runs only when asked. | 0.1.0 | - |
| [`ytsum`](ytsum/README.md) | Turns one YouTube URL into one Markdown summary file that stays faithful to the video. | 3.0.2 | `scripts/` |

Runtime requirements:

- `dither-data-viz`: Node.js, Python 3, and Chrome/Chromium (set via `CHROME_BIN` if not on `PATH`) for PNG export.
- `omarchy-agent-usage`: Linux with Omarchy (the `omarchy-agent-usage-*` wrappers) and Python 3 (standard library). Internet is optional (prices from the free Artificial Analysis Data API, needs `ARTIFICIAL_ANALYSIS_API_KEY`; without a key there are no network calls; `--offline` uses the cache/seed).
- `ytsum`: `yt-dlp`, Python 3, and the `youtube-content` skill (to fetch transcripts).
- `blog-post`: Python 3, to run the `sources.py` script of the `grounded-citations` skill.
- `bmlink`, `note-to-quote`, `kamus`, `rogarchy-setup`: no scripts. Some skills name other skills in `related_skills`; those are optional and not included in this repo.
- Output locations can be set through environment variables or the settings file `~/.config/rogarchy-skills/config.env` (see [Setup](#setup); the env var wins, and the default is used when neither is set):
  - `bmlink`: `BMLINK_FILE` (default `$HOME/bookmarks/linksaved.md`), `BMLINK_TZ` (default: system timezone).
  - `ytsum`: `YTSUM_OUTPUT_DIR` (default `$HOME/ytsum`), `YTSUM_SCRATCH_DIR` (default `${TMPDIR:-/tmp}/ytsum-scratch`).
  - `kamus`: `KAMUS_DIR` (default `$HOME/kamus`).
  - `blog-post`: `OUT` (default `$HOME/blog-posts`).
  - `omarchy-agent-usage`: `OMARCHY_USAGE_DATA` (default `${XDG_STATE_HOME:-~/.local/state}/omarchy/agents/usage-history`), `ARTIFICIAL_ANALYSIS_API_KEY`, `OMARCHY_USAGE_PRICING_CACHE`, `OMARCHY_USAGE_PRICING_SEED`, `OMARCHY_TASKS_FILE`, `OMARCHY_PATH`.
- All skills use the author `qyzh, Hermes Agent`.

## Supporting skills

Some skills refer to other skills that are **not in this repo**. Install them separately in your agent if needed.

| Supporting skill | Status | Used by |
|---|---|---|
| `grounded-citations` | Required | `blog-post` (source ledger, rendering and verifying citations) |
| `humanizer` | Required | `blog-post` (prose cleanup) |
| `youtube-content` | Required | `ytsum` (fetching transcripts) |
| `omarchy-plugin-authoring` | Route only | `omarchy-agent-usage` (handoff target for building a usage display plugin) |
| `content-brief-curation` | Route only | `blog-post` (handoff target for social asset briefs) |
| `academic-research-writer` | Route only | `blog-post` (handoff target for academic papers) |
| `web-article-to-vault` | Route only | `blog-post`, `bmlink` (handoff target for saving articles) |

"Route only" means the skill is only named as a handoff target for out-of-scope requests; the skill still works without it.

## Structure

```
<skill-name>/
├── SKILL.md        # required, for the agent
├── README.md       # required, for humans
├── references/     # optional
├── templates/      # optional
└── scripts/        # optional
```

The folder name **must** match the `name:` field in the `SKILL.md` frontmatter.

## Setup

The easiest way: symlink `rogarchy-setup` into your agent (see Install below), then run `/rogarchy-setup` in the agent. It links the other skills into the agent's skill folder, writes settings to `${XDG_CONFIG_HOME:-~/.config}/rogarchy-skills/config.env`, and can create `.local.md` files from their templates. Every change is shown first and written only after you agree. `/rogarchy-setup check` only reports status. Details: [rogarchy-setup/README.md](rogarchy-setup/README.md).

## Install (symlink)

This repo is the source of truth. Don't copy skill contents; create symlinks so that updating is just `git pull`. The commands below skip any entry that already exists (a folder, a file, or a link, even a broken one) and never replace it; remove a stale entry yourself first if you want it relinked.

```bash
git clone <repo-url> <path-to-repo>
```

### Hermes Agent

```bash
mkdir -p ~/.hermes/profiles/<profile>/skills

# all skills at once
for d in <path-to-repo>/*/; do
  [ -f "$d/SKILL.md" ] || continue
  t=~/.hermes/profiles/<profile>/skills/"$(basename "$d")"
  [ -e "$t" ] || [ -L "$t" ] || ln -s "${d%/}" "$t"
done

# one skill
t=~/.hermes/profiles/<profile>/skills/<skill-name>
[ -e "$t" ] || [ -L "$t" ] || ln -s <path-to-repo>/<skill-name> "$t"
```

### Other agents

Replace the target with that agent's skills directory.

```bash
mkdir -p <agent-skills-dir>

# all skills at once
for d in <path-to-repo>/*/; do
  [ -f "$d/SKILL.md" ] || continue
  t=<agent-skills-dir>/"$(basename "$d")"
  [ -e "$t" ] || [ -L "$t" ] || ln -s "${d%/}" "$t"
done

# one skill
t=<agent-skills-dir>/<skill-name>
[ -e "$t" ] || [ -L "$t" ] || ln -s <path-to-repo>/<skill-name> "$t"
```

## Update

```bash
cd <path-to-repo> && git pull
```

All symlinks point to the new version automatically.

## Adding a new skill

1. Create a folder `<skill-name>/` at the repo root.
2. Write `SKILL.md` with a frontmatter `name` that exactly matches the folder name.
3. Add `references/`, `templates/`, or `scripts/` if needed.
4. In `SKILL.md`, write a `## Prerequisites / Config` section in the same format as the other skills (a `Requires:` line, a `Local files:` line, a `Variable | Meaning | Default | Kind` table or `Variables: none.`), so that `rogarchy-setup` can read it. Personal files: `references/<name>.local.md` (gitignored) with the template `references/<name>.example.md`.
5. Write `<skill-name>/README.md` for humans with the same sections as the other skills: What it is, When to use / not use, Requirements, Configuration, Usage examples, Folder contents, and the version, license, and `../README.md` link line. Don't change `SKILL.md` for this.
6. If you adapt someone else's work, add an entry to `THIRD_PARTY_NOTICES.md` (source, files, copyright, license text) and a "Credits" section in the skill's README.
7. Add the skill to the table in the root README (the name links to the skill's README) and to "Supporting skills" if it uses skills outside the repo.
8. Commit, then symlink it into the agent's skills directory.

## License

Own work: MIT © qyzh, see [LICENSE](LICENSE). Parts adapted from third parties keep their original licenses, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). This is common open source attribution, not legal advice.

## Releases

Each skill's version is tagged `<skill-name>/vX.Y.Z` (e.g. `blog-post/v0.2.0`).
