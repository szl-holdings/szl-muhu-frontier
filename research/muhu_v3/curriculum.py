"""MUHU v3: stratified, rights-clean, independently testable research-method SFT.

This is source, not training admission. All labels are synthetic governance
rules; not genetics, microscopy, or therapy outcomes.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import argparse
import json
import os

from muhu.core import CASE_FIELDS, enumerate_groups, status_of

SCHEMA = "szl.muhu.methodology-curriculum.v3"
TARGETS = ("BLOCKED", "CONFLICT", "STALE", "REVIEWABLE")
REASON = {
    "BLOCKED": "Required provenance, a nonzero denominator or independent verification is absent.",
    "CONFLICT": "Contradictory evidence exists; do not collapse incompatible claims.",
    "STALE": "The evidence is older than the seven-day verification rule.",
    "REVIEWABLE": "The methodological fields permit review, not scientific validity or clinical use.",
}
RIGHTS = {"license": "CC-BY-4.0", "creator": "SZL Holdings",
          "content": "original synthetic methodology-only, no partner or biological data"}
SYSTEM = ("Classify a fictional scientific-evidence note. Use states BLOCKED, "
          "CONFLICT, STALE, REVIEWABLE, observing precedence; output only a state "
          "and limitation, never biological, clinical, or therapeutic conclusions.")

TRAIN_TEMPLATES = (
 "Synthetic evidence audit: source citation {src}, reported sample size {n}, age since verification {age} days, independent reviewer {check}, contradictory result {contra}. State its method status.",
 "For a fabricated scientific report, record whether an origin exists ({src}); count={n}; last checked {age} days ago; external corroboration={check}; conflicting observation={contra}. Evaluate sufficiency.",
 "A mock evidence card has source bound={src}; measured items={n}; freshness elapsed={age} days; outside check={check}; dissenting source={contra}. Return the conservative verdict.",
 "Invented research extract: traceable citation? {src}. Denominator {n}. Days since source read {age}. Independent verification? {check}. Competing findings? {contra}.",
 "Review the fictional methodology inputs: provenance {src}; actual denominator {n}; staleness days {age}; second auditor {check}; contradiction flag {contra}.",
 "Do not infer biology. The synthetic case has named original source={src}, n={n}, previous validation age={age}, independently checked={check}, adverse evidence={contra}.",
 "Fictional evidence register: source listed {src}; sample records {n}; verified {age} days ago; independent observer {check}; contrary report {contra}. Classify."
)
VALID_TEMPLATES = (
 "Method-screening note (invented): source accessible {src}. Enrollment count {n}. Age of last verification {age} days. Independent check recorded {check}. Conflicting result present {contra}. What is its status?",
 "The simulated paper-entry states whether it has a citable origin ({src}), a denominator ({n}), a review lag ({age} days), replication by another operator ({check}), and contradicting data ({contra}). Return the gate state.",
 "Synthetic audit: original evidence retained={src}; measured observations={n}; time since external read={age} days; verified by another analyst={check}; contradictory material exists={contra}."
)
TEST_TEMPLATES = (
 "A fabricated project update supplies source provenance ({src}), observations counted ({n}), elapsed source-check time ({age} days), external corroboration ({check}), and disagreement ({contra}); classify without extrapolating.",
 "In this mock research note: citation is {src}, denominator is {n}, last independent inspection was {age} days ago, separate verification is {check}, opposing result is {contra}. Determine the evidence gate.",
 "Synthetic reporting record: documented origin {src}; counted participants {n}; days after validation {age}; unaffiliated confirmation {check}; contrary findings {contra}. Which state?",
 "Evaluate only methodological admissibility: provenance={src}; n={n}; evidence_age_days={age}; corroborated={check}; contradiction={contra}. The record is invented."
)
TEMPLATES = {"train": TRAIN_TEMPLATES, "validation": VALID_TEMPLATES, "test": TEST_TEMPLATES}
GROUPS_PER_CLASS = {"train": 24, "validation": 5, "test": 6}

def canon(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))+"\n").encode("utf-8")

def digest(raw: bytes) -> str:
    return sha256(raw).hexdigest()

def group_key(factors: dict) -> str:
    return digest(canon(factors))

def assigned_groups() -> dict:
    by_state = defaultdict(list)
    for case in enumerate_groups():
        by_state[status_of(case)].append(case)
    allocated = {split: [] for split in GROUPS_PER_CLASS}
    unseen_counts = {}
    for state in TARGETS:
        candidates = sorted(by_state[state], key=lambda x: digest(
            ("muhu-v3-sort|" + group_key(x)).encode()))
        required = sum(GROUPS_PER_CLASS.values())
        if len(candidates) < required:
            raise RuntimeError("INSUFFICIENT_GROUP_SUPPORT_" + state)
        pos=0
        for split,num in GROUPS_PER_CLASS.items():
            allocated[split].extend(candidates[pos:pos+num])
            pos+=num
        unseen_counts[state] = len(candidates) - required
    return allocated, unseen_counts

def render(case: dict, split: str, variant: int) -> dict:
    if split not in TEMPLATES or variant not in range(len(TEMPLATES[split])):
        raise ValueError("INVALID_TEMPLATE")
    truth = status_of(case)
    params = {
        "src": "yes" if case["source_bound"] else "no",
        "n": case["sample_n"], "age": case["age_days"],
        "check": "yes" if case["independent_check"] else "no",
        "contra": "yes" if case["contradiction"] else "no",
    }
    text=TEMPLATES[split][variant].format(**params)
    target=f"STATE: {truth}\nLIMIT: {REASON[truth]}"
    # This sample ID is never included in the model-facing prompt.
    identity=group_key(case)
    return {
        "schema": SCHEMA, "id": f"{split}-{identity[:15]}-{variant}",
        "split": split, "semantic_group_sha256": identity, "target_state": truth,
        "input": text, "output": target,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": text},
                     {"role": "assistant", "content": target}],
        "oracle_inputs": case, "rights": RIGHTS, "synthetic": True,
        "scope": "Research-method evidence-status exercise; not actual data or model quality.",
    }

def generated() -> tuple[dict, dict]:
    allotted, unselected = assigned_groups()
    datasets={}
    for split,groups in allotted.items():
        result=[]
        for case in groups:
            for variant in range(len(TEMPLATES[split])):
                result.append(render(case,split,variant))
        datasets[split]=sorted(result,key=lambda r:r["id"])
    return datasets,unselected

def verify(datasets: dict) -> dict:
    group_to_split={}
    all_ids=set()
    labels={}
    for split in TEMPLATES:
        data=datasets[split]
        if not data:
            raise ValueError("EMPTY_SPLIT")
        labels[split]=Counter()
        for row in data:
            if row["schema"] != SCHEMA or row["split"]!=split or row["synthetic"] is not True:
                raise ValueError("WRONG_SCHEMA")
            case=row["oracle_inputs"]
            status=status_of(case)
            if status != row["target_state"] or row["output"]!=f"STATE: {status}\nLIMIT: {REASON[status]}":
                raise ValueError("INVALID_ORACLE_LABEL")
            if row["semantic_group_sha256"] != group_key(case):
                raise ValueError("FALSIFIED_GROUP_ID")
            if row["id"] in all_ids:
                raise ValueError("DUPLICATE_ID")
            all_ids.add(row["id"])
            group=row["semantic_group_sha256"]
            if group in group_to_split and group_to_split[group]!=split:
                raise ValueError("SEMANTIC_GROUP_LEAKAGE")
            group_to_split[group]=split
            if row["messages"][1]["content"]!=row["input"] or row["messages"][2]["content"]!=row["output"]:
                raise ValueError("CHAT_FORMAT_BROKEN")
            if row["rights"]!=RIGHTS or any(key in row for key in ("patient","genome","therapy","lab_record")):
                raise ValueError("PROHIBITED_DATA")
            labels[split][status]+=1
    for split in TEMPLATES:
        expected_num=GROUPS_PER_CLASS[split]*len(TEMPLATES[split])
        if any(labels[split][c]!=expected_num for c in TARGETS):
            raise ValueError("CLASS_IMBALANCE_OR_TRUNCATION_"+split)
    return {
        "total_rows":len(all_ids), "unique_condition_groups":len(group_to_split),
        "condition_group_leakage":0,
        "row_counts":{k:len(v) for k,v in datasets.items()},
        "per_split_class_counts":{k:dict(v) for k,v in labels.items()},
        "per_split_unique_groups":{
            k:len({r["semantic_group_sha256"] for r in v}) for k,v in datasets.items()
        },
    }

def encode_rows(rows: list[dict]) -> bytes:
    return b"".join(canon(r) for r in rows)

def exclusive_write(path:Path, data:bytes)->str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    if path.read_bytes()!=data:raise RuntimeError("READBACK_MISMATCH")
    return digest(data)

def build(public_dir: Path, private_dir: Path)->dict:
    if public_dir.exists() or private_dir.exists():
        raise RuntimeError("REFUSE_EXISTING_GENERATION")
    if public_dir.resolve()==private_dir.resolve():
        raise RuntimeError("PRIVATE_PUBLIC_COLLISION")
    data,skipped=generated()
    checks=verify(data)
    # Each private split remains separate and append-only; no ML model launched.
    private_dir.mkdir(parents=True)
    hashes={}
    for split in ("validation","test"):
        hashes[split]=exclusive_write(private_dir/(split+".jsonl"),encode_rows(data[split]))
    public_dir.mkdir(parents=True)
    hashes["train"]=exclusive_write(public_dir/"train.jsonl",encode_rows(data["train"]))
    manifest={
        "schema":"szl.muhu.methodology-manifest.v3","synthetic":True,
        "scientific_qualification":"NONE","flagship_admitted":False,
        "training_performed":False,"clinical_use":"DENIED",
        "license":"CC-BY-4.0","owner":"SZL Holdings",
        "task":"Source-based methodological reasoning exercises, not scientific diagnosis",
        "source_policy":"public deterministic v3 generation; open-source test not truly blind",
        "source_software":"szl-holdings/szl-muhu-frontier",
        "planned_fixed_training_algorithm":"offline bounded sklearn CPU, no GPU/paid jobs",
        "row_counts":checks["row_counts"],
        "per_class":checks["per_split_class_counts"],
        "per_split_unique_groups":checks["per_split_unique_groups"],
        "condition_group_overlap":0,
        "unused_source_condition_groups_by_class":skipped,
        "sha256":hashes,
        "no_genomes":True,"no_clinical_records":True,"no_lab_data":True,
        "no_partner_source_text":True,"train_only_public":True,
        "external_independent_test_completed":False,
        "limitations":"Finite enumerated rule combinations and public generator; do not claim biological, clinical or real-world generalization."
    }
    hashes["manifest"]=exclusive_write(public_dir/"manifest.json",canon(manifest))
    return {"manifest_sha256":hashes["manifest"],"dataset_manifest":manifest}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--public-dir", type=Path, required=True)
    p.add_argument("--private-dir", type=Path, required=True)
    a=p.parse_args()
    result=build(a.public_dir,a.private_dir)
    print(json.dumps({"state":"GENERATED_SOURCE_ONLY","manifest_sha256":result["manifest_sha256"],
                      "row_counts":result["dataset_manifest"]["row_counts"],
                      "class_counts":result["dataset_manifest"]["per_class"]},sort_keys=True))

if __name__=="__main__":main()
