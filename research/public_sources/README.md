# MUHU Public Bibliographic Provenance — Source-Identity Preview

**Observed from official NCBI PubMed ESummary v2:** 2026-11-17 09:44:19 UTC.
**Quality-gated admission snapshot:** 2026-11-17 09:46:05 UTC.
**Status:** SOURCE IDENTIFIER RETRIEVED; SCIENTIFIC CLAIM **NOT EVALUATED**.

This release takes a meaningful step beyond the five-field fictional
Method Witness: it verifies that **selected public PMID identifiers and
their reported DOI, journal, title and publication dates exist in an
official indexed bibliographic source at a specified observation time**.
This is not a scientific, clinical or collaborator-quality validation.

## Evidence and source identity

The candidate contains 19 PubMed IDs, selected before the batched
ESummary request. Exactly 19/19 were returned with nonblank titles,
valid URL identities, and readable metadata.

| Bounded selected topic | Selected IDs | Query-matched total observed |
| --- | ---: | ---: |
| WWOX-related molecular / clinical-context literature | 9 | 98 |
| Vidal-Gadea AG *author-name query candidates* | 7 | 24 |
| C. elegans locomotion and calcium-methodology literature | 3 | 20 |

Counts describe the search at the original observation—not every
publication in either lab or all research available globally. Queries
may return preprints, reviews or records not directly applicable to an
individual research question. The author query is a metadata index
candidate set, **not a complete bibliography or an adjudication of
an author's identity**. Sara's published mathematical material is
separately linked on the MUHU /sara page; none of Sara's manuscript or
puzzle sources were copied into this PubMed snapshot.

The complete NCBI PubMed ESummary JSON response was preserved
owner-privately and hashed:

- Initial source selection snapshot SHA-256:
  `fd1a66b359a45e10595ea83432df597ceb4766c42868beec225b52893bb27306`.
- Official batched response SHA-256:
  `dd332e5f349a1b198d5b59cdceee3cbe5e0f0f3ea1d151063128791df762f373`.
- Quality-gated public metadata SHA-256:
  `d0bcf237127b41873e70d2a20c1e0e5666b1250b30244732af608bedff14eda6`.
- Raw response and private capture manifest are in
  `C:\Users\steph\SZL-private-evidence\muhu-pubmed-citations-20261117T0945Z\`,
  not committed to GitHub or Hugging Face.

One title contains a valid Unicode non-breaking space (U+00A0), which
was incorrectly rendered by one shell text view as a replacement
character. Exact-byte inspection confirmed that the captured JSON
contains **no U+FFFD replacement character**; all 19 records were
admitted. This does not license silent repair of damaged source bytes.

No abstracts, full-text articles, copyrighted PDFs, patient genomes,
laboratory raw data, therapy-design information, or unpublished
research were copied into the public snapshot.

## HTTP contract (read-only; no live provider requests)

- `GET /sources`: source list, query scope and DOI/PMID input.
- `GET /api/v1/sources`: fixed coverage, public metadata and source links.
- `GET /api/v1/source?pmid=42422765`: one selected PubMed record.
- `GET /api/v1/source?pmid=42422765&doi=10.1016%2Fj.omta.2026.201791`:
  identifier-level DOI match against the captured citation metadata.
- A conflicting DOI is returned as `DOI_IDENTITY_CONFLICT_AT_CAPTURE`;
  it is **not** a conflict between biological study outcomes.
- A PMID missing from the selected set yields
  `UNAVAILABLE_NOT_IN_SAMPLED_INDEX`, **not** an assertion that the
  PubMed record or publication is nonexistent.
- Unknown/duplicate/malformed query keys return HTTP 400; all HTTP
  mutations remain 405. Untrusted Host values fail 403. Source
  access uses only a pinned local JSON file, not caller-supplied URLs.

The registry loader checks the exact source SHA-256 before serving.
A successful identifier match cannot certify authenticity of a
laboratory experiment or validate a medical claim. An NCBI record
may be a preprint and metadata may be corrected after capture;
`observation_utc` must be reported with any citation reuse.

## Safety, rights and qualification

NCBI [scripting policies and disclaimers](https://www.ncbi.nlm.nih.gov/home/about/policies/)
apply. Public bibliographic records and source links remain attributed
to PubMed and their authors/publishers. No paper abstract or full text
is redistributed here. The capture script made only one batched
provider GET, did not submit a patient or internal document, and
did not bypass provider authorization/rate limits.

This is a first **source-identity** wedge supporting later evidence
curation. Its scientific limitation is explicit:
**Indexed citation ≠ validated methods, reproduced result, true gene–disease
mechanism, variant pathogenicity, treatment safety, clinical approval
or collaborator endorsement.**

Before any computational genetics or wet-lab model:
rights-cleared data, canonical source/experiment revision, protocol,
repeated independent measurements, human adjudication, blinded
comparators, subgroup support and no-claim/abstention calibration are
all required. Flagship54 and Khipu training remain governed by their
separate owner-controlled signed-job contracts; no new GPU job or
training admission is implied by this citation snapshot.

**License:** MIT for original SZL source code; public metadata remain
subject to the upstream service and publication rights.
