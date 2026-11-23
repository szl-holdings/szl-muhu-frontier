"""Source-bound, no-side-effects validation of MUHU v2 public training artifact.

This check itself is not model training or scientific validation.
"""
import argparse
import json
from hashlib import sha256
from pathlib import Path
from .core import canonical, generate, verify_splits,byte_lines,sha256_bytes

def _unique_manifest_pairs(pairs):
 out={}
 for key,value in pairs:
  if key in out:raise ValueError("AMBIGUOUS_MANIFEST_JSON")
  out[key]=value
 return out

def _reject_nonfinite_manifest(_value):
 raise ValueError("AMBIGUOUS_MANIFEST_JSON")

def validate(public:Path)->dict:
 manifest_path=public/"manifest.json"
 train_path=public/"train.jsonl"
 manifest=json.loads(manifest_path.read_text("utf-8"),
                     object_pairs_hook=_unique_manifest_pairs,
                     parse_constant=_reject_nonfinite_manifest)
 if manifest.get("schema")!="szl.muhu.dataset_manifest.v2":raise ValueError("SCHEMA_MISMATCH")
 if manifest.get("training_performed") is not False:raise ValueError("FALSE_TRAINING_CLAIM")
 if manifest.get("admitted_into_any_flagship") is not False:raise ValueError("UNAUTHORIZED_PROMOTION")
 if any(manifest.get(k) != 0 for k in ("raw_genomic_sequences","partner_lab_records","patient_records","third_party_text_training_rows")):
  raise ValueError("PROHIBITED_MATERIAL_REPORTED")
 train_bytes=train_path.read_bytes()
 if sha256_bytes(train_bytes)!=manifest["split_hashes_sha256"]["train"]:
  raise ValueError("PUBLIC_TRAIN_BYTES_CHANGED")
 partitions=generate()
 checks=verify_splits(partitions)
 if byte_lines(partitions["train"])!=train_bytes:
  raise ValueError("GENERATOR_REPLAY_MISMATCH")
 for split in ("train","validation","test"):
  if manifest["split_hashes_sha256"][split]!=sha256_bytes(byte_lines(partitions[split])):
   raise ValueError("PARTITION_RECEIPT_MISMATCH_"+split)
 if manifest["public_training_records"]!=checks["counts"]["train"]:
  raise ValueError("TRAIN_ROW_COUNT_MISMATCH")
 if manifest["private_validation_records"]!=checks["counts"]["validation"]:
  raise ValueError("VALIDATION_COUNT_MISMATCH")
 if manifest["private_test_records"]!=checks["counts"]["test"]:
  raise ValueError("TEST_COUNT_MISMATCH")
 if (public/"test.jsonl").exists() or (public/"validation.jsonl").exists():
  raise ValueError("PRIVATE_EVALUATION_LEAKAGE")
 return {
  "state":"OFFLINE_SOURCE_BOUND_TRAINING_DATA_VERIFIED",
  "training_rows":checks["counts"]["train"],
  "withheld_evaluation_rows":checks["counts"]["validation"]+checks["counts"]["test"],
  "distinct_semantic_groups":checks["unique_groups"],
  "semantic_group_overlap":0,
  "manifest_sha256":sha256(manifest_path.read_bytes()).hexdigest(),
  "train_sha256":sha256(train_bytes).hexdigest(),
  "training_running":False,
  "model_evaluated":False,
  "clinical_qualified":False
 }

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--public-dir",type=Path,required=True)
 args=p.parse_args()
 print(json.dumps(validate(args.public_dir),sort_keys=True))

if __name__=="__main__":main()
