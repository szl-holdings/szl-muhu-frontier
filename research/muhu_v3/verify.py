"""Immutable-byte verification of MUHU v3 public candidate source.

Offline, pure Python 3.11+. No provider calls, training or model loading.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import json
from hashlib import sha256
from research.muhu_v3.curriculum import (
    SCHEMA, TARGETS, GROUPS_PER_CLASS, TEMPLATES,
    canon, digest, encode_rows, generated, verify
)

def verify_public(public:Path)->dict:
    if not (public/"train.jsonl").is_file() or not (public/"manifest.json").is_file():
        raise ValueError("SOURCE_ARTIFACTS_MISSING")
    manifest_raw=(public/"manifest.json").read_bytes()
    manifest=json.loads(manifest_raw)
    if manifest.get("schema")!="szl.muhu.methodology-manifest.v3":
        raise ValueError("INVALID_MANIFEST_SCHEMA")
    if manifest.get("flagship_admitted") is not False:
        raise ValueError("UNAUTHORIZED_ADMISSION_CLAIM")
    if manifest.get("training_performed") is not False:
        raise ValueError("UNSUPPORTED_TRAINING_CLAIM")
    if not manifest.get("no_genomes",False) or not manifest.get("no_lab_data",False):
        raise ValueError("DATA_RIGHTS_UNVERIFIED")
    for banned in ("validation.jsonl","test.jsonl","private-raw.jsonl"):
        if (public/banned).exists():
            raise ValueError("PRIVATE_EVALUATION_PUBLISHED")
    generated_rows,unused=generated()
    checks=verify(generated_rows)
    expected_hashes={k:digest(encode_rows(v)) for k,v in generated_rows.items()}
    if manifest["sha256"]!=expected_hashes:
        raise ValueError("GROUP_HASH_OR_SPLIT_RECEIPT_MISMATCH")
    if (public/"train.jsonl").read_bytes()!=encode_rows(generated_rows["train"]):
        raise ValueError("PUBLIC_TRAIN_CONTENT_MISMATCH")
    if manifest["row_counts"]!=checks["row_counts"] or manifest["per_class"]!=checks["per_split_class_counts"]:
        raise ValueError("CLASS_SUPPORT_OR_COUNT_MISMATCH")
    if manifest["per_split_unique_groups"]!=checks["per_split_unique_groups"]:
        raise ValueError("GROUP_COVERAGE_MISMATCH")
    if manifest["unused_source_condition_groups_by_class"]!=unused:
        raise ValueError("UNUSED_SOURCE_SCOPE_MISMATCH")
    if manifest["condition_group_overlap"]!=0:raise ValueError("LEAKAGE_FLAG_CHANGED")
    return {
        "state":"OFFLINE_V3_SOURCE_DATA_VERIFIED_NOT_TRAINED",
        "rows":checks["row_counts"],"class_support":checks["per_split_class_counts"],
        "unique_condition_groups":checks["unique_condition_groups"],
        "manifest_sha256":sha256(manifest_raw).hexdigest(),
        "public_train_sha256":expected_hashes["train"],
        "source_group_overlap":0,
        "flagship_training_admitted":False,
        "biomedical_qualification":False,
        "external_blind_evaluation":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--public-dir",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(verify_public(a.public_dir),sort_keys=True))

if __name__=="__main__":main()
