# Next Authorized Task

## Milestone 021 — prospective paper/forward validation

Milestone 020 is **CLOSED**.

Accepted M020 implementation SHA:

`0d85b82278ae08a88f8b5b942fb23ec000b11411`

Accepted M020-D classification:

**PROMISING**

M020-D is not promoted to production/live trading.

## Frozen candidate

The only candidate carried forward is the independent M020-D rule:

- reject a new order only when observable decision-time spread is **>10
  points**;
- allow **<=10 points**;
- use only bid/ask observable at submission time.

Do not stack M020-A.

Do not change the threshold.

Do not add symbol, side, time, ATR, SL, TP, trailing, stochastic, EMA, RSI,
trend, position-size, or execution-cost treatments.

## Purpose of M021

Obtain genuinely later paper/forward evidence without reusing the inspected
June–September history as if it were a holdout.

The first M021 task is to **predeclare the forward-validation protocol before
inspecting forward outcomes**.

The protocol must define at minimum:

1. the exact prospective observation start/cutoff;
2. the minimum observation horizon and/or trade-count requirement;
3. the frozen control and frozen M020-D candidate;
4. deterministic reporting fields and hashes;
5. aggregate P/L and maximum drawdown;
6. per-symbol, BUY/SELL, and calendar-period stability;
7. rejected-order counts and spread-boundary enforcement;
8. the existing wrong-side TP, negative-TP, remaining-position, and
   no-strategy-artifact safety gates;
9. explicit treatment of commission/slippage/swap assumptions;
10. a classification rule written before results are inspected.

## Data isolation

The accepted M019/M020 dataset ends at:

`2026-09-25T00:00:00Z`

M021 evidence used for classification must be genuinely later than the
already-inspected dataset and must not be backfilled with previously inspected
June–September observations.

Do not call a tiny later sample decisive merely because it is new. The minimum
horizon/trade-count rule must be fixed before interpreting results.

## Safety

Historical or market-data MT5 access remains read-only.

Never:

- enable real MT5 trading;
- place, modify, or close a real MT5 order;
- promote M020-D directly into production strategy behavior;
- tune the >10 threshold from M021 results;
- stack M020-A automatically;
- invent actual commission, slippage, or swap costs.

## Milestone boundary

M020-E is not authorized.

M021 must remain a prospective paper/forward validation milestone. Any eventual
move toward live risk requires separate review and explicit authorization after
the forward evidence is complete.
