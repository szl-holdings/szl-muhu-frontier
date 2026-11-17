"""MUHU Claim Evidence Firewall v1: bounded, deterministic, source-grounded.

Converts a PMID / optional DOI plus an enumerated claim class into an
explainable evidence-admission decision. This system contains ONLY public
bibliographic metadata: no abstracts, full-text findings, biological
measurements, patient records, or claimed efficacy.

A citation identity match CANNOT admit a scientific/clinical claim.
It has no write side effects and no incoming free-text claim field.
"""
from __future__ import annotations
from hashlib import sha256
from urllib.parse import parse_qs
import json

from .provenance_graph import (
    PMID_PATTERN,DOI_PATTERN,GRAPH_SCHEMA,source_path_for_pmid,validate_graph,
)

SCHEMA="szl.muhu.claim_evidence_firewall.v1"
POLICY="muhu-epistemic-firewall-20261117"
CLAIM_CLASSES={
    "citation_identity":{
        "name":"PMID / reported DOI bibliographic identity",
        "level":"INDEXED_BIBLIOGRAPHIC_METADATA",
        "requirements":(),
    },
    "paper_peer_review":{
        "name":"Paper is peer-reviewed",
        "level":"PUBLICATION_PROCESS",
        "requirements":(
            "Verify publication venue, article version, and independently documented editorial status",
            "Resolve preprint / journal / conference version and retraction status at use time",
        ),
    },
    "author_endorsement":{
        "name":"Researcher endorses this interpretation or collaboration",
        "level":"PERSONAL_APPROVAL",
        "requirements":(
            "Obtain explicit direct authorization from the named researcher",
            "Disambiguate author identity against authoritative institutional or ORCID records",
        ),
    },
    "gene_disease_causality":{
        "name":"A gene causally explains a disease",
        "level":"BIOMEDICAL_CAUSAL_CLAIM",
        "requirements":(
            "Review rights-cleared primary genetic and experimental evidence",
            "Review independent curated gene-disease validity and conflicting findings",
            "Document inheritance mechanism, relevant phenotype, and independent expert evaluation",
        ),
    },
    "variant_pathogenicity":{
        "name":"A particular genetic variant is pathogenic",
        "level":"PATIENT_RELEVANT_VARIANT_CLAIM",
        "requirements":(
            "Normalize allele and genome build against authorized variant evidence",
            "Evaluate independent variant-level submissions, review status and conflicting interpretations",
            "Require qualified clinical review; a gene-level assertion does not classify a variant",
        ),
    },
    "therapy_effectiveness":{
        "name":"Gene therapy is effective in humans",
        "level":"INTERVENTIONAL_HUMAN_OUTCOME_CLAIM",
        "requirements":(
            "Review protocol-defined human outcomes, adverse events and comparator evidence",
            "Distinguish animal/organoid experiments from appropriately evaluated human evidence",
            "Require independent clinical and regulatory evaluation for the precise indication",
        ),
    },
    "laboratory_reproducibility":{
        "name":"A reported experiment is independently reproducible",
        "level":"EXPERIMENTAL_VALIDITY_CLAIM",
        "requirements":(
            "Obtain rights-cleared experimental methods, recorded instrument conditions and sample denominators",
            "Require authorized independent blinded reruns and source-bound raw measurements",
            "Document negative controls, staleness, failure cases and unproved handoff fields",
        ),
    },
    "cross_study_mechanism":{
        "name":"Two papers prove a shared biological mechanism",
        "level":"CROSS_SOURCE_MECHANISTIC_CLAIM",
        "requirements":(
            "Independently extract the exact mechanistic assertions from reviewed primary sources",
            "Verify shared biological entities, experimental system, context, comparators and intervention",
            "Adjudicate contradictory or noncomparable methods; citation graph edges are not causal edges",
        ),
    },
    "patient_treatment_recommendation":{
        "name":"Recommend a particular medical treatment for a person",
        "level":"PERSONALIZED_CLINICAL_CLAIM",
        "requirements":(
            "No treatment recommendations are provided by this experimental research platform",
            "Seek an appropriately qualified medical team for individual clinical decisions",
        ),
    },
}
EVIDENCE_LEVELS={
    "BIBLIOGRAPHIC":"Official public citation metadata, exact selected PMID and source snapshot",
    "SCIENTIFIC_CONTENT":"Source text, experimental methods and claim-specific results, NOT INGESTED",
    "INDEPENDENT_REPLICATION":"Blinded expert reruns and independent adjudication, NOT OBSERVED",
    "CLINICAL":"Human clinical/therapeutic assessment and authorization, NOT EVALUATED",
}
REASON_CODES={
    "NOT_SAMPLED":"The PMID is not one of the 23 selected public citations; absence is not implied.",
    "DOI_NOT_REPORTED":"This selected record has no DOI in the stored PubMed metadata.",
    "DOI_MISMATCH":"The supplied DOI does not match this selected PubMed metadata.",
    "SOURCE_METADATA_MATCH":"The PMID and reported DOI are consistent in the pinned source snapshot, not at request time.",
    "SOURCE_METADATA_PRESENT":"The PMID was included in a pinned PubMed selection; no DOI comparison requested.",
    "SCIENTIFIC_CONTENT_ABSENT":"Citation title, journal, DOI and date cannot establish the claimed experimental, mechanistic or clinical conclusion.",
    "AUTHORIZATION_ABSENT":"Author name string does not establish endorsement, permission, identity, or collaboration.",
    "CLINICAL_SCOPE_DENIED":"This research preview cannot provide individualized care recommendations.",
}

def canonical(obj:object)->bytes:
    return (json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n").encode("utf-8")

def _sha(obj:object)->str:
    return sha256(canonical(obj)).hexdigest()

def parse_request(qs:str)->dict:
    if not isinstance(qs,str) or len(qs)>350:
        raise ValueError("QUERY_LENGTH_LIMIT")
    try:
        args=parse_qs(qs,strict_parsing=True,keep_blank_values=True,max_num_fields=4)
    except ValueError:
        raise ValueError("MALFORMED_QUERY") from None
    if set(args)-{"pmid","claim_type","doi"}:
        raise ValueError("UNSUPPORTED_FREE_TEXT_QUERY")
    if any(len(value)!=1 for value in args.values()):
        raise ValueError("DUPLICATED_QUERY_KEY")
    if "pmid" not in args or "claim_type" not in args:
        raise ValueError("PMID_AND_CLAIM_TYPE_REQUIRED")
    pmid=args["pmid"][0]
    claim_type=args["claim_type"][0]
    if not isinstance(pmid,str) or not PMID_PATTERN.fullmatch(pmid):
        raise ValueError("INVALID_PMID")
    if claim_type not in CLAIM_CLASSES:
        raise ValueError("UNSUPPORTED_CLAIM_CLASS")
    doi=args.get("doi",[None])[0]
    if doi is not None and (not isinstance(doi,str) or not DOI_PATTERN.fullmatch(doi)):
        raise ValueError("INVALID_EXPECTED_DOI")
    return {"pmid":pmid,"claim_type":claim_type,"doi":doi}

def rulebook()->dict:
    return {
        "schema":"szl.muhu.claim_firewall_rulebook.v1",
        "policy_version":POLICY,
        "supported_claim_classes":[
            {"id":key,**CLAIM_CLASSES[key]} for key in CLAIM_CLASSES
        ],
        "epistemic_tiers":EVIDENCE_LEVELS,
        "permitted_positive_status":"ONLY BIBLIOGRAPHIC SOURCE IDENTITY",
        "biological_and_clinical_claim_admitted":False,
        "source_absence_falsely_claimed":False,
        "signed_external_attestation":False,
        "model_trained":False,
    }

def adjudicate(graph:dict,*,pmid:str,claim_type:str,doi:str|None=None)->dict:
    if claim_type not in CLAIM_CLASSES:
        raise ValueError("UNSUPPORTED_CLAIM_CLASS")
    if not isinstance(pmid,str) or not PMID_PATTERN.fullmatch(pmid):
        raise ValueError("INVALID_PMID")
    if doi is not None and (not isinstance(doi,str) or not DOI_PATTERN.fullmatch(doi)):
        raise ValueError("INVALID_DOI")
    if graph.get("schema")!=GRAPH_SCHEMA or graph.get("graph_sha256") is None:
        raise ValueError("SOURCE_GRAPH_NOT_VERIFIED")
    # Also verify the graph has not been modified since its exact-source
    # digest and allowed edge structure were reviewed.
    validate_graph(graph)
    # Graph always built from exact SHA-pinned approved PubMed sources at
    # server startup. Runtime performs no network calls.
    trace=source_path_for_pmid(graph,pmid)
    requirements=list(CLAIM_CLASSES[claim_type]["requirements"])
    input_vals={"pmid":pmid,"claim_type":claim_type,"doi":doi}
    known=trace["state"]=="BIBLIOGRAPHIC_SOURCE_PATH_OBSERVED_AT_SNAPSHOT"
    provider_status="SELECTED_PUBMED_INDEX_ONLY" if known else "NOT_IN_SELECTED_INDEX"
    recorded_doi=trace["publication"].get("doi") if known else None
    source_sha=trace["publication"]["snapshot_sha256"] if known else None
    observed_candidates=[
        n.get("observed_utc") for n in graph["nodes"]
        if n["kind"]=="snapshot" and n.get("sha256")==source_sha
    ] if known else []
    if known and (len(observed_candidates)!=1 or not observed_candidates[0]):
        raise ValueError("HISTORICAL_SOURCE_OBSERVATION_MISSING")
    observed_utc=observed_candidates[0] if known else None
    if not known:
        state="UNAVAILABLE_SOURCE_NOT_SAMPLED"
        reasons=["NOT_SAMPLED"]
        requirements.insert(0,"Locate and independently verify the exact relevant primary source")
    elif doi is not None and recorded_doi is None:
        state="UNAVAILABLE_DOI_NOT_REPORTED"
        reasons=["DOI_NOT_REPORTED"]
        requirements.insert(0,"Verify the authoritative DOI and publication version independently")
    elif doi is not None and recorded_doi.casefold()!=doi.casefold():
        state="CONFLICTING_SOURCE_IDENTIFIER"
        reasons=["DOI_MISMATCH"]
        requirements.insert(0,"Resolve the mismatch against NCBI, Crossref/publisher and article version before use")
    elif claim_type=="citation_identity":
        state=("BIBLIOGRAPHIC_IDENTITY_MATCH_ONLY" if doi is not None
               else "BIBLIOGRAPHIC_PMID_INDEXED_AT_SNAPSHOT")
        reasons=["SOURCE_METADATA_MATCH"] if doi is not None else ["SOURCE_METADATA_PRESENT"]
    elif claim_type=="author_endorsement":
        state="HOLD_NOT_AUTHORIZED"
        reasons=["AUTHORIZATION_ABSENT"]
    elif claim_type=="patient_treatment_recommendation":
        state="DENY_CLINICAL_DECISION"
        reasons=["CLINICAL_SCOPE_DENIED"]
    else:
        state="HOLD_UNREVIEWED_SCIENTIFIC_CLAIM"
        reasons=["SCIENTIFIC_CONTENT_ABSENT"]
    body={
        "schema":SCHEMA,"policy_version":POLICY,
        "input":input_vals,"state":state,
        "reason_codes":reasons,
        "reasons":[REASON_CODES[code] for code in reasons],
        "requirements_not_verified":requirements,
        "source_provenance":{
            "provider":provider_status,
            "graph_sha256":graph["graph_sha256"],
            "pmid":pmid,
            "pubmed_uri":f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if known else None,
            "source_snapshot_sha256":source_sha,
            "source_observed_utc":observed_utc,
            "recorded_doi":recorded_doi,
            "doi_comparison":"MATCH" if doi is not None and known and recorded_doi is not None and doi.casefold()==recorded_doi.casefold() else
                             "MISMATCH" if doi is not None and known and recorded_doi is not None else
                             "NOT_RECORDED" if doi is not None and known else
                             "NOT_SUPPLIED" if doi is None else "SOURCE_UNAVAILABLE",
            "observation_time_is_historical":True,
        },
        "claim_type_label":CLAIM_CLASSES[claim_type]["name"],
        "required_evidence_tier":CLAIM_CLASSES[claim_type]["level"],
        "scientific_claim_supported":False,
        "clinical_claim_supported":False,
        "independent_expert_adjudication":"NOT_PERFORMED",
        "actual_provider_lookup_during_request":False,
        "no_model_execution":True,
        "not_authorized_training_data":True,
        "limited_to_public_bibliographic_identifiers":True,
        "limitation":"Source identity and paper titles do not substantiate experimental findings, causal mechanisms, clinical outcomes, or author endorsement.",
    }
    body["receipt_sha256"]=_sha(body)
    return body

def matrix(graph:dict)->dict:
    if graph.get("schema")!=GRAPH_SCHEMA:
        raise ValueError("GRAPH_SCHEMA_MISMATCH")
    validate_graph(graph)
    papers=sorted([n for n in graph["nodes"] if n["kind"]=="publication"],key=lambda n:int(n["pmid"]))
    if len(papers)!=23:raise ValueError("BIBLIOGRAPHY_CHANGED")
    # Mechanically test every selected PMID against every claim type.
    by_class={}
    for claim_type in CLAIM_CLASSES:
        decisions=CounterLike()
        for paper in papers:
            result=adjudicate(graph,pmid=paper["pmid"],claim_type=claim_type,doi=paper["doi"])
            decisions[result["state"]]+=1
            if claim_type!="citation_identity" and result["scientific_claim_supported"] is not False:
                raise ValueError("BIOLOGICAL_CLAIM_PROMOTED")
        by_class[claim_type]=dict(sorted(decisions.items()))
    return {
        "schema":"szl.muhu.claim_firewall_coverage.v1",
        "source_graph_sha256":graph["graph_sha256"],
        "selected_papers":len(papers),
        "claim_classes":len(CLAIM_CLASSES),
        "combinations_checked":len(papers)*len(CLAIM_CLASSES),
        "status_by_claim_type":by_class,
        "real_biological_outcomes_assessed":0,
        "scientific_or_clinical_claims_admitted":0,
        "actual_model_training_samples_added":0,
        "denial_and_abstention_are_policy_not_model_validation":True,
    }

class CounterLike(dict):
    def __missing__(self,key):
        return 0
