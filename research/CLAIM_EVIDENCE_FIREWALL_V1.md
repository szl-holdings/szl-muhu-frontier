# MUHU Claim Evidence Firewall v1 — Source-bound Claim Admission

**Implementation date:** 2026-11-17. **Source:** SZL Holdings,
`szl-holdings/szl-muhu-frontier`. **Claim qualification:** Research-only.
**Clinical readiness:** HTTP 503 / HOLD.
**Training admission to Khipu or Flagship54:** Not granted.

## Problem being solved

Previously MUHU built a reproducible *bibliographic provenance graph*
covering **23 deliberately selected public PubMed citations**:
9 WWOX-context, 7 Vidal-Gadea author-query candidates, 3
C. elegans movement/calcium-method references, and 4 Sara
Behnamian author-query candidates. That graph establishes
that a PMID/DOI was indexed, selected under one of four recorded
search scopes, and had metadata reported by NCBI at a pinned
observation time.

None of those metadata edges proves any biological, experimental,
mathematical or therapeutic proposition.

The present gate addresses the next critical misuse: **someone
citing an existing paper as proof of a claim that the paper's
bibliographic record cannot support**. It is an explicit deterministic
policy, not an AI model, and therefore cannot independently review the
underlying paper's full text or infer mechanistic conclusions.

## Exact supported claim categories

| Claim type | Can MUHU admit from bibliographic metadata? |
| --- | --- |
| `citation_identity` | **PMID selected**; optional DOI identity may match the snapshot. No content assessed. |
| `paper_peer_review` | **HOLD**: a PubMed entry alone does not establish the article-version-specific editorial process. |
| `author_endorsement` | **HOLD**: coauthor index string does not imply endorsement, rights, or scientific collaboration. |
| `gene_disease_causality` | **HOLD**: requires primary evidence, conflicting findings and independent curation. |
| `variant_pathogenicity` | **HOLD**: gene-level evidence is not a patient-specific variant classification. |
| `therapy_effectiveness` | **HOLD**: preclinical rescue is not demonstrated human efficacy. |
| `laboratory_reproducibility` | **HOLD**: requires independent protocol/data/negative controls, not a paper title. |
| `cross_study_mechanism` | **HOLD**: provenance edges do not establish shared biological mechanisms. |
| `patient_treatment_recommendation` | **DENY**: individual treatment choices are outside this research preview. |

**DOI identity conflicts preempt all classes.** For a selected PMID,
an optional supplied DOI differing from the recorded DOI yields
`CONFLICTING_SOURCE_IDENTIFIER`, not a fabricated validation.
If no DOI is provided, `citation_identity` reports only
`BIBLIOGRAPHIC_PMID_INDEXED_AT_SNAPSHOT`; it does not claim
that a DOI was checked. A missing DOI in the selected source is
`UNAVAILABLE_DOI_NOT_REPORTED`.

A PMID not in the 23 selected citations is
`UNAVAILABLE_SOURCE_NOT_SAMPLED` — *not* a claim that the paper is
absent from PubMed or scientific literature.

## Runnable API and UI

This is a **no-JavaScript, read-only Python implementation**:

- `GET /claim-gate`: human-interactive source/claim selection;
  the default safe example shows a WWOX gene-therapy effectiveness
  claim as **HOLD**, despite a real PMID/DOI metadata match.
- `GET /api/v1/claim-gate?pmid=42422765&claim_type=therapy_effectiveness&doi=10.1016%2Fj.omta.2026.201791`:
  structured refusal with source proof and requirements.
- `GET /api/v1/claim-policy`: complete finite whitelist,
  evidence requirements and nonqualification flags.
- `GET /api/v1/claim-matrix`: exhaustively checks all
  **23 citations × 9 claim categories = 207** internal
  source-to-policy combinations. This is **not 207 real
  scientific tests** and confers no scientific accuracy.
- `POST`, `PUT`, `DELETE`, `PATCH`: **HTTP 405**.
- Missing, duplicate, invalid, unbounded and free-text query
  fields: **HTTP 400**. Only `pmid`, `claim_type`, and
  optional `doi` are accepted.
- An untrusted Host header: **HTTP 403**.
- `/readyz` remains **503**: no scientific/clinical qualification.

No patient/genome/therapy details or collaborator unpublished
information can be uploaded. The public service stores no form
submissions itself, although the hosting provider may retain standard
web request URL logs. **Only public identifiers should be entered.**
No external PubMed calls are made at request time: the snapshot is
pinned before release and every decision includes the historical
observation timestamp and source SHA-256.

The canonical receipt is a deterministic SHA-256 over
the exact decision payload. **It is not a signed attestation** and
does not prove truth. The source graph was already validated against
two exact PubMed snapshots; no evidence can be manufactured by
free-text prompting this gate.

## Falsification and negative controls

- For each of the nine claim categories, rerun all 23 selected
  PMIDs with their recorded DOIs: verify the allowed states,
  zero approved clinical or scientific statements, and
  per-class denominator/coverage.
- Challenge an authentic PMID/DOI with a gene-therapy
  effectiveness claim: **HOLD**, never efficacy proven.
- Challenge a Sara or Vidal author-name candidate with
  collaborator endorsement: **HOLD**, never consent inferred.
- Challenge a known PMID with a forged DOI: explicit identifier
  conflict, not a silent match.
- Challenge an unselected PMID: **UNAVAILABLE**, not nonexistent.
- Challenge a patient-treatment request: clinical **DENY**.
- Challenge incomplete, repeated, malicious, unknown, or
  non-public source parameters: **HTTP 400**.
- Check the legacy graph UI, citation view, MUHU v3
  failed-results report and original v2/v3 dataset replay
  for regressions. **No active training job may be modified.**

## Source and research limitations

The input source is a *small selected bibliography* whose two pinned
PubMed snapshots have SHA-256:
- Prior 19: `d0bcf237127b41873e70d2a20c1e0e5666b1250b30244732af608bedff14eda6`
- Sara four: `3af1e866cc72b8ed5a72bb865541bee589c10e19bcc58db16894103d1f850406`
- Provenance DAG: `8bd6c9fce288a64053db1b46f1fdf3f312e4dd4da0bfc9372b45b051f7f1dff8`

A PubMed author-name match is not independent author-identity
adjudication. A paper title is not a quoted or analyzed result.
No full texts, abstracts, rights-cleared lab datasets, ClinGen
assertions, ClinVar conflicting variant submissions, microscope
recordings or human patient outcomes are ingested into this version.

The next scientific improvement requires an owner-approved
independent, rights-reviewed source-to-claim annotation protocol,
with claim-specific blinded expert tests, versioned primary evidence,
explicit evidence levels and disagreement tracking. Validation
must happen **before** proposing a next-cycle Khipu research adapter.

MUHU v3's CPU-only synthetic classifier still **FAILED**
preregistered minority-class recall, coverage and stress tests.
This deterministic firewall does **not** cure those ML
generalization weaknesses. It is a separate safety/research
proof-of-concept for citation discipline.

Nothing in this scope authorizes GPU spending, signed-job creation,
Khipu/Flagship54 checkpoint modification, tool ingress, publishing
unreleased partner research, or clinical decisions.
