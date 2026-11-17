"""Independent MUHU Claim Evidence Firewall regression and false-promotion tests."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import unittest

from muhu.claim_firewall import (
 CLAIM_CLASSES,SCHEMA,POLICY,adjudicate,canonical,matrix,
 parse_request,rulebook,
)
from muhu.provenance_graph import build_from_paths,source_path_for_pmid

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"research"/"public_sources"

class ClaimFirewallTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.graph=build_from_paths(SOURCE/"pubmed-sources-admitted-20261117.json",
                             SOURCE/"sara-pubmed-sources-20261117.json")

 def ask(self,pmid="42422765",claim_type="therapy_effectiveness",doi="10.1016/j.omta.2026.201791"):
  return adjudicate(self.graph,pmid=pmid,claim_type=claim_type,doi=doi)

 def test_good_citation_matches_only_bibliography(self):
  result=self.ask(claim_type="citation_identity")
  self.assertEqual(result["state"],"BIBLIOGRAPHIC_IDENTITY_MATCH_ONLY")
  self.assertEqual(result["source_provenance"]["doi_comparison"],"MATCH")
  self.assertTrue(result["source_provenance"]["source_observed_utc"].startswith("2026-11-17T"))
  self.assertFalse(result["scientific_claim_supported"])
  self.assertFalse(result["clinical_claim_supported"])
  self.assertEqual(result["independent_expert_adjudication"],"NOT_PERFORMED")
  self.assertIs(result["not_authorized_training_data"],True)

 def test_therapy_claim_not_proven_by_metadata(self):
  obj=self.ask()
  self.assertEqual(obj["state"],"HOLD_UNREVIEWED_SCIENTIFIC_CLAIM")
  self.assertIn("SCIENTIFIC_CONTENT_ABSENT",obj["reason_codes"])
  self.assertGreater(len(obj["requirements_not_verified"]),2)
  self.assertFalse(obj["scientific_claim_supported"])
  self.assertTrue(obj["source_provenance"]["observation_time_is_historical"])

 def test_all_23_times_nine_never_promote_science(self):
  m=matrix(self.graph)
  self.assertEqual(m["combinations_checked"],23*len(CLAIM_CLASSES))
  self.assertEqual(m["selected_papers"],23)
  self.assertEqual(m["scientific_or_clinical_claims_admitted"],0)
  for typ,counts in m["status_by_claim_type"].items():
   self.assertEqual(sum(counts.values()),23)
   if typ!="citation_identity":
    self.assertFalse("BIBLIOGRAPHIC_IDENTITY_MATCH_ONLY" in counts)

 def test_identical_source_but_clinical_person_decision_denied(self):
  obj=self.ask(claim_type="patient_treatment_recommendation")
  self.assertEqual(obj["state"],"DENY_CLINICAL_DECISION")
  self.assertIn("CLINICAL_SCOPE_DENIED",obj["reason_codes"])

 def test_gene_level_and_variant_level_distinct(self):
  gene=self.ask(claim_type="gene_disease_causality")
  variant=self.ask(claim_type="variant_pathogenicity")
  self.assertEqual(gene["state"],"HOLD_UNREVIEWED_SCIENTIFIC_CLAIM")
  self.assertEqual(variant["state"],"HOLD_UNREVIEWED_SCIENTIFIC_CLAIM")
  self.assertNotEqual(gene["required_evidence_tier"],variant["required_evidence_tier"])
  self.assertNotEqual(gene["requirements_not_verified"],variant["requirements_not_verified"])

 def test_cross_study_paper_author_and_reproducibility_are_not_equivalent(self):
  for claim in ("paper_peer_review","author_endorsement","laboratory_reproducibility",
                "cross_study_mechanism"):
   with self.subTest(claim=claim):
    got=self.ask(claim_type=claim)
    self.assertNotEqual(got["state"],"BIBLIOGRAPHIC_IDENTITY_MATCH_ONLY")
    self.assertFalse(got["scientific_claim_supported"])

 def test_author_index_is_not_endorsement(self):
  obj=self.ask(pmid="40627371",claim_type="author_endorsement",doi=None)
  self.assertEqual(obj["state"],"HOLD_NOT_AUTHORIZED")
  self.assertEqual(obj["source_provenance"]["pmid"],"40627371")
  self.assertEqual(obj["source_provenance"]["doi_comparison"],"NOT_SUPPLIED")

 def test_conflicting_doi_preempts_citation_and_therapy(self):
  for claim in ("citation_identity","therapy_effectiveness","patient_treatment_recommendation"):
   with self.subTest(claim=claim):
    result=self.ask(claim_type=claim,doi="10.1000/not-the-real-doi")
    self.assertEqual(result["state"],"CONFLICTING_SOURCE_IDENTIFIER")
    self.assertEqual(result["source_provenance"]["doi_comparison"],"MISMATCH")
    self.assertIn("DOI_MISMATCH",result["reason_codes"])

 def test_sampled_list_absence_does_not_claim_pubmed_absence(self):
  obj=self.ask(pmid="99999999",claim_type="gene_disease_causality",doi=None)
  self.assertEqual(obj["state"],"UNAVAILABLE_SOURCE_NOT_SAMPLED")
  self.assertEqual(obj["source_provenance"]["provider"],"NOT_IN_SELECTED_INDEX")
  self.assertIn("NOT_SAMPLED",obj["reason_codes"])
  self.assertIsNone(obj["source_provenance"]["pubmed_uri"])

 def test_integrity_receipt_is_not_a_signature(self):
  obj=self.ask()
  rec=obj.pop("receipt_sha256")
  self.assertEqual(rec,sha256(canonical(obj)).hexdigest())
  self.assertEqual(len(rec),64)
  rule=rulebook()
  self.assertIs(rule["signed_external_attestation"],False)
  self.assertIs(rule["model_trained"],False)

 def test_never_accepts_external_patient_or_free_text_field(self):
  for query in (
   "pmid=42422765&claim_type=therapy_effectiveness&patient_name=Alex",
   "pmid=42422765&claim_type=gene_disease_causality&source=http%3A%2F%2Fevil.invalid",
   "pmid=42422765&claim_type=citation_identity&prompt=Make+it+true",
   "pmid=42422765&claim_type=therapy_effectiveness&clinical_note=secret"
  ):
   with self.subTest(query=query):
    with self.assertRaises(ValueError):parse_request(query)

 def test_missing_invalid_duplicate_are_errors(self):
  for query in (
    "","pmid=42422765","claim_type=therapy_effectiveness",
    "pmid=abc&claim_type=citation_identity",
    "pmid=42422765&pmid=42422765&claim_type=citation_identity",
    "pmid=42422765&claim_type=unbounded_new_science",
    "pmid=42422765&claim_type=therapy_effectiveness&doi=http%3A%2F%2Fevil.invalid",
    "pmid=42422765&claim_type=therapy_effectiveness&doi=%0A10.1000%2Ftest"
  ):
   with self.subTest(query=query):
    with self.assertRaises(ValueError):parse_request(query)

 def test_missing_doi_comparison_is_explicit_not_inferred(self):
  out=self.ask(claim_type="citation_identity",doi=None)
  self.assertEqual(out["state"],"BIBLIOGRAPHIC_PMID_INDEXED_AT_SNAPSHOT")
  self.assertEqual(out["source_provenance"]["doi_comparison"],"NOT_SUPPLIED")

 def test_correct_doi_and_source_is_not_a_reproduction(self):
  for n in [n for n in self.graph["nodes"] if n["kind"]=="publication"]:
   result=adjudicate(self.graph,pmid=n["pmid"],
                     claim_type="laboratory_reproducibility",doi=n["doi"])
   self.assertFalse(result["scientific_claim_supported"])
   self.assertNotEqual(result["state"],"BIBLIOGRAPHIC_IDENTITY_MATCH_ONLY")

 def test_forged_direct_library_graph_cannot_approve_citation(self):
  forged=deepcopy(self.graph)
  target=next(n for n in forged["nodes"] if n["kind"]=="publication")
  target["label"]="Proven human gene therapy"
  with self.assertRaisesRegex(ValueError,"GRAPH_SOURCE_CONTENT_TAMPERED"):
   adjudicate(forged,pmid="42422765",claim_type="citation_identity")

if __name__=="__main__":unittest.main()
