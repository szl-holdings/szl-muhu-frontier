"""Read-only x402 v2 PAYMENT-REQUIRED challenge shape checker.

Supports Cloudflare Monetization Gateway's documented v2 header only.
This module never signs, validates wallet ownership, pays, settles,
refunds, accesses a facilitator, or trusts PAYMENT-CONTEXT. A valid
base64-encoded challenge is not a sale or proof of authorization.
"""
from __future__ import annotations

import base64
import binascii
import json
import re
from typing import Mapping
from urllib.parse import urlsplit

SCHEMA = "szl.muhu.x402_challenge_structure.v1"
MAX_HEADER_BYTES = 16384
MAX_OPTIONS = 12
NETWORK = re.compile(r"[A-Za-z0-9-]{1,32}:[A-Za-z0-9-]{1,100}\Z")
AMOUNT = re.compile(r"(?:0|[1-9][0-9]{0,11})\Z")
WALLET = re.compile(r"0x[a-fA-F0-9]{40}\Z")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _no_nonfinite(value: str):
    raise ValueError("NONFINITE_JSON_NUMBER_NOT_ALLOWED")


def inspect_challenge(
    status: int,
    headers: Mapping[str, str],
    *,
    expected_host: str,
) -> dict:
    """Inspect structure only; no secrets or payment credentials read."""
    if not isinstance(status, int) or type(status) is bool or not 100 <= status <= 599:
        raise ValueError("INVALID_HTTP_STATUS")
    if not isinstance(expected_host, str) or not re.fullmatch(
        r"[A-Za-z0-9.-]{1,253}", expected_host
    ):
        raise ValueError("UNSAFE_EXPECTED_HOST")
    if not isinstance(headers, Mapping):
        raise ValueError("INVALID_HEADERS")
    result = {
        "schema": SCHEMA,
        "http_status": status,
        "origin_host": expected_host.lower(),
        "has_confirmed_settlement": False,
        "payment_signed": False,
        "jwt_origin_context_verified": False,
        "revenue_confirmed": False,
        "scientific_or_clinical_qualification": False,
    }
    # Do not print or parse PAYMENT-SIGNATURE, PAYMENT-CONTEXT,
    # cookies, bearer tokens or sensitive request headers.
    if status != 402:
        return {**result, "state": "NOT_A_PAYMENT_CHALLENGE", "v2_structure_valid": False}
    offered = [value for key, value in headers.items() if key.lower() == "payment-required"]
    if len(offered) != 1 or type(offered[0]) is not str or not offered[0]:
        return {**result, "state": "INVALID_OR_MISSING_V2_PAYMENT_REQUIRED_HEADER",
                "v2_structure_valid": False}
    encoded = offered[0]
    if len(encoded) > MAX_HEADER_BYTES or not encoded.isascii():
        return {**result, "state": "INVALID_V2_HEADER_BOUNDS", "v2_structure_valid": False}
    try:
        payload = base64.b64decode(encoded, validate=True)
        if len(payload) > MAX_HEADER_BYTES:
            raise ValueError("DECODED_TOO_LARGE")
        obj = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_pairs,
            parse_constant=_no_nonfinite,
        )
        if not isinstance(obj, dict) or type(obj.get("x402Version")) is not int or obj["x402Version"] != 2:
            raise ValueError("REQUIRES_X402_V2")
        res = obj.get("resource")
        if not isinstance(res, dict) or not isinstance(res.get("url"), str):
            raise ValueError("RESOURCE_MISSING")
        uri = urlsplit(res["url"])
        if (uri.scheme != "https" or uri.hostname != expected_host.lower()
                or uri.username or uri.password or uri.fragment):
            raise ValueError("UNEXPECTED_RESOURCE_ORIGIN")
        offered_options = obj.get("accepts")
        if not isinstance(offered_options, list) or not 1 <= len(offered_options) <= MAX_OPTIONS:
            raise ValueError("PAYMENT_OPTIONS_MISSING")
        options = []
        for opt in offered_options:
            if not isinstance(opt, dict):
                raise ValueError("PAYMENT_OPTION_NOT_OBJECT")
            scheme = opt.get("scheme")
            network = opt.get("network")
            amount = opt.get("amount")
            wallet = opt.get("payTo")
            asset = opt.get("asset")
            timeout = opt.get("maxTimeoutSeconds")
            if scheme not in ("exact", "upto") or type(scheme) is not str:
                raise ValueError("UNSUPPORTED_PAYMENT_SCHEME")
            if not isinstance(network, str) or not NETWORK.fullmatch(network):
                raise ValueError("NETWORK_NOT_CAIP_2")
            if not isinstance(asset, str) or not 1 <= len(asset) <= 300:
                raise ValueError("ASSET_MISSING")
            if not isinstance(amount, str) or not AMOUNT.fullmatch(amount):
                raise ValueError("ATOMIC_AMOUNT_NOT_CANONICAL_STRING")
            # Cloudflare Monetization Gateway fixed-price range for USDC 6 decimals:
            if not 1000 <= int(amount) <= 100000000:
                raise ValueError("AMOUNT_OUTSIDE_MONETIZATION_RULE_RANGE")
            if not isinstance(wallet, str) or not WALLET.fullmatch(wallet):
                raise ValueError("PAY_TO_MISSING_OR_NOT_ETHEREUM_ADDRESS")
            if type(timeout) is not int or not 1 <= timeout <= 86400:
                raise ValueError("INVALID_TIMEOUT")
            options.append({
                "scheme": scheme, "network": network,
                "amount_atomic": amount, "asset_identifier_present": True,
                "receiving_wallet_present": True,
                "max_timeout_seconds": timeout,
            })
    except (ValueError, binascii.Error, UnicodeError, TypeError, OverflowError):
        return {**result, "state": "INVALID_V2_CHALLENGE_STRUCTURE",
                "v2_structure_valid": False}
    return {
        **result,
        "state": "VALID_V2_CHALLENGE_STRUCTURE_ONLY",
        "v2_structure_valid": True,
        "resource_path": uri.path,
        "options": options,
        "payment_network_verified_on_chain": False,
        "wallet_screening_verified": False,
        "origin_jwt_signature_verified": False,
        "settlement_receipt_verified": False,
    }
