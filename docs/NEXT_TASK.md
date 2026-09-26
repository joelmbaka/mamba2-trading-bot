# Next Authorized Task

## Milestone 020-D — decision-time spread treatment

Milestone 020 remains **IN PROGRESS**.

Branch:

`backtest-controlled-experiments`

M020-A:

**PROMISING, NOT PROMOTED**

M020-B:

**COMPLETE — fill-spread confound diagnosis**

M020-C:

**COMPLETE — decision-time spread observability**

M020-C deterministic artifact SHA-256:

`0bb6e878eacfce9982cba23b05e8c4c4e437731554fe8b5f913125429b8f6a4f`

Accepted M019 ordinary-control hashes remain:

- baseline:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`;
- diagnostic:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`.

## Evidence motivating M020-D

Decision-time spread is causal information available when the strategy submits
an order.

M020-C shows:

- p90 decision-time spread: **10 points**;
- decision/fill spread correlation: **0.9213069050932308**;
- decision spread >10 points:
  **444 trades / USD -1,119.284653164277**;
- >10-point trades were negative in every inspected calendar period;
- >10-point trades were negative for all five symbols;
- >10-point trades were negative for BUY and SELL.

The >10-point boundary was predeclared before M020-C result interpretation and
was not selected by a parameter sweep.

## Treatment

Reject exactly one class of new orders:

- if observable decision-time bid/ask spread is **>10 points**, reject the new
  order;
- if spread is **<=10 points**, preserve ordinary entry behavior.

Do not inspect next-bar fill spread to make the decision.

## Isolation

M020-D must run directly against the immutable M019 control.

Do not stack:

- M020-A's 00:00–03:59 UTC filter;
- symbol filters;
- side filters;
- additional spread thresholds;
- strategy parameter changes;
- ATR/SL/TP/trailing changes.

## Validation sequence

1. full native suite;
2. full Wine suite;
3. immutable M019 control regression at current treatment-code HEAD;
4. deterministic M020-D treatment pair;
5. zero accepted entries with decision spread >10 points;
6. existing wrong-side TP and negative-TP gates remain zero;
7. no new strategy-reporting artifacts;
8. compare aggregate, drawdown, symbol, side, and calendar-period effects.

Do not accept M020-D merely because aggregate P/L improves.

A genuinely later paper/forward milestone remains mandatory before any
experimental strategy behavior is promoted toward live risk.
