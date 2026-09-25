# Next Authorized Task

## Milestone 018 — Proven-defect review and corrections

Milestone 017 is accepted.

Accepted M017 implementation SHA:

`e653ba87df2ff1e8afbad5704f9a8d81428d7b27`

Accepted baseline report SHA-256:

`d73a86c8af9063a5831f38131bc9e9a7fdc956971cb0b65971cf1709b6509f6a`

Accepted diagnostic SHA-256:

`edf01f4a1f936d386e618faa65fb9a7afb65fff6ae7ae9b4373c35692ced987a`

Proposed branch:

`backtest-proven-defect-review`

## Objective

Use M017 trade-level evidence to prove or disprove implementation/replay defects.

Do **not** optimize the strategy.

A code/semantic change is authorized only after deterministic evidence proves
that current behavior is incorrect relative to the documented backtest
semantics or intended production behavior.

If an observation is economically poor but semantically correct, leave it
unchanged for later controlled experiments.

## Source evidence

Reuse exactly:

- accepted M016 dataset:
  `2026-09-01T00:00:00Z` through `2026-09-25T00:00:00Z`
- accepted M016 ordinary baseline report
- accepted M017 deterministic diagnostic artifact
- current strategy/configuration unchanged

## First investigation — negative take-profit exits

M017 observed:

- 54 take-profit exits
- 51 positive
- 3 negative

For each of the 3 negative-P/L take-profit trades, reconstruct:

- order ID / position ticket;
- symbol / side;
- entry timestamp and fill;
- initial ATR;
- initial SL/TP;
- every successful protection/trailing modification;
- exit timestamp;
- final TP;
- Bid/Ask bar used for exit;
- gross quote P/L;
- account-currency conversion route;
- final realized P/L.

Determine whether negative take-profit P/L is:

1. a legitimate consequence of a moved TP / spread / path under current
   semantics; or
2. a replay/position-management defect.

Do not change code until that determination is proven by a regression test.

## Second investigation — extreme spread tails

Inspect the largest observed entry spreads, especially:

- EURJPY 300 points
- GBPJPY 229 points
- USDJPY 113 points
- GBPUSD 56 points
- EURUSD 18 points

For each extreme case establish whether:

- tick-derived Ask and Bid timestamps align;
- the exported spread is genuinely present in historical data;
- the entry used the documented next-M1 execution rule;
- no stale/future quote was used;
- point-size/digits interpretation is correct.

Do not add a spread filter during M018.

## Third investigation — payoff asymmetry

M017 observed nearly identical non-flat win rates:

- BUY 41.72%
- SELL 41.48%

but:

- BUY net P/L: USD -330.9923055212326
- SELL net P/L: USD +62.44931537578547

Describe the difference in average winning/losing trade magnitude, exit path,
symbol mix, and trailing behavior.

This is a defect investigation only. If execution is semantically correct,
defer any directional strategy change to M020 controlled experiments.

## Session and clustering checks

Use evidence to explain, without optimizing:

- 00:00–03:59 UTC losses;
- 12:00–15:59 UTC losses;
- maximum 17-loss streak;
- early recovered ~4.0% drawdown;
- later unrecovered ~3.11% drawdown.

Control for symbol mix and spread before attributing results to time-of-day.

## Acceptance rules

If no implementation defect is proven:

- make no strategy/replay semantic change;
- document that M018 found no proven defect in the inspected anomaly;
- preserve M016 baseline exactly.

If a defect is proven:

1. add a focused failing regression test;
2. make the narrowest correction;
3. keep strategy parameters unchanged;
4. run full native and Wine suites;
5. rerun the exact M016 dataset twice;
6. require deterministic reports;
7. compare corrected result to the accepted M016 baseline;
8. document the semantic reason for the difference.

## Prohibited during M018

Do not:

- tune stochastic thresholds/periods;
- enable trend/RSI/higher-TF filters;
- disable symbols;
- introduce session filters;
- introduce spread filters;
- change position size;
- tune ATR multipliers;
- optimize trailing;
- invent commission/slippage/swap;
- enable real MT5 trading;
- place/modify/close real orders.

M018 separates proven simulator/implementation defects from strategy-quality
observations. Controlled strategy experiments remain M020 work.
