"""Pure Python HTML/SVG view of selected PubMed editorial history.

Only bounded, publicly indexed version/correction metadata. A blank
editorial notice field is NOT a paper-quality or retraction clearance.
"""
from __future__ import annotations
from html import escape
from urllib.parse import urlencode

from .lifecycle import lookup

def page(snapshot:dict,graph:dict,selected_pmid:str|None=None)->str:
    node_map={n["pmid"]:n for n in graph["nodes"] if n["kind"]=="publication"}
    selected=lookup(snapshot,selected_pmid) if selected_pmid else None
    categories=snapshot["editorial_category_counts"]
    group_info=snapshot["version_components"]
    groups=group_info["groups"]
    version_pairs=[g for g in groups if len(g["selected_pmids"])>1]
    html=[
        '<p class="eyebrow">MUHU · Public PubMed Editorial History Witness</p>',
        '<h1>Scientific papers evolve. Evidence must remember versions.</h1>',
        '<div class="banner"><strong>EDITORIAL METADATA ONLY, NOT A RESEARCH-QUALITY JUDGMENT.</strong> '
        'A PubMed preprint, update link, correction, or expression-of-concern '
        'metadata relationship is a recorded source relationship—not proof '
        'that a study is right or wrong. A paper with no indexed notice '
        'is NOT certified clean, peer-reviewed, reliable, or unretracted.</div>',
        '<p>The full selected MUHU bibliography remains <strong>23 public citations</strong>. '
        'Their NCBI EFetch metadata includes published versions, preprint '
        'flags, and linked editorial records at the recorded observation time. '
        'One pair in the sample is explicitly version-linked; a preprint '
        'and its linked update should not automatically be counted as '
        'independent corroborating studies.</p>',
        '<section class="cards">',
        f'<article class="card"><div class="kpi">{len(snapshot["normalized_records"])}</div><strong>Selected indexed publications</strong></article>',
        f'<article class="card"><div class="kpi">{group_info["selected_pmid_version_group_count"]}</div><strong>Distinct observed version groups</strong></article>',
        f'<article class="card"><div class="kpi">{categories.get("PREPRINT_WITH_VERSION_UPDATE_LINK",0)}</div><strong>Preprints with version links</strong></article>',
        '<article class="card"><div class="kpi">0</div><strong>Claims scientifically validated</strong></article>',
        '</section>',
        '<h2>Inspect one indexed citation</h2>',
        '<form action="/lifecycle" method="get" class="card">',
        '<label for="pmid">Selected PubMed article</label> <select id="pmid" name="pmid">'
    ]
    for row in snapshot["normalized_records"]:
        pmid=row["pmid"]
        title=node_map[pmid]["label"]
        chosen=" selected" if selected_pmid==pmid else ""
        excerpt=title if len(title)<=80 else title[:77].rstrip()+"…"
        html.append(f'<option value="{escape(pmid)}"{chosen}>PMID {escape(pmid)} — {escape(excerpt)}</option>')
    html.append('</select> <button type="submit">Inspect editorial history</button></form>')
    if selected is not None:
        html.append('<section class="card"><h2>Source metadata readback</h2>')
        if selected["state"].startswith("UNAVAILABLE"):
            html.append('<p class="tag">NOT IN SELECTED SOURCE SNAPSHOT</p>'
                        '<p>This does not mean the publication is nonexistent.</p>')
        else:
            row=selected["publication"]
            pub=node_map[selected["pmid"]]
            html.append('<h3><a href="'+escape(pub["source_url"],quote=True)+'" rel="noopener noreferrer">'
                        +escape(pub["label"])+'</a></h3>')
            html.append('<p>Editorial-index observation: <strong>'
                        +escape(row["editorial_index_state"])+'</strong></p>')
            html.append('<p>PubMed publication types: '
                        +escape("; ".join(row["publication_types"]))+'</p>')
            html.append('<p>PubMed index status: '
                        +escape(row["indexing_status_reported"])+'; publication status: '
                        +escape(row["publication_status_reported"])+'</p>')
            html.append('<p>Version group: <code>'
                        +escape(selected["version_group"]["version_group_id"])
                        +'</code> · selected IDs: '
                        +escape(", ".join(selected["version_group"]["selected_pmids"]))+'</p>')
            if row["correction_links"]:
                html.append('<h3>Indexed related citation links</h3><ul>')
                for link in row["correction_links"]:
                    ref=link["linked_pmid"]
                    text=(f'PMID {ref}' if ref else "Related PMID not supplied by NCBI")
                    html.append('<li>'+escape(link["type"])+" — ")
                    if ref is not None:
                        html.append('<a rel="noopener noreferrer" href="https://pubmed.ncbi.nlm.nih.gov/'
                                    +escape(ref)+'/">'+escape(text)+'</a>')
                    else:
                        html.append(escape(text))
                    if link["reference_label_as_reported"]:
                        html.append(' · '+escape(link["reference_label_as_reported"]))
                    html.append('</li>')
                html.append('</ul>')
            else:
                html.append('<p><strong>No tracked correction/update links in this capture.</strong> '
                            'This is not evidence of a clean or uncorrected publication history.</p>')
            html.append('<p class="muted">Observed at '
                        +escape(selected["source_observed_utc"])+'; snapshot SHA-256 <code>'
                        +escape(selected["source_snapshot_sha256"])
                        +'</code>. Historical-only source; not refreshed by each user request.</p>')
        html.append('</section>')
    html.append('<h2>Visible version relationships</h2><section class="card">')
    if not version_pairs:
        html.append('<p>No explicit pair among these 23 selected records was '
                    'linked by an NCBI update/republication relationship. '
                    'External versions may still exist.</p>')
    for group in version_pairs:
        ids=group["selected_pmids"]
        html.append('<p><strong>Version group — '
                    +escape(" ↔ ".join(ids))+'</strong></p>')
        html.append('<p>Source-derived association, not evidence of identical results, '
                    'independent replication, or confirmed model performance.</p>')
        for id in ids:
            html.append('<p><a href="https://pubmed.ncbi.nlm.nih.gov/'+escape(id)+
                        '/" rel="noopener noreferrer">PMID '+escape(id)+'</a> — '
                        +escape(node_map[id]["label"])+'</p>')
    html.append('</section>')
    outside=group_info["unselected_linked_version_targets"]
    html.append('<h2>Linked records outside this sample</h2>')
    html.append('<p>'+str(len(outside))+' indexed version links point '
                'to articles that have not been admitted to the selected '
                '23-record source set. Their content and editorial status remain '
                'unobserved here.</p>')
    html.append('<p><a href="/api/v1/lifecycle">Inspect normalized source '
                'notice counts and version groups</a></p>')
    html.append('<p><a href="/graph">Return to the source provenance graph</a></p>')
    html.append('<footer>Upstream: NCBI PubMed EFetch XML and its typed '
                'CommentsCorrections relationships, revision captured '
                +escape(snapshot["observed_utc"])+'. '
                'No abstract, full text, unpublished collaborator material or '
                'patient data is stored. No live external provider calls, '
                'clinical advice, paper-quality scoring or treatment decisions. '
                'Historical non-observation of a retraction is not a clean-status '
                'attestation. /readyz remains HTTP 503.</footer></main></html>')
    return "".join(html)
