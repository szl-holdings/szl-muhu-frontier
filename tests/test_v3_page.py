"""MUHU v3 honest results page: no private examples, no clinical readiness."""
import http.client
import json
from pathlib import Path
import threading
import unittest
from http.server import ThreadingHTTPServer

from muhu.server import create_handler, ROOT

class V3ResearchSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(("127.0.0.1",0),create_handler(ROOT/"dataset"))
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def get(self,path):
        cn=http.client.HTTPConnection("127.0.0.1",self.port,timeout=4)
        cn.request("GET",path,headers={"Host":f"127.0.0.1:{self.port}"})
        response=cn.getresponse()
        code=response.status
        body=response.read()
        cn.close()
        return code,body

    def test_v3_result_page_reports_failed_gate(self):
        code,body=self.get("/v3")
        self.assertEqual(code,200)
        self.assertIn(b"MUHU v3",body)
        self.assertIn(b"QUALITY: HOLD",body)
        self.assertIn(b"Macro F1 with abstentions",body)
        self.assertIn(b"RESEARCH",body)
        self.assertNotIn(b"patient_record",body)

    def test_v3_machine_readable_public_aggregates_only(self):
        code,body=self.get("/api/v1/v3-results")
        self.assertEqual(code,200)
        report=json.loads(body)
        self.assertEqual(report["schema"],"szl.muhu.v3.public_aggregate_results.v1")
        self.assertEqual(report["test"]["n"],96)
        self.assertEqual(report["training_rows"],672)
        self.assertEqual(report["quality_gate"],"FAILED_HOLD")
        self.assertFalse(report["flagship_training_admitted"])
        self.assertEqual(report["test"]["abstentions"],48)
        self.assertNotIn("test_inputs",report)
        self.assertNotIn("full_evaluation",report)

    def test_v3_page_cannot_make_runtime_ready(self):
        code,body=self.get("/readyz")
        self.assertEqual(code,503)
        self.assertFalse(json.loads(body)["ready"])

if __name__=="__main__":
    unittest.main()
