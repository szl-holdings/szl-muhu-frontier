"""MUHU source-bound research viewer, pure Python + SVG, never clinical."""
from __future__ import annotations
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs,urlsplit,urlencode
from .witness import FIELDS, BOOL_FIELDS, DEMO, witness_query
from .public_sources import load_snapshot, lookup, summary, parse_source_query, SNAPSHOT_SHA256
from .provenance_graph import (
 build_from_paths, validate_graph, filtered_graph, source_path_for_pmid,
 lexical_search, TOPICS as PROVENANCE_TOPICS,
)
from .graph_ui import page as graph_page
from .claim_firewall import adjudicate, parse_request as parse_claim_request, rulebook as claim_rulebook, matrix as claim_matrix
from .claim_ui import page as claim_page
import argparse
import json
import math
from hashlib import sha256

from .core import canonical, status_of,generate,verify_splits

ROOT=Path(__file__).resolve().parents[1]
APP_TITLE="MUHU | Research Methodology Frontier"
CONTENT_SECURITY=("default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; "
                  "base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
ALLOWED_PUBLIC_HOST="szlholdings-szl-muhu-frontier.hf.space"

READINGS=(
 ("Sara Behnamian — Formal Reasoning","Published certificate-verified, unique-solution logic puzzle research. We do not train on partner-created puzzles or claim to have re-certified the original 242-item bank.",
  "https://github.com/sarabehnamian/Puzzle-generation-with-guaranteed-uniqueness"),
 ("Vidal-Gadea Lab — Reproducible Measurement","Independent neurobiology and movement measurement research. All wave plots here are invented signals, NOT WINK or laboratory recordings.",
  "https://agvg75.github.io/lab/"),
 ("WWOX — Source-Bound Public Research","Research context for gene–disease validity and preclinical investigations; no genomic interpretation, treatment efficacy claims, or patient advice.",
  "https://pubmed.ncbi.nlm.nih.gov/?term=WWOX"),
 ("SZL — Controlled Training Ownership","Signed-job bridge and training gate reference. MUHU v2 has not been admitted into any existing training process.",
  "https://github.com/szl-holdings/szl-gpu-bridge/pull/228"),
)
STATE_DESCRIPTION={
 "BLOCKED":"A required input is absent. Insufficient evidence—not zero and not a scientific conclusion.",
 "CONFLICT":"Competing claims require adjudication. Preserve both source identities.",
 "STALE":"Revalidate older-than-seven-day observations before downstream use.",
 "REVIEWABLE":"Required metadata can be reviewed; no biological truth or clinical validity is implied."
}

def synthetic_wave_svg():
 w,h=920,250
 def line(phase,color,amp):
  pts=[]
  for i in range(160):
   x=45+i*(830/159)
   y=122-amp*math.sin((i/159)*math.pi*7+phase)
   pts.append(f"{x:.1f},{y:.1f}")
  return f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="3"/>'
 grid=''.join(f'<line x1="{x}" y1="38" x2="{x}" y2="210" stroke="#284457" stroke-width="1"/>' for x in range(45,876,83))
 return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Invented sine-wave demonstration; two mathematically phase-lagged signals, not biological measurements"><rect width="{w}" height="{h}" rx="16" fill="#0d2232"/>{grid}{line(0,"#38d7c9",55)}{line(0.85,"#f4bc72",40)}<text x="45" y="25" fill="#e9f5ff" font-size="14">SYNTHETIC SIGNALS ONLY · no recordings · no biology</text><text x="45" y="232" fill="#38d7c9" font-size="13">■ simulated movement</text><text x="250" y="232" fill="#f4bc72" font-size="13">■ simulated indicator</text></svg>'

def head_and_style():
 return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MUHU — SZL Research Methodology Frontier</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;font:16px/1.56 system-ui,-apple-system,Segoe UI,sans-serif;color:#e8f3f8;background:radial-gradient(circle at 80% 5%,#1b4651,#081421 60%)}
main{max-width:1080px;margin:auto;padding:3rem 1.3rem 5rem}nav{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:2rem}nav a{color:#9debdc;text-decoration:none;border:1px solid #436875;border-radius:28px;padding:.35rem .85rem}
h1{font-size:clamp(2.3rem,5vw,4rem);line-height:1.1;letter-spacing:-.05em;margin:.5rem 0;color:#efffff}h2{font-size:1.5rem;margin:2rem 0 1rem}p{color:#c5d9e0}.eyebrow{color:#91edce;font-weight:750;letter-spacing:.12em;text-transform:uppercase;font-size:.82rem}
.banner{background:#322d20;border-left:5px solid #f4bc72;border-radius:8px;padding:1rem 1.2rem;margin:1.5rem 0;color:#f5e6ce}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1rem}.card{padding:1.4rem;background:#11293a;border:1px solid #345161;border-radius:14px;min-width:0}.card strong{font-size:1.14rem;color:#fff}.card a{color:#8fd8fe}
.kpi{font-weight:800;font-size:2.2rem;color:#9aefda}.muted{color:#9dbbc6;font-size:.94rem}code{color:#9fe7f8;word-break:break-word}
svg{width:100%;height:auto}.tag{display:inline-block;background:#264556;padding:.2rem .6rem;border-radius:8px;color:#b8e3ef}a{color:#90dcff}
footer{margin-top:3rem;border-top:1px solid #315366;padding-top:1.4rem;color:#98bcc6}
</style><main>
<nav><a href="/">MUHU home</a><a href="/claim-gate">Claim Evidence Firewall</a><a href="/graph">Source provenance graph</a><a href="/witness">Evidence witness</a><a href="/sources">Publication provenance</a><a href="/methods">Evidence protocol</a><a href="/sara">Sara research</a><a href="/vidal">Vidal research</a><a href="/genomics">Genomic context</a><a href="/v3">V3 evaluation</a><a href="/api/v1/manifest">Machine-readable evidence</a></nav>
"""

def html_page(panel:str,summary:dict,cases:list[dict]):
 title={
  "/":"A seed for reproducible scientific intelligence",
  "/methods":"Evidence before conclusions",
  "/sara":"Certified reasoning, not unverified model claims",
  "/vidal":"Neuroscience measurement without invented biology",
  "/genomics":"Genetic research with explicit uncertainty"
 }.get(panel,"Research methodology")
 first=f"<p class='eyebrow'>SZL Holdings · MUHU v2 · source-bound research</p><h1>{escape(title)}</h1>"
 first+="<div class='banner'><strong>RESEARCH ONLY — NOT A CLINICAL OR BIOLOGICAL MODEL.</strong> No genomic sequences, patients, collaborator recordings or therapeutic advice. A passing software test does not establish scientific truth. /readyz intentionally returns 503.</div>"
 first+="<section class='cards'>"
 metrics=[("Public training examples",str(summary["public_training_records"])),
          ("Private evaluation examples",str(summary["private_validation_records"]+summary["private_test_records"])),
          ("Semantic group overlap",str(summary["group_disjointness"]["semantic_group_overlap"])),
          ("Provider-trained flagship adapters","0")]
 for a,b in metrics:first+=f"<div class='card'><div class='kpi'>{escape(b)}</div><strong>{escape(a)}</strong></div>"
 first+="</section>"
 if panel in ("/","/vidal"):
  first+="<h2>Visualizing uncertainty, not experiments</h2>"+synthetic_wave_svg()
 if panel in ("/","/methods"):
  first+="<h2>Falsifiable methodological states</h2><section class='cards'>"
  for s,desc in STATE_DESCRIPTION.items():
   first+=f"<div class='card'><strong>{escape(s)}</strong><p>{escape(desc)}</p></div>"
  first+="</section><h2>Original synthetic training examples</h2>"
  for row in cases[:3]:
   first+=f"<article class='card'><div class='muted'>{escape(row['id'])} · ORIGINAL SYNTHETIC</div><p>{escape(row['input'])}</p><strong>{escape(row['target_state'])}</strong></article><br>"
 else:
  first+="<h2>Relevant independently owned research</h2><section class='cards'>"
  show=READINGS if panel=="/" else (READINGS[0],) if panel=="/sara" else (READINGS[1],) if panel=="/vidal" else (READINGS[2],)
  for name,desc,url in show:
   first+=f"<article class='card'><strong>{escape(name)}</strong><p>{escape(desc)}</p><a rel='noopener noreferrer' href='{escape(url,quote=True)}'>Open source documentation ↗</a></article>"
  first+="</section>"
 first+="<h2>Source and scientific gates</h2><p>Code and synthetic source admission are separate from model evaluation, independent replication, laboratory deployment, and clinical qualification. The training set is not used by any active Flagship54 job.</p>"
 first+=("<footer>MUHU means “seed” in Quechua Chanka; a metaphor, not a translation of genetics. "
         "MIT software · CC BY 4.0 synthetic examples · canonical GitHub source required for deployment. "
         "Evidence hashes are not signatures.</footer></main></html>")
 return head_and_style()+first

def v3_page(results:dict)->str:
 """Render only source-admitted, aggregated synthetic results, not private rows."""
 test=results["test"]
 if results.get("quality_gate")!="FAILED_HOLD" or results.get("flagship_training_admitted") is not False:
  raise ValueError("UNQUALIFIED_RESEARCH_RESULT_REJECTED")
 report=(f"<p class='eyebrow'>SZL MUHU v3 · negative controls · reproducibility</p>"
         "<h1>Learn from a failure, not a headline</h1>"
         "<div class='banner'><strong>RESEARCH QUALITY: HOLD.</strong> "
         "This is synthetic methodological text classification, NOT genetics, "
         "microscopy, gene therapy or clinical validation. No Khipu adapter was trained.</div>"
         "<p>Test labels were balanced and each synthetic condition group appeared "
         "in only one partition. The public generator makes this test reconstructable; "
         "there was no independent blinded or human-adjudicated biological evaluation.</p>")
 display=[
  ("Training examples",results["training_rows"]),
  ("Test cases",test["n"]),
  ("Raw argmax accuracy",str(round(test["raw_argmax_accuracy"]*100,2))+"%"),
  ("Selective coverage",str(round(test["thresholded_selective_coverage"]*100,2))+"%"),
  ("Macro F1 with abstentions",round(test["macro_f1_abstentions_counted_as_misses"],3)),
  ("Stress-case accuracy",str(round(results["presealed_stress"]["accuracy"]*100,2))+"%"),
 ]
 report+="<h2>Fixed, preregistered CPU experiment</h2><section class='cards'>"
 for label,value in display:
  report+=f"<article class='card'><div class='kpi'>{escape(str(value))}</div><strong>{escape(label)}</strong></article>"
 report+="</section><h2>Per-class recall: which states were missed?</h2><section class='cards'>"
 for label,recall in test["per_class_recall"].items():
  rate=max(0.0,min(1.0,float(recall)))
  report+=(f"<article class='card'><strong>{escape(label)}</strong>"
           f"<div class='kpi'>{rate*100:.1f}%</div>"
           f"<svg viewBox='0 0 250 18' role='img' aria-label='{escape(label)} recall "
           f"{rate*100:.1f} percent'><rect width='250' height='18' fill='#244e5a' rx='6'/>"
           f"<rect width='{rate*250:.1f}' height='18' fill='#68cfbb' rx='6'/></svg>"
           "<p class='muted'>24 invented observations per label; not biomedical cases.</p></article>")
 report+=("</section><h2>What remains missing</h2>"
          "<p>The strict quality gates failed: synthetic test macro F1 was below "
          "0.85, minimum recall below 0.70, selective coverage below 0.85, "
          "and internal stress accuracy below 0.75. No post-test tuning was "
          "used to recast those failures as successes.</p>"
          "<p>Next: genuinely new expert-adjudicated conditions and language "
          "shifts, robust low-prevalence tests, Khipu forgetting and abstention "
          "comparison, approved new training generation. No existing flagship "
          "job or collaborator data has been changed.</p>"
          "<footer>SHA-256 binds files; it is not an independent attestation. "
          "Source: SZL Holdings; research-model weights retained privately. "
          "Model state: HOLD, not deployable.</footer></main></html>")
 return head_and_style()+report

def witness_page(result:dict)->str:
 """A one-screen, Python-rendered nonclinical evidence gate.

 Does not accept uploads, arbitrary scientific claims or personal data.
 """
 data=result.get("inputs") or DEMO
 parts=[
  "<p class='eyebrow'>MUHU Method Witness · deterministic · synthetic</p>",
  "<h1>What would make this evidence reviewable?</h1>",
  "<div class='banner'><strong>DEMONSTRATION ONLY.</strong> No patient, genetic, "
  "biological or laboratory data. A reviewable metadata record is not a "
  "verified scientific finding. No model is trained or invoked.</div>",
  "<p>Change five invented metadata fields and independently inspect which "
  "rule blocks, contradicts or marks a record stale. Nothing is stored, "
  "and the application does not persist them; hosting infrastructure may log URLs.</p>",
  "<form method='get' action='/witness' class='card'>",
 ]
 choices={
  "source_bound":"Original source pointer supplied",
  "independent_check":"Independent corroboration recorded",
  "contradiction":"Conflicting report present",
 }
 for field in FIELDS:
  if field in BOOL_FIELDS:
   parts.append(f"<p><label>{escape(choices[field])} <select name='{field}'>")
   for b in (True,False):
    key=str(b).lower()
    chosen=" selected" if data[field] is b else ""
    parts.append(f"<option value='{key}'{chosen}>{'Yes' if b else 'No'}</option>")
   parts.append("</select></label></p>")
  else:
   title="Actual observed denominator" if field=="sample_n" else "Days since last source verification"
   mx=1000 if field=="sample_n" else 365
   parts.append(f"<p><label>{title} "
                f"<input name='{field}' type='number' required min='0' max='{mx}' "
                f"value='{int(data[field])}'></label></p>")
 parts.append("<button type='submit'>Evaluate synthetic evidence</button></form>")
 state=str(result["state"])
 parts.append(f"<h2>Current verdict: <span class='tag'>{escape(state)}</span></h2>")
 if "inputs" not in result:
  parts.append("<p class='banner'>UNAVAILABLE: some required inputs were not provided. "
               "No classification was inferred.</p>")
  parts.append("<p>Missing fields: "+escape(", ".join(result.get("missing_fields",[])))+"</p>")
 else:
  parts.append("<p>"+escape(result["limitation"])+"</p>")
  parts.append("<section class='cards'>")
  for item in result["checks"]:
   label="PASS" if item["passed"] else "NEEDS EVIDENCE"
   parts.append("<article class='card'><strong>"+escape(item["id"])+" — "+label+"</strong>"
                "<p>"+escape(item["observation"])+"</p></article>")
  parts.append("</section>")
  parts.append("<p class='muted'>Canonical witness SHA-256 (integrity only, not signed): "
               "<code>"+escape(result["witness_sha256"])+"</code></p>")
  canonical_query=urlencode({k:str(data[k]).lower() if k in BOOL_FIELDS else data[k] for k in FIELDS})
  parts.append("<p><a href='/api/v1/witness?"+escape(canonical_query,quote=True)+"'>"
               "Inspect machine-readable evidence and source fields</a></p>")
 parts.append("<h2>Evidence still required</h2><section class='card'><ul>")
 for item in result.get("required_evidence",[]):
  parts.append("<li>"+escape(item)+"</li>")
 parts.append("</ul></section>")
 parts.append("<footer>Methodological policy only. SOURCE ≠ CORRECT, CURRENT ≠ "
              "VALIDATED, REVIEWABLE ≠ QUALIFIED. GitHub source and independent "
              "testing remain the governing authorities.</footer></main></html>")
 return head_and_style()+"".join(parts)

def publication_sources_page(snapshot:dict, selected:dict|None=None)->str:
 """Render only pinned public citation metadata. Never infer biological truth."""
 scope=summary(snapshot)
 parts=[
  "<p class='eyebrow'>MUHU public-source atlas · NCBI PubMed</p>",
  "<h1>From declared source to indexed citation</h1>",
  "<div class='banner'><strong>BIBLIOGRAPHIC METADATA ONLY — NOT A SCIENTIFIC OR CLINICAL VERDICT.</strong> "
  "These records are selected, public PubMed citation identifiers checked at a recorded time. "
  "The system has not reviewed abstracts or full text, reproduced experiments, "
  "validated gene–disease mechanisms or established therapeutic benefit.</div>",
  f"<p><span class='tag'>{scope['indexed_records']} indexed public records</span> "
  f"<span class='tag'>3 bounded research search categories</span> "
  f"<span class='tag'>observed {escape(scope['observed_utc'])}</span></p>",
  "<p>Check a PMID against the pinned reference list, optionally comparing a DOI. "
  "A citation match means only that its metadata identifiers agree in this stored snapshot. "
  "An absent ID means <em>not sampled</em>, not that no publication exists.</p>",
  "<form action='/sources' method='get' class='card'>",
  "<p><label>PubMed identifier (digits only): <input name='pmid' pattern='[0-9]{5,10}' "
  "inputmode='numeric' maxlength='10' required value='42422765'></label></p>",
  "<p><label>Optional expected DOI (public citation identifier): "
  "<input name='doi' maxlength='220' value='10.1016/j.omta.2026.201791'></label></p>",
  "<button type='submit'>Compare public citation identity</button></form>",
 ]
 if selected is not None:
  state=str(selected["state"])
  parts.append("<section class='card'><h2>Identifier comparison</h2><p>"
               f"<strong>{escape(state)}</strong></p>")
  if "metadata" in selected:
   row=selected["metadata"]
   parts.append(f"<h3>{escape(row['title'])}</h3>"
                f"<p>DOI comparison: {escape(selected['doi_comparison'])}</p>"
                "<p>Index record <a rel='noopener noreferrer' href='"+
                escape(row["source_url"],quote=True)+"'>"+escape(row["pmid"])+
                "</a> · NCBI PubMed</p>")
  else:
   parts.append("<p>The PMID is not among this sampled list. "
                "No source absence or scientific conclusion is inferred.</p>")
  parts.append("<p class='muted'>"+escape(selected["limitation"])+"</p></section>")
 parts.append("<h2>Evidence origin and coverage</h2>")
 parts.append("<section class='cards'>")
 categories={
 "WWOX_mechanisms_and_preclinical":"WWOX publications — selected mechanistic, preclinical and clinical-context citations",
 "Vidal_Gadea_author_index_candidates":"Vidal-Gadea author-query results — selected candidates, not the full laboratory bibliography",
 "C_elegans_motion_calcium_methods":"C. elegans movement and calcium-analysis methodology — selected public sources",
 }
 for g,description in categories.items():
  selected_count=sum(g in row["query_groups"] for row in snapshot["items"])
  source=snapshot["search_coverage"][g]
  parts.append("<article class='card'><strong>"+escape(description)+"</strong>"
               f"<div class='kpi'>{selected_count}</div><p class='muted'>"
               f"PubMed query reported {source['retrieved_search_count_at_initial_check']} hits; "
               "selected items here are not a systematic review.</p></article>")
 parts.append("</section><h2>Exact selected citation references</h2>")
 for row in snapshot["items"]:
  ptitle=escape(row["title"])
  doi=row["doi"] or "DOI unavailable in snapshot"
  tags=", ".join(row["query_groups"]).replace("_"," ")
  date=escape(row["pubdate_as_reported"] or "Publication date unavailable")
  parts.append(
    "<article class='card'><p class='muted'>PMID "+escape(row["pmid"])+
    " · "+date+" · "+escape(tags)+"</p>"
    "<h3><a href='"+escape(row["source_url"],quote=True)+
    "' rel='noopener noreferrer'>"+ptitle+"</a></h3>"
    "<p>"+escape(row["journal"])+" · DOI: <code>"+escape(doi)+"</code></p>"
    "<p class='muted'>Indexed citation only. No effectiveness, causal validity, "
    "peer-review status, or patient relevance assessed.</p></article><br>"
  )
 parts.append(
  "<footer>Upstream source: NCBI ESummary v2. Public snapshot SHA-256: "
  "<code>"+SNAPSHOT_SHA256+"</code>. SHA-256 is an integrity check, not "
  "an external signature. An author-name query candidate does not establish "
  "collaboration, consent or a complete publication audit. "
  "<a href='https://www.ncbi.nlm.nih.gov/home/about/policies/' "
  "rel='noopener noreferrer'>NCBI policies and disclaimers</a>. "
  "This public preview makes no live PubMed requests and stores no user inputs."
  "</footer></main></html>"
 )
 return head_and_style()+"".join(parts)

class Handler(BaseHTTPRequestHandler):
 server_version="SZL-MUHU/2"
 manifest:dict={}
 examples:list[dict]=[]
 source_snapshot:dict={}
 citation_graph:dict={}
 claim_matrix:dict={}

 def log_message(self,*args):return

 def reply(self,code:int,data:object,typ:str="application/json; charset=utf-8"):
  raw=(data.encode("utf-8") if isinstance(data,str) else canonical(data))
  self.send_response(code)
  for k,v in {
   "Content-Type":typ,"Content-Length":str(len(raw)),"Cache-Control":"no-store",
   "X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer",
   "X-Frame-Options":"DENY","Content-Security-Policy":CONTENT_SECURITY
  }.items():self.send_header(k,v)
  self.end_headers()
  if self.command!="HEAD":self.wfile.write(raw)

 def allowed_host(self):
  host=self.headers.get("Host","").strip().lower()
  port=self.server.server_address[1]
  return host in (f"127.0.0.1:{port}",f"localhost:{port}",ALLOWED_PUBLIC_HOST)

 def do_GET(self):
  if not self.allowed_host():return self.reply(403,{"state":"DENIED_UNRECOGNIZED_HOST"})
  if len(self.path)>1024:return self.reply(414,{"state":"QUERY_TOO_LONG"})
  path=urlsplit(self.path).path
  if path=="/healthz":
   return self.reply(200,{"alive":True,"product":"MUHU methodological research preview","scientifically_qualified":False})
  if path=="/readyz":
   return self.reply(503,{"ready":False,"reason":"INDEPENDENT_EVALUATION_AND_OWNER_TRAINING_ADMISSION_HOLD",
                          "clinical_qualification":"DENIED","lab_data":"NOT_CONNECTED"})
  if path=="/api/v1/manifest":
   return self.reply(200,self.manifest)
  if path=="/api/v1/v3-results":
   return self.reply(200,self.v3_metrics)
  if path=="/api/v1/claim-policy":
   return self.reply(200,claim_rulebook())
  if path=="/api/v1/claim-matrix":
   return self.reply(200,self.claim_matrix)
  if path in ("/claim-gate","/api/v1/claim-gate"):
   try:
    raw_query=urlsplit(self.path).query
    selected=({"pmid":"42422765","claim_type":"therapy_effectiveness",
               "doi":"10.1016/j.omta.2026.201791"}
              if path=="/claim-gate" and not raw_query
              else parse_claim_request(raw_query))
    decision=adjudicate(self.citation_graph,**selected)
   except ValueError:
    return self.reply(400,{"state":"INVALID_BOUNDED_CLAIM_QUERY",
                           "clinical_claim_supported":False})
   if path=="/api/v1/claim-gate":
    return self.reply(200,decision)
   options=[(n["pmid"],n["label"]) for n in self.citation_graph["nodes"]
            if n["kind"]=="publication"]
   return self.reply(200,head_and_style()+claim_page(decision,self.claim_matrix,options),
                     "text/html; charset=utf-8")
  if path=="/v3":
   return self.reply(200,v3_page(self.v3_metrics),"text/html; charset=utf-8")
  if path in ("/graph","/api/v1/graph"):
   try:
    raw_q=urlsplit(self.path).query
    params=parse_qs(raw_q,keep_blank_values=True,max_num_fields=3)
    if set(params)-{"topic","q"} or any(len(v)!=1 for v in params.values()):
     raise ValueError("QUERY_SHAPE_INVALID")
    if path=="/api/v1/graph" and "q" in params:
     raise ValueError("UNEXPECTED_SEARCH_ON_GRAPH_JSON")
    topic=params.get("topic",["all"])[0]
    view=filtered_graph(self.citation_graph,topic)
    query=params.get("q")
    matches=lexical_search(self.citation_graph,query[0]) if query is not None else None
   except ValueError:
    return self.reply(400,{"state":"INVALID_GRAPH_QUERY",
                           "scientific_quality":"NOT_ASSESSED"})
   if path=="/api/v1/graph":
    return self.reply(200,view)
   return self.reply(200,head_and_style()+graph_page(view,matches),"text/html; charset=utf-8")
  if path=="/api/v1/graph/source":
   try:
    args=parse_qs(urlsplit(self.path).query,strict_parsing=True,
                  keep_blank_values=True,max_num_fields=2)
    if set(args)!={"pmid"} or len(args["pmid"])!=1:
     raise ValueError("BAD_GRAPH_SOURCE_QUERY")
    trace=source_path_for_pmid(self.citation_graph,args["pmid"][0])
   except ValueError:
    return self.reply(400,{"state":"INVALID_GRAPH_SOURCE_ID"})
   return self.reply(200,trace)
  if path=="/api/v1/graph/search":
   try:
    args=parse_qs(urlsplit(self.path).query,strict_parsing=True,
                  keep_blank_values=True,max_num_fields=2)
    if set(args)!={"q"} or len(args["q"])!=1:
     raise ValueError("BAD_GRAPH_SEARCH_QUERY")
    result=lexical_search(self.citation_graph,args["q"][0])
   except ValueError:
    return self.reply(400,{"state":"INVALID_BOUNDED_TITLE_SEARCH"})
   return self.reply(200,result)
  if path=="/api/v1/sources":
   return self.reply(200,{
     "summary":summary(self.source_snapshot),
     "items":[{"pmid":r["pmid"],"title":r["title"],"doi":r["doi"],
               "source_url":r["source_url"],"query_groups":r["query_groups"]}
              for r in self.source_snapshot["items"]]})
  if path in ("/api/v1/source","/sources"):
   query=urlsplit(self.path).query
   try:
    if not query and path=="/sources":
     selected=None
    else:
     expected=parse_source_query(query)
     selected=lookup(self.source_snapshot,**expected)
   except ValueError:
    return self.reply(400,{"state":"INVALID_PUBLIC_CITATION_QUERY",
                           "scientific_claim_validity":"NOT_ASSESSED"})
   if path=="/api/v1/source":
    return self.reply(200,selected)
   return self.reply(200,publication_sources_page(self.source_snapshot,selected),
                     "text/html; charset=utf-8")
  if path in ("/witness","/api/v1/witness"):
   try:
    witness=witness_query(urlsplit(self.path).query,demo_if_empty=(path=="/witness"))
   except ValueError:
    return self.reply(400,{"state":"INVALID_SYNTHETIC_METADATA_INPUT",
                           "clinical_quality":"NOT_ASSESSED"})
   if path=="/api/v1/witness":
    return self.reply(200,witness)
   return self.reply(200,witness_page(witness),"text/html; charset=utf-8")
  if path=="/api/v1/example":
   query=parse_qs(urlsplit(self.path).query,keep_blank_values=True,max_num_fields=2)
   if set(query)-{"i"} or len(query.get("i",["0"]))!=1:return self.reply(400,{"state":"BAD_QUERY"})
   try:i=int(query.get("i",["0"])[0])
   except ValueError:return self.reply(400,{"state":"BAD_INDEX"})
   if i not in range(min(6,len(self.examples))):return self.reply(400,{"state":"OUT_OF_BOUNDS"})
   return self.reply(200,self.examples[i])
  if path in ("/","/methods","/sara","/vidal","/genomics"):
   return self.reply(200,html_page(path,self.manifest,self.examples),"text/html; charset=utf-8")
  return self.reply(404,{"state":"NOT_FOUND"})
 def do_HEAD(self):return self.do_GET()
 def do_POST(self):return self.reply(405,{"state":"READ_ONLY"})
 do_PUT=do_POST
 do_PATCH=do_POST
 do_DELETE=do_POST

def create_handler(public_dir:Path):
 manifest=json.loads((public_dir/"manifest.json").read_text("utf-8"))
 if manifest.get("schema")!="szl.muhu.dataset_manifest.v2":raise ValueError("INVALID_MANIFEST")
 from .core import sha256_bytes
 raw=(public_dir/"train.jsonl").read_bytes()
 if sha256_bytes(raw)!=manifest["split_hashes_sha256"]["train"]:
  raise ValueError("PUBLIC_TRAINING_BYTES_CHANGED")
 rows=[json.loads(x) for x in raw.splitlines() if x.strip()]
 if len(rows)!=manifest["public_training_records"] or any(row["split"]!="train" for row in rows):
  raise ValueError("UNEXPECTED_PUBLIC_TRAINING_ROWS")
 v3_path=ROOT/"research"/"muhu_v3"/"public_results.json"
 v3_bytes=v3_path.read_bytes()
 if sha256(v3_bytes).hexdigest()!="1de7f605b564ea88918702b551513385fde6680d4e49d74d6bf5c360dd930e87":
  raise ValueError("PUBLIC_V3_RESULT_BYTES_UNREVIEWED")
 v3=json.loads(v3_bytes)
 if v3.get("schema")!="szl.muhu.v3.public_aggregate_results.v1":
  raise ValueError("INVALID_V3_PUBLIC_REPORT")
 if v3.get("quality_gate")!="FAILED_HOLD" or v3.get("flagship_training_admitted") is not False:
  raise ValueError("UNSAFE_V3_QUALIFICATION")
 if v3.get("training_rows")!=672 or v3.get("test",{}).get("n")!=96:
  raise ValueError("UNBOUND_V3_EVALUATION_POPULATION")
 public_snapshot=load_snapshot(ROOT/"research"/"public_sources"/"pubmed-sources-admitted-20261117.json")
 citation_graph=build_from_paths(
   ROOT/"research"/"public_sources"/"pubmed-sources-admitted-20261117.json",
   ROOT/"research"/"public_sources"/"sara-pubmed-sources-20261117.json")
 validate_graph(citation_graph)
 matrix_report=claim_matrix(citation_graph)
 if matrix_report["combinations_checked"]!=207 or matrix_report["scientific_or_clinical_claims_admitted"]!=0:
  raise ValueError("CLAIM_FIREWALL_QUALITY_BOUNDS_BROKEN")
 return type("MUHUBoundHandler",(Handler,),{"manifest":manifest,"examples":rows[:6],
                                         "v3_metrics":v3,"source_snapshot":public_snapshot,
                                         "citation_graph":citation_graph,
                                         "claim_matrix":matrix_report})

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--host",default="0.0.0.0",choices=["127.0.0.1","0.0.0.0"])
 p.add_argument("--port",default=7860,type=int)
 p.add_argument("--data-dir",default="dataset",type=Path)
 args=p.parse_args()
 if not 1024<=args.port<=65535:raise SystemExit("BAD_PORT")
 server=ThreadingHTTPServer((args.host,args.port),create_handler(args.data_dir))
 print(json.dumps({"state":"LOCAL_RESEARCH_PREVIEW_ONLY","host":args.host,"port":args.port,
                   "source_training_rows":server.RequestHandlerClass.manifest["public_training_records"],
                   "scientific_ready":False}),flush=True)
 server.serve_forever()

if __name__=="__main__":main()
