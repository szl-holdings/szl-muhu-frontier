"""Server-rendered evidence map: SVG is a 2D diagram, NOT a 3D simulation.

A visual *citation/provenance* graph over author-query and topic-selected
records only. No JavaScript, patient inputs, therapeutic assertions or
model inference. Every clickable publication URI is a validated PubMed URL.
"""
from __future__ import annotations

from html import escape
from collections import defaultdict

TOPIC_LABELS={
 "sara":"Sara public author-index citations",
 "vidal":"Vidal-Gadea author-query candidates",
 "wwox":"WWOX selected public citations",
 "worm_methods":"Worm movement/calcium research",
}
LANE_COLORS={"sara":"#8ddfe8","vidal":"#d7bcff","wwox":"#f6c379","worm_methods":"#a8d9ae"}

def svg_map(view):
    records=[node for node in view["nodes"] if node["kind"]=="publication"]
    order={name:i for i,name in enumerate(TOPIC_LABELS)}
    records.sort(key=lambda row:(min(order.get(q,9) for q in row["query_scope"]),int(row["pmid"])))
    ys={row["id"]:132+i*52 for i,row in enumerate(records)}
    height=220+len(records)*52
    parts=[
      f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 {height}" '
      'role="img" aria-label="Two-dimensional SVG provenance map of selected public PubMed citation identifiers, not biological associations">',
      '<defs>',
      '<linearGradient id="pocket" x1="0" y1="0" x2="1" y2="1">'
      '<stop offset="0" stop-color="#19374a"/><stop offset="1" stop-color="#091b2d"/>'
      '</linearGradient>',
      '<radialGradient id="halo"><stop offset="0" stop-color="#37717e" stop-opacity=".35"/>'
      '<stop offset="1" stop-color="#133140" stop-opacity=".04"/></radialGradient>',
      '</defs>',
      f'<rect width="1120" height="{height}" rx="16" fill="url(#pocket)"/>',
      f'<ellipse cx="540" cy="{height/2:.0f}" rx="550" ry="{max(200,height/2):.0f}" '
      'fill="url(#halo)"/>',
      '<text x="42" y="44" font-size="20" fill="#e8fbff" font-weight="bold">'
      'SOURCE PROVENANCE // NOT A BIOLOGICAL CAUSAL GRAPH</text>',
      '<text x="42" y="68" font-size="13" fill="#a8d2dd">'
      'Query selection → indexed PMID → reported DOI | NCBI PubMed ESummary v2</text>',
    ]
    topics=defaultdict(list)
    for row in records:
        for t in row["query_scope"]:
            topics[t].append(row["id"])
    center={}
    for t,ids in topics.items():
        center[t]=sum(ys[x] for x in ids)/len(ids)
    for t,y in center.items():
        color=LANE_COLORS[t]
        label={"sara":"SARA","vidal":"VIDAL-GADEA","wwox":"WWOX","worm_methods":"WORM-METHODS"}[t]
        parts.append(f'<rect x="37" y="{y-26:.1f}" width="219" height="54" rx="11" '
                     f'fill="#133143" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<text x="50" y="{y-3:.1f}" font-size="15" fill="{color}" '
                     f'font-weight="bold">{escape(label)}</text>')
        parts.append(f'<text x="50" y="{y+16:.1f}" font-size="12" '
                     f'fill="#adc6d7">{len(ids)} selected PMID records</text>')
        for paper in ids:
            py=ys[paper]
            parts.append(f'<path d="M256,{y:.1f} C292,{y:.1f} 300,{py:.1f} 327,{py:.1f}" '
                         f'fill="none" stroke="{color}" stroke-opacity=".5" stroke-width="1.4"/>')
    for row in records:
        y=ys[row["id"]]
        color=LANE_COLORS[row["query_scope"][0]]
        title=row["label"]
        summary=title if len(title)<=55 else title[:52].rstrip()+"…"
        doi=row.get("doi")
        if doi:
            doi_disp=doi if len(doi)<=28 else doi[:26]+"…"
            parts.append(f'<path d="M827,{y} C852,{y} 858,{y} 880,{y}" '
                         'fill="none" stroke="#5faaba" stroke-width="1.3" stroke-opacity=".7"/>')
            parts.append(f'<a href="{escape("https://doi.org/"+doi,quote=True)}" '
                         'target="_blank" rel="noopener noreferrer">')
            parts.append(f'<rect x="884" y="{y-19}" rx="9" width="204" height="38" '
                         'fill="#214252" stroke="#4c8494"/>')
            parts.append(f'<text x="899" y="{y+4}" fill="#c8e7f4" font-size="12">'
                         +escape(doi_disp)+'</text><title>'+escape("DOI "+doi)
                         +'</title></a>')
        parts.append(f'<a href="{escape(row["source_url"],quote=True)}" '
                     'target="_blank" rel="noopener noreferrer">')
        parts.append(f'<rect x="327" y="{y-20}" rx="10" width="500" height="40" '
                     f'fill="#133149" stroke="{color}" stroke-width="1.2"/>')
        parts.append(f'<text x="340" y="{y-3}" font-size="13" '
                     f'fill="{color}" font-weight="bold">PMID {escape(row["pmid"])}</text>')
        parts.append(f'<text x="435" y="{y+4}" font-size="13" '
                     'fill="#edfaff">'+escape(summary)+'</text>')
        parts.append('<title>'+escape(title)+
                     ' — indexed citation metadata; no scientific validity inferred</title></a>')
    parts.append(f'<rect x="327" y="{height-59}" width="754" height="38" rx="9" '
                 'fill="#152e42" stroke="#4d7e8b"/>')
    parts.append(f'<text x="341" y="{height-35}" fill="#b7d8e2" font-size="12">'
                 'All citations retrieved via NCBI ESummary v2, at recorded dates. '
                 'No verified biological or therapeutic edges.</text></svg>')
    return "".join(parts)

def page(view,search=None):
    selected=view["selected_publications"]
    topic=view["topic"]
    parts=[
      '<p class="eyebrow">MUHU · bibliographic provenance graph · pure Python</p>',
      '<h1>Connect research sources, not unsupported claims</h1>',
      '<div class="banner"><strong>RESEARCH SOURCE MAP ONLY.</strong> '
      'No gene–disease causal graph, genomic/therapeutic prediction, or scientific '
      'validation is claimed. These are selected PubMed citations, not all '
      'publications by Sara or Vidal-Gadea; author-name candidates are not '
      'independently identity-adjudicated. No private wet-lab or patient data.</div>',
      '<p>The evidence graph has typed, auditable relationships: a PubMed '
      'identifier is in a selected snapshot, belongs to a recorded search scope, '
      'and may have a DOI. No edge says a gene causes a disease, '
      'or that a therapy is effective.</p>',
      '<section class="cards">',
      '<article class="card"><div class="kpi">'+str(selected)+'</div><strong>Selected citations</strong></article>',
      '<article class="card"><div class="kpi">'+str(len(view["nodes"]))+'</div><strong>Bounded provenance nodes</strong></article>',
      '<article class="card"><div class="kpi">'+str(len(view["edges"]))+'</div><strong>Mechanical retrieval edges</strong></article>',
      '<article class="card"><div class="kpi">0</div><strong>Biomedical causal claims</strong></article>',
      '</section>',
      '<h2>Explore source selection</h2><form action="/graph" method="get" class="card">',
      '<p><label for="topic">Research lane</label> <select id="topic" name="topic">',
    ]
    labels={"all":"All selected public research"}
    labels.update(TOPIC_LABELS)
    for name,label in labels.items():
        sel=" selected" if name==topic else ""
        parts.append(f'<option value="{escape(name)}"{sel}>{escape(label)}</option>')
    parts.append('</select> <button type="submit">Update provenance map</button></p></form>')
    parts.append("<section class='card'>"+svg_map(view)+"</section>")
    parts.append('<p class="muted">This is a server-rendered, layered SVG '
                 'projection—not an interactive 3D model, a knowledge-discovery '
                 'system, or biological evidence. Select a topic above or open '
                 'the linked PubMed identifier/DOI for source metadata.</p>')
    parts.append('<p><a href="/api/v1/graph?topic='+escape(topic,quote=True)+'">'
                 'Inspect every typed graph edge and SHA-256 identity</a></p>')
    parts.append('<h2>Title-only research discovery</h2>')
    parts.append('<p>Find matching words in the 23 indexed titles. '
                 'This does not read full texts or infer relationships. '
                 'Do not enter patient, unpublished, or confidential text.</p>')
    parts.append('<form action="/graph" method="get" class="card">'
                 '<input type="hidden" name="topic" value="'+escape(topic,quote=True)+'">'
                 '<label for="search">Public scientific keywords</label> '
                 '<input id="search" type="search" name="q" '
                 'placeholder="e.g. AncestryGeni or locomotion" '
                 'minlength="3" maxlength="100" pattern="[A-Za-z0-9 -]{3,100}">'
                 '<button type="submit">Search bounded titles</button></form>')
    if search is not None:
        parts.append('<section class="card"><h2>Title search</h2>')
        parts.append('<strong>'+escape(search["state"])+'</strong>')
        parts.append('<p class="muted">Title-only lexical ranking; '
                     'score is not a probability or scientific claim.</p>')
        for row in search["results"]:
            parts.append('<p><a href="'+escape(row["source_url"],quote=True)+
                         '" rel="noopener noreferrer">PMID '+escape(row["pmid"])+
                         ' · '+escape(row["title"])+'</a></p>')
        parts.append('</section>')
    parts.append('<h2>Falsifiable boundaries</h2><section class="card"><p>'
                 'The graph does not contain gene-to-therapy, gene-to-disease, '
                 'variant-to-phenotype, or study-to-treatment-effect edges. '
                 'Absent PMIDs return UNAVAILABLE—not nonexistent. '
                 'Every publication can be traced to the exact source-snapshot '
                 'SHA-256 and its explicit selection topic. The source graph '
                 'requires all edges to be acyclic, provenance-typed, and '
                 'noncausal; malformed or tampered snapshots fail closed.</p></section>')
    parts.append('<footer>Source graph SHA-256 <code>'+
                 escape(view["source_graph_sha256"])+'</code> · '
                 'Filtered projection SHA-256 <code>'+escape(view["view_sha256"])+'</code>. '
                 'Hashes provide byte identity, not an independent digital '
                 'signature or scientific proof. W3C PROV / Biolink are '
                 'informative design references, not compliance claims. '
                 'Hugging Face Space remains research-only and /readyz HTTP 503.'
                 '</footer></main></html>')
    return "".join(parts)
