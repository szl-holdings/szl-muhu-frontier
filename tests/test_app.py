import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from muhu.core import build
from muhu.server import create_handler, synthetic_wave_svg

class HttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory()
  p=Path(cls.temp.name)
  build(p/"public",p/"private")
  cls.server=ThreadingHTTPServer(("127.0.0.1",0),create_handler(p/"public"))
  cls.port=cls.server.server_address[1]
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
  cls.thread.start()
 @classmethod
 def tearDownClass(cls):
  cls.server.shutdown();cls.server.server_close();cls.thread.join(2)
  cls.temp.cleanup()
 def query(self,path,method="GET",host=None):
  cn=http.client.HTTPConnection("127.0.0.1",self.port,timeout=3)
  cn.request(method,path,headers={"Host":host or "127.0.0.1:"+str(self.port)})
  r=cn.getresponse();code=r.status;body=r.read();cn.close()
  return code,body
 def test_health_is_not_ready(self):
  code,raw=self.query("/healthz")
  self.assertEqual(code,200)
  self.assertIs(json.loads(raw)["scientifically_qualified"],False)
 def test_readyz_refuses(self):
  code,raw=self.query("/readyz")
  self.assertEqual(code,503)
  self.assertEqual(json.loads(raw)["clinical_qualification"],"DENIED")
 def test_frontend_get(self):
  for path in ("/","/methods","/sara","/vidal","/genomics"):
   code,raw=self.query(path)
   self.assertEqual(code,200)
   self.assertIn(b"MUHU",raw)
   self.assertIn(b"RESEARCH ONLY",raw)
 def test_api_returns_public_training_only(self):
  code,raw=self.query("/api/v1/manifest")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(raw)["schema"],"szl.muhu.dataset_manifest.v2")
  code,raw=self.query("/api/v1/example?i=0")
  self.assertEqual(code,200)
  self.assertEqual(json.loads(raw)["split"],"train")
 def test_mutations_rejected(self):
  for m in ("POST","PUT","DELETE","PATCH"):
   self.assertEqual(self.query("/",method=m)[0],405)
 def test_foreign_host_rejected(self):
  self.assertEqual(self.query("/",host="attacker.example.com")[0],403)
 def test_unknown_api_error(self):
  self.assertEqual(self.query("/missing")[0],404)
 def test_bad_queries(self):
  self.assertEqual(self.query("/api/v1/example?i=999")[0],400)
  self.assertEqual(self.query("/api/v1/example?i=none")[0],400)
  self.assertEqual(self.query("/api/v1/example?evil=x")[0],400)
 def test_synthetic_svg_clear_limits(self):
  svg=synthetic_wave_svg()
  self.assertIn("SYNTHETIC SIGNALS ONLY",svg)
  self.assertNotIn("<script",svg)

if __name__=="__main__":unittest.main()
