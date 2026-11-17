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

## New: Interactive Method Witness (research-only)

The read-only [Method Witness](https://szlholdings-szl-muhu-frontier.hf.space/witness) and
[verifiable five-field API](https://szlholdings-szl-muhu-frontier.hf.space/api/v1/witness) illustrate why the MUHU v3
model's high raw accuracy is **not** a substitute for explicit evidence.
The witness classifies five invented, typed metadata inputs using
a deterministic and falsifiable policy. It returns which requirements
are missing, a canonical SHA-256 integrity checksum (**not a digital
signature**) and the evidence needed for a human reviewer.

Missing inputs return `UNAVAILABLE` rather than inferred values.
Unknown fields, malformed values and duplicates return HTTP 400.
The system accepts no biomedical narratives, genomic sequences,
collaborator lab records or private uploads. Its rules have 640
independently cross-checked synthetic cases; that is a **software
behavior test**, not external scientific validation.

[Read the trust boundary and negative controls](research/METHOD_WITNESS.md).
The platform remains `/readyz` 503 (scientific and clinical HOLD).

## New: Public PMID/DOI source-identity research preview

The [MUHU Publication Provenance page](https://szlholdings-szl-muhu-frontier.hf.space/sources)
(now subject to GitHub/Hub release admission) connects **19 selected,
publicly indexed PubMed citations** to their observed source metadata.
Selection includes 9 WWOX-context articles, 7 Vidal-Gadea
*author-index candidates*, and 3 C. elegans motion/calcium
methodology references. These are a bounded subset, not a systematic
review or complete collaborator bibliography.

The immutable public snapshot stores exact PMID, DOI if available,
title, publication dates, journal, topic selection, source URL and
provider-observation timestamp. Its SHA-256 is
`d0bcf237127b41873e70d2a20c1e0e5666b1250b30244732af608bedff14eda6`.
No paper abstract, full-text article, genetic sequence, patient record
or partner lab measurement is redistributed.

The [typed source API](https://szlholdings-szl-muhu-frontier.hf.space/api/v1/sources)
answers bounded identifier questions. A DOI mismatch is flagged as an
identifier conflict—not evidence that a biomedical finding is false.
An unlisted PMID is **UNAVAILABLE/not sampled**, not nonexistent.
Read-only runtime makes no upstream NCBI calls and does not accept
user-supplied fetch URLs. Every result states
**bibliographic identity only, never scientific validity or treatment
efficacy**.

[Source methodology, explicit coverage and failure cases](research/public_sources/README.md).
This addition does not alter the existing MUHU v3 **FAILED/HOLD**
model result or admit any examples into Khipu/Flagship54.

## New: Source-bound Sara × Vidal × WWOX research provenance graph

The [MUHU research provenance graph](https://szlholdings-szl-muhu-frontier.hf.space/graph)
(now subject to CI and provider release admission) connects **23
selected public PubMed citation records** into a typed, auditable
bibliographic provenance graph: 9 WWOX-context, 7 Vidal-Gadea
author-name-query candidates, 3 worm movement/calcium-method references,
and **4 independently fetched Sara Behnamian PubMed author-name
candidates**.

The exact Sara source capture is bounded to PMIDs `36046618`,
`40627371`, `42213236`, and `42740140`; the public metadata
snapshot SHA-256 is
`3af1e866cc72b8ed5a72bb865541bee589c10e19bcc58db16894103d1f850406`.
Existing 19-source metadata remains immutable. The initial graph
comprises **53 nodes and 92 directed provenance-only edges**:
publication, DOI, source snapshot, query-scope, and PubMed authority.
No gene-to-therapy, gene-to-disease, efficacy or biological
causality edges are allowed.

[Source scope, typed graph protocol and proof limits](research/public_sources/PROVENANCE_GRAPH_V1.md).
The graph UI is **layered, interactive by server-side topic selection,
and Python-generated SVG**; it is intentionally 2D, not a simulated
3D molecular digital twin. Source titles and links are attributed to
the NCBI PubMed index; a DOI match establishes **bibliographic
identity at a recorded time only**. A missing PMID means not
sampled—not nonexistent. Search is restricted to public paper-title
words, with explicit abstention when no selected title matches.

This feature does not alter the existing MUHU v3 experimental model
**FAILED/HOLD**, publish third-party article texts, ingest Sara or
Vidal lab data, or authorize a Khipu/Flagship54 training job.

## New: Explainable Claim Evidence Firewall

The source-bound [Claim Evidence Firewall](https://szlholdings-szl-muhu-frontier.hf.space/claim-gate)
is a separate, **deterministic research-only** component that prevents
a paper's bibliographic metadata from being presented as proof of
gene–disease causality, variant pathogenicity, gene therapy efficacy,
laboratory reproducibility, author endorsement or patient-treatment
safety.

It uses exactly the **23 prior public PubMed citation records**,
nine finite claim classes and a fully explainable decision policy.
All **207 source × claim-class combinations** are independently
tested as software cases—not actual biomedical experiments.
A correct PMID/DOI match proves only indexed citation identity at
the pinned observation date. A contradictory DOI is a provenance
conflict; an unlisted PMID is an explicit source-scope UNAVAILABLE;
a patient treatment request is DENIED.

The public [machine-readable decision API](https://szlholdings-szl-muhu-frontier.hf.space/api/v1/claim-policy)
documents claim tiers, missing evidence, and the exact source SHA-256.
It accepts only public identifiers and enumerated categories; no
free-text biomedical reports or patient information. All updates are
read-only; `/readyz` remains 503 (scientific and clinical HOLD).

[Read the predeclared scope, falsifiable controls and constraints](research/CLAIM_EVIDENCE_FIREWALL_V1.md).
This is **not a new trained genetics model**. It provides a provenance
control to evaluate future Khipu outputs, without modifying
Flagship54, scheduling compute or claiming that model accuracy improved.

## New: Publication-version and editorial-history evidence gate

The [MUHU Editorial Lifecycle Witness](https://szlholdings-szl-muhu-frontier.hf.space/lifecycle)
(now subject to protected-GitHub and Hugging Face release admission)
captures **version-aware publication index metadata** for the same
23 selected public PubMed citations. A bounded official NCBI EFetch
XML request identified **three preprints linked to updates** and
other recorded publication-history links.

One selected preprint/update pair (**PMIDs 39257798 ↔ 41431865**)
belongs to the same indexed version lineage. Consequently, MUHU
now distinguishes **23 sampled citation records from 22 observed
version groups**. This prevents a naive preprint/publication
double-count within the selected corpus; it does not establish
that the paired papers are scientifically equivalent, nor that
22 independent studies have reproduced any biological finding.

Source status is *indexed at a specific observation time only*.
The absence of an NCBI retraction or correction flag is **NOT
proof that an article has no such history, was peer reviewed,
or contains valid scientific conclusions**. MUHU also recognizes
synthetic retraction, erratum and expression-of-concern controls,
all requiring independent human review.

The exact public normalized metadata snapshot SHA-256 is
`d7d2f74651c1b19ad9b102da08781d6b40bf4109b4a3984a4bc2bd5234ccfda4`.
No raw PubMed XML, abstracts, full texts, partner lab data or
patients are stored or published; the original provider XML
was parsed in memory and discarded. The read-only public
runtime does not call NCBI on user queries.

[Lifecycle methods, official NLM definitions and source proof limits](research/public_sources/EDITORIAL_LIFECYCLE_V1.md).
[Machine-readable source lifecycle](https://szlholdings-szl-muhu-frontier.hf.space/api/v1/lifecycle).
The existing MUHU v3 learned classifier remains **FAILED/HOLD**;
no active Khipu/Flagship54 job, checkpoint or training
admission is implied by this release.

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
