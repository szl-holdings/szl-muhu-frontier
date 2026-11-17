# MUHU v3 — Equal-class, source-bound methodology experiment

This is the follow-through for the MUHU v2 CPU baseline that achieved
83.7% raw test accuracy on a dataset with an 81.5% majority baseline,
but detected 0/16 REVIEWABLE and 0/10 STALE test cases correctly.

MUHU v3 proposes a new, **smaller but class-balanced** synthetic
curriculum: 672 train (168 per class), 60 validation (15 per class),
96 test (24 per class). Counts correspond to 24/5/6 distinct
condition groups per class with differing prompt variants and
no cross-split condition-group overlap. A deterministic oracle and
negative controls are in the source.

## Exact run contract

```powershell
# On a permitted Python host; create two different NEW output paths.
python -B -m research.muhu_v3.curriculum --public-dir NEW_PUBLIC --private-dir NEW_PRIVATE
python -B -m research.muhu_v3.verify --public-dir NEW_PUBLIC

# Optional purely local research model, requires sklearn and numpy:
python -B -m research.muhu_v3.train_cpu \
  --public NEW_PUBLIC --private NEW_PRIVATE \
  --stress OWNER_ONLY_PRESEALED_STRESS.jsonl --out NEW_PRIVATE_MODEL_OUTPUT
```

No new paid GPU jobs, HF training jobs, CUDA, agent scheduler, branch
protection changes, credentials, private asset publication or model
promotion. The only trained model in the optional lane is an
experimental CPU text classifier over synthetic methodology prompts,
**not an LLM, not Khipu, not a genetics model**.

The baseline comparison and **fixed acceptance criteria** are
documented in [ACCEPTANCE.md](ACCEPTANCE.md). Treat a failed gate as
a scientific result, not a reason to alter thresholds after seeing
test scores.

Only the 672 public training examples may be published to the Hub.
The internal validation/test and authored stress fixtures remain on
the owner laptop. Since the generator is published, the internal
withheld examples can be reconstructed and do not provide a truly
blind external evaluation.

Biology, therapeutic research, clinical decision support, microscopy
or gene-editing quality are **NOT EVALUATED** by this curriculum.
The Vidal-Gadea protocol remains unfrozen and lab data must remain
inside its owner's boundary.
