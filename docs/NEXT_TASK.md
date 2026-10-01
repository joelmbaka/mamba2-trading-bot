# Next Authorized Task

## M028 — await first prospective paper decision

Current pre-decision feature SHA:

`499e088e8d77bdf7fff81f34b549ae93c5c7e8be`

Latest readiness result:

`8b715961e58c2e8a56069d26c780db52d46b194c`

Current readiness:

**SOURCE_NOT_READY**

Reason:

- BIS currently reaches **2026-09-29**;
- October requires BIS through **2026-09-30**;
- OECD **2026-08** requirement already passes;
- all eight fixed broker currencies currently pass quote+margin readiness.

Before the scheduled decision, the only authorized action is:

`m028_stage3_readiness`

It may be rerun to check whether the fixed source gate has become ready. It
must not compute formation signs, target sides/lots, or P/L.

First decision timestamp:

**2026-10-07T12:00:00Z**

At or after that timestamp, run exactly:

`m028_stage3_first_decision`

The action is time-gated and append-only. It creates or returns the single
`2026-10` decision record. Do not change parameters, sources, universe,
leverage/margin caps, or timing before that run.

After the first record exists, document its result before authorizing any
holding-period mark or subsequent monthly decision.

Safety remains:

- paper/shadow only;
- no real orders or position changes;
- no trade-history/balance/equity reads;
- no retrospective M028 net economics;
- no M027 rerun;
- no M021 post-cutoff outcome use;
- no merge/deploy/live promotion.
