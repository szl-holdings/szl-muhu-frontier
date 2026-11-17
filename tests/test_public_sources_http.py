"""HTTP regression tests for pinned public-source verification.

No runtime NCBI requests, no patient upload, no unbounded source crawl.
"""
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import json
import tempfile
import threading
import unittest
from urllib.parse import quote

from muhu.core import build
from muhu.server import create_handler

class PubmedApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        dest=Path(cls.temp.name)
        build(dest/"public",dest/"private")
        cls.server=ThreadingHTTPServer(("127.0.0.1",0),create_handler(dest/"public"))
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(3)
        cls.temp.cleanup()

    def read(self,path,method="GET",host=None):
        conn=HTTPConnection("127.0.0.1",self.port,timeout=5)
        conn.request(method,path,headers={"Host":host or f"127.0.0.1:{self.port}"})
        res=conn.getresponse()
        response=res.status,res.read()
        conn.close()
        return response

    def test_sources_page_renders_only_bibliographic_citations(self):
        code,raw=self.read("/sources")
        self.assertEqual(code,200)
        self.assertIn(b"From declared source to indexed citation",raw)
        self.assertIn(b"19 indexed public records",raw)
        self.assertIn(b"BIBLIOGRAPHIC METADATA ONLY",raw)
        self.assertNotIn(b"<script",raw)

    def test_source_list_api_is_bounded(self):
        code,raw=self.read("/api/v1/sources")
        self.assertEqual(code,200)
        obj=json.loads(raw)
        self.assertEqual(len(obj["items"]),19)
        self.assertEqual(obj["summary"]["scientific_claim_validity"],"NOT_ASSESSED")

    def test_wwoX_pmid_and_doi_match(self):
        path="/api/v1/source?pmid=42422765&doi=10.1016%2Fj.omta.2026.201791"
        code,raw=self.read(path)
        self.assertEqual(code,200)
        obj=json.loads(raw)
        self.assertEqual(obj["state"],"BIBLIOGRAPHIC_IDENTITY_MATCH_AT_CAPTURE")
        self.assertEqual(obj["metadata"]["pmid"],"42422765")
        self.assertIs(obj["external_signed_attestation"],False)

    def test_mismatch_returns_conflict_not_claim(self):
        code,raw=self.read("/api/v1/source?pmid=42422765&doi=10.9999%2Fwrong")
        self.assertEqual(code,200)
        self.assertEqual(json.loads(raw)["state"],"DOI_IDENTITY_CONFLICT_AT_CAPTURE")

    def test_unknown_pmid_does_not_imply_absence(self):
        code,raw=self.read("/api/v1/source?pmid=99999999")
        self.assertEqual(code,200)
        self.assertTrue(json.loads(raw)["does_not_mean_pubmed_record_absent"])

    def test_bad_request_no_url_fetch(self):
        for path in ("/api/v1/source","/api/v1/source?pmid=abc",
                     "/api/v1/source?pmid=42422765&pmid=42422765",
                     "/api/v1/source?pmid=42422765&url=http%3A%2F%2Fevil.invalid",
                     "/sources?doi=10.1%2Fabc"):
            with self.subTest(path=path):
                self.assertEqual(self.read(path)[0],400)

    def test_readiness_and_writes_remain_denied(self):
        self.assertEqual(self.read("/readyz")[0],503)
        self.assertEqual(self.read("/api/v1/source?pmid=42422765",method="POST")[0],405)
        self.assertEqual(self.read("/sources",method="DELETE")[0],405)
        self.assertEqual(self.read("/sources",host="untrusted.invalid")[0],403)

    def test_existing_witness_and_v3_remain_available(self):
        self.assertEqual(self.read("/witness")[0],200)
        self.assertEqual(self.read("/v3")[0],200)
        self.assertEqual(self.read("/api/v1/witness?source_bound=true")[0],200)

if __name__=="__main__":
    unittest.main()
