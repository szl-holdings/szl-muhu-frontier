"""Bounded MUHU Method Witness regression and adversarial tests.

Negative controls exercise actual HTTP behavior, not only Python functions.
No biomedical, collaborator or private source data is used.
"""
from hashlib import sha256
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import json
import tempfile
import threading
import unittest
from urllib.parse import urlencode

from muhu.core import build
from muhu.server import create_handler, witness_page
from muhu.witness import (
    DEMO,FIELDS,BOOL_FIELDS,canonical,decode_query,gate,unavailable,witness_query
)

def sample(**kwargs):
    out=dict(DEMO);out.update(kwargs);return out

class WitnessRules(unittest.TestCase):
    def test_reviewable_is_not_biological_evidence(self):
        obj=gate(sample())
        self.assertEqual(obj["state"],"REVIEWABLE")
        self.assertEqual(obj["scientific_validity"],"NOT_ASSESSED")
        self.assertFalse(obj["model_trained"])
        self.assertFalse(obj["checksum_is_signature"])

    def test_missing_source_is_blocked(self):
        self.assertEqual(gate(sample(source_bound=False))["state"],"BLOCKED")

    def test_empty_denominator_blocks_even_if_contradictory(self):
        out=gate(sample(sample_n=0,contradiction=True,age_days=12))
        self.assertEqual(out["state"],"BLOCKED")
        self.assertIn("nonzero denominator",out["required_evidence"][0]+out["required_evidence"][1])

    def test_independent_check_required(self):
        self.assertEqual(gate(sample(independent_check=False))["state"],"BLOCKED")

    def test_conflict_takes_precedence_over_staleness(self):
        self.assertEqual(gate(sample(contradiction=True,age_days=40))["state"],"CONFLICT")

    def test_staleness_boundary(self):
        self.assertEqual(gate(sample(age_days=7))["state"],"REVIEWABLE")
        self.assertEqual(gate(sample(age_days=8))["state"],"STALE")

    def test_unknown_or_omitted_field_fails_closed(self):
        self.assertEqual(witness_query("source_bound=true")["state"],"UNAVAILABLE")
        self.assertNotIn("inputs",witness_query("source_bound=true"))
        self.assertEqual(set(witness_query("")["missing_fields"]),set(FIELDS))
        with self.assertRaises(ValueError):gate({**DEMO,"patient":"none"})

    def test_invalid_types_and_values(self):
        for bad in (sample(sample_n=True),sample(age_days=False),
                    sample(sample_n=-1),sample(age_days=366)):
            with self.assertRaises(ValueError):gate(bad)
        fully_specified="source_bound=true&sample_n={n}&age_days=2&independent_check=true&contradiction=false"
        for query in ("sample_n=32&sample_n=40","evil=all",
                      fully_specified.format(n="-1"),
                      fully_specified.format(n="xx"),
                      "source_bound=TRUE&sample_n=3&age_days=2&independent_check=true&contradiction=false"):
            with self.assertRaises(ValueError):witness_query(query)
        self.assertEqual(witness_query("sample_n=-1")["state"],"UNAVAILABLE")

    def test_checksum_recomputed_independently(self):
        o=gate(sample())
        hash_value=o.pop("witness_sha256")
        self.assertEqual(hash_value,sha256(canonical(o)).hexdigest())
        self.assertEqual(gate(sample())["witness_sha256"],hash_value)

    def test_canonical_condition_trace(self):
        for f in (sample(),sample(source_bound=False),sample(sample_n=0),
                  sample(independent_check=False),sample(contradiction=True),
                  sample(age_days=11),sample(source_bound=False,contradiction=True)):
            out=gate(f)
            self.assertEqual(len(out["checks"]),5)
            self.assertEqual(set(out["inputs"]),set(FIELDS))
            self.assertFalse(out["provider_source_verified"])
            self.assertFalse(out["model_trained"])

    def test_no_free_text_fields_supported(self):
        with self.assertRaises(ValueError):
            witness_query("source_bound=true&sample_n=11&age_days=2&independent_check=true&contradiction=false&clinical_note=secret")

    def test_independent_exhaustive_640_synthetic_rule_table(self):
        # A separate, simple rule implementation; no call to status_of.
        from muhu.core import enumerate_groups
        groups=enumerate_groups()
        self.assertEqual(len(groups),640)
        for f in groups:
            if not f["source_bound"] or f["sample_n"]==0 or not f["independent_check"]:
                expected="BLOCKED"
            elif f["contradiction"]:
                expected="CONFLICT"
            elif f["age_days"]>7:
                expected="STALE"
            else:
                expected="REVIEWABLE"
            obj=gate(f)
            self.assertEqual(obj["state"],expected)
            self.assertEqual(obj["scientific_validity"],"NOT_ASSESSED")

class WitnessWeb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        root=Path(cls.tmp.name);build(root/"public",root/"private")
        cls.server=ThreadingHTTPServer(("127.0.0.1",0),create_handler(root/"public"))
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(3)
        cls.tmp.cleanup()
    def call(self,path,method="GET",host=None):
        conn=HTTPConnection("127.0.0.1",self.port,timeout=5)
        conn.request(method,path,headers={"Host":host or "127.0.0.1:"+str(self.port)})
        response=conn.getresponse()
        ret=(response.status,response.read())
        conn.close();return ret

    def test_sample_page(self):
        status,raw=self.call("/witness")
        self.assertEqual(status,200)
        self.assertIn(b"DEMONSTRATION ONLY",raw)
        self.assertIn(b"REVIEWABLE",raw)
        self.assertIn(b"<form",raw)
        self.assertNotIn(b"<script",raw)

    def test_api_all_states(self):
        for f in (sample(),sample(sample_n=0),sample(age_days=8),
                  sample(contradiction=True),sample(independent_check=False)):
            query=urlencode({k:str(v).lower() if k in BOOL_FIELDS else v for k,v in f.items()})
            status,raw=self.call("/api/v1/witness?"+query)
            self.assertEqual(status,200)
            expected=gate(f)
            self.assertEqual(json.loads(raw)["state"],expected["state"])
            self.assertEqual(json.loads(raw)["witness_sha256"],expected["witness_sha256"])

    def test_missing_is_unavailable_not_reviewable(self):
        status,raw=self.call("/api/v1/witness?source_bound=true")
        self.assertEqual(status,200)
        obj=json.loads(raw)
        self.assertEqual(obj["state"],"UNAVAILABLE")
        self.assertNotIn("witness_sha256",obj)

    def test_bad_query_and_host(self):
        self.assertEqual(self.call("/api/v1/witness?evil=1")[0],400)
        self.assertEqual(self.call("/api/v1/witness?sample_n=3&sample_n=7")[0],400)
        self.assertEqual(self.call("/witness",host="attacker.invalid")[0],403)

    def test_read_only_and_readiness(self):
        self.assertEqual(self.call("/api/v1/witness",method="POST")[0],405)
        self.assertEqual(self.call("/readyz")[0],503)

if __name__=="__main__":unittest.main()
