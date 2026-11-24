# blog-post

## What it is

A skill for writing one cited Markdown blog post. The order is research first (a research packet with a pro/con stance map and a *Balance* block), then the draft, then scoring against a rubric. The skill stops at one post; it does not publish, commit, or post.

## When to use / not use

Use it when:

- The user asks for a blog post, article, or sourced explainer for publication.
- The user wants current statistics and gaps left by competitors, then an editable draft.

Don't use it for:

- Academic papers (`academic-research-writer`).
- YouTube notes (`ytsum` / `youtube-content`).
- Saving an existing URL to a vault (`web-article-to-vault`).
- Social asset briefs (`content-brief-curation`).
- Coding tasks that happen to contain the word "blog".

## Requirements

Skills outside this repo (install separately):

| Skill | Status | Purpose |
|---|---|---|
| `grounded-citations` | **Required** | Source logging (`sources.py`), rendering `[n]` citations, and `verify`. |
| `humanizer` | **Required** | Prose cleanup before verification. |
| `content-brief-curation` | Route only | Named as the handoff target for social asset briefs. |
| `academic-research-writer` | Route only | Named as the handoff target for academic papers. |
| `web-article-to-vault` | Route only | Named as the handoff target for saving articles. |
| `youtube-content` | Route only | Named (together with `ytsum`, which is in this repo) as the handoff target for YouTube notes. |

Runtime tools: Python (for the `sources.py` of `grounded-citations`), `curl`, and web search access from the agent. The skill itself has no scripts.

## Configuration

| Variable | Meaning | Default |
|---|---|---|
| `OUT` | Output folder for drafts, research packets, and source ledgers | `$HOME/blog-posts` |

An absolute path the user names in the request takes priority over `OUT`. The skill does not write into a notes vault unless the user names that vault.

The values above can also be stored in the settings file `${XDG_CONFIG_HOME:-~/.config}/rogarchy-skills/config.env` (via [`rogarchy-setup`](../rogarchy-setup/README.md)); the env var still wins, then that file, then the default.

## Usage examples

```text
Write a blog post about the impact of HTTP caching on Core Web Vitals, in Indonesian.
```

The agent runs the pre-flight check, plans supporting and counter queries, then writes the research packet and **stops** for approval. Once resumed, the result is `<slug>_<date>.md` with a short answer, the body, a "When it doesn't hold" / "Kapan ini tidak berlaku" section, and the source list, plus `_research-<slug>-<date>.md` and `.sources-<slug>-<date>.json`. The research score (≥70) and draft score (≥80) are reported in chat.

```text
Write a post about Rust for beginner backend devs, write-through.
```

"Write-through" (or the Indonesian "tulis sampai selesai", "write until done") makes the agent not stop between phases.

## Folder contents

```
blog-post/
├── SKILL.md                      # instructions for the agent
├── references/
│   ├── research-quality.md       # source tiers, pre-flight check, stance map and Balance block format, research rubric
│   ├── voice-personal.example.md # personal voice template (copy to voice-personal.local.md)
│   └── voice-personal.local.md   # your personal voice (optional, gitignored)
└── templates/
    └── post.md                   # draft skeleton (short answer, body, When it doesn't hold, Sources)
```

## Credits

Adapted from [AgriciDaniel/claude-blog](https://github.com/AgriciDaniel/claude-blog) (MIT): the research and citation discipline, and `references/research-quality.md` (which also draws on [last30days-skill](https://github.com/mvanhorn/last30days-skill), MIT). The original license text and copyright are in [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

---

Version 0.2.1 · MIT License · [Repo README](../README.md) · 0.2.1: reads `OUT` from config.env too
