---
language:
- en
license: cc-by-4.0
task_categories:
- text-generation
tags:
- synthetic
- scientific-method
- reasoning
- reproducibility
- non-clinical
size_categories:
- 1K<n<10K
---

# MUHU v2 — Original Synthetic Methodology Curriculum

**Not a genetics model or clinical dataset.** All training examples are
newly generated, synthetic, and about evidence-reporting discipline.
There are no patient records, biological experiment measurements,
sequence data, collaborator recordings, private papers or licensed
full texts.

The sole public training file is `train.jsonl`; it contains SFT-format
`messages` and separate verification metadata. For SFT, use only
`messages` as the conversation. Never feed model labels or oracle
metadata into the user prompt as additional context.

Validation/test records are intentionally retained outside the public
publication. The publicly auditable rulebook means a determined reader
can reconstruct analogues; therefore a future model must still be
tested on independently selected, newly collected and genuinely blind
examples before any performance or production claim.

`manifest.json` records source policies, file SHA-256, semantic-group
separation, dataset sizes, rights and nonqualification. Do not infer
anything about a live training job, HF Space runtime or quality from
a dataset upload or a successful HTTP response. **Training admitted: NO.**

The four target classifications describe whether synthetic evidence
is reviewable: BLOCKED, CONFLICT, STALE, REVIEWABLE. REVIEWABLE is
**not** verified truth. Stale age threshold: greater than 7 days.
Missing source, denominator zero or missing independent corroboration
fail closed.

Source: `szl-holdings/szl-muhu-frontier` (commit/revision binding must
be checked at actual publication); license original synthetic data
CC BY 4.0. This small curriculum may be useful for methods-testing;
there are **no measured downstream AI improvements**.
