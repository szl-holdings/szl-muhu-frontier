"""Minimal, deterministic MUHU evidence CLI. No network, payments or training."""
from __future__ import annotations

import argparse
import json
from typing import Sequence

from .witness import gate, unavailable

VERSION = "0.1.0"
BOOL_CHOICES = ("true", "false")


def inspect_fields(
    *,
    source_bound: str | None,
    sample_n: int | None,
    age_days: int | None,
    independent_check: str | None,
    contradiction: str | None,
) -> dict:
    supplied = {
        "source_bound": source_bound,
        "sample_n": sample_n,
        "age_days": age_days,
        "independent_check": independent_check,
        "contradiction": contradiction,
    }
    missing = {k for k, v in supplied.items() if v is None}
    if missing:
        record = unavailable(missing)
    else:
        record = gate(
            {
                "source_bound": source_bound == "true",
                "sample_n": sample_n,
                "age_days": age_days,
                "independent_check": independent_check == "true",
                "contradiction": contradiction == "true",
            }
        )
    # Machine operators must not confuse successful execution with a
    # science/clinical/training admission. The return code means nothing
    # about qualification.
    record["model_trained"] = False
    record["training_authorized"] = False
    record["clinical_qualified"] = False
    record["not_a_digital_signature"] = True
    return record


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify synthetic research metadata. Not medical or clinical."
    )
    parser.add_argument("--version", action="version", version=f"szl-muhu-evidence {VERSION}")
    parser.add_argument("--source-bound", choices=BOOL_CHOICES)
    parser.add_argument("--sample-n", type=int)
    parser.add_argument("--age-days", type=int)
    parser.add_argument("--independent-check", choices=BOOL_CHOICES)
    parser.add_argument("--contradiction", choices=BOOL_CHOICES)
    args = parser.parse_args(argv)
    try:
        result = inspect_fields(
            source_bound=args.source_bound,
            sample_n=args.sample_n,
            age_days=args.age_days,
            independent_check=args.independent_check,
            contradiction=args.contradiction,
        )
    except (ValueError, TypeError):
        parser.error("Invalid bounded synthetic evidence values; no claim was admitted")
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
