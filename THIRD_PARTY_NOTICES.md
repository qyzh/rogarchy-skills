# Third-Party Notices

This repo's own work is licensed under MIT, copyright qyzh (see [LICENSE](LICENSE)).
Some parts are adapted from other projects. Those parts stay under their original licenses;
the original license texts and copyright lines are copied verbatim below.

This document follows common open-source attribution practice; it is not legal advice.

Note: some of this repo's content is adapted from third-party work and remains under
its own license (LICENSE holds the plain MIT text for this repo's own work).

---

## 1. claude-blog

- Project: claude-blog, <https://github.com/AgriciDaniel/claude-blog>
- Skill: `blog-post`
- Adapted parts (not a full copy; shortened and rewritten for other agents):
  the research and citation discipline in `blog-post/SKILL.md`, and `blog-post/references/research-quality.md`
  (based on the upstream `research-quality.md`).
- Original copyright: `Copyright (c) 2025-2026 AgriciDaniel`
- License: MIT

```text
MIT License

Copyright (c) 2025-2026 AgriciDaniel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 2. last30days-skill

claude-blog itself adapted its research-quality rubric from this project, and
`blog-post/references/research-quality.md` names it as a source.

- Project: last30days-skill, <https://github.com/mvanhorn/last30days-skill>
- Skill: `blog-post`
- Adapted parts: the research-quality rubric idea in `blog-post/references/research-quality.md`
  (adapted, rewritten).
- Original copyright: `Copyright (c) 2026 Matt Van Horn`
- License: MIT

```text
MIT License

Copyright (c) 2026 Matt Van Horn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 3. dither-kit-rs

- Project: dither-kit-rs, <https://github.com/DeepanshuMishraa/dither-kit-rs>
- Skill: `dither-data-viz`
- Adapted parts: the dither engine in `dither-data-viz/scripts/dither.js` and its copy
  `dither-data-viz/design-options/dither.js`. This is a JavaScript port (adapted, not a copy):
  the 2/4/8 Bayer matrices, the 4x4 halftone matrix, hash-based noise, and the component ideas
  (area chart, pie, radar, button, avatar, gradient, background, meter, sparkline) follow
  the upstream `crates/dither-core`. The card code, templates, and export script are original.
- Original copyright: `Copyright (c) 2026 Deepanshu Mishra`
- Note: dither-kit-rs itself is based on [Boring-Software-Inc/dither-kit](https://github.com/Boring-Software-Inc/dither-kit)
  (the React version; its `package.json` states MIT). The code in this repo is adapted from the Rust version.
- License: upstream offers "MIT OR Apache-2.0" (see `Cargo.toml`). This repo uses the MIT option
  (upstream `LICENSE-MIT`); its text is below.

```text
MIT License

Copyright (c) 2026 Deepanshu Mishra

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 4. Artificial Analysis (price data source)

This is a **data source**, not adapted code, and differs from entries 1-3: there is no open-source license text
that could be copied.

- Source: Artificial Analysis, <https://artificialanalysis.ai/>
- Skill: `omarchy-agent-usage`
- Usage: `omarchy-agent-usage/scripts/cost.py` calls the free Artificial Analysis Data API
  (`https://artificialanalysis.ai/api/v2/language/models/free`) with the user's own API key, which is
  read only from the env var `ARTIFICIAL_ANALYSIS_API_KEY`, to get token prices per 1 million tokens
  (input, output, cache). The result is kept in the user's local cache and called rarely (24-hour cache).
  Without a key there are no network calls. This repo includes no copy of their price data.
  See `omarchy-agent-usage/references/pricing-sources.md`.
- Copyright and rights in the data: belong to Artificial Analysis. This repo does not claim to own them.
- Attribution: the API documentation (<https://artificialanalysis.ai/data-api/docs>, <https://artificialanalysis.ai/api-reference>)
  states that attribution to Artificial Analysis is required for API use. In line with Data Platform Terms v1.1
  (<https://artificialanalysiscdn.com/legal/ProDataPlatformTerms.pdf>, §5), this skill's cost reports
  state exactly "Source: Artificial Analysis (artificialanalysis.ai)" with a link to
  <https://artificialanalysis.ai/>; for derived numbers (costs computed from AA prices) it adds
  "Based on data from Artificial Analysis" and the statement "Created by <skill name>, not by Artificial
  Analysis. Artificial Analysis does not endorse
  this report/tool". Cards or charts shared publicly must also show the Artificial
  Analysis logo (the logo is not included in the repo). The skill README carries the credit.
- Terms: API use is subject to the Artificial Analysis Terms of Use and Data Platform Terms v1.1. Those terms can
  change, and interpreting them is not this repo's call; check the latest version before sharing or using
  the price data commercially. This is not legal advice.

---

## 5. Omarchy

- Project: Omarchy, <https://github.com/omacom/omarchy>
- Skill: `omarchy-agent-usage`
- Adapted parts: small pieces in `omarchy-agent-usage/scripts/collect.py` (three
  `*_PI_PATTERN` regexes and a few one-line predicates such as `claude_billed`, `codex_pi_billed`)
  copied from the upstream `omarchy-agent-usage-claude` / `-codex` wrappers; the rest is original.
  `omarchy-agent-usage/references/collector-internals.md` describes those wrappers' interface.
- Original copyright: `Copyright (c) David Heinemeier Hansson`
- License: MIT; its text is below.
- This skill is not affiliated with or endorsed by Omarchy/Basecamp.

```text
Copyright (c) David Heinemeier Hansson

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
