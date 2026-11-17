# MUHU: Source-Bound Methodological Evidence and Release-Honesty Controls

*SZL Holdings — technical research note, November 17, 2026*

**Status:** Public technical draft. Not peer reviewed, not submitted to a
journal, not a coauthored laboratory publication, and not a clinical model.

## Abstract

MUHU is a pure-Python research preview for auditing methodological
claims with explicit evidence states and bibliographic provenance.
Its research objects distinguish source identity, publication
versions, machine-readable evidence rules, human scientific review
and release admission. This note describes a reproducible synthetic
method-classification experiment, an observed failure of its learned
baseline, and the resulting deterministic controls. The system makes
no claims about gene therapy effectiveness, genome variant
pathogenicity, patient outcomes or the experimental reproducibility
of external collaborators' work.

## 1. Research question

Can source-controlled methodological gates prevent a common category
error: treating an observed reference or a high model accuracy number
as validated scientific evidence?

The architecture separates five evidence levels: (i) publication
identity at a recorded date, (ii) metadata completeness and
contradictory statements, (iii) primary study findings, (iv)
independent expert replication, and (v) clinical or production
qualification. MUHU only implements parts of (i) and (ii); (iii)–(v)
are deliberately held.

## 2. Public-source provenance

MUHU's bounded source-indexed corpus contains 23 selected PubMed
citation records: 9 WWOX-context, 7 Vidal-Gadea author-query
candidates, 3 C. elegans movement/calcium method records, and 4
Sara Behnamian author-name-query candidates. Selection is not a
systematic review or proof of author identity.

The source metadata are hashed and typed into a 53-node, 92-edge
provenance DAG with four allowed noncausal relations. A later
NCBI EFetch editorial snapshot found three preprints with update
links and one linked preprint/update pair within the selected set,
yielding 22 observed version groups. These are not 22
scientifically independent validated studies.

Original source details and limitations:
[provenance graph](../../research/public_sources/PROVENANCE_GRAPH_V1.md);
[editorial lifecycle](../../research/public_sources/EDITORIAL_LIFECYCLE_V1.md).

## 3. Synthetic model experiment and negative outcome

The separate MUHU v3 exercise generated 672 synthetic, class-balanced
training examples, 60 validation examples, and 96 test examples.
None were sourced from Sara's manuscript, private lab measurements,
patient records or real genomic sequences. Train/validation/test
source-condition groups were disjoint, although the public generator
means the held-out cases were not genuinely blind.

The prespecified CPU-only TF-IDF and logistic-regression baseline
produced:
- Raw held-out accuracy: **87.5%**.
- Balanced majority-class baseline: **25.0%**.
- Selective coverage: **50.0%**.
- Macro F1 including abstention as errors: **0.642**.
- Minimum class recall: **33.3%**.
- Prespecified internal adversarial stress: **7/32** correct.

The model FAILED preregistered acceptance thresholds. No post-hoc
threshold adjustment turns that result into model qualification.

Source:
[MUHU v3 experiment, exact populations and failure report](../../research/muhu_v3/RESULTS_20261117.md).

## 4. Deterministic safety/reproducibility instruments

MUHU added three independent code controls: a five-field methodology
witness, an immutable public citation/DOI verifier, and a claim-type
evidence firewall. The firewall considers 23 sources across nine
claim classes for 207 deterministic rule cases. A bibliographic
match does not support causality, therapy benefit or human
treatment guidance. Unknown sources are labeled UNAVAILABLE,
rather than nonexistent.

Publication-version and correction-link metadata prevent selected
preprint/update pairs from being counted as separate indexed
version groups. They do not establish actual scientific agreement
between the two papers. No tracked correction in a selected
snapshot cannot be interpreted as proof of a clean or current
retraction status.

Code:
[public protected repository](https://github.com/szl-holdings/szl-muhu-frontier).
The proof/UI is a source-bound read-only research preview; `/readyz`
intentionally remains HTTP 503.

## 5. Software distribution and payment boundary

The `szl-muhu-evidence` Python package distributes a narrow
zero-dependency library and offline CLI to illustrate the
methodological control states. A successful wheel build is
not a public PyPI release.

Cloudflare's Monetization Gateway uses a Base64-encoded x402 v2
`PAYMENT-REQUIRED` challenge, a separately signed
`PAYMENT-SIGNATURE` and verified origin `PAYMENT-CONTEXT`.
The offline MUHU parser only assesses the challenge's structure;
it does not sign a transaction or prove settlement. No commercial
revenue is established in this research note.

## 6. Limitations and next studies

This work lacks real rights-cleared source-text annotation,
independent experiment replication, expert-disagreement adjudication,
blinded generalization tests and evidence-calibrated model
comparators. The synthetic rules are designed and checked by
the same software project; passing them does not establish
real-world scientific intelligence. The selected bibliography
may omit relevant studies and version histories.

A defensible next experiment requires an independent panel,
documented source and version permissions, preregistered
claim-level labels, negative controls, unseen evaluation
corpus, denominator-aware coverage metrics and confidence
intervals. Independent laboratory participation and
coauthorship require explicit collaborator agreement.

## 7. Reproducibility and rights

Canonical source: [GitHub](https://github.com/szl-holdings/szl-muhu-frontier).
Public train-only synthetic dataset:
[Hugging Face](https://huggingface.co/datasets/SZLHOLDINGS/muhu-methodology-sft-v2).
Research interface: [MUHU Space](https://huggingface.co/spaces/SZLHOLDINGS/szl-muhu-frontier).

Original software is MIT; original synthetic examples are
CC BY 4.0. External papers remain controlled by their original
authors and publishers. No PDF, full-text article, patient/genomic
record, or unpublished partner lab content is redistributed.

**Conclusion:** MUHU is a reproducible engineering research preview
with meaningful negative findings and explicit evidence boundaries.
It is not yet a validated biomedical, clinical or proprietary
genetics discovery model.
