"""Investor/developer proof is source-bound and never fabricates revenue."""
from hashlib import sha256
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import json
import tempfile
import threading
import unittest

from muhu.core import build
from muhu.release_proof import PINNED_SHA256, load, public_api
from muhu.release_ui import page, source_chain_svg
from muhu.server import create_handler

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "release" / "public_proof.json"


class ReleaseProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load(PROOF)

    def test_exact_snapshot_hash(self):
        self.assertEqual(sha256(PROOF.read_bytes()).hexdigest(), PINNED_SHA256)
        self.assertEqual(self.doc["schema"], "szl.muhu.public_release_status.v1")

    def test_historical_observation_not_live_claim(self):
        data = public_api(self.doc)
        self.assertIs(data["status_is_live"], False)
        self.assertIs(data["payment_settlement_proven"], False)
        self.assertIs(data["signed_attestation"], False)

    def test_no_invented_pypi_publication_or_money(self):
        self.assertEqual(self.doc["distribution"]["publication_state"],
                         "UNPUBLISHED_AT_OBSERVATION")
        self.assertIsNone(self.doc["monetization"]["verified_revenue_usd"])
        self.assertEqual(self.doc["monetization"]["facilitator_settlement"],
                         "NOT_VERIFIED")
        self.assertIs(self.doc["release_admission"]["all_layers_operational"], False)

    def test_original_scientific_hold_remains(self):
        self.assertEqual(self.doc["scientific"]["model_state"], "FAILED_HOLD")
        self.assertFalse(self.doc["scientific"]["flagship_training_admitted"])
        self.assertFalse(self.doc["scientific"]["gene_therapy_clinical_qualification"])

    def test_attacker_mutation_of_revenue_fails(self):
        with tempfile.TemporaryDirectory() as d:
            altered = Path(d) / "status.json"
            copy = json.loads(PROOF.read_text(encoding="utf-8"))
            copy["monetization"]["verified_revenue_usd"] = 9999999
            altered.write_text(json.dumps(copy), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SOURCE_BYTES_CHANGED"):
                load(altered)

    def test_pages_do_not_mask_unverified_payment(self):
        for audience in ("investors", "developers"):
            html = page(self.doc, audience=audience)
            self.assertIn("UNPUBLISHED_AT_OBSERVATION", html)
            self.assertIn("Cloudflare", html)
            self.assertIn("FAILED_HOLD", html)
            self.assertIn("NOT", html)
            self.assertNotIn("<script", html.lower())
        with self.assertRaises(ValueError):
            page(self.doc, audience="patient")

    def test_svg_explicitly_not_settlement(self):
        svg = source_chain_svg()
        self.assertIn("SETTLEMENT UNVERIFIED", svg)
        self.assertIn("PYPI", svg)
        self.assertIn("CANONICAL SOURCE", svg)


class ReleaseProofHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        p = Path(cls.temp.name)
        build(p / "public", p / "private")
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(p / "public"))
        cls.port = cls.server.server_address[1]
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join(3)
        cls.temp.cleanup()

    def read(self, path, method="GET", host=None):
        c = HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request(method, path, headers={"Host":host or f"127.0.0.1:{self.port}"})
        r = c.getresponse()
        data = r.status, r.read()
        c.close()
        return data

    def test_investor_and_developer_pages(self):
        for route in ("/proof", "/developers"):
            status, raw = self.read(route)
            self.assertEqual(status, 200)
            self.assertIn(b"HISTORICAL RELEASE SNAPSHOT", raw)
            self.assertIn(b"SETTLEMENT UNVERIFIED", raw)

    def test_api_is_frozen_and_unqualified(self):
        status, raw = self.read("/api/v1/release-proof")
        self.assertEqual(status, 200)
        doc = json.loads(raw)
        self.assertEqual(doc["snapshot_sha256"], PINNED_SHA256)
        self.assertFalse(doc["status_is_live"])
        self.assertFalse(doc["payment_settlement_proven"])
        self.assertFalse(doc["clinical_or_scientific_ready"])

    def test_no_paywall_or_runtime_readiness_inflation(self):
        self.assertEqual(self.read("/readyz")[0], 503)
        self.assertEqual(self.read("/proof", method="POST")[0], 405)
        self.assertEqual(self.read("/api/v1/release-proof", method="PUT")[0], 405)
        self.assertEqual(self.read("/developers", host="evil.invalid")[0], 403)
        self.assertEqual(self.read("/v3")[0], 200)


if __name__ == "__main__":
    unittest.main()
