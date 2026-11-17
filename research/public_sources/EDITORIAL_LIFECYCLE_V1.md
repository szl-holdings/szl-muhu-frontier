# MUHU Editorial Lifecycle Witness v1 — Source-Linked Publication Versions

**Research observation:** November 17, 2026, 13:23:00 UTC.
**Status:** Public PubMed editorial metadata, snapshot only. Scientific/clinical
qualification **HOLD**. Khipu/Flagship54 training admission **HOLD**.

## Why this matters for the research collaborations

Citation identity is not enough. If the same line of work exists as a
preprint and a linked updated publication, counting both as independent
validation can leak labels, exaggerate supporting evidence and conceal
methodological revisions.

MUHU's previous 23-paper graph stored citation and DOI identities.
This new source-bound *editorial lifecycle witness* adds only the
**indexed publication-type tags, publication/indexing statuses and
PubMed CommentsCorrections relationships** reported by NCBI.

The release explicitly **does not** read article findings, quantify
reproducibility or infer any biological conclusion. A current NCBI
record does not establish peer review, scientific validity, therapy
benefit, author consent or patient safety.

## Official references governing interpretation

- [NLM: Errata, Retractions and Other Linked Citations in PubMed](https://mainweb.awsprod.nlm.nih.gov/bsd/policy/errata.html).
- [NLM PubMed DTD: CommentsCorrections RefType](https://dtd.nlm.nih.gov/ncbi/pubmed/doc/out/250101/att-RefType-c.html).
- [PubMed Help: comment/correction and linked citation types](https://www.ncbi.nlm.nih.gov/entrez/query/static/faq.html).
- [NLM PubMed Data Provider guidance](https://www.ncbi.nlm.nih.gov/books/NBK3828/).

**Important terminology:** An `UpdateIn` or `UpdateOf` link is
a direction-specific publication-index relationship. It is not
proof that the two versions report identical methods, measurements
or conclusions. The `Preprint` publication type is an indexed
type, not a peer-review adjudication.

## Verified, bounded observation

Exactly the same 23 previously admitted PMIDs were retrieved in one
read-only NCBI `EFetch` PubMed XML batch. The request used exact IDs,
a hard size ceiling, strict XML parsing and no authorization bypass
or provider mutation. The raw XML response was parsed transiently;
**no source XML, abstracts or article text were persisted or published**.

The public normalized source is:

`research/public_sources/pubmed-editorial-lifecycle-20261117.json`

Its SHA-256 is:

`d7d2f74651c1b19ad9b102da08781d6b40bf4109b4a3984a4bc2bd5234ccfda4`

The non-persisted original provider XML response had SHA-256:

`0e7e90afe48bf344233762c3f5bfbc231606061ec95b11f7e169036382ed98ec`

The owner-private *capture receipt* (which does not contain the raw
XML or abstracts) is located on BETTERWITHAGE:

`C:\Users\steph\SZL-private-evidence\muhu-editorial-lifecycle-20261117T1326Z\capture-receipt.json`

Receipt SHA-256:

`5f1b538f16641327a32c549b9d880b72e3f493e791f46ec62f6f74b2d27472df`

### What the 23 PubMed records actually disclosed

| Observed editorial/index category | Records |
| --- | ---: |
| No tracked editorial link in this snapshot; **NOT VERIFIED CLEAR** | 18 |
| `Preprint` with one or more update/version links | 3 |
| Other records with update/version links | 2 |
| **Total** | **23** |

Across the 23, the official XML contained:
**3 `UpdateIn`, 4 `UpdateOf`, and 1 `CommentIn` links**.
No retraction or expression-of-concern link was indexed in this
captured sample. **That last statement must never be presented as
proof that every article is unretracted or free of notices.**

A particularly important indexed version relationship is the pair
**PMID 39257798 ↔ PMID 41431865**, linked by official update
metadata. They belong to **one selected version lineage** for
source-deduplication purposes, not two independently reproduced
experiments. This reduces the 23 selected records to **22
observed version groups**, **not** 22 independently valid studies.

Two additional outgoing update links point to PubMed identifiers
**41429758** and **40979067** that are **not** among the 23
admitted records. Their publication texts, editorial states and
experimental relationships remain **UNOBSERVED** here. Several
`UpdateOf` relationships have no linked PMID in the response;
the system preserves that absence instead of fabricating identifiers.

The selected Sara and Vidal-Gadea author-name records are still
candidate bibliographies, not identity-verified complete publication
lists or collaborator endorsements.

## Research API contract and UI

The pure-Python source viewer provides, once admitted and deployed:

- `GET /lifecycle` — current 23-source editorial metadata coverage,
  version-link pair, outside-sample targets, and source cautions.
- `GET /lifecycle?pmid=39257798` — source-specific historical
  publication types and related indexed PMIDs.
- `GET /api/v1/lifecycle` — machine-readable category counts, explicit
  version groups, source/retrieval timestamps and checksum.
- `GET /api/v1/lifecycle/source?pmid=39257798` — source-bound editorial
  history and linked selected version group.
- `GET /api/v1/claim-gate?pmid=39257798&claim_type=paper_peer_review` —
  still **HOLD**, now with preprint/index-version cautions and
  version-deduplication requirements.

Missing or invalid PMIDs fail as **UNAVAILABLE** or HTTP 400, not
as proof the source is nonexistent. Untrusted hosts get HTTP 403;
HTTP write operations return 405. No live PubMed request is made
by public-user queries. `/readyz` remains 503.

## Falsification: what tests are supposed to catch

Offline tests use the exact pinned NCBI snapshot plus fabricated
**synthetic** PubMed XML controls. Controls include:

- Original source SHA, 23/23 selected PMIDs and 22 version groups.
- Three observed `Preprint` + `UpdateIn` relationships and
  one two-record selected version pair.
- No unselected linked record materialized as a real paper.
- Synthetic `Retracted Publication`, `RetractionIn`,
  `ExpressionOfConcernIn`, and `ErratumIn` records labeled as
  human-review-required; they never receive positive clearance.
- A source with *no* indexed correction is marked
  `NO_TRACKED_EDITORIAL_LINK_OBSERVED_NOT_VERIFIED_CLEAR`,
  never `NOT_RETRACTED` or `PEER_REVIEWED`.
- Invalid XML, extra/duplicate PMIDs, unknown RefType, doctored
  source hash, missing source, malformed/duplicated URL query keys,
  mutation requests and host spoofing fail closed.
- Source-to-claim decisions remain HOLD for human therapy and
  variant inferences, even if the PMID/DOI match and no
  editorial notice was observed.
- Existing original MUHU v2/v3 datasets and the negative v3 model
  evaluation remain byte-identical.

This is **source hygiene and evaluation-leakage prevention**, not
proof that Khipu learned new genetic knowledge.

## Next genuine research frontier

Before the system supports a scientific source-to-claim inference
model, add expert annotation with source-version review, blinded
reference outcomes, disagreement adjudication, explicit rights and
experiment-type grouping. A preprint and its linked update must
share a leakage group in every downstream evaluation split.

No active Flagship54 dataset, GPU job, checkpoint, training
controller, signed job or clinical tool was changed.
