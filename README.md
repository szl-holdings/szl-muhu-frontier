---
title: MUHU | Research Methodology Frontier
emoji: 🌱
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Python research evidence; synthetic and nonclinical
tags:
  - research
  - reproducibility
  - scientific-method
  - synthetic-data
  - python
  - source-bound
---

# MUHU — SZL Research Methodology Frontier 🌱

**MUHU** (Quechua Chanka: *seed*) is the SZL Holdings **original,
nonclinical, independent research** platform for scientific-method
education and training-data integrity. The name is a metaphor, not a
literal translation of genetics.

**Stage:** SOURCE-IMPLEMENTED / SYNTHETIC TESTED. **Clinical, biomedical,
gene-therapy and flagship-model qualification: NOT ESTABLISHED.**
The preview exposes no patient information, genetic sequences,
collaborator recordings, unpublished laboratory documents or
medical-treatment guidance. No model has been trained on the new v2
curriculum, and no active SZL flagship trainer has been changed.

## Purpose and what is different from MUHU v1

The first MUHU prototype exposed an important exact-input validation
leakage defect: repeated research-gate input patterns appeared in its
train/validation/test splits. The reviewed hold is
[Bridge PR #228](https://github.com/szl-holdings/szl-gpu-bridge/pull/228).

MUHU **v2** is a **new, separate** source-controlled training-data
candidate, not a silent replacement or retroactive repair of v1.

- Falsifiable four-state scientific-method classification of **entirely
  invented research records**: BLOCKED, CONFLICT, STALE and REVIEWABLE.
- Deterministic source-group partitioning: no matching complete oracle
  condition tuple crosses train/validation/test.
- All chat-format SFT examples are **originally written by SZL**, under
  CC BY 4.0; no copyrighted publications or collaborator-created
  puzzle texts are copied.
- Publish **train only**. The validation/test records remain in
  private owner evidence until independently evaluated.
- The generation policy source is public, so regenerating evaluation
  cases is technically possible; this does **not** establish
  secret, independent, prospective, or blinded generalization.
- All verification is pure Python 3.11+ and uses only the standard
  library. Model training is NOT performed by building the dataset.

## Run locally

```sh
python -B -m unittest discover -s tests -v
python -B -m muhu.verify --public-dir dataset
python -B app.py --host 127.0.0.1 --port 7860 --data-dir dataset
```

Visit `http://127.0.0.1:7860/`, `/methods`, `/sara`,
`/vidal`, `/genomics`. API readbacks: `/api/v1/manifest`,
`/api/v1/example?i=0`, `/healthz` (liveness-only 200),
`/readyz` (always 503 / scientific and clinical qualification HOLD).
All HTTP write methods return 405. Unrecognized Host values fail 403.
The frontend is Python-rendered HTML and SVG: no JavaScript, external
fonts, analytics, third-party model loading, or API credentials.

## Regenerate the original source-bound curriculum

Use two separate **new directories**, public output for train-only data
and private output for evaluation samples:

```sh
python -B -m muhu.core --public-dir NEW_PUBLIC_DIR --private-dir NEW_OWNER_PRIVATE_DIR
python -B -m muhu.verify --public-dir NEW_PUBLIC_DIR
```

Existing outputs refuse overwrite. `dataset/train.jsonl` and
`dataset/manifest.json` are the only training-data artifacts in the
public repository. The manifest records private evaluation SHA-256
commitments, group coverage, counts, rights and *admission=false*.

The actual training SFT input is each row's `messages` field.
Every other field is metadata and MUST be excluded from the
model's user prompt. No validation/test row is allowed in training.

## Relation to earlier work

- [Sara Behnamian's published certified puzzle research](https://github.com/sarabehnamian/Puzzle-generation-with-guaranteed-uniqueness) is an **external research reference**, not this training corpus. Its author retains paper and manuscript authority.
- [Vidal-Gadea Lab](https://agvg75.github.io/lab/) is referenced with no use of unpublished biology records. The shared methodological protocol remains independently governed and unfrozen.
- [WWOX public literature](https://pubmed.ncbi.nlm.nih.gov/?term=WWOX) is cited as context only. MUHU v2 does not predict genomic variants, cell pathology, off-target effects, or gene-therapy efficacy.
- Canonical training ownership remains
  [szl-gpu-bridge](https://github.com/szl-holdings/szl-gpu-bridge);
  MUHU v2 does not inject into Flagship54, restart a GPU lane, create
  a paid job or override its completion guard.

## MUHU v3 research result — quality HOLD

A **separate** preregistered MUHU v3 original synthetic methodology
curriculum is in `dataset/v3/` and `research/muhu_v3/`. It contains
**672 class-balanced training examples** plus **60 validation and 96
test examples kept in owner-private evidence**. It does not use Sara
Behnamian's authored puzzle text or Vidal-Gadea lab data. No Khipu
or Flagship54 weights were trained from it.

One CPU-only TF-IDF + logistic research classifier was fitted to the
672 invented training prompts. Its test raw argmax accuracy was 87.5%
against a balanced 25.0% majority baseline, **but strict selective
coverage was just 50.0%, minimum-class recall 33.3%, macro F1
(with abstentions as misses) 0.642, and presealed internal stress
accuracy 7/32**. These FAIL the frozen acceptance thresholds.
No post-test tuning or model promotion was authorized.

See the [public negative result](research/muhu_v3/RESULTS_20261117.md),
[fixed preregistration](research/muhu_v3/ACCEPTANCE.md), and the
read-only [MUHU v3 results page](https://szlholdings-szl-muhu-frontier.hf.space/v3).
A public source generator means that withheld internal test cases
can be reconstructed; outside blinded expert review is still absent.
A functioning preview and green CI do NOT establish scientific validity.

## Next-cycle model admission gate

Before any distinct future Khipu/Flagship research adapter, require:
an admitted GitHub source SHA, immutable HF dataset commit, rights
manifest, **unseen independent test data**, a pinned base and tokenizer,
frozen SFT config and train/validation/test separation, real authorized
GPU/runtime preflight, measured abstention/forgetting and exact-solution
comparators, verified backups, and explicit human/budget/signer approval.

Passing software checks proves only software behavior. A hash is not a
signature; README publication is not running infrastructure; model
training is not evaluation, and evaluation is not clinical qualification.

**License:** MIT (software); CC BY 4.0 (original synthetic training
examples). All content belongs to SZL Holdings except linked external
references, which are not redistributed.
