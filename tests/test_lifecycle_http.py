"""HTTP verification of source-bound PubMed editorial notices and version groups."""
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import json,threading,tempfile,unittest
from muhu.core import build
from muhu.server import create_handler

class LifecycleHttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory()
  r=Path(cls.temp.name)
  build(r/"public",r/"private")
  cls.server=ThreadingHTTPServer(("127.0.0.1",0),create_handler(r/"public"))
  cls.port=cls.server.server_address[1]
  cls.worker=threading.Thread(target=cls.server.serve_forever,daemon=True)
  cls.worker.start()
 @classmethod
 def tearDownClass(cls):
  cls.server.shutdown();cls.server.server_close();cls.worker.join(3)
  cls.temp.cleanup()
 def req(self,path,method="GET",host=None):
  cn=HTTPConnection("127.0.0.1",self.port,timeout=6)
  cn.request(method,path,headers={"Host":host or f"127.0.0.1:{self.port}"})
  rs=cn.getresponse();res=rs.status,rs.read();cn.close();return res

 def test_editorial_home_disclaims_retraction_clearance(self):
  code,body=self.req("/lifecycle")
  self.assertEqual(code,200)
  self.assertIn(b"Scientific papers evolve",body)
  self.assertIn(b"NOT certified clean",body)
  self.assertIn(b"Distinct observed version groups",body)
  self.assertNotIn(b"<script",body.lower())

 def test_summary_is_bounded_and_source_bound(self):
  code,raw=self.req("/api/v1/lifecycle")
  self.assertEqual(code,200)
  doc=json.loads(raw)
  self.assertEqual(doc["selected_publications"],23)
  self.assertEqual(doc["version_group_count"],22)
  self.assertEqual(doc["linked_version_pairs"],[["39257798","41431865"]])
  self.assertEqual(doc["editorial_index_category_counts"]["PREPRINT_WITH_VERSION_UPDATE_LINK"],3)
  self.assertTrue(doc["absence_of_editorial_notice_not_a_clear_status"])
  self.assertEqual(doc["clinical_qualification"],"DENIED")

 def test_preprint_with_linked_update_is_highlighted(self):
  code,raw=self.req("/api/v1/lifecycle/source?pmid=39257798")
  self.assertEqual(code,200)
  obj=json.loads(raw)
  self.assertEqual(obj["publication"]["editorial_index_state"],"PREPRINT_WITH_VERSION_UPDATE_LINK")
  self.assertEqual(obj["version_group"]["selected_pmids"],["39257798","41431865"])
  self.assertTrue(obj["editorial_notice_absence_does_not_prove_clean_status"])
  self.assertEqual(obj["scientific_claim_validity"],"NOT_ASSESSED")
  code,html=self.req("/lifecycle?pmid=39257798")
  self.assertEqual(code,200)
  self.assertIn(b"UpdateIn",html)
  self.assertIn(b"41431865",html)

 def test_preprint_info_attaches_to_paper_peer_review_hold(self):
  code,raw=self.req("/api/v1/claim-gate?pmid=39257798&claim_type=paper_peer_review")
  self.assertEqual(code,200)
  obj=json.loads(raw)
  self.assertEqual(obj["state"],"HOLD_UNREVIEWED_SCIENTIFIC_CLAIM")
  editorial=obj["source_editorial_history"]
  self.assertEqual(editorial["editorial_index_state"],"PREPRINT_WITH_VERSION_UPDATE_LINK")
  self.assertIn("41431865",editorial["selected_version_group_members"])
  self.assertTrue(any("do not assume peer review" in x for x in obj["requirements_not_verified"]))
  self.assertTrue(any("not count linked preprint" in x for x in obj["requirements_not_verified"]))

 def test_no_notice_observed_does_not_clear_original_paper(self):
  code,raw=self.req("/api/v1/claim-gate?pmid=42422765&claim_type=therapy_effectiveness")
  self.assertEqual(code,200)
  obj=json.loads(raw)
  self.assertEqual(obj["state"],"HOLD_UNREVIEWED_SCIENTIFIC_CLAIM")
  self.assertEqual(obj["source_editorial_history"]["editorial_index_state"],
   "NO_TRACKED_EDITORIAL_LINK_OBSERVED_NOT_VERIFIED_CLEAR")
  self.assertTrue(obj["absence_of_editorial_notice_is_not_clearance"])
  self.assertFalse(obj["scientific_claim_supported"])

 def test_matrix_reports_not_23_independent_studies(self):
  code,raw=self.req("/api/v1/claim-matrix")
  self.assertEqual(code,200)
  obj=json.loads(raw)
  self.assertEqual(obj["combinations_checked"],207)
  self.assertEqual(obj["version_disjointness"]["version_groups_in_selected_sample"],22)
  self.assertEqual(obj["version_disjointness"]["linked_preprint_update_pairs_in_selected_sample"],1)
  self.assertEqual(obj["scientific_or_clinical_claims_admitted"],0)

 def test_unknown_and_unsafe_requests_do_not_fetch_or_clear(self):
  code,raw=self.req("/api/v1/lifecycle/source?pmid=99999999")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(raw)["state"],"UNAVAILABLE_NOT_IN_23_SELECTED_PMIDS")
  for uri in (
     "/api/v1/lifecycle/source",
     "/api/v1/lifecycle/source?pmid=abc",
     "/api/v1/lifecycle/source?pmid=42422765&pmid=42422765",
     "/api/v1/lifecycle/source?url=https%3A%2F%2Fevil.invalid",
     "/lifecycle?pmid=42422765&gene=BRCA1",
  ):
   with self.subTest(uri=uri):
    self.assertEqual(self.req(uri)[0],400)

 def test_readonly_and_existing_failed_scientific_gate(self):
  self.assertEqual(self.req("/lifecycle",method="POST")[0],405)
  self.assertEqual(self.req("/api/v1/lifecycle",method="DELETE")[0],405)
  self.assertEqual(self.req("/lifecycle",host="malicious.invalid")[0],403)
  self.assertEqual(self.req("/readyz")[0],503)
  self.assertEqual(self.req("/graph")[0],200)
  self.assertEqual(self.req("/claim-gate")[0],200)
  code,data=self.req("/api/v1/v3-results")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(data)["quality_gate"],"FAILED_HOLD")

if __name__=="__main__":unittest.main()
