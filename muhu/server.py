"""MUHU source-bound research viewer, pure Python + SVG, never clinical."""
from __future__ import annotations
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
import argparse
import json
import math

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
<nav><a href="/">MUHU home</a><a href="/methods">Evidence protocol</a><a href="/sara">Sara research</a><a href="/vidal">Vidal research</a><a href="/genomics">Genomic context</a><a href="/api/v1/manifest">Machine-readable evidence</a></nav>
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

class Handler(BaseHTTPRequestHandler):
 server_version="SZL-MUHU/2"
 manifest:dict={}
 examples:list[dict]=[]

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
 return type("MUHUBoundHandler",(Handler,),{"manifest":manifest,"examples":rows[:6]})

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
