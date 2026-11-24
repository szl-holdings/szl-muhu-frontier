# Leader study: source-bound research-methodology platforms

Status: PROPOSE-only draft (leader-study/p9-muhu-20261124). Adopting anything below requires
separate owner approval. This file is documentation only: it does not merge itself, alter any
model or training pipeline, or change MUHU's scientific and clinical HOLD.

## Why this study was written

MUHU is a source-bound, nonclinical research-methodology platform whose core problem is
**training-data integrity**: invented research records must be classified by a falsifiable
scientific method (BLOCKED / CONFLICT / STALE / REVIEWABLE), partitioned deterministically with
no oracle-tuple leakage across train/validation/test, and published **train only** while
evaluation evidence stays with the owner. MUHU v3's honest negative result (raw accuracy 87.5%
but selective coverage, minimum-class recall and macro-F1 all below frozen thresholds) is
preserved as a discipline anchor: a green pipeline is not scientific validity.

The four leaders below solved adjacent, well-audited versions of the same integrity problems at
industry scale. Each is cited with a primary source.

## Leader 1: production readiness gates (kubernetes.io)

MUHU's `/healthz` (liveness-only 200) versus `/readyz` (always 503 while on HOLD) mirrors the
Kubernetes probe model: a service can be alive but not qualified to serve. Kubernetes
distinguishes liveness, readiness and startup probes precisely because "process is running" and
"process is safe to use" are different claims
(https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/).
Leader takeaway for MUHU-class platforms: readiness to *publish* or *serve conclusions* must be a
separate, fail-closed gate from readiness to *run*, and it must be observable from outside.

## Leader 2: build provenance levels (slsa.dev)

SLSA's provenance model ties an artifact to a verifiable record of how it was built: who, from
what source, on what machine, with which commands, at which build level
(https://slsa.dev/spec/v1.0/levels). MUHU's release-admission runbook applies the same ladder
to a research artifact: a wheel build does not establish a PyPI release, a green workflow does
not establish verified revenue or clinical qualification. Leader takeaway: attach the exact
build/provenance metadata to every release candidate and refuse promotion claims the provenance
level does not support (https://slsa.dev/spec/v1.0/terminology).

## Leader 3: deterministic canonicalization (RFC 8785, JSON Canonicalization Scheme)

MUHU relies on SHA-256 integrity commitments over JSON metadata snapshots, over canonical
source-group partitioning, and over deterministic policy outputs (the Method Witness and Claim
Evidence Firewall). Hashing is only reproducible if bytes are canonical first. RFC 8785 defines
a strict, single canonical form for JSON: sorted keys, no insignificant whitespace, defined
number serialization, defined string escaping (https://www.rfc-editor.org/rfc/rfc8785).
Leader takeaway: every published commitment in a source-bound platform should name the
canonicalization scheme beside the hash, or cross-implementation comparisons will silently
disagree (https://www.rfc-editor.org/rfc/rfc8785#name-generation-of-canonical-json).

## Leader 4: append-only transparency logs (sigstore / Rekor)

MUHU publishes immutable public metadata snapshots with recorded observation timestamps and
distinguishes past evidence from current claims. Rekor solves the same problem for signatures:
an append-only, cryptographically verifiable transparency log that can prove a record existed
at a time without trusting the log operator (https://github.com/sigstore/rekor; protocol docs:
https://docs.sigstore.dev/rekor/protocol). Leader takeaway: bibliographic identity at a
recorded time only (MUHU's own rule) is the same evidence class as a Rekor inclusion proof:
existence at time T, not validity, and "absence of a flag is not absence of history".

## What is deliberately NOT adopted

- No Kubernetes deployment, no signing infrastructure, no third-party service dependency is
  added to MUHU by this document.
- Nothing here softens the MUHU v3 FAILED/HOLD result, admits any example into training,
  establishes clinical or biomedical qualification, or overrides any owner decision.
- These leaders are pattern references for research integrity engineering, not endorsements
  of MUHU by the linked projects.

## Provenance

Branch off main at pinned HEAD 9bf8d62794a856dfdfe248ec4b02e1be49083d04.
Governance receipt: Kimi cloud rail GO_WITH_AMENDMENTS, nonce P9-MUHU-GOV-77b3e91aa42c
(nonce-echo verified). All citations were opened and checked at draft time. Propose-only:
merge requires explicit owner approval.
