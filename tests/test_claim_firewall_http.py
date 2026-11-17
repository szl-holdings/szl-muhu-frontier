"""Source-bound MUHU Claim Firewall HTTP contract tests."""
import http.client
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile,threading,unittest
from muhu.core import build
from muhu.server import create_handler
from muhu.claim_firewall import CLAIM_CLASSES

class ClaimFirewallHttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory()
  root=Path(cls.tmp.name)
  build(root/"public",root/"private")
  cls.server=ThreadingHTTPServer(("127.0.0.1",0),create_handler(root/"public"))
  cls.port=cls.server.server_address[1]
  cls.worker=threading.Thread(target=cls.server.serve_forever,daemon=True)
  cls.worker.start()
 @classmethod
 def tearDownClass(cls):
  cls.server.shutdown();cls.server.server_close()
  cls.worker.join(3);cls.tmp.cleanup()
 def req(self,path,method="GET",host=None):
  conn=http.client.HTTPConnection("127.0.0.1",self.port,timeout=5)
  conn.request(method,path,headers={"Host":host or f"127.0.0.1:{self.port}"})
  resp=conn.getresponse()
  result=(resp.status,resp.read())
  conn.close()
  return result

 def test_initial_html_defaults_to_hold(self):
  code,body=self.req("/claim-gate")
  self.assertEqual(code,200)
  self.assertIn(b"RESEARCH-ONLY SAFETY GATE",body)
  self.assertIn(b"HOLD_UNREVIEWED_SCIENTIFIC_CLAIM",body)
  self.assertIn(b"gene therapy",body.lower())
  self.assertNotIn(b"<script",body.lower())

 def test_policy_machine_readable_is_unqualified(self):
  code,body=self.req("/api/v1/claim-policy")
  self.assertEqual(code,200)
  policy=json.loads(body)
  self.assertEqual(len(policy["supported_claim_classes"]),len(CLAIM_CLASSES))
  self.assertFalse(policy["biological_and_clinical_claim_admitted"])
  self.assertFalse(policy["model_trained"])

 def test_matrix_proves_all_bounded_source_claim_combinations(self):
  code,raw=self.req("/api/v1/claim-matrix")
  self.assertEqual(code,200)
  matrix=json.loads(raw)
  self.assertEqual(matrix["combinations_checked"],23*len(CLAIM_CLASSES))
  self.assertEqual(matrix["scientific_or_clinical_claims_admitted"],0)
  self.assertEqual(matrix["actual_model_training_samples_added"],0)

 def test_gene_therapy_context_does_not_validate_human_treatment(self):
  path="/api/v1/claim-gate?pmid=42422765&claim_type=therapy_effectiveness&doi=10.1016%2Fj.omta.2026.201791"
  code,body=self.req(path)
  self.assertEqual(code,200)
  data=json.loads(body)
  self.assertEqual(data["state"],"HOLD_UNREVIEWED_SCIENTIFIC_CLAIM")
  self.assertFalse(data["scientific_claim_supported"])
  self.assertFalse(data["clinical_claim_supported"])
  self.assertEqual(data["source_provenance"]["doi_comparison"],"MATCH")
  self.assertFalse(data["actual_provider_lookup_during_request"])

 def test_real_doi_mismatch_detected_and_held(self):
  code,body=self.req("/api/v1/claim-gate?pmid=42422765&claim_type=citation_identity&doi=10.9999%2Ffake")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(body)["state"],"CONFLICTING_SOURCE_IDENTIFIER")

 def test_unobserved_pmid_is_not_called_nonexistent(self):
  code,body=self.req("/api/v1/claim-gate?pmid=99999999&claim_type=therapy_effectiveness")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(body)["state"],"UNAVAILABLE_SOURCE_NOT_SAMPLED")

 def test_personal_medical_case_is_denied(self):
  code,body=self.req("/api/v1/claim-gate?pmid=42422765&claim_type=patient_treatment_recommendation")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(body)["state"],"DENY_CLINICAL_DECISION")

 def test_invalid_and_adversarial_requests_rejected(self):
  for path in (
   "/api/v1/claim-gate",
   "/api/v1/claim-gate?pmid=42422765",
   "/api/v1/claim-gate?pmid=42422765&claim_type=therapy_effectiveness&claim_type=therapy_effectiveness",
   "/api/v1/claim-gate?pmid=42422765&claim_type=therapy_effectiveness&patient=x",
   "/api/v1/claim-gate?pmid=42422765&claim_type=therapy_effectiveness&source=http%3A%2F%2Fevil.invalid",
   "/api/v1/claim-gate?pmid=42422765&claim_type=unlimited",
   "/api/v1/claim-gate?pmid=42422765&claim_type=therapy_effectiveness&doi=%3Cscript%3E",
   "/claim-gate?pmid=42422765"
  ):
   with self.subTest(path=path):
    self.assertEqual(self.req(path)[0],400)

 def test_original_workflows_remain_read_only_and_hold(self):
  self.assertEqual(self.req("/api/v1/claim-gate",method="POST")[0],405)
  self.assertEqual(self.req("/claim-gate",host="evil.invalid")[0],403)
  self.assertEqual(self.req("/readyz")[0],503)
  self.assertEqual(self.req("/v3")[0],200)
  self.assertEqual(self.req("/witness")[0],200)
  code,raw=self.req("/api/v1/v3-results")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(raw)["quality_gate"],"FAILED_HOLD")
  code,raw=self.req("/api/v1/graph?topic=sara")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(raw)["selected_publications"],4)

if __name__=="__main__":unittest.main()
