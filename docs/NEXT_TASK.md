# Next Authorized Task

## Milestone 021 — wait for the frozen primary cutoff

M020 is **CLOSED**.

M021 is **OPEN — PROTOCOL AND EXECUTION MACHINERY FROZEN**.

Branch:

`prospective-forward-validation`

Protocol-freeze commit:

`471892e247942ed91c0bbd9adae46e4a990c5db6`

Accepted M021 machinery implementation SHA:

`f53d38b93434eb52b19f0f12a441e4439822e39e`

Frozen protocol:

`docs/milestones/021-prospective-forward-validation.md`

## Current state

The machinery phase is accepted.

Validation completed on 2026-09-26:

- native: **206 passed, 2 skipped**;
- Wine: **206 passed, 2 skipped**;
- M019 baseline preserved exactly:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`;
- M019 diagnostic preserved exactly:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`;
- M020-D baseline preserved exactly:
  `94259afb5657303c4eb8081feeec9fc4ad64c62d68addc550a0215c04cd2e766`;
- M020-D diagnostic preserved exactly:
  `45c67d0ed51c2ec3fb80bff8f13d9f9984730bc68afad774cbbd1ade3806298e`;
- M020-D evidence preserved exactly:
  `e9398c614a90e55399a8a5bb2c281277601c99457764a7f290771dc2f438b05a`;
- pre-cutoff readiness: **not ready**;
- pre-cutoff primary export: **refused, no export attempted**;
- pre-cutoff paired replay: **refused, no economic results computed**.

No post-cutoff economic outcome has been inspected.

## Do not run the economic validation early

The primary source-data window is:

`[2026-09-25T00:00:00Z, 2026-10-23T00:00:00Z)`

Do not run or bypass the economic replay before:

`2026-10-23T00:00:00Z`

The local-control actions already enforce this gate.

Do not inspect a partial-window P/L, drawdown, symbol result, side result,
calendar-period result, or treatment classification.

## First authorized action at or after the primary cutoff

At or after `2026-10-23T00:00:00Z`:

1. verify the feature branch is clean and matches origin;
2. record exact native/Wine/runtime versions;
3. run `m021_historical_regression` and require all accepted M019/M020-D
   hashes to remain exact;
4. run the read-only `m021_primary_export`;
5. validate the manifest, requested range, row counts, Ask coverage, artifact
   SHA-256 values, and runtime/source metadata;
6. run `m021_primary_pair`;
7. require byte-identical A/B artifacts for control and candidate;
8. apply all treatment-boundary and safety gates;
9. check the **predeclared count thresholds before interpreting economic
   outcomes**.

## Count-gate decision

The primary cutoff can be classified only if all are met:

- control closed trades >= **1,000**;
- candidate closed trades >= **900**;
- candidate closed trades >= **100 per symbol**;
- candidate BUY closed trades >= **300**;
- candidate SELL closed trades >= **300**.

If any threshold is unmet, do not interpret P/L or drawdown. Extend the window
only to the next frozen cutoff:

- 2026-10-30T00:00:00Z
- 2026-11-06T00:00:00Z
- 2026-11-13T00:00:00Z
- 2026-11-20T00:00:00Z

Use the first cutoff that satisfies all count thresholds.

If the eight-week cutoff is reached without all count thresholds, classify
**INSUFFICIENT FOR CLASSIFICATION** and close M021 without tuning.

## Frozen candidate

Candidate remains exactly:

- reject a new order only when observable decision-time spread is **>10
  points**;
- allow **<=10 points**;
- use only bid/ask observable at submission time.

Never:

- stack M020-A;
- change the threshold;
- add symbol, side, session, ATR, SL, TP, trailing, stochastic, EMA, RSI,
  trend, position-size, or execution-cost treatments;
- invent commission, slippage, or swap;
- enable real MT5 trading;
- place, modify, or close a real MT5 order;
- promote M020-D directly to production/live behavior.

Cost contract remains exactly:

`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / SWAP-UNMODELED`

## Classification

Use only the classification rule already frozen in the milestone document.

Do not change the rule after seeing the prospective result.

Even **FORWARD-SUPPORTED** does not authorize live trading. Any live-risk step
requires a separate later review and explicit authorization.
