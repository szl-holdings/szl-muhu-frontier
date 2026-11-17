import json
from pathlib import Path
import tempfile
import unittest
from research.muhu_v3.curriculum import build,canon
from research.muhu_v3.verify import verify_public

class PublicationTests(unittest.TestCase):
 def test_replay_and_unsafe_state_refused(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   build(root/"public",root/"private")
   result=verify_public(root/"public")
   self.assertEqual(result["rows"]["train"],672)
   self.assertEqual(result["rows"]["validation"],60)
   self.assertEqual(result["rows"]["test"],96)
   self.assertFalse(result["flagship_training_admitted"])
   self.assertFalse(result["biomedical_qualification"])
   pub=root/"public"
   manifest=json.loads((pub/"manifest.json").read_text("utf-8"))
   manifest["flagship_admitted"]=True
   (pub/"manifest.json").write_bytes(canon(manifest))
   with self.assertRaisesRegex(ValueError,"UNAUTHORIZED_ADMISSION_CLAIM"):
    verify_public(pub)
 def test_tampered_train_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   build(root/"public",root/"private")
   p=root/"public"/"train.jsonl"
   p.write_bytes(p.read_bytes()+b"tampering")
   with self.assertRaisesRegex(ValueError,"PUBLIC_TRAIN_CONTENT_MISMATCH"):
    verify_public(root/"public")
 def test_private_test_publication_refused(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   build(root/"public",root/"private")
   (root/"public"/"test.jsonl").write_text("{}\n",encoding="utf-8")
   with self.assertRaisesRegex(ValueError,"PRIVATE_EVALUATION_PUBLISHED"):
    verify_public(root/"public")

if __name__=="__main__":unittest.main()
