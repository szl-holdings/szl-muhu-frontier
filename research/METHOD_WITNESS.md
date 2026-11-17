# MUHU Method Witness v1 — transparent, bounded methodological evidence gate

**State:** Offline deterministic rule implemented; running research preview
requires separate CI, immutable provider publication and HTTP readback.
**Not a genetics model, a clinical algorithm, or an independent witness.**

## Why this exists

The [MUHU v3 negative result](muhu_v3/RESULTS_20261117.md) showed that
87.5% raw accuracy on balanced synthetic prompts concealed 50% selective
coverage, poor minority-state recall and 7/32 internal stress accuracy.
Threshold retuning after examining that result would violate the
predeclared scientific acceptance contract.

A transparent, deterministic rule over *explicit typed inputs* provides
a different kind of research instrument. It tests which metadata fields
were supplied and whether the declared policy can be evaluated. It
does **not** infer which facts are true from natural language.

## Input and output contract

`GET /api/v1/witness` accepts exactly five synthetic fields:

| Field | Type | Range or allowed values |
| --- | --- | --- |
| `source_bound` | Boolean | `true` or `false` |
| `sample_n` | Strict integer | 0–1000 |
| `age_days` | Strict integer | 0–365 |
| `independent_check` | Boolean | `true` or `false` |
| `contradiction` | Boolean | `true` or `false` |

An omitted field returns `UNAVAILABLE`, never an inferred absence.
Malformed values, duplicate fields or unknown fields receive HTTP 400.
No free-text source or patient-data field is supported. The GET endpoint
does not upload or persist its inputs in the application; infrastructure
providers may retain ordinary URL access logs, which is another reason
to use only invented metadata here. The application does not execute
any model or external tool.

A complete case follows fixed priority:

1. No declared source, zero sample count or missing independent check:
   `BLOCKED`.
2. Otherwise, contradiction present: `CONFLICT`.
3. Otherwise, age greater than seven days: `STALE`.
4. Otherwise: `REVIEWABLE`.

Every complete result includes the exact input values, five rule
checks, limitations, outstanding evidence requirements and SHA-256 of
the canonical witness payload. That hash is **not a signature**.
The application does not check the reality of a claimed source,
observations or independent corroboration.

`GET /witness` provides one interactive, Python-rendered screen that
evaluates five artificial metadata fields. It starts with a visibly
synthetic example and has no free-text entry or write endpoint.
`/readyz` stays HTTP 503 because no scientific/clinical qualification
has occurred.

## Verification and negative controls

Unit tests independently compute all 640 synthetic condition
combinations and compare their expected status with the witness.
Additional tests cover omitted and invalid inputs, repeated query
parameters, source-less false REVIEWABLE attempts, zero denominators,
contradiction-before-staleness precedence, deterministic digest
readback, interactive page rendering and POST denial.

**What this does not prove:** It does not validate input truth, verify
original source identities, establish predictive accuracy, improve
Sara's puzzle difficulty model, measure Vidal-Gadea laboratory biology,
evaluate WWOX genetics, or qualify Khipu weights. A rule-book passing
its own generated cases is not an external scientific benchmark.

The next scientific test is independent annotation of actual source
documents against a preregistered scope and public measurement
protocol. Such data and lab records remain outside this public
research service until owners approve access, licensing and validation.

## Ownership

The MUHU source repository owns this demonstration only.
The existing `szl-gpu-bridge` and A11oy training controllers retain
exclusive Flagship54 and Khipu execution authority. No new scheduler,
cloud jobs, GPU resources, model-card promotion or receipt signer
is created by this implementation.
