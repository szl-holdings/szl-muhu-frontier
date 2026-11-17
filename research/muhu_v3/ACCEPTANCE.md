# MUHU v3 Research Candidate — Fixed Evaluation Contract

**Date fixed:** 2026-11-17, before fitting or opening either v3 evaluation file.
**Status:** CPU-ONLY EXPERIMENT; **NO FLAGSHIP ADMISSION**.
**Data rights:** SZL original synthetic CC-BY-4.0; no Sara puzzle text,
Vidal-Gadea recordings, unpublished laboratory results, patient records,
genomes, biological sequences or therapeutic-design material.

## Primary question and exactly what is being classified

Does a fixed CPU text classifier trained on original synthetic
methodological evidence notes learn the four *method* labels better than
a majority baseline, and correctly preserve rare REVIEWABLE and STALE
labels on previously withheld synthetic conditions?

The label oracle is an explicitly declared rule set:
1. Missing source OR zero denominator OR missing independent corroborator
   → BLOCKED (takes precedence over all others).
2. Else contradictory evidence → CONFLICT.
3. Else evidence older than seven days → STALE.
4. Else → REVIEWABLE (never proof of scientific truth).

**This does not classify gene variants, microscope footage, animal behavior,
therapy efficacy or safety, and is not a clinical model.** A deterministic
rule executor is the oracle ceiling, not evidence of learned intelligence.

## Experimental design (locked before evaluation)

- Fixed generator `research/muhu_v3/curriculum.py`, no internet text.
- Condition groups enumerated from the existing v2 frozen rule; **35
  selected distinct groups per class**, 24 train / 5 validation / 6 test.
  640 possible source factor combinations exist; 140 selected distinct
  condition groups. Remaining groups are not silently counted as tested.
- Prompt variants: 7 train / 3 validation / 4 test; no verbatim template
  crossing partitions, no condition-group overlap.
- Train **672** examples: 168/class. Validation **60**: 15/class.
  Test **96**: 24/class. No test cases enter training.
- Train/test labels are synthetic deterministic rules. The public generator
  can reconstruct held-out cases, so **this is not a hidden or externally
  independent benchmark**, despite private file storage.
- Separate operator-authored stress cases are sealed in a private SHA-256
  fixture **before training**. They are additional internal tests, not
  independent human adjudication or laboratory results.
- One selected CPU model **without hyperparameter search**:
  word + character TF-IDF features (1–2 word and 3–5 character n-grams),
  logistic regression `C=1.0`, class-weight balanced, `random_state=42`,
  `max_iter=2000`. No GPU or provider training jobs; synthetic only.
- Text model gets the model-facing `input` only, never `target_state`,
  `oracle_inputs`, `messages[-1]`, group identifier or future samples.
- Abstain when top two uncalibrated softmax probabilities differ by
  less than **0.20**. Scores are not calibrated probabilities.
- Majority-class baseline and fixed oracle rule upper bound must both
  be reported. No dataset row may be dropped post hoc.
- Report exact confusion by class with abstention as a separate output,
  macro F1, per-class recall, selective accuracy/coverage, false
  REVIEWABLE admissions, denominator, and label support.
  The test-set interval is Wilson 95% for all-guess accuracy.

## Predeclared minimum research gates

Pass *on synthetic group-disjoint data* requires all:
- Macro F1 >= 0.85 on the 96 example test set (abstentions counted
  as misses).
- Per-class recall >= 0.70 for **each** of the four labels.
- False REVIEWABLE admissions among non-REVIEWABLE test records <= 2%.
- Selective coverage >= 0.85.
- Internal independently phrased stress-case accuracy >= 0.75, with no
  false REVIEWABLE on incomplete-source cases.
- Exact input hashes, group disjointness, rights and no prohibited data,
  plus all local and protected GitHub tests green.

Any failure leaves model quality **HOLD**. Passing would still mean
**synthetic methods-test passed only**—not flagship model admission,
real-world robustness, clinical qualification, scientific discovery or
rights to Sara/Vidal data. No test score is transferred to any Khipu
checkpoint without a new immutable bound evaluation.

## Next gates regardless of outcome

Independent external blinded cases with human adjudication; exact
pinned Khipu base/tokenizer/runtime, sealed negative controls, ablation,
context- and domain-shift evaluations, governance/abstention battery,
budget and signer approval, no conflicting training controller, and
separate owner-controlled next-cycle job. Active Flagship54 config,
source, target and guard must remain unchanged.
