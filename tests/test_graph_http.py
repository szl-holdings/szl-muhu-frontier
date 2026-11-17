"""MUHU provenance graph end-to-end HTTP gates; no live PubMed lookups."""
import http.client,json,threading,tempfile,unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from muhu.core import build
from muhu.server import create_handler

class GraphHttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory()
  root=Path(cls.tmp.name)
  build(root/"public",root/"private")
  cls.server=ThreadingHTTPServer(("127.0.0.1",0),create_handler(root/"public"))
  cls.port=cls.server.server_address[1]
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
  cls.thread.start()
 @classmethod
 def tearDownClass(cls):
  cls.server.shutdown();cls.server.server_close();cls.thread.join(3)
  cls.tmp.cleanup()
 def req(self,path,method="GET",host=None):
  conn=http.client.HTTPConnection("127.0.0.1",self.port,timeout=5)
  conn.request(method,path,headers={"Host":host or f"127.0.0.1:{self.port}"})
  r=conn.getresponse();res=(r.status,r.read());conn.close();return res
 def test_topic_scopes_remain_bounded(self):
  for topic,num in (("all",23),("sara",4),("vidal",7),("wwox",9),("worm_methods",3)):
   with self.subTest(topic=topic):
    code,raw=self.req("/api/v1/graph?topic="+topic)
    self.assertEqual(code,200)
    val=json.loads(raw)
    self.assertEqual(val["selected_publications"],num)
    self.assertFalse(val["clinical_qualification"])
    self.assertEqual(val["knowledge_level"],"BIBLIOGRAPHIC_METADATA_ONLY")
    self.assertGreater(len(val["edges"]),num)
 def test_source_lineages(self):
  code,raw=self.req("/api/v1/graph/source?pmid=40627371")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(raw)["publication"]["query_scope"],["sara"])
  code,raw=self.req("/api/v1/graph/source?pmid=41431865")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(raw)["publication"]["query_scope"],["vidal"])
 def test_html_graph_renders_and_is_not_3d(self):
  code,raw=self.req("/graph?topic=sara")
  self.assertEqual(code,200)
  self.assertIn(b"PMID 40627371",raw)
  self.assertIn(b"Two-dimensional SVG",raw)
  self.assertIn(b"research-only",raw.lower())
  self.assertNotIn(b"<script",raw.lower())
 def test_title_search_can_find_and_abstain(self):
  code,raw=self.req("/api/v1/graph/search?q=AncestryGeni")
  self.assertEqual(code,200)
  obj=json.loads(raw)
  self.assertEqual(obj["results"][0]["pmid"],"40627371")
  self.assertEqual(obj["scientific_validity"],"NOT_EVALUATED")
  code,raw=self.req("/api/v1/graph/search?q=impossiblyunlikelyword")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(raw)["state"],"ABSTAIN_NO_SELECTED_TITLE_MATCH")
  self.assertEqual(self.req("/graph?topic=all&q=locomotion")[0],200)
 def test_unknown_pmids_do_not_imply_absence(self):
  code,raw=self.req("/api/v1/graph/source?pmid=99999999")
  self.assertEqual(code,200)
  obj=json.loads(raw)
  self.assertEqual(obj["state"],"UNAVAILABLE_NOT_IN_SELECTED_RESEARCH_SNAPSHOTS")
  self.assertTrue(obj["publication_may_exist_elsewhere"])
 def test_malformed_and_untrusted_queries_fail(self):
  for route in (
    "/graph?topic=biology_works",
    "/api/v1/graph?topic=invalid",
    "/api/v1/graph?topic=wwox&topic=wwox",
    "/api/v1/graph?any=http%3A%2F%2Fevil.invalid",
    "/api/v1/graph?topic=all&q=WWOX",
    "/api/v1/graph/source?pmid=invalid",
    "/api/v1/graph/source?url=http%3A%2F%2Fevil.invalid",
    "/api/v1/graph/search?q=%3Cscript%3E",
    "/api/v1/graph/search?q=WWOX&q=WWOX",
  ):
   with self.subTest(route=route):
    self.assertEqual(self.req(route)[0],400)
 def test_existing_research_and_mutation_gates(self):
  self.assertEqual(self.req("/readyz")[0],503)
  self.assertEqual(self.req("/api/v1/graph",method="POST")[0],405)
  self.assertEqual(self.req("/graph",method="DELETE")[0],405)
  self.assertEqual(self.req("/graph",host="untrusted.invalid")[0],403)
  self.assertEqual(self.req("/v3")[0],200)
  self.assertEqual(self.req("/witness")[0],200)
  code,raw=self.req("/api/v1/v3-results")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(raw)["quality_gate"],"FAILED_HOLD")
 def test_legacy_pubmed_page_still_19_sources(self):
  code,raw=self.req("/api/v1/sources")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(raw)["summary"]["indexed_records"],19)

if __name__=="__main__":unittest.main()
