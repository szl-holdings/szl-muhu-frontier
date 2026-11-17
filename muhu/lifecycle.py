"""Source-bound PubMed editorial lifecycle and version lineage, not proof of quality.

Uses NCBI PubMed EFetch XML bibliographic/editiorial metadata to retain
publication types and CommentsCorrections RefType relationships. No article
abstract, full text, human genome, treatment payload or private lab records
are retained. A missing editorial notice at the capture time is *not*
proof that a paper is not retracted, peer-reviewed, or correct.

Important: the same preprint/update lineage is not independent evidence.
Only explicit PubMed version/update links are used to group records.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from collections import Counter,defaultdict
from xml.etree import ElementTree as ET
import json,re

from .provenance_graph import PMID_PATTERN, DOI_PATTERN, GRAPH_SCHEMA, validate_graph

SCHEMA="szl.muhu.pubmed_editorial_lifecycle.v1"
PROVIDER="NCBI PubMed EFetch XML (retmode=xml)"
SELECTED_RECORDS=23
# Matched from official NLM PubMed DTD RefType attributes.
REF_TYPES={
 "AssociatedDataset","AssociatedPublication","CommentIn","CommentOn",
 "CorrectedandRepublishedIn","CorrectedandRepublishedFrom",
 "ErratumIn","ErratumFor","ExpressionOfConcernIn","ExpressionOfConcernFor",
 "RepublishedIn","RepublishedFrom","RetractedandRepublishedIn",
 "RetractedandRepublishedFrom","RetractionIn","RetractionOf",
 "UpdateIn","UpdateOf","SummaryForPatientsIn","OriginalReportIn",
 "ReprintIn","ReprintOf","Cites",
}
VERSION_LINKS={
 "UpdateIn","UpdateOf","RepublishedIn","RepublishedFrom",
 "CorrectedandRepublishedIn","CorrectedandRepublishedFrom",
 "RetractedandRepublishedIn","RetractedandRepublishedFrom",
}
RETRACTIONS={
 "RetractionIn","RetractionOf","RetractedandRepublishedIn",
 "RetractedandRepublishedFrom",
}
CONCERNS={"ExpressionOfConcernIn","ExpressionOfConcernFor"}
ERRATA={"ErratumIn","ErratumFor"}
SUSPICIOUS_TYPES={"Retracted Publication","Retraction Notice","Expression of Concern"}
PUBLICATION_TYPE_SOURCE="PUBMED_MEDLINE_ARTICLE_PUBLICATION_TYPES"
DTD_URL="https://dtd.nlm.nih.gov/ncbi/pubmed/doc/out/250101/att-RefType-c.html"
SOURCE_CEILING="INDEXED_EDITORIAL_METADATA_NOT_PAPER_QUALITY_OR_RETRACTION_CLEANLINESS"
VERSION_LIMITATION=("An update/version link indicates an editorial metadata "
                    "relationship, not that two papers have identical conclusions. "
                    "They must not count as independent evidence without review.")
CLEAN_LIMITATION=("No tracked editorial correction type appeared in the "
                  "source XML snapshot; this is not proof that the article "
                  "is unretracted, up-to-date, peer-reviewed or scientifically valid.")

def canonical(obj):
    return (json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n").encode()

def sha(raw):
    return sha256(raw).hexdigest()

def _note_category(types,links):
    typ_set=set(types)
    refs={x["type"] for x in links}
    if refs.intersection(RETRACTIONS) or typ_set.intersection({"Retracted Publication","Retraction Notice"}):
        return "RETRACTION_INDEX_FLAG_REVIEW_REQUIRED"
    if refs.intersection(CONCERNS) or "Expression of Concern" in typ_set:
        return "EXPRESSION_OF_CONCERN_INDEX_FLAG_REVIEW_REQUIRED"
    if refs.intersection(ERRATA) or "Published Erratum" in typ_set:
        return "ERRATUM_INDEX_FLAG_REVIEW_REQUIRED"
    if "Preprint" in typ_set and refs.intersection(VERSION_LINKS):
        return "PREPRINT_WITH_VERSION_UPDATE_LINK"
    if "Preprint" in typ_set:
        return "PREPRINT_INDEXED_VERSION_REVIEW_REQUIRED"
    if refs.intersection(VERSION_LINKS):
        return "VERSION_UPDATE_LINK_OBSERVED"
    if refs:
        return "RELATED_CITATION_LINK_OBSERVED"
    return "NO_TRACKED_EDITORIAL_LINK_OBSERVED_NOT_VERIFIED_CLEAR"

def _as_short_text(value,limit=230):
    if value is None:return ""
    if not isinstance(value,str) or len(value)>limit or "\ufffd" in value:
        raise ValueError("UNSAFE_UPSTREAM_TEXT_FIELD")
    return value.strip()

def _extract(article,pmid):
    citation=article.find("./MedlineCitation")
    if citation is None:raise ValueError("MISSING_MEDLINE_CITATION")
    status=citation.get("Status")
    if not isinstance(status,str) or len(status)>70:
        raise ValueError("UNKNOWN_SOURCE_INDEX_STATUS")
    pub_status=article.findtext("./PubmedData/PublicationStatus")
    pub_status=_as_short_text(pub_status,70)
    ptypes=[]
    for node in citation.findall("./Article/PublicationTypeList/PublicationType"):
        name=_as_short_text(node.text,140)
        if not name:raise ValueError("EMPTY_PUBLICATION_TYPE")
        ptypes.append(name)
    if not ptypes:raise ValueError("PUBLICATION_TYPE_MISSING")
    if len(ptypes)!=len(set(ptypes)):raise ValueError("DUPLICATED_PUBLICATION_TYPE")
    linked=[]
    for link in citation.findall("./CommentsCorrectionsList/CommentsCorrections"):
        name=link.get("RefType")
        if name not in REF_TYPES:
            raise ValueError("UNRECOGNIZED_NLM_EDITORIAL_REFTYPE")
        target=link.findtext("./PMID")
        if target is not None:
            if not PMID_PATTERN.fullmatch(target):
                raise ValueError("INVALID_LINKED_PUBMED_IDENTIFIER")
        refsource=_as_short_text(link.findtext("./RefSource"),300)
        linked.append({
            "type":name,
            "linked_pmid":target,
            "reference_label_as_reported":refsource if refsource else None,
            "note_present_not_republished":link.find("./Note") is not None,
        })
    if len(linked)>40:raise ValueError("UNEXPECTED_RELATED_CITATIONS")
    articleids=article.findall("./PubmedData/ArticleIdList/ArticleId")
    dois=[_as_short_text(n.text,250) for n in articleids if n.get("IdType")=="doi"]
    if len(set(dois))>1:raise ValueError("CONFLICTING_PUBMED_DOI_VALUES")
    doi=dois[0] if dois else None
    if doi and not DOI_PATTERN.fullmatch(doi):raise ValueError("INVALID_PUBMED_DOI")
    date=citation.find("./DateRevised")
    revised=None
    if date is not None:
        pieces=[date.findtext(c) for c in ("Year","Month","Day")]
        if all(s is not None and s.isdecimal() for s in pieces):
            revised="-".join([pieces[0],pieces[1].zfill(2),pieces[2].zfill(2)])
    title=article.findtext("./MedlineCitation/Article/ArticleTitle")
    # Intentionally discard title contents and abstracts: original pinned
    # bibliographic snapshot already defines the paper identity.
    return {
        "pmid":pmid,
        "publication_types":sorted(ptypes),
        "publication_status_reported":pub_status,
        "indexing_status_reported":status,
        "citation_revised_date_reported":revised,
        "doi_as_reported_in_efetch":doi,
        "correction_links":sorted(linked,key=lambda x:(x["type"],x["linked_pmid"] or "",x["reference_label_as_reported"] or "")),
        "editorial_index_state":_note_category(ptypes,linked),
        "retraction_status_comprehensively_verified":False,
        "scientific_or_clinical_quality":"NOT_EVALUATED",
    }

def parse_efetch(raw:bytes,expected_pmids:set[str]):
    if not isinstance(raw,bytes) or len(raw)>1_500_000:
        raise ValueError("PROVIDER_MAX_BYTES_EXCEEDED")
    if not expected_pmids or len(expected_pmids)>50:
        raise ValueError("UNBOUNDED_SOURCE_REQUEST")
    try:root=ET.fromstring(raw)
    except ET.ParseError as error:
        raise ValueError("PUBMED_XML_PARSE_FAILED") from error
    if root.tag!="PubmedArticleSet":
        raise ValueError("EXPECTED_PUBMED_ARTICLE_SET")
    articles=root.findall("./PubmedArticle")
    if len(articles)!=len(expected_pmids):
        raise ValueError("PUBMED_XML_RECORD_COUNT_MISMATCH")
    recorded={}
    for a in articles:
        pmid=a.findtext("./MedlineCitation/PMID")
        if pmid not in expected_pmids or pmid in recorded:
            raise ValueError("UNKNOWN_OR_DUPLICATE_PUBMED_ID")
        recorded[pmid]=_extract(a,pmid)
    if set(recorded)!=expected_pmids:raise ValueError("PROVIDER_MISSING_SELECTED_PUBMED")
    return [recorded[pmid] for pmid in sorted(expected_pmids,key=int)]

def version_components(records):
    """Deterministic connected components from explicit version/update links.

    A linked PMID not in the 23 selected sources is reported but not
    invented as an independent article or silently counted as a group.
    """
    by_pmid={r["pmid"]:r for r in records}
    parents={p:p for p in by_pmid}
    def root(x):
        while parents[x]!=x:
            parents[x]=parents[parents[x]]
            x=parents[x]
        return x
    def union(a,b):
        a,b=root(a),root(b)
        if a!=b:parents[max(a,b)]=min(a,b)
    external=[]
    links=set()
    for record in records:
        pmid=record["pmid"]
        for edge in record["correction_links"]:
            if edge["type"] not in VERSION_LINKS or edge["linked_pmid"] is None:
                continue
            target=edge["linked_pmid"]
            if target in by_pmid:
                if target==pmid:raise ValueError("SELF_VERSION_LINK_UNEXPECTED")
                union(pmid,target)
                links.add(tuple(sorted([pmid,target],key=int)))
            else:
                external.append({"pmid":pmid,"linked_pmid":target,"type":edge["type"],
                                 "linked_record_in_sample":False})
    grouped=defaultdict(list)
    for pmid in by_pmid:
        grouped[root(pmid)].append(pmid)
    clusters=[]
    for pmids in grouped.values():
        pmids=sorted(pmids,key=int)
        key="muhu:version-group:"+sha(canonical(pmids))[:20]
        clusters.append({
            "version_group_id":key,"selected_pmids":pmids,
            "independent_observation_count":"NOT_INFERRED",
            "source_ambiguity":"Version links do not imply result equivalence",
        })
    clusters.sort(key=lambda c:int(c["selected_pmids"][0]))
    return {
        "groups":clusters,
        "selected_pmid_version_group_count":len(clusters),
        "explicit_in_sample_version_links":[list(pair) for pair in sorted(links)],
        "unselected_linked_version_targets":sorted(external,key=lambda x:(int(x["pmid"]),int(x["linked_pmid"]),x["type"])),
        "version_links_not_independent_scientific_replication":True,
    }

def create_snapshot(graph,xml_raw,observed_utc:str):
    validate_graph(graph)
    if graph["schema"]!=GRAPH_SCHEMA:raise ValueError("SOURCE_GRAPH_SCHEMA_CHANGED")
    ids={n["pmid"] for n in graph["nodes"] if n["kind"]=="publication"}
    if len(ids)!=SELECTED_RECORDS:raise ValueError("SOURCE_CARDINALITY_CHANGED")
    recs=parse_efetch(xml_raw,ids)
    graph_paper={n["pmid"]:n for n in graph["nodes"] if n["kind"]=="publication"}
    for record in recs:
        doi=record["doi_as_reported_in_efetch"]
        graph_doi=graph_paper[record["pmid"]]["doi"]
        if doi is not None and graph_doi is not None and doi.casefold()!=graph_doi.casefold():
            raise ValueError("ESUMMARY_EFETCH_DOI_IDENTITY_CONFLICT")
        record["doi_comparison_with_prior_snapshot"]=(
            "MATCH" if doi is not None and graph_doi is not None else
            "NOT_BOTH_RECORDED_NOT_INFERRED")
        record["previous_graph_source_snapshot_sha256"]=graph_paper[record["pmid"]]["snapshot_sha256"]
    versions=version_components(recs)
    categories=Counter(r["editorial_index_state"] for r in recs)
    links=Counter(e["type"] for r in recs for e in r["correction_links"])
    return {
        "schema":SCHEMA,
        "source_provider":PROVIDER,
        "observed_utc":observed_utc,
        "upstream_source_sha256":sha(xml_raw),
        "parent_bibliographic_graph_sha256":graph["graph_sha256"],
        "expected_pmid_count":len(ids),
        "normalized_records":recs,
        "editorial_category_counts":dict(sorted(categories.items())),
        "correction_link_type_counts":dict(sorted(links.items())),
        "version_components":versions,
        "rights":"NCBI public XML editorial metadata only; source XML/abstracts not published or persisted",
        "source_dtd_ref_types_url":DTD_URL,
        "editorial_quality_ceiling":SOURCE_CEILING,
        "absence_of_notice_is_evidence_of_clean_status":False,
        "clinical_or_biological_validity":"NOT_EVALUATED",
        "peer_review_status":"NOT_INFERRED",
        "external_signature":False,
        "not_training_data":True,
        "no_provider_lookup_on_user_request":True,
    }

def validate_snapshot(obj):
    if obj.get("schema")!=SCHEMA or obj.get("expected_pmid_count")!=SELECTED_RECORDS:
        raise ValueError("UNKNOWN_OR_UNEXPECTED_LIFECYCLE_SCHEMA")
    if obj.get("absence_of_notice_is_evidence_of_clean_status") is not False:
        raise ValueError("FALSE_NEGATIVE_RETRACTION_CLAIM")
    if obj.get("external_signature") is not False or obj.get("peer_review_status")!="NOT_INFERRED":
        raise ValueError("EDITORIAL_OR_SIGNER_OVERCLAIM")
    if obj.get("clinical_or_biological_validity")!="NOT_EVALUATED":
        raise ValueError("FALSE_CLINICAL_QUALIFICATION")
    if obj.get("not_training_data") is not True:
        raise ValueError("UNAUTHORIZED_TRAINING_PROMOTION")
    if not isinstance(obj.get("normalized_records"),list) or len(obj["normalized_records"])!=SELECTED_RECORDS:
        raise ValueError("BAD_EDITORIAL_SOURCE_CARDINALITY")
    ids=[r["pmid"] for r in obj["normalized_records"]]
    if len(set(ids))!=SELECTED_RECORDS or not all(PMID_PATTERN.fullmatch(x) for x in ids):
        raise ValueError("INVALID_PUBMED_IDENTIFIERS")
    for record in obj["normalized_records"]:
        if record.get("retraction_status_comprehensively_verified") is not False or record.get("scientific_or_clinical_quality")!="NOT_EVALUATED":
            raise ValueError("UNSUPPORTED_RETRACTION_CLEANLINESS_OR_SCIENCE")
        if record.get("editorial_index_state")!=_note_category(record["publication_types"],record["correction_links"]):
            raise ValueError("EDITORIAL_INDEX_CATEGORY_TAMPERED")
        for edge in record["correction_links"]:
            if edge["type"] not in REF_TYPES:raise ValueError("UNKNOWN_EDITORIAL_RELATION")
    if obj["version_components"]!=version_components(obj["normalized_records"]):
        raise ValueError("SOURCE_VERSION_GROUPS_CHANGED")
    if obj.get("parent_bibliographic_graph_sha256") is None or len(obj["parent_bibliographic_graph_sha256"])!=64:
        raise ValueError("SOURCE_BIBLIOGRAPHIC_GRAPH_UNBOUND")
    return {"selected_pmids":len(ids),
            "version_groups":obj["version_components"]["selected_pmid_version_group_count"],
            "index_state_counts":obj["editorial_category_counts"],
            "source_sha256":obj["upstream_source_sha256"],
            "clinical_use":"DENIED"}

def lookup(snapshot,pmid):
    if not isinstance(pmid,str) or not PMID_PATTERN.fullmatch(pmid):
        raise ValueError("INVALID_PUBMED_ID")
    records={p["pmid"]:p for p in snapshot["normalized_records"]}
    entry=records.get(pmid)
    if entry is None:
        return {"state":"UNAVAILABLE_NOT_IN_23_SELECTED_PMIDS",
                "pmid":pmid,"upstream_publication_absence_not_inferred":True,
                "editorial_status":"UNOBSERVED",
                "retraction_cleanliness":"NOT_VERIFIED"}
    matched=[g for g in snapshot["version_components"]["groups"] if pmid in g["selected_pmids"]]
    if len(matched)!=1:raise ValueError("VERSION_GROUP_NOT_UNIQUE")
    return {"state":"BOUNDED_INDEX_LIFECYCLE_METADATA_OBSERVED",
            "pmid":pmid,"publication":entry,
            "version_group":matched[0],
            "source_observed_utc":snapshot["observed_utc"],
            "source_snapshot_sha256":PINNED_SNAPSHOT_SHA,
            "editorial_notice_absence_does_not_prove_clean_status":True,
            "scientific_claim_validity":"NOT_ASSESSED",
            "therapeutic_or_clinical_claim":"NOT_ASSESSED",
            "source_current_at_request":False}
PINNED_SNAPSHOT_SHA="d7d2f74651c1b19ad9b102da08781d6b40bf4109b4a3984a4bc2bd5234ccfda4"

def load(path):
    raw=Path(path).read_bytes()
    if sha(raw)!=PINNED_SNAPSHOT_SHA:raise ValueError("SOURCE_LIFECYCLE_SNAPSHOT_HASH_DRIFT")
    obj=json.loads(raw)
    validate_snapshot(obj)
    return obj
