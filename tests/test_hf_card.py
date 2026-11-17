"""Prevent HF Docker Space metadata format failures before provider writes."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
class HubCardTests(unittest.TestCase):
 def test_space_metadata(self):
  text=(ROOT/"README.md").read_text(encoding="utf-8")
  self.assertTrue(text.startswith("---\n"))
  front=text.split("---",2)[1]
  fields={}
  for line in front.splitlines():
   if ":" in line and not line.lstrip().startswith("-"):
    k,v=line.split(":",1)
    fields[k.strip()]=v.strip()
  self.assertEqual(fields.get("sdk"),"docker")
  self.assertEqual(fields.get("app_port"),"7860")
  self.assertEqual(fields.get("license"),"mit")
  short=fields.get("short_description","")
  self.assertGreater(len(short),10)
  self.assertLessEqual(len(short),60)
  self.assertNotIn("clinical claims",short.lower())
 def test_dataset_card_metadata_and_privacy(self):
  p=ROOT/"dataset"
  text=(p/"README.md").read_text(encoding="utf-8")
  self.assertTrue(text.startswith("---\n"))
  self.assertIn("license: cc-by-4.0",text)
  self.assertTrue((p/"train.jsonl").is_file())
  self.assertFalse((p/"test.jsonl").exists())
  self.assertFalse((p/"validation.jsonl").exists())

if __name__=="__main__":unittest.main()
