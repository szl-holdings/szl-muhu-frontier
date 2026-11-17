# MUHU release admission — GitHub → HF → Cloudflare → PyPI

**Source baseline observed 2026-11-17 19:35–19:38 UTC.**
This is a reusable research-release pattern, first implemented for
`szl-holdings/szl-muhu-frontier`. It is **not a claim that every SZL
repository has been aligned or deployed**.

## Authority, scope, and audience

GitHub protected `main` is the canonical software source. Hugging Face
hosts a CPU research preview and public synthetic data. Cloudflare's
A11oy domain is a product and payment-edge surface, not a proven payment
settlement. PyPI is an independent package registry; a built wheel is not
a released package.

Public investor/technical surfaces:
- [Evidence / investor proof](https://szlholdings-szl-muhu-frontier.hf.space/proof)
- [Developer quickstart](https://szlholdings-szl-muhu-frontier.hf.space/developers)
- [Exact historical JSON](https://szlholdings-szl-muhu-frontier.hf.space/api/v1/release-proof)
- [Canonical GitHub repo](https://github.com/szl-holdings/szl-muhu-frontier)
- [Hugging Face Space](https://huggingface.co/spaces/SZLHOLDINGS/szl-muhu-frontier)
- [Original train-only dataset](https://huggingface.co/datasets/SZLHOLDINGS/muhu-methodology-sft-v2)
- [Published negative research result](../../research/muhu_v3/RESULTS_20261117.md)

All public proof pages are **historical snapshots**. Their reported
GitHub/HF SHAs and HTTP status identify the *earlier observation*, not
necessarily current `main`, live deployment, or post-release parity.
An updated deployment requires an **independent readback receipt**.

## Evidence and release states

| Layer | Observed status | Must establish before marking ready |
| --- | --- | --- |
| GitHub | Protected source at previously observed SHA | Green reviewed PR + merged protected SHA + changed-files/security checks |
| Frontend / Python backend | HF Docker research preview responsive | Code, metadata, UI route, JSON API, bad-input and readiness readbacks |
| HF | CPU basic RUNNING at snapshot | Exact uploaded source bytes from merge SHA, pinned Space revision and HTTP readbacks |
| Cloudflare website | a-11-oy.com and a11oy.net HTTP 200 | Route/DNS authority, actual protected rule and signed PAYMENT-CONTEXT origin validation |
| Cloudflare sales | x402 gateway settlement not verified | 402 v2 challenge, valid authorized purchase, facilitator settlement ID and independent accounting |
| PyPI | `szl-muhu-evidence` 0.1.0 unpublished as observed | Proven artifact, trusted publisher, protected tag, registry JSON, wheel install and hash readback |
| Scientific research | MUHU v3 classifier FAILED/HOLD | Independent, human-adjudicated source-bound blind test and approved training generation |
| Clinical | NOT QUALIFIED | Qualified independent clinical/regulatory review, if ever intended |

The **read-only** `/healthz` endpoint returns liveness status, but
`/readyz` deliberately remains HTTP 503 until scientific and clinical
qualification are separately established. Do not turn that failure into
an unqualified readiness success.

No clinical data, patient records or unpublished collaborator materials
are admitted to the public release. Sara and Vidal-Gadea are public
research references, not asserted endorsers or coauthors.

## Package build and independent verification

The source-root package is `szl-muhu-evidence==0.1.0`, import
namespace `muhu`. It is **library and CLI only**, not the runnable
full research-data-backed web application.

```sh
python -B -m unittest discover -s tests -q
python -B -m unittest discover -s research/tests -q
python -B -m muhu.verify --public-dir dataset
python -B -m research.muhu_v3.verify --public-dir dataset/v3
python -m build --sdist --wheel --no-isolation
python -m twine check dist/*
python -B release/check_distributions.py
```

The package manifest excludes public training files, private evaluation
samples, article PDFs, research snapshots, model weights, runtime tokens,
Cloudflare configuration and secrets. `MANIFEST.in` and the content
auditor refuse non-package artifacts in both wheel and sdist.

### PyPI Trusted Publishing — explicit owner action

The **source workflow** `.github/workflows/pypi-release.yml` uses
GitHub OIDC via PyPA's official publish action, with no persistent PyPI
token in source or Actions secrets. It builds and tests in one job,
and publishes in a separate `pypi` environment-scoped job.

The publisher must be registered in PyPI before a release:

- Project name: **`szl-muhu-evidence`**
- GitHub owner: **`szl-holdings`**
- GitHub repository: **`szl-muhu-frontier`**
- Workflow file: **`pypi-release.yml`**
- GitHub environment: **`pypi`**

Configure the GitHub `pypi` environment with a human review
requirement and immutable source/tag protections; register the exact
project's Trusted Publisher at
[PyPI Publishing](https://pypi.org/manage/account/publishing/).
For a new project, a pending publisher can claim the name only at
successful OIDC-backed first release. Checking that the public registry
currently returns 404 **does not reserve the name**.

After all repository checks and the environment are green, the owner
can push tag **`muhu-v0.1.0`** at the reviewed, protected main commit.
This triggers a source-bound release. Do not create/push the tag if the
trusted publisher or environment review gate is absent. Do not
treat a GitHub workflow starting, a build artifact existing, or
HTTP 404 as proof of PyPI publication. Confirm the registry's
`https://pypi.org/pypi/szl-muhu-evidence/0.1.0/json` and install the
actual published wheel by digest to finish the publication receipt.

Official guide:
[PyPI Trusted Publisher / GitHub Actions](https://docs.pypi.org/trusted-publishers/using-a-publisher/).

## Cloudflare x402 v2 and origin-payment admission

Cloudflare Monetization Gateway uses an HTTP `402` and a
**Base64-encoded JSON `PAYMENT-REQUIRED` header** for v2. A valid
v2 client returns **Base64-encoded signed `PAYMENT-SIGNATURE`**.
The Cloudflare gateway must authenticate/verify and settle payment
through its facilitator before treating an exchange as a paid sale.
For paid origin routes, a signed Cloudflare
`PAYMENT-CONTEXT` JWT must be validated against the official pinned
JWKS and accepted algorithms—**never trust an unsigned, decoded JWT
or self-asserted payment header**.

The new pure-Python `muhu.x402.inspect_challenge` is a
**syntax-only, read-only diagnostic**. It proves neither blockchain
settlement nor wallet authority, seller revenue, origin authorization
or correct paid-route coverage.

Exact account rules, receiving wallet, real settlement metrics and
buyer-side signed payment tests were unavailable in this source
snapshot. **No production paywall, DNS, Worker deployment or wallet
change has been executed from this release.** Review the separately
owned [Cloudflare monetization admission runbook](../../cloudflare/MONETIZATION_ADMISSION.md)
before onboarding premium routes.

## Publication and model research admission

[Technical methods research note](../publications/MUHU_METHODS_TECHNICAL_NOTE_20261117.md)
documents actual source identities, synthetic results and limitations.
It is a **public technical draft**, not a peer-reviewed paper, accepted
journal article, awarded grant or lab coauthorship agreement.

The codebase and research metadata can become a reusable platform
primitive after production-grade data authorization and independent
evaluation. MUHU v3's negative-model results must remain visible, with
the old baseline never quietly replaced by a post-test tuned result.

**Release rule:** NEVER equate green CI with runtime, deployed preview
with production, HTTP 402 with settlement, wheel build with PyPI
publication, bibliographic citation with biological proof, or software
hash with an external signature.
