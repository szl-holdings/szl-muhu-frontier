"""MUHU v2: rights-clean, source-disjoint scientific-method curriculum.

Not a biology/clinical/genetics predictor. No external training materials are read.
Held-out case records are stored separately in private owner evidence.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from itertools import product
from pathlib import Path
import argparse
import json
import os
import re
import tempfile

SCHEMA = "szl.muhu.methodology-sft/v2"
POLICY_VERSION = "muhu-rulebook-20261117-v2"
TARGETS = ("BLOCKED", "CONFLICT", "STALE", "REVIEWABLE")
LICENSE = "CC-BY-4.0"
INTENT = "Synthetic methodological evidence screening, not gene/variant/therapy assessment"
SYSTEM = ("You are auditing a synthetic research claim. Return only the classification "
          "and its evidence limitation. Never give clinical or biological conclusions.")
CASE_FIELDS = ("source_bound", "sample_n", "age_days", "independent_check", "contradiction")
INPUT_TEMPLATES = {
 "train": (
  "Assess synthetic report {ref}. Source revision {source}; denominator {n}; age {age} days; independent check {check}; contradictory record {conflict}.",
  "Inspect this invented evidence card: record {ref}, cited source={source}, sample count={n}, last verified={age} days ago, outside replication={check}, rival observation={conflict}.",
  "For fictional report {ref}, evaluate the documentation: revision present? {source}; n={n}; elapsed days={age}; separate corroboration? {check}; counter-observation? {conflict}."
 ),
 "validation":(
  "Independent fixture {ref} states: accessible origin {source}, measured population size {n}, freshness interval {age} days, second reviewer {check}, dissenting evidence {conflict}. Determine whether its method claim is reviewable.",
  "The mock study {ref} includes an origin ({source}), count ({n}), observation age ({age} days), corroborator ({check}) and disagreement ({conflict}). Classify evidence sufficiency."
 ),
 "test":(
  "An artificial investigator's note {ref} reports a source pointer {source}; cohort size {n}; time since last evidence check {age} days; independent corroboration {check}; competing assertion {conflict}. What evidence state applies?",
  "For sample {ref}, can the finding be used in a research synthesis? Given source={source}; denominator={n}; staleness={age} days; external validation={check}; contrary finding={conflict}, produce the conservative methodological verdict."
 )
}
REASON = {
 "BLOCKED": "A required source, nonzero denominator, or independent check is missing. Refuse substantive reliance.",
 "CONFLICT": "A contradictory observation exists; preserve both assertions and request adjudication.",
 "STALE": "The last evidence verification is older than seven days; repeat the source read before reuse.",
 "REVIEWABLE": "Required metadata is present and current; this is reviewable, not scientifically or clinically validated."
}

def canonical(obj:object)->bytes:
 return (json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n").encode("utf-8")

def sha256_bytes(raw:bytes)->str:
 return sha256(raw).hexdigest()

def status_of(factors:dict)->str:
 if set(factors)!=set(CASE_FIELDS):raise ValueError("EXACT_FIELDS_REQUIRED")
 a,b,c,d,e=(factors[k] for k in CASE_FIELDS)
 if type(a)!=bool or type(b)!=int or type(c)!=int or type(d)!=bool or type(e)!=bool:
  raise ValueError("STRICT_FIELD_TYPES")
 if b<0 or c<0 or b>1000 or c>365:raise ValueError("FIELD_OUT_OF_RANGE")
 if not a or b==0 or not d:return "BLOCKED"
 if e:return "CONFLICT"
 if c>7:return "STALE"
 return "REVIEWABLE"

def partition(factors:dict)->str:
 digest=sha256(("MUHU-v2/partition/"+json.dumps(factors,sort_keys=True)).encode("utf-8")).digest()
 bucket=int.from_bytes(digest[:4],"big")%100
 return "train" if bucket<70 else "validation" if bucket<85 else "test"

def fingerprint(factors:dict)->str:
 return sha256_bytes(canonical(factors))

def enumerate_groups()->list[dict]:
 all_factors=[]
 for origin,n,age,check,contradiction in product((True,False),(0,1,3,7,11,19,32,90),(0,1,2,4,7,8,9,14,21,35),(True,False),(True,False)):
  f=dict(zip(CASE_FIELDS,(origin,n,age,check,contradiction)))
  all_factors.append(f)
 return all_factors

def render(factors:dict,split:str,variant:int)->dict:
 if split not in INPUT_TEMPLATES:raise ValueError("BAD_SPLIT")
 templates=INPUT_TEMPLATES[split]
 group=fingerprint(factors)
 # Model-facing identifiers uniquely bind the sample, without encoding the label.
 ref="sim-"+group[:12]+"-"+str(variant)
 prompt=templates[variant%len(templates)].format(
  ref=ref, source="yes" if factors["source_bound"] else "no",
  n=factors["sample_n"],age=factors["age_days"],
  check="yes" if factors["independent_check"] else "no",
  conflict="yes" if factors["contradiction"] else "no")
 gold=status_of(factors)
 answer="STATE: "+gold+"\nLIMIT: "+REASON[gold]
 return {
  "schema":SCHEMA,"id":ref,"group_sha256":group,"split":split,
  "task":"synthetic_evidence_methodology",
  "input":prompt,"output":answer,
  "messages":[{"role":"system","content":SYSTEM},{"role":"user","content":prompt},
              {"role":"assistant","content":answer}],
  "oracle_inputs":factors,
  "target_state":gold,"synthetic":True,
  "rights":{"license":LICENSE,"source":"SZL original, procedurally generated, no partner or private material"},
  "limitations":"No gene, variant, diagnosis, efficacy, animal result, or real-world scientific validity is assessed."
 }

def generate()->dict[str,list[dict]]:
 out={k:[] for k in INPUT_TEMPLATES}
 for f in enumerate_groups():
  split=partition(f)
  for variant in range(len(INPUT_TEMPLATES[split])):
   out[split].append(render(f,split,variant))
 for name,rows in out.items():
  rows.sort(key=lambda x:x["id"])
  if not rows:raise ValueError("EMPTY_SPLIT_"+name)
 return out

def verify_splits(parts:dict[str,list[dict]])->dict:
 seen_ids=set();seen_group={}
 counts={}
 for part,rows in parts.items():
  if part not in INPUT_TEMPLATES:raise ValueError("UNKNOWN_SPLIT")
  counts[part]=len(rows)
  for row in rows:
   if row["schema"]!=SCHEMA or row["split"]!=part or row["synthetic"] is not True:
    raise ValueError("INVALID_SCHEMA_OR_SPLIT")
   if row["rights"]["license"]!=LICENSE or "SZL original" not in row["rights"]["source"]:
    raise ValueError("BAD_RIGHTS")
   if row["target_state"]!=status_of(row["oracle_inputs"]):raise ValueError("ORACLE_MISMATCH")
   if row["output"]!="STATE: "+row["target_state"]+"\nLIMIT: "+REASON[row["target_state"]]:
    raise ValueError("ANSWER_MISMATCH")
   # The SFT loader consumes messages, not the parallel input/output metadata.
   # A tampered system/user/assistant message must never pass a split audit.
   expected_messages=[
    {"role":"system","content":SYSTEM},
    {"role":"user","content":row.get("input")},
    {"role":"assistant","content":row["output"]},
   ]
   if type(row.get("input")) is not str or row.get("messages")!=expected_messages:
    raise ValueError("CHAT_TRAINING_PAYLOAD_MISMATCH")
   if row["group_sha256"]!=fingerprint(row["oracle_inputs"]):raise ValueError("GROUP_ID_MISMATCH")
   if partition(row["oracle_inputs"])!=part:raise ValueError("PARTITION_MISMATCH")
   if row["id"] in seen_ids:raise ValueError("DUPLICATE_SAMPLE")
   seen_ids.add(row["id"])
   prev=seen_group.setdefault(row["group_sha256"],part)
   if prev!=part:raise ValueError("SEMANTIC_GROUP_LEAKAGE")
   # Every record remains a synthetic exercise; no real collaborator or patient input.
   if any(k in row for k in ("genome","patient_record","lab_measurement","clinical_diagnosis","gene_editing")):
    raise ValueError("PROHIBITED_CONTENT")
 return {"unique_groups":len(seen_group),"samples":len(seen_ids),"counts":counts,
         "labels_by_split":{k:dict(Counter(x["target_state"] for x in rows)) for k,rows in parts.items()},
         "semantic_group_overlap":0}

def byte_lines(rows:list[dict])->bytes:
 return b"".join(canonical(row) for row in rows)

def atomic_new(path:Path,raw:bytes)->str:
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open("xb") as f:
  f.write(raw);f.flush();os.fsync(f.fileno())
 if path.read_bytes()!=raw:raise RuntimeError("WRITE_READBACK_MISMATCH")
 return sha256_bytes(raw)

def build(public_dir:Path,private_dir:Path)->dict:
 if public_dir.exists() or private_dir.exists():raise ValueError("REFUSE_EXISTING_OUTPUT")
 if public_dir.resolve()==private_dir.resolve():raise ValueError("REFUSE_PUBLIC_PRIVATE_COLLISION")
 parts=generate()
 report=verify_splits(parts)
 # Public only train rows; validation/test cases remain exclusively in owner-controlled evidence.
 private_dir.mkdir(parents=True)
 hashes={}
 for split in ("validation","test"):
  hashes[split]=atomic_new(private_dir/(split+".jsonl"),byte_lines(parts[split]))
 public_dir.mkdir(parents=True)
 hashes["train"]=atomic_new(public_dir/"train.jsonl",byte_lines(parts["train"]))
 manifest={
  "schema":"szl.muhu.dataset_manifest.v2",
  "curriculum":"Synthetic experimental-methodology classification in chat SFT form",
  "policy_revision":POLICY_VERSION,
  "training_source":"SZL original generated examples, CC-BY-4.0",
  "public_training_records":len(parts["train"]),
  "private_validation_records":len(parts["validation"]),
  "private_test_records":len(parts["test"]),
  "split_hashes_sha256":hashes,
  "group_disjointness":report,
  "admitted_into_any_flagship":False,
  "training_performed":False,
  "published_provider_revision":None,
  "raw_genomic_sequences":0,"partner_lab_records":0,"patient_records":0,
  "third_party_text_training_rows":0,
  "status":"CURATED_SOURCE_ONLY_UNEVALUATED",
  "notes":"Private eval copies not published; public generator code allows reconstructive sampling and therefore does not establish a secret blind test. Separate prospective sealed evaluation required for flagship admission.",
 }
 raw=canonical(manifest)
 hashes["manifest"]=atomic_new(public_dir/"manifest.json",raw)
 print(json.dumps({"status":"BUILT_OFFLINE", "manifest_sha256":hashes["manifest"],
                   "counts":report["counts"],"group_overlap":report["semantic_group_overlap"]},sort_keys=True))
 return manifest

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--public-dir",type=Path,required=True)
 p.add_argument("--private-dir",type=Path,required=True)
 args=p.parse_args()
 try:build(args.public_dir,args.private_dir)
 except Exception as e:
  print(json.dumps({"status":"REFUSED","reason":type(e).__name__+":"+str(e)}))
  raise SystemExit(3)

if __name__=="__main__":main()
