# Next Authorized Task

## Milestone 021 — prospective paper/forward validation

M020 is **CLOSED**.

Accepted M020 implementation SHA:

`0d85b82278ae08a88f8b5b942fb23ec000b11411`

Frozen M021 protocol commit:

`471892e247942ed91c0bbd9adae46e4a990c5db6`

Frozen protocol:

`docs/milestones/021-prospective-forward-validation.md`

Branch:

`prospective-forward-validation`

## Current authorized phase

Implement only the machinery needed to execute the frozen M021 protocol.

Do **not** inspect, summarize, compare, classify, or otherwise interpret
post-`2026-09-25T00:00:00Z` economic outcomes before the predeclared minimum
window is complete.

The primary window ends:

`2026-10-23T00:00:00Z`

The exact minimum evidence and extension rules are frozen in the M021 milestone
document and must not be changed based on outcomes.

## Frozen arms

Control:

- accepted M019 strategy behavior unchanged.

Candidate:

- reject a new order only when observable decision-time spread is **>10
  points**;
- allow **<=10 points**;
- use only bid/ask observable at submission time.

Do not stack M020-A.

Do not change the threshold.

Do not add symbol, side, time, ATR, SL, TP, trailing, stochastic, EMA, RSI,
trend, position-size, or execution-cost treatments.

## Implementation scope

Prepare deterministic M021 execution support for the frozen protocol.

Allowed work:

1. add protocol constants/metadata needed by the forward-validation harness;
2. support the exact prospective start and fixed cutoff schedule from the
   milestone document;
3. support read-only MT5 export of prospective M1 Bid, Ask M1, M5, and M15 data
   into a dataset isolated from M019/M020;
4. record deterministic manifest metadata and SHA-256 hashes for all source
   artifacts;
5. add paired control/candidate replay support for a supplied **completed**
   M021 window;
6. add the required fixed symbol, BUY/SELL, seven-day-period, spread-boundary,
   safety, P/L, and drawdown reporting fields;
7. add A/B artifact determinism checks;
8. add a readiness gate that refuses economic M021 execution before the
   applicable frozen cutoff is complete;
9. add fixed local-control actions needed for M021 export/validation;
10. add synthetic/unit coverage for the frozen date, threshold, readiness, and
    reporting rules.

## Required regression gates

Before any future M021 economic result is interpreted, preserve exactly:

M019 baseline:

`114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`

M019 diagnostic:

`84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`

If executable code changes, also preserve the accepted M020-D treatment
artifacts exactly:

baseline:

`94259afb5657303c4eb8081feeec9fc4ad64c62d68addc550a0215c04cd2e766`

diagnostic:

`45c67d0ed51c2ec3fb80bff8f13d9f9984730bc68afad774cbbd1ade3806298e`

evidence:

`e9398c614a90e55399a8a5bb2c281277601c99457764a7f290771dc2f438b05a`

## Cost contract

Keep exactly:

`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / SWAP-UNMODELED`

Do not invent actual broker commission, slippage, or swap.

## Safety

Historical/market-data MT5 access remains read-only.

Never:

- enable real MT5 trading;
- place, modify, or close a real MT5 order;
- promote M020-D into production/live strategy behavior;
- inspect early M021 P/L as a basis for changing the protocol;
- tune the >10 threshold from M021 data;
- stack M020-A;
- rewrite accepted replay semantics silently.

## Acceptance for this implementation phase

This machinery phase is acceptable when:

- native and Wine suites pass;
- synthetic M021 protocol/readiness/reporting tests pass;
- immutable M019 control hashes remain exact;
- accepted M020-D historical treatment hashes remain exact if executable code
  changed;
- a pre-cutoff M021 economic action is proven to refuse execution;
- no post-cutoff economic outcome has been interpreted;
- no production/live strategy behavior changed.

After that, M021 waits for the first frozen observation cutoff that satisfies
the protocol.