# szl-muhu-evidence

**Pure-Python, nonclinical research-method evidence gates from SZL Holdings.**

This package provides deterministic classification of **invented**
methodological records, a source/denominator/freshness witness, and
developer-readable provenance policy helpers. It contains **no trained
genetics model**, clinical recommendations, patient records, private
laboratory information, live data scraper, or signed payment handler.

MUHU means *seed* in Quechua Chanka as a project metaphor, not a
literal translation of genetics.

## Install from reviewed local source

```bash
python -m pip install .
muhu-witness --source-bound true --sample-n 32 --age-days 2 \
  --independent-check true --contradiction false
```

The PyPI project `szl-muhu-evidence` is a **release candidate** until
the PyPI trusted-publisher deployment and published registry revision
are independently verified. Do not treat an available package name
or a passing wheel build as a successful public publication.

The CLI emits a stable JSON assessment with its exact input fields,
the evaluated rule, outstanding requirements, and SHA-256 checksum
(**not** a cryptographic signature). Its process exit code means
the CLI executed successfully—it never authorizes a study, patient
decision, cloud request, paid action, or model training.

## Direct library use

```python
from muhu.witness import gate

result = gate({
    "source_bound": True,
    "sample_n": 32,
    "age_days": 2,
    "independent_check": True,
    "contradiction": False,
})
assert result["state"] == "REVIEWABLE"
assert result["scientific_validity"] == "NOT_ASSESSED"
```

The four *synthetic methods* states are:

- `BLOCKED`: required source pointer, nonzero denominator, or
  independent corroboration is missing.
- `CONFLICT`: a contradictory assertion is present.
- `STALE`: source was not checked in the previous seven days.
- `REVIEWABLE`: required metadata is present; **not** a finding of
  scientific or clinical validity.

A missing field returns `UNAVAILABLE` through the query decoder;
malformed fields refuse processing. A claim of source presence does not
verify the actual source. The separate Hugging Face research preview
makes public bibliographic identifier checks and never infers
gene–disease causality or therapeutic effectiveness from PubMed titles.

## Developer and investor proof

- Canonical source: https://github.com/szl-holdings/szl-muhu-frontier
- HF hosted preview: https://huggingface.co/spaces/SZLHOLDINGS/szl-muhu-frontier
- Training data: https://huggingface.co/datasets/SZLHOLDINGS/muhu-methodology-sft-v2
- Public failed-model evaluation: https://github.com/szl-holdings/szl-muhu-frontier/blob/main/research/muhu_v3/RESULTS_20261117.md
- Owner training HOLD: https://github.com/szl-holdings/szl-gpu-bridge/pull/228
- Release governance: https://github.com/szl-holdings/szl-muhu-frontier/blob/main/docs/release/RELEASE_ADMISSION.md

The hosted application needs a full **repository checkout and pinned
public reference dataset files**; the PyPI wheel is a **library/CLI
distribution**, not a drop-in replacement for the hosted backend.
It does not contain withheld evaluation samples, training checkpoints,
or live credentialed Cloudflare configuration.

## License and scope

Software: MIT. The separately published *original synthetic training
examples* are CC BY 4.0 and are **not** distributed in the wheel. Third-
party scientific publications retain their authors' rights. Scientific
claims, medical advice, research-partner endorsement, x402 settlement,
and production training readiness are explicitly outside this package.
