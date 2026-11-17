"""Pinned public release-readiness snapshot, not a live revenue or CI feed.

The public proof page never turns an observed HTTP 200, 402 challenge,
wheel build, or GitHub green check into a settlement, signed artifact,
clinical clearance or model training admission.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

SCHEMA = "szl.muhu.public_release_status.v1"
PINNED_SHA256 = "c71d45e016c3f4673a4b8860972a69a6f6094bc6b62d17c0fdf6d706b1ad89f9"


def load(path: Path) -> dict:
    raw = Path(path).read_bytes()
    if sha256(raw).hexdigest() != PINNED_SHA256:
        raise ValueError("PUBLIC_PROOF_SOURCE_BYTES_CHANGED")
    try:
        obj = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("PUBLIC_PROOF_JSON_INVALID") from exc
    if obj.get("schema") != SCHEMA:
        raise ValueError("PUBLIC_PROOF_SCHEMA_UNREVIEWED")
    if obj.get("snapshot_kind") != "HISTORICAL_SOURCED_OBSERVATIONS_NOT_LIVE_POLLING":
        raise ValueError("FALSE_LIVE_UPDATE_CLAIM")
    scientific = obj["scientific"]
    distribution = obj["distribution"]
    revenue = obj["monetization"]
    gates = obj["release_admission"]
    if scientific.get("model_state") != "FAILED_HOLD":
        raise ValueError("MODEL_HOLD_LOST")
    if scientific.get("independent_expert_benchmark") != "NOT_PERFORMED":
        raise ValueError("INDEPENDENT_EVAL_FALSIFIED")
    if scientific.get("flagship_training_admitted") is not False:
        raise ValueError("FLAGSHIP_ADMISSION_FALSIFIED")
    if distribution.get("publication_state") != "UNPUBLISHED_AT_OBSERVATION":
        raise ValueError("UNVERIFIED_PYPI_PUBLICATION")
    if distribution.get("pypi_http_at_observation") != 404:
        raise ValueError("PYPI_SOURCE_SNAPSHOT_NOT_MATCHED")
    if revenue.get("facilitator_settlement") != "NOT_VERIFIED":
        raise ValueError("FALSE_PAYMENT_SETTLEMENT")
    if revenue.get("verified_revenue_usd") is not None:
        raise ValueError("UNVERIFIED_REVENUE_CLAIM")
    if revenue.get("revenue_claim_authorized") is not False:
        raise ValueError("UNVERIFIED_REVENUE_AUTHORITY")
    if gates.get("all_layers_operational") is not False:
        raise ValueError("FALSE_END_TO_END_PRODUCTION_CLAIM")
    if gates.get("scientific_production_qualified") is not False:
        raise ValueError("FALSE_SCIENTIFIC_PRODUCTION_CLAIM")
    if obj["research_preview"].get("qualification") != "RESEARCH_PREVIEW_ONLY":
        raise ValueError("FALSE_HF_PRODUCTION_CLAIM")
    if obj["research_dataset"].get("contents") != "ORIGINAL_SYNTHETIC_TRAIN_ONLY":
        raise ValueError("PRIVATE_DATA_CLAIM_UNVERIFIED")
    return obj


def public_api(document: dict) -> dict:
    if document.get("schema") != SCHEMA:
        raise ValueError("UNADMITTED_RELEASE_DOCUMENT")
    return {
        **document,
        "snapshot_sha256": PINNED_SHA256,
        "status_is_live": False,
        "payment_settlement_proven": False,
        "clinical_or_scientific_ready": False,
        "signed_attestation": False,
    }
