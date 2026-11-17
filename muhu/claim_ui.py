"""Server-rendered, no-JavaScript research Claim Evidence Firewall.

The screen permits only enumerated questions about selected public PMIDs,
not free-text clinical/genomic/partner claims or uploads. Decisions are
explainable deterministic coverage gates, not expert review.
"""
from __future__ import annotations

from html import escape
from urllib.parse import urlencode

from .claim_firewall import CLAIM_CLASSES, EVIDENCE_LEVELS

def page(result:dict,coverage:dict,options:list[tuple[str,str]])->str:
    choices=result["input"]
    state=result["state"]
    src=result["source_provenance"]
    intro=[
       '<p class="eyebrow">MUHU Research Claim Evidence Firewall · v1</p>',
       '<h1>A citation is not a scientific conclusion</h1>',
       '<div class="banner"><strong>RESEARCH-ONLY SAFETY GATE.</strong> '
       'This tool verifies only limited bibliographic identity and whether '
       'essential evidence is missing for a proposed claim type. It does not '
       'read the research paper, assess its biological findings, recommend '
       'gene therapy, make diagnostic decisions, or record partner data.</div>',
       '<p>Start from one of the 23 selected public PubMed identifiers, '
       'select the <em>type</em> of statement someone wants to make, '
       'and inspect what MUHU can actually support. '
       'Every biologically consequential statement remains unqualified '
       'until independent primary-source review and human adjudication.</p>',
       '<section class="cards">',
       '<article class="card"><div class="kpi">'+str(coverage["selected_papers"])+
       '</div><strong>Indexed citations</strong></article>',
       '<article class="card"><div class="kpi">'+str(coverage["claim_classes"])+
       '</div><strong>Claim categories examined</strong></article>',
       '<article class="card"><div class="kpi">'+str(coverage["combinations_checked"])+
       '</div><strong>Deterministic source-to-policy tests</strong></article>',
       '<article class="card"><div class="kpi">0</div><strong>Scientific claims validated</strong></article>',
       '</section>',
       '<h2>Ask a bounded research question</h2>',
       '<form action="/claim-gate" method="get" class="card">',
       '<p><label>Selected public PMID <select name="pmid">',
    ]
    for pmid,title in options:
        selected=' selected' if pmid==choices["pmid"] else ""
        short=title if len(title)<72 else title[:69]+"…"
        intro.append(f'<option value="{escape(pmid)}"{selected}>'
                     f'PMID {escape(pmid)} — {escape(short)}</option>')
    intro.append('</select></label></p>')
    intro.append('<p><label>What is being claimed? <select name="claim_type">')
    for key,meta in CLAIM_CLASSES.items():
        selected=' selected' if key==choices["claim_type"] else ""
        intro.append(f'<option value="{escape(key)}"{selected}>'
                     +escape(meta["name"])+'</option>')
    intro.append('</select></label></p>')
    intro.append('<p><label>Expected DOI (optional, public identifier only) '
                 '<input name="doi" type="text" maxlength="220" '
                 'placeholder="e.g. 10.1016/j.omta.2026.201791" value="'
                 +escape(choices.get("doi") or "",quote=True)+'"></label></p>')
    intro.append('<button type="submit">Evaluate the evidence boundary</button></form>')
    intro.append("<h2>Evidence decision: <span class='tag'>"+escape(state)+"</span></h2>")
    intro.append('<section class="card"><strong>'+escape(result["claim_type_label"])+'</strong>')
    for reason in result["reasons"]:
        intro.append('<p>'+escape(reason)+'</p>')
    intro.append('<p class="muted">Required evidence tier: '
                 +escape(result["required_evidence_tier"])+'</p>')
    intro.append('</section>')
    intro.append('<h2>What is verifiable?</h2><section class="cards">')
    flags=[
     ("PMID",result["input"]["pmid"]),
     ("DOI comparison",src["doi_comparison"]),
     ("Original citation source",src["provider"]),
     ("Independent scientific review",result["independent_expert_adjudication"]),
    ]
    for label,value in flags:
        intro.append('<article class="card"><strong>'+escape(label)+'</strong>'
                     '<p>'+escape(str(value))+'</p></article>')
    intro.append('</section>')
    editorial=result.get("source_editorial_history")
    if editorial is not None:
        intro.append('<h2>Indexed editorial and version history</h2><section class="card">')
        intro.append('<p><strong>Observed metadata state:</strong> '+
                     escape(editorial["editorial_index_state"])+'</p>')
        intro.append('<p>Version-linked selected PMIDs: <code>'+
                     escape(", ".join(editorial["selected_version_group_members"]))+
                     '</code></p>')
        intro.append('<p class="muted">Source observed '+
                     escape(editorial["source_observed_utc"])+
                     '. A PubMed update link does not establish identical findings; '
                     'the absence of a correction flag does not prove the publication '
                     'unretracted or its conclusions correct.</p>')
        intro.append('<p><a href="/lifecycle?pmid='+
                     escape(result["input"]["pmid"],quote=True)+
                     '">Inspect the exact editorial history and reported links</a></p></section>')
    intro.append('<h2>Evidence required before making this claim</h2>')
    if result["requirements_not_verified"]:
        intro.append('<section class="card"><ol>')
        for item in result["requirements_not_verified"]:
            intro.append('<li>'+escape(item)+'</li>')
        intro.append('</ol></section>')
    else:
        intro.append('<section class="card"><p>For a citation identity check '
                     'only, the reported PMID/DOI match in a historical public '
                     'snapshot; this does not validate the paper\'s methods or '
                     'findings.</p></section>')
    intro.append('<h2>Falsifiable scope</h2><p>MUHU can distinguish a '
                 'bibliographic match from an unrelated therapeutic claim. '
                 'The nine categories are deterministic policy tests; '
                 'the counted combinations are <em>not</em> nine independent '
                 'scientific experiments per citation, nor a model-accuracy result.</p>')
    intro.append('<p><a href="/api/v1/claim-gate?'+escape(urlencode({
                "pmid":choices["pmid"],"claim_type":choices["claim_type"],
                **({"doi":choices["doi"]} if choices.get("doi") else {})
               }),quote=True)+'">Inspect canonical machine-readable result</a></p>')
    intro.append('<p><a href="/api/v1/claim-matrix">Inspect all source × claim-type '
                 'policy combinations</a></p>')
    intro.append('<footer>Canonical graph SHA-256: <code>'+
                 escape(src["graph_sha256"])+'</code> · Decision receipt SHA-256: <code>'+
                 escape(result["receipt_sha256"])+'</code>. '
                 'These are integrity checks, not signatures or scientific '
                 'attestations. The public service does not persist these '
                 'inputs; hosting infrastructure may retain ordinary URL '
                 'access logs. Use only nonconfidential public identifiers. '
                 'MUHU /readyz remains HTTP 503 until independent scientific '
                 'review and separate clinical qualification.</footer></main></html>')
    return "".join(intro)
