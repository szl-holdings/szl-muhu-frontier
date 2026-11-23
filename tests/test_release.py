from pathlib import Path
import json
import tempfile
import unittest
from muhu.core import build,canonical
from muhu.verify import validate

class PublicationTests(unittest.TestCase):
 def test_admitted_public_only(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)
   build(p/"data",p/"private")
   r=validate(p/"data")
   self.assertGreater(r["training_rows"],0)
   self.assertEqual(r["semantic_group_overlap"],0)
   self.assertFalse(r["clinical_qualified"])
   self.assertFalse((p/"data"/"test.jsonl").exists())
 def test_mutated_training_data_refused(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)
   build(p/"data",p/"private")
   path=p/"data"/"train.jsonl"
   path.write_bytes(path.read_bytes()+b"\n")
   with self.assertRaisesRegex(ValueError,"PUBLIC_TRAIN_BYTES_CHANGED"):
    validate(p/"data")
 def test_ambiguous_manifest_json_refused(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)
   build(p/"data",p/"private")
   path=p/"data"/"manifest.json"
   original=path.read_text("utf-8")
   self.assertIn('"split_hashes_sha256":{',original)
   cases={
    "duplicate_root":original.rstrip()[:-1]+',"admitted_into_any_flagship":false}',
    "duplicate_nested":original.replace('"split_hashes_sha256":{','"split_hashes_sha256":{"train":"ambiguous",',1),
    "nan":original.rstrip()[:-1]+',"extra":NaN}',
    "positive_infinity":original.rstrip()[:-1]+',"extra":Infinity}',
    "negative_infinity":original.rstrip()[:-1]+',"extra":-Infinity}',
   }
   for label,payload in cases.items():
    with self.subTest(label=label):
     path.write_text(payload,encoding="utf-8")
     with self.assertRaisesRegex(ValueError,"AMBIGUOUS_MANIFEST_JSON"):
      validate(p/"data")
   path.write_text(original,encoding="utf-8")
   self.assertEqual(validate(p/"data")["state"],"OFFLINE_SOURCE_BOUND_TRAINING_DATA_VERIFIED")
 def test_false_flagship_admission_refused(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)
   build(p/"data",p/"private")
   path=p/"data"/"manifest.json"
   obj=json.loads(path.read_bytes())
   obj["admitted_into_any_flagship"]=True
   path.write_bytes(canonical(obj))
   with self.assertRaisesRegex(ValueError,"UNAUTHORIZED_PROMOTION"):
    validate(p/"data")

if __name__=="__main__":unittest.main()
