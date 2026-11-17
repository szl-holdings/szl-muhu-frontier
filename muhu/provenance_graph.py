"""Source-restricted public bibliographic provenance graph (not a biology KG).

Compatible in spirit with W3C PROV and Biolink retrieval-provenance
distinctions, but NOT a conformance claim or a gene–disease association.

All edges are mechanical metadata relationships, never causal, therapeutic
or experimental assertions. No model, external service, or user-uploaded
source is invoked at request time.
"""
from __future__ import annotations
from hashlib import sha256
from math import log
from pathlib import Path
from collections import Counter,defaultdict
import json,re

from .public_sources import load_snapshot,SNAPSHOT_SHA256

SARA_SHA256="3af1e866cc72b8ed5a72bb865541bee589c10e19bcc58db16894103d1f850406"
SARA_SCHEM="szl.muhu.sara.pubmed_selection.v1"
GRAPH_SCHEMA="szl.muhu.bibliographic_provenance_graph.v1"
TOPICS={
 "wwox":"WWOX-related selected public citations",
 "vidal":"Vidal-Gadea author-query candidates",
 "worm_methods":"C. elegans motion/calcium public methods",
 "sara":"Sara Behnamian PubMed author-name index candidates",
}
OLD_TOPICS={
 "WWOX_mechanisms_and_preclinical":"wwox",
 "Vidal_Gadea_author_index_candidates":"vidal",
 "C_elegans_motion_calcium_methods":"worm_methods",
}
PREDICATES={
 "INDEXED_IN_SELECTED_SNAPSHOT",
 "SELECTED_FOR_BIBLIOGRAPHIC_QUERY",
 "REPORTED_DOI_IN_METADATA",
 "METADATA_RETRIEVED_FROM_PUBMED",
}
NODES={"publication","doi","scope","snapshot","source_authority"}
DECLARED_SCOPE=("Only selected public bibliographic metadata; no independent "
                "paper appraisal, gene–disease inference, therapeutic efficacy, "
                "clinical validation, scientific causality or lab endorsement.")
DOI_PATTERN=re.compile(r"10\.\d{4,9}/[^\s<>\"']{1,220}\Z",re.I)
PMID_PATTERN=re.compile(r"[1-9][0-9]{4,9}\Z")

def canonical(data):
 return (json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n").encode("utf-8")

def digest(raw):
 return sha256(raw).hexdigest()

def validate_sara(raw):
 if digest(raw)!=SARA_SHA256:raise ValueError("UNREVIEWED_SARA_SOURCE_BYTES")
 try:doc=json.loads(raw)
 except (ValueError,UnicodeDecodeError) as e:
  raise ValueError("SARA_SOURCE_JSON_BAD") from e
 if doc.get("schema")!=SARA_SCHEM or doc.get("record_count")!=4:
  raise ValueError("SARA_SOURCE_SCHEMA_OR_COUNT")
 if doc.get("scientific_quality")!="NOT_EVALUATED" or doc.get("clinical_quality")!="NOT_EVALUATED":
  raise ValueError("SARA_SOURCE_CLAIMS_OVERSTATED")
 if doc.get("external_signature") is not False:
  raise ValueError("UNSUPPORTED_SARA_SIGNER")
 expected={"36046618","40627371","42213236","42740140"}
 items=doc.get("items")
 if not isinstance(items,list) or {r.get("pmid") for r in items}!=expected or len(items)!=4:
  raise ValueError("UNPINNED_SARA_SELECTION")
 for row in items:
  if not PMID_PATTERN.fullmatch(row["pmid"]):raise ValueError("BAD_SARA_PMID")
  if row.get("pubmed_url")!="https://pubmed.ncbi.nlm.nih.gov/"+row["pmid"]+"/":
   raise ValueError("SARA_SOURCE_LINK_UNBOUND")
  if not DOI_PATTERN.fullmatch(row.get("doi","")):raise ValueError("SARA_BAD_DOI")
  if row.get("sara_author_query_name_as_reported")!="Behnamian S":
   raise ValueError("SARA_AUTHOR_STRING_CHANGED")
  if row.get("author_source_status")!="PUBMED_AUTHOR_NAME_INCLUDED_NOT_IDENTITY_ADJUDICATED":
   raise ValueError("IDENTITY_ASSERTION_NOT_GROUNDED")
  if row.get("scientific_truth")!="NOT_ASSESSED" or row.get("clinical_implication")!="NOT_ASSESSED":
   raise ValueError("SCIENTIFIC_CEILING_EXCEEDED")
  if not isinstance(row.get("title"),str) or not row["title"] or "\ufffd" in row["title"]:
   raise ValueError("SARA_TITLE_DAMAGED")
 return doc

def new_sara_snapshot(path):
 return validate_sara(Path(path).read_bytes())

def _node(id,kind,label,**more):
 return {"id":id,"kind":kind,"label":label,**more}

def _edge(source,predicate,target,snapshot_digest):
 body={
  "subject":source,"predicate":predicate,"object":target,
  "source_snapshot_sha256":snapshot_digest,
  "knowledge_level":"PUBLIC_BIBLIOGRAPHIC_METADATA_ONLY",
  "supports_biological_claim":False,
  "is_sci_or_clinical_evidence":False,
 }
 return {"id":"muhu:edge:"+digest(canonical(body))[:24],**body}

def assemble_graph(old_snapshot,sara_snapshot):
 nodes={}
 edges=[]
 def add(n):
  i=n["id"]
  if i in nodes and n!=nodes[i]:raise ValueError("DUPLICATE_NODE_ID_CONFLICT_"+i)
  nodes[i]=n
 def edge(a,p,b,source_sha):
  if p not in PREDICATES:raise ValueError("UNREVIEWED_PREDICATE")
  edges.append(_edge(a,p,b,source_sha))
 authority="infores:pubmed"
 add(_node(authority,"source_authority","NCBI PubMed ESummary v2",
           url="https://pubmed.ncbi.nlm.nih.gov/"))
 for topic,label in TOPICS.items():
  add(_node("muhu:topic:"+topic,"scope",label,
            scope_status="SEARCH_SELECTION_NOT_BIOLOGICAL_ASSOCIATION"))
 old_id="muhu:snapshot:"+SNAPSHOT_SHA256[:16]
 sara_id="muhu:snapshot:"+SARA_SHA256[:16]
 add(_node(old_id,"snapshot","Prior selected public PubMed snapshot",
           sha256=SNAPSHOT_SHA256,observed_utc=old_snapshot["source_observation_utc"]))
 add(_node(sara_id,"snapshot","Sara author-name indexed PubMed snapshot",
           sha256=SARA_SHA256,observed_utc=sara_snapshot["source_observed_utc"]))
 seen_pmids=set()
 for original,source_sha,snapshot_id,source_tag in (
  (old_snapshot["items"],SNAPSHOT_SHA256,old_id,"prior"),
  (sara_snapshot["items"],SARA_SHA256,sara_id,"sara"),
 ):
  for item in original:
   pmid=item["pmid"]
   if pmid in seen_pmids:raise ValueError("CROSS_SNAPSHOT_DUPLICATE_PMID")
   seen_pmids.add(pmid)
   doi=item.get("doi")
   query_groups=([OLD_TOPICS[group] for group in item["query_groups"]]
                 if source_tag=="prior" else ["sara"])
   if not all(q in TOPICS for q in query_groups):raise ValueError("UNKNOWN_QUERY_GROUP")
   item_id="PMID:"+pmid
   title=item["title"]
   if not isinstance(title,str) or not title.strip():
    raise ValueError("MISSING_PUBLICATION_TITLE")
   add(_node(item_id,"publication",title,
             pmid=pmid,source_url=item["source_url" if source_tag=="prior" else "pubmed_url"],
             doi=doi,pubdate_as_reported=item["pubdate_as_reported"],
             query_scope=sorted(query_groups),
             status="INDEXED_BIBLIOGRAPHIC_IDENTITY_ONLY",
             snapshot_sha256=source_sha,metadata_origin="NCBI_PUBMED_ESUMMARY_V2",
             scientific_claim_validity="NOT_EVALUATED"))
   edge(snapshot_id,"INDEXED_IN_SELECTED_SNAPSHOT",item_id,source_sha)
   for topic in query_groups:
    edge("muhu:topic:"+topic,"SELECTED_FOR_BIBLIOGRAPHIC_QUERY",item_id,source_sha)
   edge(item_id,"METADATA_RETRIEVED_FROM_PUBMED",authority,source_sha)
   if doi is not None:
    if not DOI_PATTERN.fullmatch(doi):raise ValueError("SOURCE_DOI_INVALID")
    doi_id="DOI:"+doi.casefold()
    add(_node(doi_id,"doi",doi,identity_url="https://doi.org/"+doi))
    edge(item_id,"REPORTED_DOI_IN_METADATA",doi_id,source_sha)
 if len(seen_pmids)!=23:raise ValueError("MISSING_SOURCE_PMIDS")
 graph={
  "schema":GRAPH_SCHEMA,
  "graph_kind":"SOURCE_CITATION_PROVENANCE_ONLY",
  "observed_utc":{"prior":old_snapshot["source_observation_utc"],
                  "sara":sara_snapshot["source_observed_utc"]},
  "parent_snapshot_sha256":{"prior":SNAPSHOT_SHA256,"sara":SARA_SHA256},
  "nodes":sorted(nodes.values(),key=lambda x:x["id"]),
  "edges":sorted(edges,key=lambda x:x["id"]),
  "scientific_qualification":False,
  "clinical_qualification":False,
  "mechanistic_or_causal_edges_present":False,
  "source_claim_limitation":DECLARED_SCOPE,
  "provenance_standard_alignment":"PROV/Biolink concepts INFORMATIVE ONLY; NOT certified model conformance",
 }
 audit=validate_graph(graph)
 graph["graph_sha256"]=digest(canonical(graph))
 return graph

def validate_graph(graph):
 if graph.get("schema")!=GRAPH_SCHEMA:raise ValueError("UNKNOWN_GRAPH_SCHEMA")
 if "graph_sha256" in graph:
  unsigned={k:v for k,v in graph.items() if k!="graph_sha256"}
  if digest(canonical(unsigned))!=graph["graph_sha256"]:
   raise ValueError("GRAPH_SOURCE_CONTENT_TAMPERED")
 if graph.get("mechanistic_or_causal_edges_present") is not False:
  raise ValueError("FALSE_BIOLOGY_CLAIM")
 if graph.get("scientific_qualification") is not False or graph.get("clinical_qualification") is not False:
  raise ValueError("UNQUALIFIED_MODEL_PROMOTION")
 nodes=graph["nodes"]; edges=graph["edges"]
 node_by_id={n["id"]:n for n in nodes}
 ids=[n["id"] for n in nodes]
 if len(ids)!=len(set(ids)):raise ValueError("DUPLICATE_GRAPH_NODE")
 all_nodes=set(ids)
 for node in nodes:
  if node["kind"] not in NODES:raise ValueError("UNREVIEWED_NODE_CLASS")
  if node["kind"]=="publication" and node.get("scientific_claim_validity")!="NOT_EVALUATED":
   raise ValueError("BIOLOGICAL_VALIDITY_MISSING_HOLD")
 publications={n["pmid"] for n in nodes if n["kind"]=="publication"}
 if len(publications)!=23:raise ValueError("GRAPH_PMID_COUNT_INCORRECT")
 if set(TOPICS)!={n["id"].split(":")[-1] for n in nodes if n["kind"]=="scope"}:
  raise ValueError("GRAPH_QUERY_SCOPE_NOT_BOUNDED")
 edge_ids=set()
 adjacency=defaultdict(list);indegree={n:0 for n in all_nodes}
 for link in edges:
  a,b,p=link["subject"],link["object"],link["predicate"]
  if a not in all_nodes or b not in all_nodes:
   raise ValueError("DANGLING_GRAPH_REFERENCE")
  if a==b:raise ValueError("SELF_REFERENTIAL_EDGE")
  if p not in PREDICATES:raise ValueError("CAUSAL_OR_UNKNOWN_PREDICATE_DENIED")
  expected_types={
   "INDEXED_IN_SELECTED_SNAPSHOT":("snapshot","publication"),
   "SELECTED_FOR_BIBLIOGRAPHIC_QUERY":("scope","publication"),
   "REPORTED_DOI_IN_METADATA":("publication","doi"),
   "METADATA_RETRIEVED_FROM_PUBMED":("publication","source_authority"),
  }
  if (node_by_id[a]["kind"],node_by_id[b]["kind"])!=expected_types[p]:
   raise ValueError("INVALID_PROVENANCE_EDGE_TYPES")
  if link.get("supports_biological_claim") is not False or link.get("is_sci_or_clinical_evidence") is not False:
   raise ValueError("UNSUPPORTED_SCIENTIFIC_ASSOCIATION")
  if link["source_snapshot_sha256"] not in (SARA_SHA256,SNAPSHOT_SHA256):
   raise ValueError("EDGE_ORIGIN_UNBOUND")
  body={k:v for k,v in link.items() if k!="id"}
  if link["id"]!="muhu:edge:"+digest(canonical(body))[:24]:
   raise ValueError("EDGE_IDENTIFIER_TAMPERED")
  if link["id"] in edge_ids:raise ValueError("DUPLICATED_GRAPH_EDGE")
  edge_ids.add(link["id"])
  adjacency[a].append(b);indegree[b]+=1
 order=[node for node in indegree if indegree[node]==0]
 processed=0
 while order:
  x=order.pop();processed+=1
  for y in adjacency[x]:
   indegree[y]-=1
   if indegree[y]==0:order.append(y)
 if processed!=len(nodes):raise ValueError("CYCLIC_PROVENANCE_GRAPH")
 expected_counts={"wwox":9,"vidal":7,"worm_methods":3,"sara":4}
 observed_counts={k:sum(e["predicate"]=="SELECTED_FOR_BIBLIOGRAPHIC_QUERY"
                        and e["subject"]=="muhu:topic:"+k for e in edges)
                  for k in expected_counts}
 if observed_counts!=expected_counts:
  raise ValueError("TOPIC_SOURCE_SCOPE_COUNTS_CHANGED")
 for pmid in publications:
  pid="PMID:"+pmid
  incoming=[e for e in edges if e["object"]==pid]
  outgoing=[e for e in edges if e["subject"]==pid]
  if sum(e["predicate"]=="INDEXED_IN_SELECTED_SNAPSHOT" for e in incoming)!=1:
   raise ValueError("SNAPSHOT_IDENTITY_NOT_UNIQUE")
  if sum(e["predicate"]=="SELECTED_FOR_BIBLIOGRAPHIC_QUERY" for e in incoming)<1:
   raise ValueError("PAPER_WITHOUT_SELECTION_TRACE")
  if sum(e["predicate"]=="METADATA_RETRIEVED_FROM_PUBMED" for e in outgoing)!=1:
   raise ValueError("PAPER_WITHOUT_PROVIDER_TRACE")
  declared_doi=node_by_id[pid]["doi"]
  if sum(e["predicate"]=="REPORTED_DOI_IN_METADATA" for e in outgoing)!=int(declared_doi is not None):
   raise ValueError("DOI_COUNT_DISAGREES_WITH_SOURCE")
 return {
  "nodes":len(nodes),"edges":len(edges),"papers":len(publications),
  "topic_nodes":4,"topic_counts":observed_counts,
  "biological_associations":0,"acyclic":True,
 }

def build_from_paths(old_path,sara_path):
 old=load_snapshot(Path(old_path))
 sara=new_sara_snapshot(Path(sara_path))
 return assemble_graph(old,sara)

def filtered_graph(graph,topic="all"):
 if topic not in set(TOPICS)|{"all"}:raise ValueError("BAD_GRAPH_TOPIC")
 if topic=="all":
  selected=[n for n in graph["nodes"] if n["kind"]=="publication"]
 else:
  selected=[n for n in graph["nodes"] if n["kind"]=="publication" and topic in n["query_scope"]]
 pub_ids={n["id"] for n in selected}
 keep_ids=pub_ids|{"infores:pubmed"}
 kept_edges=[e for e in graph["edges"] if
             (e["subject"] in pub_ids) or
             (e["object"] in pub_ids)]
 for edge in kept_edges:
  keep_ids.add(edge["subject"]);keep_ids.add(edge["object"])
 kept_nodes=[n for n in graph["nodes"] if n["id"] in keep_ids]
 view={
  "schema":"szl.muhu.bibliographic_graph_view.v1",
  "topic":topic,"topic_label":"All selected public references" if topic=="all" else TOPICS[topic],
  "source_graph_sha256":graph["graph_sha256"],
  "selected_publications":len(selected),
  "nodes":kept_nodes,
  "edges":kept_edges,
  "knowledge_level":"BIBLIOGRAPHIC_METADATA_ONLY",
  "scientific_qualification":False,
  "clinical_qualification":False,
  "limitations":DECLARED_SCOPE,
  "query_generated_facts":False,
 }
 view["view_sha256"]=digest(canonical(view))
 return view

def source_path_for_pmid(graph,pmid):
 if not isinstance(pmid,str) or not PMID_PATTERN.fullmatch(pmid):
  raise ValueError("INVALID_PMID")
 nodes={n["id"]:n for n in graph["nodes"]}
 id="PMID:"+pmid
 if id not in nodes:
  return {"state":"UNAVAILABLE_NOT_IN_SELECTED_RESEARCH_SNAPSHOTS",
          "pmid":pmid,"publication_may_exist_elsewhere":True,
          "source_absence_not_claimed":True,"science_claims":"NOT_EVALUATED"}
 node=nodes[id]
 incoming=[{"relation":e["predicate"],"node":e["subject"],
            "source_snapshot_sha256":e["source_snapshot_sha256"]}
           for e in graph["edges"] if e["object"]==id]
 incoming=sorted(incoming,key=lambda x:(x["relation"],x["node"]))
 return {"state":"BIBLIOGRAPHIC_SOURCE_PATH_OBSERVED_AT_SNAPSHOT",
         "pmid":pmid,"publication":node,
         "incoming_metadata_edges":incoming,
         "no_causal_claims":True,
         "clinical_quality":"NOT_EVALUATED",
         "graph_sha256":graph["graph_sha256"]}

def tokenize_title(txt):
 return re.findall(r"[a-z][a-z0-9]{1,}",txt.casefold())

def lexical_search(graph,phrase,max_results=8):
 if not isinstance(phrase,str) or not 3<=len(phrase)<=100 or not isinstance(max_results,int) or not 1<=max_results<=12:
  raise ValueError("INVALID_BOUNDED_QUERY")
 if not re.fullmatch(r"[A-Za-z0-9\s\-]{3,100}",phrase):
  raise ValueError("UNSAFE_QUERY_CHARACTERS")
 tokens=set(tokenize_title(phrase))
 if not tokens:return {"state":"ABSTAIN_NO_VALID_TERMS","results":[]}
 docs=[n for n in graph["nodes"] if n["kind"]=="publication"]
 tf=[Counter(tokenize_title(n["label"])) for n in docs]
 df=Counter()
 for counts in tf:df.update(counts.keys())
 matches=[]
 for node,counts in zip(docs,tf):
  if not tokens.intersection(counts):continue
  score=sum((1+log(counts[w]))*(1+log((len(docs)+1)/(1+df[w])))
            for w in tokens if counts[w])
  matches.append((score,int(node["pmid"]),node))
 matches.sort(key=lambda x:(-x[0],-x[1]))
 results=[{"pmid":n["pmid"],"title":n["label"],"source_url":n["source_url"],
           "query_scope":n["query_scope"],"title_only_score_not_probability":round(s,6)}
          for s,_,n in matches[:max_results]]
 return {"state":"BIBLIOGRAPHIC_TITLE_RETRIEVAL_ONLY" if results else "ABSTAIN_NO_SELECTED_TITLE_MATCH",
         "query":phrase,"retrieved_count":len(results),
         "results":results,
         "no_claims_about_relevance_beyond_title":True,
         "scientific_validity":"NOT_EVALUATED"}
