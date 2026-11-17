"""Exact-byte source boundary on Windows and Linux, without invoking git."""
import hashlib
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
HASHES={
    "dataset/v3/train.jsonl":"b5cacc3ef1fa365b56a37af4cbabc600fc169565d83a4c0f2edc00f0520ddcdc",
    "dataset/v3/manifest.json":"e25dcc429ede01f959da538667aa570300203e3226853d38a20be5000d4c7441",
    "research/muhu_v3/public_results.json":"1de7f605b564ea88918702b551513385fde6680d4e49d74d6bf5c360dd930e87",
}
class ByteParityTests(unittest.TestCase):
    def test_released_source_bytes_unchanged(self):
        for filename,expected in HASHES.items():
            with self.subTest(path=filename):
                source=(ROOT/filename).read_bytes()
                self.assertNotIn(b"\r\n",source,
                                 "Checkout line-endings must be LF on all operating systems")
                self.assertEqual(hashlib.sha256(source).hexdigest(),expected)

    def test_source_code_and_cards_are_lf(self):
        for rel in ("muhu/server.py","README.md","dataset/v3/README.md"):
            with self.subTest(path=rel):
                self.assertNotIn(b"\r\n",(ROOT/rel).read_bytes())

    def test_repository_line_ending_contract(self):
        g=(ROOT/".gitattributes").read_text(encoding="utf-8")
        for ext in ("*.py","*.json","*.jsonl","*.md","*.yml"):
            self.assertIn(ext+" text eol=lf",g)

if __name__=="__main__":
    unittest.main()
