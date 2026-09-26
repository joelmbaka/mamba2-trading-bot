# Next Authorized Task

## Milestone 020-C — decision-time spread observability audit

Milestone 020 remains **IN PROGRESS**.

Branch:

`backtest-controlled-experiments`

M020-A is classified:

**PROMISING, NOT PROMOTED**

M020-B is complete and deterministic.

M020-B output SHA-256:

`8b57c2e8bbb4313e3d4e4aef758290a81d140ddd1797759944ab573f9b893a67`

M020-B key finding:

- 00:00–03:59 UTC at <=5 spread points:
  **USD +141.85132131550108** across 490 trades;
- 00:00–03:59 UTC at >10 spread points:
  **USD -910.8776340034257** across 258 trades;
- >10-point spread population was negative in every inspected calendar period,
  both BUY/SELL, and all five symbols.

The broad time filter is therefore over-inclusive. Spread is the stronger
candidate mechanism.

## Objective

Measure the spread that was actually observable when each order was submitted,
then compare it with the eventual next-bar fill spread and realized result.

This is a **diagnostic-only** task.

## Required evidence

For each submitted order that becomes a closed trade, record without changing
execution:

- order ID;
- symbol and side;
- submission UTC timestamp;
- decision-time bid;
- decision-time ask;
- decision-time spread points;
- fill UTC timestamp;
- fill-time spread points;
- outcome;
- net realized P/L.

Report deterministic summaries for:

1. decision-time spread percentiles;
2. the existing fixed spread bands:
   <=2, >2–5, >5–10, >10–20, >20–50, >50–100, >100;
3. P/L by decision-time spread band;
4. decision-time vs fill-time spread-band transition counts;
5. symbol breakdown;
6. BUY/SELL breakdown;
7. Jun 23–30, July, August, and Sep 1–24 breakdown.

## Must not change

Do not:

- reject an order;
- add a spread threshold;
- change M020-A;
- change strategy conditions;
- alter order/fill timing;
- alter ATR, SL, TP, trailing, position size, conversion, or costs;
- enable real MT5 trading.

The ordinary accepted M019 control path must still reproduce exactly:

- baseline SHA-256:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`;
- diagnostic SHA-256:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`.

## Decision rule

M020-C may justify one later global decision-time spread treatment only if the
harmful relationship persists using information available at submission time.

No threshold is authorized yet.
