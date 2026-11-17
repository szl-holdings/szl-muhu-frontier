"""Executive, investor and developer proof pages rendered by pure Python.

This is a historical, SHA-bound source-status snapshot; external URLs
are descriptive links, not live independently verified payment or CI.
"""
from __future__ import annotations

from html import escape

from .release_proof import PINNED_SHA256


def source_chain_svg() -> str:
    stages = (
        ("GITHUB", "CANONICAL SOURCE", "#8ee7d1"),
        ("HUGGING FACE", "RESEARCH PREVIEW", "#8ee7d1"),
        ("CLOUDFLARE", "SETTLEMENT UNVERIFIED", "#f0c48a"),
        ("PYPI", "UNPUBLISHED AS OBSERVED", "#f0c48a"),
    )
    out = [
        '<svg viewBox="0 0 1140 214" xmlns="http://www.w3.org/2000/svg" '
        'role="img" aria-label="Release chain from canonical GitHub source to '
        'Hugging Face preview, Cloudflare settlement not verified, and PyPI '
        'publication not yet verified">',
        '<rect x="0" y="0" width="1140" height="214" rx="19" fill="#0b2633"/>',
        '<text x="36" y="32" fill="#d8f9f2" font-size="17" '
        'font-weight="700">SOURCE → PREVIEW → EDGE PAYMENT → PUBLICATION</text>',
    ]
    for idx, (name, state, accent) in enumerate(stages):
        x = 36 + 281 * idx
        out.append(
            f'<rect x="{x}" y="63" width="246" height="114" rx="16" '
            f'fill="#173848" stroke="{accent}" stroke-width="2"/>'
        )
        out.append(
            f'<text x="{x+16}" y="98" fill="#eefcff" font-size="17" '
            f'font-weight="700">{escape(name)}</text>'
        )
        out.append(
            f'<text x="{x+16}" y="130" fill="{accent}" '
            f'font-size="11" font-weight="700">{escape(state)}</text>'
        )
        if idx < len(stages) - 1:
            end = x + 276
            out.append(
                f'<path d="M{x+246} 120 L{end} 120" '
                'fill="none" stroke="#638c94" stroke-width="2"/>'
            )
    out.append(
        '<text x="36" y="200" fill="#a7c6cf" font-size="12">'
        'An observed page or challenge is not a settlement, release, or clinical claim.'
        '</text></svg>'
    )
    return "".join(out)


def page(document: dict, *, audience: str) -> str:
    if audience not in ("investors", "developers"):
        raise ValueError("UNADMITTED_PUBLIC_AUDIENCE")
    src = document["source"]
    hf = document["research_preview"]
    dist = document["distribution"]
    science = document["scientific"]
    web = document["external_web"]
    time = escape(document["observed_utc"])
    links = [
        ("Canonical GitHub source", src["repo"]),
        ("Live research Space", hf["repo"]),
        ("Public reference dataset", document["research_dataset"]["repo"]),
        ("Product website", web["product_url"]),
        ("Public proof website", web["proof_url"]),
    ]
    heading = (
        "MUHU — An evidence-first research platform"
        if audience == "investors"
        else "MUHU — Pure-Python developer release"
    )
    body = [
        '<p class="eyebrow">SZL Holdings · Evidence-driven research infrastructure</p>',
        f"<h1>{escape(heading)}</h1>",
        '<div class="banner"><strong>HISTORICAL RELEASE SNAPSHOT, '
        'NOT A LIVE FINANCIAL OR DEPLOYMENT FEED.</strong> '
        f'Recorded {time}. Research preview is not clinical qualification. '
        'Cloudflare settlement, earned revenue and PyPI publication '
        'remain unverified or unpublished.</div>',
        source_chain_svg(),
        '<section class="cards">',
        '<article class="card"><div class="kpi">23</div>'
        '<strong>Selected public citations</strong>'
        '<p>Source-only PubMed identifiers, not independently validated studies.</p></article>',
        '<article class="card"><div class="kpi">22</div>'
        '<strong>Observed version groups</strong>'
        '<p>Preprint/update links limit double-counting of citation versions.</p></article>',
        '<article class="card"><div class="kpi">207</div>'
        '<strong>Deterministic evidence-policy checks</strong>'
        '<p>Software checks, not biological experiments or model accuracy.</p></article>',
        '<article class="card"><div class="kpi">HOLD</div>'
        '<strong>Scientific qualification</strong>'
        '<p>Independent human-adjudicated benchmarks have not been completed.</p></article>',
        '</section>',
    ]
    if audience == "investors":
        body += [
            '<h2>What exists today</h2>',
            '<section class="cards">',
            '<article class="card"><strong>Audit-friendly original research software</strong>'
            '<p>Python-rendered methodological screens, exact source identities, '
            'publication-version lineage and fail-closed claim analysis.</p></article>',
            '<article class="card"><strong>Reproducible source governance</strong>'
            '<p>GitHub protected main governs the public source. Hugging Face hosts '
            'a historical, CPU-based research preview with public datasets.</p></article>',
            '<article class="card"><strong>Clear scientific boundaries</strong>'
            '<p>A real published article is not automatically valid evidence for '
            'genetics, a gene therapy, or a collaborator endorsement.</p></article>',
            '</section>',
            '<h2>What is not yet commercially proven</h2>',
            '<section class="card"><p>There is currently no independently '
            'verified Cloudflare payment settlement, paid-customer cohort, '
            'recurring revenue, PyPI release receipt, or clinical product '
            'qualification in this observed release snapshot.</p>',
            '<p>Cloudflare payment challenges are not revenue. Local package '
            'builds are not PyPI publications. Passing software tests is not '
            'independent biomedical validation.</p></section>',
            '<h2>Evidence investors can audit</h2>',
        ]
    else:
        body += [
            '<h2>Architecture</h2>',
            '<section class="card"><p><code>GitHub protected main → '
            'pure-Python package and tests → Hugging Face Docker research '
            'preview → audited Cloudflare monetization (HOLD) → '
            'PyPI Trusted Publishing (HOLD)</code></p>',
            '<p>The library has zero mandatory third-party runtime dependencies. '
            'The hosted site requires the source repository and pinned public '
            'metadata files; the PyPI wheel only distributes the library and CLI.'
            '</p></section>',
            '<h2>Local, source-verifiable quickstart</h2>',
            '<section class="card"><pre><code>git clone '
            'https://github.com/szl-holdings/szl-muhu-frontier.git\n'
            'cd szl-muhu-frontier\n'
            'python -m pip install .\n'
            'muhu-witness --source-bound true --sample-n 32 '
            '--age-days 2 --independent-check true '
            '--contradiction false\n'
            'python -B -m unittest discover -s tests -v</code></pre>'
            '<p class="muted">The CLI status REVIEWABLE means only '
            'synthetic methodological metadata suffices for human review.'
            ' It never authorizes training or clinical action.</p></section>',
            '<h2>APIs and integration boundaries</h2>',
            '<section class="cards">',
            '<article class="card"><strong>Research preview health</strong>'
            '<p><code>GET /healthz</code> is liveness only; '
            '<code>GET /readyz</code> remains HTTP 503.</p></article>',
            '<article class="card"><strong>Source-to-claim verification</strong>'
            '<p><code>GET /api/v1/claim-gate</code> returns structured '
            'requirements and source provenance, not scientific conclusions.</p></article>',
            '<article class="card"><strong>Publication and graph lineage</strong>'
            '<p><code>GET /api/v1/graph</code> and '
            '<code>GET /api/v1/lifecycle</code> expose selected '
            'bibliographic evidence with immutable hashes.</p></article>',
            '<article class="card"><strong>Release and revenue admission</strong>'
            '<p><code>GET /api/v1/release-proof</code> exposes a frozen '
            'historical snapshot. No real-time revenue API is provided.</p></article>',
            '</section>',
            '<h2>Developer source links</h2>',
        ]
    body.append('<section class="cards">')
    for name, uri in links:
        body.append(
            '<article class="card"><strong>' + escape(name) + '</strong>'
            '<p><a rel="noopener noreferrer" href="' +
            escape(uri, quote=True) +
            '">Open authoritative public resource</a></p></article>'
        )
    body.append('</section>')
    body += [
        '<h2>Release gates</h2>',
        '<section class="card">',
        '<p><strong>GitHub:</strong> canonical source snapshot '
        '<code>' + escape(src["protected_main_observed"][:12]) + '</code> '
        '(observed, not the new release commit).</p>',
        '<p><strong>Hugging Face:</strong> ' +
        escape(hf["runtime_observed"]) + ' at observation; revision '
        '<code>' + escape(hf["revision_observed"][:12]) + '</code>. '
        'Post-change source parity must be independently checked.</p>',
        '<p><strong>Cloudflare:</strong> both public web origins responded '
        'HTTP 200 at observation. Monetization rule readback, origin '
        'payment JWT validation and settlement remain unverified.</p>',
        '<p><strong>PyPI:</strong> package candidate ' +
        '<code>' + escape(dist["candidate_name"]) + '</code> ' +
        'version <code>' + escape(dist["version"]) + '</code>; ' +
        escape(dist["publication_state"]) +
        '. Do not attempt production pip install from PyPI until a '
        'verified registry artifact exists.</p>',
        '<p><strong>Research:</strong> the MUHU v3 synthetic classifier '
        'remains ' + escape(science["model_state"]) + ', not trained '
        'on Sara/Vidal laboratory records and not admitted to Flagship54.</p>',
        '</section>',
        '<p><a href="/api/v1/release-proof">Inspect frozen JSON evidence '
        'with exact snapshot SHA-256</a></p>',
        '<footer>Release status snapshot SHA-256: <code>' +
        PINNED_SHA256 + '</code>. Source observation at ' + time +
        '. Original software MIT; synthetic training data separately '
        'CC BY 4.0. No partner endorsement, revenue recognition, '
        'payment settlement, or clinical clearance is implied. '
        'Review GitHub and hosting-provider receipts for fresh deployment '
        'status before making production claims.</footer></main></html>',
    ]
    return "".join(body)
