"""No-payment, no-network x402 v2 challenge contract negative controls."""
import base64
import json
import unittest

from muhu.x402 import inspect_challenge


def encode(payload):
    return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")


def example():
    return {
        "x402Version": 2,
        "resource": {
            "url": "https://a-11-oy.com/api/premium/research",
            "description": "Fictional premium metadata",
            "mimeType": "application/json",
        },
        "accepts": [
            {
                "scheme": "exact", "network": "eip155:8453",
                "asset": "0x" + ("a" * 40),
                "amount": "25000",
                "payTo": "0x" + ("b" * 40),
                "maxTimeoutSeconds": 3600, "extra": {},
            }
        ],
    }


class X402StructureTests(unittest.TestCase):
    def inspect(self, data, status=402, host="a-11-oy.com"):
        return inspect_challenge(
            status, {"PAYMENT-REQUIRED": encode(data)}, expected_host=host
        )

    def test_valid_v2_is_not_a_settlement(self):
        result = self.inspect(example())
        self.assertEqual(result["state"], "VALID_V2_CHALLENGE_STRUCTURE_ONLY")
        self.assertEqual(result["options"][0]["amount_atomic"], "25000")
        self.assertFalse(result["has_confirmed_settlement"])
        self.assertFalse(result["jwt_origin_context_verified"])
        self.assertFalse(result["payment_signed"])
        self.assertFalse(result["revenue_confirmed"])

    def test_non_402_does_not_imply_paid(self):
        r = self.inspect(example(), status=200)
        self.assertEqual(r["state"], "NOT_A_PAYMENT_CHALLENGE")
        self.assertFalse(r["revenue_confirmed"])

    def test_missing_header_fail_closed(self):
        data = inspect_challenge(402, {}, expected_host="a-11-oy.com")
        self.assertFalse(data["v2_structure_valid"])

    def test_legacy_v1_rejected(self):
        data = example()
        data["x402Version"] = 1
        self.assertFalse(self.inspect(data)["v2_structure_valid"])

    def test_wrong_host_rejected(self):
        self.assertFalse(self.inspect(example(), host="attacker.example")["v2_structure_valid"])

    def test_numeric_amount_rejected(self):
        data = example()
        data["accepts"][0]["amount"] = 25000
        self.assertFalse(self.inspect(data)["v2_structure_valid"])

    def test_noncanonical_amount_rejected(self):
        for amount in ("025000", "-1", "2.5", "0", "99999999999"):
            data = example()
            data["accepts"][0]["amount"] = amount
            self.assertFalse(self.inspect(data)["v2_structure_valid"])

    def test_legacy_network_not_caip_rejected(self):
        data = example()
        data["accepts"][0]["network"] = "base"
        self.assertFalse(self.inspect(data)["v2_structure_valid"])

    def test_receiving_wallet_required(self):
        data = example()
        data["accepts"][0]["payTo"] = ""
        self.assertFalse(self.inspect(data)["v2_structure_valid"])

    def test_signed_request_header_not_interpreted_as_payment(self):
        obj = example()
        result = inspect_challenge(402, {
            "PAYMENT-REQUIRED": encode(obj),
            "PAYMENT-SIGNATURE": "not-a-payment-token",
            "PAYMENT-CONTEXT": "fake-jwt-must-never-be-trusted",
        }, expected_host="a-11-oy.com")
        self.assertFalse(result["payment_signed"])
        self.assertFalse(result["origin_jwt_signature_verified"])
        self.assertNotIn("not-a-payment-token", json.dumps(result))

    def test_empty_accepts_rejected(self):
        data = example()
        data["accepts"] = []
        self.assertFalse(self.inspect(data)["v2_structure_valid"])

    def test_duplicate_json_fields_rejected(self):
        raw = '{"x402Version":2,"x402Version":2}'
        encoded = base64.b64encode(raw.encode()).decode()
        result = inspect_challenge(402, {"PAYMENT-REQUIRED": encoded},
                                   expected_host="a-11-oy.com")
        self.assertFalse(result["v2_structure_valid"])

    def test_bad_base64_rejected(self):
        result = inspect_challenge(402, {"payment-required": "!!not-base64!!"},
                                   expected_host="a-11-oy.com")
        self.assertFalse(result["v2_structure_valid"])

    def test_bounded_header_size(self):
        result = inspect_challenge(402, {"payment-required": "A" * 100000},
                                   expected_host="a-11-oy.com")
        self.assertEqual(result["state"], "INVALID_V2_HEADER_BOUNDS")


if __name__ == "__main__":
    unittest.main()
