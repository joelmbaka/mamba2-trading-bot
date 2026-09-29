# Next Authorized Task

## Milestone 024 — Symbol Specialization Research

M023 has closed with **zero supported Stage-B sessions**.

Create the next feature branch from the final durable M023 closeout commit:

`symbol-specialization-research`

Protocol file:

`docs/milestones/024-symbol-specialization-research.md`

## First gate — diagnostic only

Use only the accepted, already-seen M023 Stage-A D-B / BUY-only all-hours
evidence on the fixed 225-date research sample:

`2025-08-25T00:00:00Z` → `2026-07-08T00:00:00Z`

Ordered date-list SHA-256:

`50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0`

The bounded symbol hypotheses are exactly:

- **SYM-R** — all five symbols;
- **SYM-UJ** — USDJPY only;
- **SYM-JPY** — EURJPY + GBPJPY + USDJPY;
- **SYM-NONJPY** — EURUSD + GBPUSD.

Do not add or search arbitrary symbol subsets.

The diagnostic gate may aggregate existing deterministic D-B evidence by these
fixed subsets and report total/fold/week/symbol contribution and stability. It
must not run a fresh symbol-filtered strategy replay yet.

## Hypothesis source

In accepted D-B, USDJPY was the only positive full-sample symbol:

- closed trades: **1,335**;
- net realized P/L: **+$15.0437376424**;
- mean trade P/L: **+$0.0112687173**.

This is a hypothesis generator only. USDJPY was not positive in every
chronological fold, so it is not evidence of a proven or production-ready
USDJPY-only edge.

## Hard boundaries

Do not:

- inspect/open historical holdout
  `2026-07-08T00:00:00Z` → `2026-09-25T00:00:00Z`;
- use M021 post-cutoff outcomes;
- use M025 public-benchmark economic results to tune M024;
- run fresh symbol-filtered economics before a later prospective freeze;
- add symbol subsets;
- revive SELL/BOTH as candidate directions;
- mine sessions or weekdays;
- add M15;
- alter production defaults;
- merge or deploy;
- enable/place/modify/close real MT5 orders.

First freeze the M024 diagnostic protocol on the new branch, then implement only
the deterministic read-only diagnostic machinery and tests.
