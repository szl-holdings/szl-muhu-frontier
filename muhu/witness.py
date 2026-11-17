"""MUHU WITNESS v1 — transparent, deterministic research-metadata gate.

Inputs are five bounded *synthetic* metadata fields. No free text, biology,
patient records, genetic sequences, experimental claims, or private uploads.
This is NOT independent scientific validation or a machine-learning model.

The SHA-256 digest is an integrity checksum over the canonical witness, not
a digital signature, scientific attestation, or source authentication.
"""
from __future__ import annotations

from hashlib import sha256
import json
from urllib.parse import parse_qs

from .core import status_of

SCHEMA = "szl.muhu.method_witness.v1"
VERSION = "muhu-method-witness-20261117"
FIELDS = ("source_bound","sample_n","age_days","independent_check","contradiction")
BOOL_FIELDS = ("source_bound","independent_check","contradiction")
INT_FIELDS = ("sample_n","age_days")
DEMO = {
    "source_bound":True, "sample_n":32, "age_days":2,
    "independent_check":True, "contradiction":False,
}
CONSTRAINTS = {
    "sample_n":{"minimum":0,"maximum":1000},
    "age_days":{"minimum":0,"maximum":365},
}
STATE_LIMITATIONS = {
    "BLOCKED":"Missing required provenance, nonzero denominator, or external check. No scientific inference.",
    "CONFLICT":"An opposing report exists; independent adjudication is required.",
    "STALE":"Evidence age exceeds seven days; revalidation required.",
    "REVIEWABLE":"Administrative metadata is sufficient for human review; no scientific or clinical validity inferred.",
}

def canonical(obj:object)->bytes:
    return (json.dumps(obj,sort_keys=True,ensure_ascii=True,separators=(",",":"))+"\n").encode("utf-8")

def source_type(value):
    if type(value) is bool:
        return value
    raise ValueError("BOOLEAN_REQUIRED")

def typed_factors(items:dict)->dict:
    if set(items)!=set(FIELDS):
        raise ValueError("EXACT_FIVE_FIELDS_REQUIRED")
    out={}
    for field in BOOL_FIELDS:
        out[field]=source_type(items[field])
    for field in INT_FIELDS:
        val=items[field]
        if type(val) is not int:
            raise ValueError("STRICT_INTEGER_REQUIRED")
        if not CONSTRAINTS[field]["minimum"]<=val<=CONSTRAINTS[field]["maximum"]:
            raise ValueError("INTEGER_OUT_OF_RANGE")
        out[field]=val
    return out

def decode_query(text:str, *, allow_missing:bool=True)->dict|None:
    if not isinstance(text,str) or len(text)>240:
        raise ValueError("QUERY_TOO_LONG")
    try:
        query=parse_qs(text,keep_blank_values=True,max_num_fields=6,strict_parsing=True)
    except ValueError:
        raise ValueError("BAD_QUERY_STRING") from None
    if set(query)-set(FIELDS):
        raise ValueError("UNEXPECTED_QUERY_FIELD")
    if any(len(val)!=1 for val in query.values()):
        raise ValueError("DUPLICATE_QUERY_FIELD")
    if set(query)!=set(FIELDS):
        if allow_missing:return None
        raise ValueError("MISSING_QUERY_FIELD")
    out={}
    for name in FIELDS:
        value=query[name][0]
        if name in BOOL_FIELDS:
            if value not in ("true","false"):raise ValueError("BAD_BOOLEAN_VALUE")
            out[name]=value=="true"
        else:
            if not value.isascii() or not value.isdecimal() or len(value)>4:
                raise ValueError("BAD_NUMERIC_VALUE")
            out[name]=int(value)
    return typed_factors(out)

def needed_evidence(facts:dict, state:str)->list[str]:
    required=[]
    if not facts["source_bound"]:
        required.append("Identify a verifiable original source; do not invent a citation")
    if facts["sample_n"]==0:
        required.append("Supply an actually observed nonzero denominator; do not fabricate counts")
    if not facts["independent_check"]:
        required.append("Obtain an independent check and record its provenance")
    if facts["contradiction"]:
        required.append("Retain both contradictory assertions and obtain human adjudication")
    if facts["age_days"]>7:
        required.append("Recheck the source and record the fresh observation timestamp")
    if state=="REVIEWABLE":
        required.append("Request qualified independent scientific assessment before making any domain claim")
    return required

def gate(factors:dict)->dict:
    f=typed_factors(factors)
    state=status_of(f)
    checks=[
        {"id":"source_cited","passed":f["source_bound"],
         "observation":"Source pointer claimed present" if f["source_bound"] else "Source pointer missing"},
        {"id":"measured_nonempty","passed":f["sample_n"]>0,
         "observation":"Nonzero reported count" if f["sample_n"]>0 else "Zero denominator"},
        {"id":"independently_checked","passed":f["independent_check"],
         "observation":"External check claimed present" if f["independent_check"] else "External check missing"},
        {"id":"not_contradicted","passed":not f["contradiction"],
         "observation":"No conflict claimed" if not f["contradiction"] else "Contrary evidence reported"},
        {"id":"fresh_under_policy","passed":f["age_days"]<=7,
         "observation":"Last verified within seven days" if f["age_days"]<=7 else "More than seven days old"},
    ]
    # The classification above is the sole canonical oracle, independent
    # of this explanatory trace (which may be checked by separate tests).
    body={
        "schema":SCHEMA,
        "version":VERSION,
        "state":state,
        "inputs":f,
        "checks":checks,
        "required_evidence":needed_evidence(f,state),
        "limitation":STATE_LIMITATIONS[state],
        "model_trained":False,
        "scientific_validity":"NOT_ASSESSED",
        "clinical_safety":"NOT_ASSESSED",
        "provider_source_verified":False,
        "method":"Deterministic five-field synthetic metadata rule, no AI inference",
        "checksum_is_signature":False,
    }
    return {**body,"witness_sha256":sha256(canonical(body)).hexdigest()}

def unavailable(missing:set[str])->dict:
    if not missing or not missing.issubset(set(FIELDS)):
        raise ValueError("INVALID_MISSING_FIELD_SET")
    return {
        "schema":SCHEMA,"state":"UNAVAILABLE","missing_fields":sorted(missing),
        "required_evidence":["Provide the five explicitly typed fields to classify a synthetic record"],
        "scientific_validity":"NOT_ASSESSED",
        "clinical_safety":"NOT_ASSESSED",
        "verified":False,"no_inference":True,
    }

def witness_query(text:str,*,demo_if_empty:bool=False)->dict:
    if text=="" and demo_if_empty:
        result=gate(DEMO)
        result["fixture_mode"]="ORIGINAL_SYNTHETIC_DEMONSTRATION"
        return result
    if not isinstance(text,str) or len(text)>240:raise ValueError("QUERY_TOO_LONG")
    try:raw=parse_qs(text,keep_blank_values=True,max_num_fields=6,strict_parsing=True)
    except ValueError:raise ValueError("BAD_QUERY_STRING") from None
    if set(raw)-set(FIELDS):raise ValueError("UNKNOWN_FIELD")
    if any(len(v)!=1 for v in raw.values()):raise ValueError("DUPLICATE_FIELD")
    missing=set(FIELDS)-set(raw)
    if missing:return unavailable(missing)
    parsed=decode_query(text,allow_missing=False)
    assert parsed is not None
    return gate(parsed)
