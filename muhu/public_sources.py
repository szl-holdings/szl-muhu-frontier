"""MUHU public bibliographic provenance, independent of source-claim truth.

Local immutable, quality-gated PubMed metadata; no network from web runtime.
DOI and PMID identity matching is not a gene, paper-quality, or lab-data witness.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qs
import json
import re

SNAPSHOT_SHA256="d0bcf237127b41873e70d2a20c1e0e5666b1250b30244732af608bedff14eda6"
ORIGINAL_CAPTURE_SHA256="fd1a66b359a45e10595ea83432df597ceb4766c42868beec225b52893bb27306"
RAW_ESUMMARY_SHA256="dd332e5f349a1b198d5b59cdceee3cbe5e0f0f3ea1d151063128791df762f373"
SCHEMA="szl.muhu.pubmed_sources_admission.v1"
PMID=re.compile(r"[1-9][0-9]{4,9}\Z")
DOI=re.compile(r"10\.\d{4,9}/[^\s<>\"']{1,220}\Z",re.IGNORECASE)
TOPICS={
 "WWOX_mechanisms_and_preclinical",
 "Vidal_Gadea_author_index_candidates",
 "C_elegans_motion_calcium_methods",
}
SCOPE="PUBLIC_BIBLIOGRAPHIC_IDENTIFIER_ONLY"
LIMITATION=("Matching a PubMed citation or DOI establishes only indexed bibliographic "
            "identity at the snapshot's observation time. It does not establish gene "
            "causality, variant pathogenicity, experimental reproducibility, therapy "
            "efficacy, patient safety, peer review or collaborator endorsement.")

def canonical(x)->bytes:
 return (json.dumps(x,sort_keys=True,ensure_ascii=True,separators=(",",":"))+"\n").encode("utf-8")

def validate_snapshot(raw:bytes)->dict:
 if sha256(raw).hexdigest()!=SNAPSHOT_SHA256:
  raise ValueError("PUBLIC_SNAPSHOT_BYTE_IDENTITY_MISMATCH")
 try:doc=json.loads(raw)
 except (json.JSONDecodeError,UnicodeDecodeError) as e:
  raise ValueError("SNAPSHOT_PARSE_FAILURE") from e
 if doc.get("schema")!=SCHEMA:raise ValueError("UNKNOWN_SNAPSHOT_SCHEMA")
 if doc.get("initial_captured_snapshot_sha256")!=ORIGINAL_CAPTURE_SHA256:
  raise ValueError("ORIGIN_SNAPSHOT_HASH_MISMATCH")
 if doc.get("upstream_provider_response_sha256")!=RAW_ESUMMARY_SHA256:
  raise ValueError("UPSTREAM_RESPONSE_DIGEST_CHANGED")
 if doc.get("selected_pmid_count")!=19 or doc.get("admitted_pmid_count")!=19:
  raise ValueError("SELECTED_SCOPE_INCONSISTENT")
 if doc.get("excluded_pmid_count")!=0 or doc.get("excluded")!=[]:
  raise ValueError("EXCLUSION_COVERAGE_CHANGED")
 if doc.get("scope_ceiling")!="BIBLIOGRAPHIC_IDENTITY_AT_CAPTURE_ONLY":
  raise ValueError("SCIENTIFIC_CEILING_EXCEEDED")
 if doc.get("signed_external_attestation") is not False or doc.get("live_provider_verification_at_request") is not False:
  raise ValueError("UNSUPPORTED_ATTESTATION_OR_LIVE_CLAIM")
 if not isinstance(doc.get("search_coverage"),dict) or set(doc["search_coverage"])!=TOPICS:
  raise ValueError("QUERY_COVERAGE_UNBOUND")
 records=doc.get("items")
 if not isinstance(records,list) or len(records)!=19:
  raise ValueError("RECORD_COUNT_MISMATCH")
 ids=set()
 for row in records:
  if type(row)!=dict:raise ValueError("INVALID_ROW_TYPE")
  expected={
   "pmid","title","journal","pubdate_as_reported","epubdate_as_reported",
   "doi","publication_types_as_reported","source_url","query_groups",
   "metadata_origin","bibliographic_identity","scientific_or_clinical_claim",
   "therapy_efficacy_or_safety"
  }
  if set(row)!=expected:raise ValueError("UNEXPECTED_METADATA_FIELD")
  pmid=row["pmid"]
  if not isinstance(pmid,str) or not PMID.fullmatch(pmid) or pmid in ids:
   raise ValueError("INVALID_OR_DUPLICATE_PMID")
  ids.add(pmid)
  if row["source_url"]!=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/":
   raise ValueError("INVALID_SOURCE_URL")
  if not isinstance(row["title"],str) or len(row["title"])>1000 or not row["title"].strip() or "\ufffd" in row["title"]:
   raise ValueError("BROKEN_OR_UNSAFE_SOURCE_TITLE")
  for field in ("journal","pubdate_as_reported","epubdate_as_reported"):
   if not isinstance(row[field],str) or len(row[field])>300:
    raise ValueError("INVALID_METADATA_FIELD_"+field)
  if row["doi"] is not None and (not isinstance(row["doi"],str) or not DOI.fullmatch(row["doi"])):
   raise ValueError("INVALID_DOI_FORMAT")
  if not isinstance(row["query_groups"],list) or not row["query_groups"] or not set(row["query_groups"]).issubset(TOPICS):
   raise ValueError("UNREVIEWED_QUERY_MEMBERSHIP")
  if len(set(row["query_groups"]))!=len(row["query_groups"]):
   raise ValueError("DUPLICATE_QUERY_TOPIC")
  if (not isinstance(row["publication_types_as_reported"],list)
      or len(row["publication_types_as_reported"])>15
      or not all(isinstance(x,str) and len(x)<150 for x in row["publication_types_as_reported"])):
   raise ValueError("INVALID_PUBMED_PUBLICATION_TYPES")
  if row["metadata_origin"]!="NCBI_PUBMED_ESUMMARY_JSON_V2":
   raise ValueError("UNBOUND_PROVIDER")
  if row["bibliographic_identity"]!="RETRIEVED_AT_OBSERVATION":
   raise ValueError("UNSUPPORTED_PROVIDER_STATUS")
  if row["scientific_or_clinical_claim"]!="NOT_ASSESSED" or row["therapy_efficacy_or_safety"]!="NOT_ASSESSED":
   raise ValueError("FORBIDDEN_BIOLOGICAL_QUALIFICATION")
 return doc

def load_snapshot(path:Path)->dict:
 return validate_snapshot(path.read_bytes())

def parse_source_query(qs:str)->dict:
 if not isinstance(qs,str) or len(qs)>250:
  raise ValueError("SOURCE_QUERY_TOO_LONG")
 try:
  args=parse_qs(qs,strict_parsing=True,keep_blank_values=True,max_num_fields=2)
 except ValueError:
  raise ValueError("MALFORMED_QUERY") from None
 if not set(args).issubset({"pmid","doi"}) or set(args)==set() or "pmid" not in args:
  raise ValueError("PMID_REQUIRED")
 if any(len(values)!=1 for values in args.values()):
  raise ValueError("DUPLICATE_QUERY_KEY")
 pmid=args["pmid"][0]
 if not PMID.fullmatch(pmid):raise ValueError("INVALID_PMID")
 doi=None
 if "doi" in args:
  doi=args["doi"][0].strip()
  if not DOI.fullmatch(doi):raise ValueError("INVALID_EXPECTED_DOI")
 return {"pmid":pmid,"doi":doi}

def lookup(snapshot:dict,pmid:str,doi:str|None=None)->dict:
 # Only validated snapshots are permitted in the handler.
 if not isinstance(pmid,str) or not PMID.fullmatch(pmid):
  raise ValueError("INVALID_PMID")
 if doi is not None and (not isinstance(doi,str) or not DOI.fullmatch(doi)):
  raise ValueError("INVALID_EXPECTED_DOI")
 row=next((row for row in snapshot["items"] if row["pmid"]==pmid),None)
 if row is None:
  return {
   "state":"UNAVAILABLE_NOT_IN_SAMPLED_INDEX",
   "pmid":pmid,
   "does_not_mean_pubmed_record_absent":True,
   "source_retrieval_at_request":False,
   "scientific_claim_validity":"NOT_ASSESSED",
   "limitation":"Only 19 preselected public records were captured. This is not an exhaustive PubMed search.",
  }
 if doi is None:
  status="BIBLIOGRAPHIC_PMID_INDEXED_AT_CAPTURE"
  match="NOT_REQUESTED"
 elif row["doi"] is None:
  status="DOI_UNAVAILABLE_IN_INDEX"
  match="UNAVAILABLE"
 elif doi.casefold()==row["doi"].casefold():
  status="BIBLIOGRAPHIC_IDENTITY_MATCH_AT_CAPTURE"
  match="MATCH"
 else:
  status="DOI_IDENTITY_CONFLICT_AT_CAPTURE"
  match="MISMATCH"
 return {
  "state":status,
  "pmid":pmid,
  "doi_comparison":match,
  "metadata":row,
  "upstream_metadata_observed_utc":snapshot["source_observation_utc"],
  "snapshot_admitted_utc":snapshot["admission_review_utc"],
  "snapshot_sha256":SNAPSHOT_SHA256,
  "source_retrieval_at_request":False,
  "source_provenance":"PubMed ESummary v2 public citation metadata at prior observed timestamp",
  "scientific_claim_validity":"NOT_ASSESSED",
  "clinical_safety_and_efficacy":"NOT_ASSESSED",
  "external_signed_attestation":False,
  "limitation":LIMITATION,
 }

def summary(snapshot:dict)->dict:
 return {
  "schema":SCHEMA,
  "state":"BOUNDED_PUBLIC_CITATION_INDEX",
  "selected_records":snapshot["selected_pmid_count"],
  "indexed_records":snapshot["admitted_pmid_count"],
  "excluded_records":snapshot["excluded_pmid_count"],
  "observed_utc":snapshot["source_observation_utc"],
  "admitted_utc":snapshot["admission_review_utc"],
  "snapshot_sha256":SNAPSHOT_SHA256,
  "query_coverage":snapshot["search_coverage"],
  "scientific_claim_validity":"NOT_ASSESSED",
  "external_signed_attestation":False,
  "retrieval_at_request":False,
  "limitation":LIMITATION,
 }
