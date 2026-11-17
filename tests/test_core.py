"""MUHU data integrity and falsification fixtures. Offline; no private lab data."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from muhu.core import (
 CASE_FIELDS,TARGETS,SCHEMA,build,canonical,enumerate_groups,generate,
 partition,render,sha256_bytes,status_of,verify_splits
)

class RulebookTests(unittest.TestCase):
 def fixed(self,**changes):
  f=dict(source_bound=True,sample_n=32,age_days=2,independent_check=True,contradiction=False)
  f.update(changes)
  return f
 def test_reviewable_not_validated(self):
  self.assertEqual(status_of(self.fixed()),"REVIEWABLE")
 def test_absent_source_blocks(self):
  self.assertEqual(status_of(self.fixed(source_bound=False)),"BLOCKED")
 def test_empty_denominator_blocks(self):
  self.assertEqual(status_of(self.fixed(sample_n=0)),"BLOCKED")
 def test_missing_independent_check_blocks(self):
  self.assertEqual(status_of(self.fixed(independent_check=False)),"BLOCKED")
 def test_conflict_before_staleness(self):
  self.assertEqual(status_of(self.fixed(age_days=21,contradiction=True)),"CONFLICT")
 def test_block_before_conflict(self):
  self.assertEqual(status_of(self.fixed(sample_n=0,contradiction=True)),"BLOCKED")
 def test_stale_more_than_seven_days(self):
  self.assertEqual(status_of(self.fixed(age_days=8)),"STALE")
 def test_7_days_is_current_under_policy(self):
  self.assertEqual(status_of(self.fixed(age_days=7)),"REVIEWABLE")
 def test_negative_values_refuse(self):
  for f in (self.fixed(sample_n=-1),self.fixed(age_days=-2),self.fixed(age_days=401)):
   with self.assertRaises(ValueError):status_of(f)
 def test_bool_not_valid_int(self):
  for f in (self.fixed(sample_n=True),self.fixed(age_days=False)):
   with self.assertRaises(ValueError):status_of(f)
 def test_no_extra_features(self):
  with self.assertRaises(ValueError):status_of(self.fixed(patient_record="x"))
 def test_generated_groups_are_separated(self):
  cases=generate();v=verify_splits(cases)
  self.assertEqual(v["semantic_group_overlap"],0)
  self.assertEqual(v["unique_groups"],len(enumerate_groups()))
  self.assertGreater(v["counts"]["train"],0)
  self.assertGreater(v["counts"]["validation"],0)
  self.assertGreater(v["counts"]["test"],0)
 def test_no_third_party_patient_or_genomic_inputs(self):
  cases=generate()
  for rows in cases.values():
   for row in rows:
    self.assertTrue(row["synthetic"])
    self.assertEqual(row["task"],"synthetic_evidence_methodology")
    self.assertFalse(any(k in row for k in ("patient_record","genome","gene_editing")))
    self.assertNotIn("WWOX",row["input"])
 def test_metadata_mutation_is_detected(self):
  cases=generate()
  bad=copy.deepcopy(cases)
  bad["test"][0]["target_state"]="REVIEWABLE" if bad["test"][0]["target_state"]!="REVIEWABLE" else "STALE"
  with self.assertRaisesRegex(ValueError,"ORACLE_MISMATCH"):
   verify_splits(bad)
 def test_cross_split_leakage_is_detected(self):
  cases=generate()
  bad=copy.deepcopy(cases)
  row=copy.deepcopy(bad["train"][0])
  row["split"]="test";row["id"]="cross-contamination"
  bad["test"].append(row)
  with self.assertRaises(ValueError):verify_splits(bad)
 def test_training_chat_format(self):
  row=generate()["train"][0]
  self.assertEqual([m["role"] for m in row["messages"]],["system","user","assistant"])
  self.assertEqual(row["messages"][-1]["content"],row["output"])
  self.assertEqual(row["messages"][1]["content"],row["input"])
 def test_atomic_source_readback(self):
  with tempfile.TemporaryDirectory() as tmp:
   public=Path(tmp)/"public"
   private=Path(tmp)/"private"
   manifest=build(public,private)
   self.assertEqual(manifest["admitted_into_any_flagship"],False)
   self.assertTrue((public/"train.jsonl").is_file())
   self.assertFalse((public/"test.jsonl").exists())
   self.assertFalse((public/"validation.jsonl").exists())
   for split in ("test","validation"):
    self.assertTrue((private/(split+".jsonl")).exists())
   self.assertEqual(sha256_bytes((private/"test.jsonl").read_bytes()),manifest["split_hashes_sha256"]["test"])
   with self.assertRaises(ValueError):build(public,private)
 def test_canonical_determinism(self):
  a=generate();b=generate()
  for split in a:
   self.assertEqual([canonical(x) for x in a[split]],[canonical(x) for x in b[split]])

if __name__=="__main__":unittest.main()
