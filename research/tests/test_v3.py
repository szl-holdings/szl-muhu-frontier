"""Predeclared MUHU v3 source, split, and negative controls."""
from collections import Counter
from pathlib import Path
import json
import tempfile
import unittest
from muhu.core import status_of as independent_prior_oracle
from research.muhu_v3.curriculum import (
    SCHEMA,TARGETS,GROUPS_PER_CLASS,TEMPLATES,assigned_groups,
    build,canon,digest,encode_rows,generated,group_key,verify
)

class V3DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds,cls.skipped=generated()

    def test_all_four_labels_balanced_in_every_partition(self):
        info=verify(self.ds)
        for split,rows in self.ds.items():
            frequencies=Counter(row["target_state"] for row in rows)
            self.assertEqual(set(frequencies),set(TARGETS))
            self.assertEqual(len(set(frequencies.values())),1)
            self.assertEqual(frequencies[TARGETS[0]],
                GROUPS_PER_CLASS[split]*len(TEMPLATES[split]))
        self.assertEqual(info["condition_group_leakage"],0)

    def test_no_model_facing_label_or_id_leak(self):
        for records in self.ds.values():
            for row in records:
                self.assertNotIn(row["target_state"],row["input"])
                self.assertNotIn(row["id"],row["input"])
                self.assertTrue(row["synthetic"])
                self.assertEqual(row["messages"][1]["role"],"user")
                self.assertEqual(row["messages"][-1]["content"],row["output"])

    def test_independent_v2_rule_agreement(self):
        for rows in self.ds.values():
            for row in rows:
                self.assertEqual(row["target_state"], independent_prior_oracle(row["oracle_inputs"]))

    def test_semantic_group_disjointness(self):
        groups={split:{row["semantic_group_sha256"] for row in records}
                for split,records in self.ds.items()}
        for first in groups:
            for second in groups:
                if first!=second:
                    self.assertFalse(groups[first] & groups[second])

    def test_cross_split_mutation_blocks(self):
        bad={k:[dict(row) for row in val] for k,val in self.ds.items()}
        altered=dict(bad["train"][0]);altered["id"]="injected-cross-split"
        altered["split"]="test"
        bad["test"].append(altered)
        with self.assertRaisesRegex(ValueError,"SEMANTIC_GROUP_LEAKAGE"):
            verify(bad)

    def test_label_mutation_blocks(self):
        bad={k:[dict(row) for row in val] for k,val in self.ds.items()}
        bad["validation"][0]["target_state"]="REVIEWABLE" if bad["validation"][0]["target_state"]!="REVIEWABLE" else "STALE"
        with self.assertRaisesRegex(ValueError,"INVALID_ORACLE_LABEL"):
            verify(bad)

    def test_build_is_exclusive_and_eval_not_public(self):
        with tempfile.TemporaryDirectory() as tmp:
            public=Path(tmp)/"public"
            private=Path(tmp)/"private"
            result=build(public,private)
            manifest=result["dataset_manifest"]
            self.assertEqual(manifest["condition_group_overlap"],0)
            self.assertFalse(manifest["flagship_admitted"])
            self.assertTrue(manifest["train_only_public"])
            self.assertFalse((public/"test.jsonl").exists())
            self.assertFalse((public/"validation.jsonl").exists())
            for s in ("train","validation","test"):
                path=(public if s=="train" else private)/(s+".jsonl")
                self.assertEqual(digest(path.read_bytes()),manifest["sha256"][s])
            with self.assertRaisesRegex(RuntimeError,"REFUSE_EXISTING_GENERATION"):
                build(public,private)

    def test_replay_source_hash_stable(self):
        once=generated()[0]
        again=generated()[0]
        for split in once:
            self.assertEqual(encode_rows(once[split]),encode_rows(again[split]))

    def test_private_eval_source_kind(self):
        self.assertEqual(self.skipped["REVIEWABLE"],0)
        self.assertEqual(self.skipped["STALE"],0)
        self.assertGreater(self.skipped["BLOCKED"],0)
        for split,rows in self.ds.items():
            for row in rows:
                self.assertNotIn("WWOX",row["input"])
                self.assertNotIn("patient",row["input"].lower())
                self.assertEqual(row["rights"]["license"],"CC-BY-4.0")

if __name__=="__main__":
    unittest.main()
