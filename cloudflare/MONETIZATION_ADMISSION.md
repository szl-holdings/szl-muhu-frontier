# Cloudflare Monetization Gateway — safe SZL onboarding

**Source-only preparation. This repository does not configure Cloudflare
DNS, publish a Worker, enable a paid route, or accept a real transaction.**

The product web origin `https://a-11-oy.com/` and proof origin
`https://a11oy.net/` returned HTTP 200 in the public check on
2026-11-17 at approximately 19:38 UTC. That observation is **not**
proof that Cloudflare's x402 monetization rules are correctly
configured or that any payments settled.

## Important documented x402 v2 protocol

Cloudflare Monetization Gateway (closed beta) uses version **2**:

```http
GET /api/premium/EXAMPLE HTTP/1.1
Host: a-11-oy.com
```

The gateway responds with a `402 Payment Required` containing the
Base64-encoded JSON `PAYMENT-REQUIRED` response header. Its decoded
object includes `x402Version: 2`, a resource with URL,
and an `accepts` array. Typical options contain
`scheme: exact` or `upto`, a CAIP-2 `network`,
`asset`, `amount` in decimal-string atomic units,
`payTo` and `maxTimeoutSeconds`.

**Never send private signing keys into a chat, GitHub issue, HTTP URL,
web form, or public repository.** An x402 client, operating within
its own authorized wallet, prepares `PAYMENT-SIGNATURE` and retries
the same request. Cloudflare verifies the signature and settles via
the facilitator. That successful paid flow must be reconciled with
an actual settlement receipt and account revenue analytics.

Cloudflare forwards verified requests to an origin using the
`PAYMENT-CONTEXT` JWT. The **origin** must verify JWT signature
(Ed25519), issuer/audience, expiration and intended paid resource
using the pinned JWKS before serving paid content. An unsigned or
merely decoded JWT must fail closed. No such origin validator is
implemented in this non-paid MUHU research preview.

References (official):
- [Monetization Gateway](https://developers.cloudflare.com/monetization-gateway/)
- [x402 protocol](https://developers.cloudflare.com/monetization-gateway/x402/)
- [Payment validation](https://developers.cloudflare.com/monetization-gateway/configuration/payment-validation/)
- [Rules / prices](https://developers.cloudflare.com/monetization-gateway/configuration/rules/)

## Owner-admin verification checklist

1. Confirm the current authoritative Cloudflare zone and account in
   the Cloudflare dashboard (not by copying credential values).
2. Read and pin the existing Monetization Gateway rules: zone,
   URL patterns, HTTP methods, audience, prices, receiving wallet,
   rule IDs and enabled state. Do not replace a full ruleset without
   preserving every existing rule ID and verified intended behavior.
3. Keep the **public** MUHU research proof, docs, source, datasets and
   `/healthz` reachable. Define a *distinct* premium research API
   that is source-bound, license-cleared and has a real paid origin
   contract. An example route name is not evidence it exists.
4. Probe **one actual configured premium route** without a
   `PAYMENT-SIGNATURE`: require exact HTTP 402 and inspect
   the Base64/JSON v2 `PAYMENT-REQUIRED` structure using
   `muhu.x402.inspect_challenge`. This check does not pay.
5. Independently validate **origin-side** `PAYMENT-CONTEXT`
   signature/JWKS and all authorization claims before releasing
   premium resources. Never treat the presence of a header alone
   as a successful payment.
6. Run exactly one authorized, small, real paid test using an
   account-controlled buyer and the official client and facilitator.
   Confirm settlement network transaction/receipt, delivered
   response, gateway account analytics, payout address and
   net fee accounting. No retry storm; stop on any mismatch.
7. Classify the funnel distinctly:
   `402_challenge`, `buyer_signed`, `gateway_verified`,
   `origin_authorized`, `settled`, `net_revenue`,
   and `failure_or_refund`. Empty denominators are
   `UNAVAILABLE`, not 0% success.
8. Require a source-bound, immutable readback of the Cloudflare
   configuration and real settlement before declaring monetization
   `OPERATIONAL`.

## Current gate

The current MUHU source has a **read-only x402 challenge structure
validator**, 14 negative/positive software tests and public documentation.
It does not read the user's receiving wallet, run a facilitator,
validate Cloudflare's `PAYMENT-CONTEXT` signature, spend USDC, settle
any transaction or issue paid content.

No Cloudflare API credential or authenticated Cloudflare management
workflow was accessible from the authorized workstation environment
at observation. The existing product domain remains reachable, but
**verified settlements and revenue remain UNOBSERVED**.

Do not invent merchant rules, move DNS, disable existing controls,
change wallets or post a new Worker unless the account permissions,
the exact existing rules and an appropriate maintenance window are
verified first.
