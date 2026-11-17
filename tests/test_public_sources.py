"""Immutable public citation snapshot and epistemic-limit regressions."""
from hashlib import sha256
from pathlib import Path
import copy
import json
import unittest

from muhu.public_sources import (
    SNAPSHOT_SHA256,ORIGINAL_CAPTURE_SHA256,RAW_ESUMMARY_SHA256,
    canonical,load_snapshot,lookup,parse_source_query,summary,validate_snapshot
)

ROOT=Path(__file__).resolve().parents[1]
SNAP=ROOT/"research"/"public_sources"/"pubmed-sources-admitted-20261117.json"

class PubmedSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=load_snapshot(SNAP)

    def test_19_verified_bibliographic_IDs_not_science(self):
        r=summary(self.source)
        self.assertEqual(r["indexed_records"],19)
        self.assertEqual(r["selected_records"],19)
        self.assertEqual(r["scientific_claim_validity"],"NOT_ASSESSED")
        self.assertIs(r["external_signed_attestation"],False)

    def test_raw_capture_and_prepared_source_hashes(self):
        raw=SNAP.read_bytes()
        self.assertEqual(sha256(raw).hexdigest(),SNAPSHOT_SHA256)
        self.assertEqual(self.source["initial_captured_snapshot_sha256"],ORIGINAL_CAPTURE_SHA256)
        self.assertEqual(self.source["upstream_provider_response_sha256"],RAW_ESUMMARY_SHA256)

    def test_wwox_record_matches_official_identifiers(self):
        record=lookup(self.source,"42422765","10.1016/j.omta.2026.201791")
        self.assertEqual(record["state"],"BIBLIOGRAPHIC_IDENTITY_MATCH_AT_CAPTURE")
        self.assertEqual(record["doi_comparison"],"MATCH")
        self.assertEqual(record["scientific_claim_validity"],"NOT_ASSESSED")
        self.assertIs(record["source_retrieval_at_request"],False)
        self.assertIn("gene therapy",record["metadata"]["title"].lower())

    def test_actual_mismatch_is_not_suppressed(self):
        r=lookup(self.source,"42422765","10.1000/example")
        self.assertEqual(r["state"],"DOI_IDENTITY_CONFLICT_AT_CAPTURE")
        self.assertEqual(r["doi_comparison"],"MISMATCH")
        self.assertNotIn("EVALUATED",r["state"])

    def test_uncaptured_record_abstains_not_absent(self):
        out=lookup(self.source,"99999999")
        self.assertEqual(out["state"],"UNAVAILABLE_NOT_IN_SAMPLED_INDEX")
        self.assertTrue(out["does_not_mean_pubmed_record_absent"])

    def test_no_transitive_preclinical_to_clinical_claim(self):
        for item in self.source["items"]:
            self.assertEqual(item["scientific_or_clinical_claim"],"NOT_ASSESSED")
            self.assertEqual(item["therapy_efficacy_or_safety"],"NOT_ASSESSED")
            self.assertEqual(item["metadata_origin"],"NCBI_PUBMED_ESUMMARY_JSON_V2")
            self.assertIn("https://pubmed.ncbi.nlm.nih.gov/",item["source_url"])

    def test_wwox_and_vidal_and_methods_scopes_are_distinct(self):
        groups={g:0 for g in self.source["search_coverage"]}
        for record in self.source["items"]:
            for group in record["query_groups"]:
                groups[group]+=1
        self.assertEqual(groups["WWOX_mechanisms_and_preclinical"],9)
        self.assertEqual(groups["Vidal_Gadea_author_index_candidates"],7)
        self.assertEqual(groups["C_elegans_motion_calcium_methods"],3)

    def test_correctly_accepts_nonbreaking_space_source_title(self):
        r=lookup(self.source,"42649163")
        self.assertEqual(r["state"],"BIBLIOGRAPHIC_PMID_INDEXED_AT_CAPTURE")
        self.assertIn("\xa0",r["metadata"]["title"])

    def test_rejects_tampered_snapshot_bytes(self):
        raw=SNAP.read_bytes()
        altered=raw.replace(b'"selected_pmid_count":19',b'"selected_pmid_count":99')
        self.assertNotEqual(raw,altered)
        with self.assertRaisesRegex(ValueError,"BYTE_IDENTITY_MISMATCH"):
            validate_snapshot(altered)

    def test_snapshot_is_not_accepted_with_untrusted_fields(self):
        obj=copy.deepcopy(self.source)
        obj["items"][0]["clinical_effectiveness"]="PROVEN"
        raw=canonical(obj)
        with self.assertRaises(ValueError):
            validate_snapshot(raw)

    def test_query_malformed_rejected(self):
        for query in ("", "pmid=", "pmid=not-a-number", "pmid=42422765&pmid=42422765",
                      "pmid=42422765&url=https%3A%2F%2Fevil.com",
                      "pmid=42422765&doi=javascript:alert(1)",
                      "pmid=42422765&doi=%0Asecret", "pmid=00000"):
            with self.subTest(query=query):
                with self.assertRaises(ValueError):
                    parse_source_query(query)

    def test_doi_query_verification(self):
        q=parse_source_query("pmid=42422765&doi=10.1016%2Fj.omta.2026.201791")
        out=lookup(self.source,**q)
        self.assertEqual(out["doi_comparison"],"MATCH")

    def test_no_private_or_full_text_field(self):
        words=json.dumps(self.source)
        for marker in ('"abstract"', '"full_text"', '"patient_record"',
                       '"genomic_sequence"', '"private_lab_data"'):
            self.assertNotIn(marker,words)

if __name__=="__main__":
    unittest.main()
