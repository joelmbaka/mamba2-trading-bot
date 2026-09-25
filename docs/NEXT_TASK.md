# Next Authorized Task

## Milestone 019 — Broader-history validation

Milestone 018 is accepted.

Accepted M018 implementation SHA:

`fb03bc197d60d5d7b5b218a86288811f72ec4f60`

Accepted corrected baseline SHA-256:

`e33a5400f70494356d12faebbb1e2588bd2075769da5539e9c6584dc88cedcca`

Accepted corrected diagnostic SHA-256:

`1497db0918bac89c8d10224745db4a522492ac577e845bfc1731450c39e3dda7`

Proposed branch:

`backtest-broader-history`

## Objective

Validate the corrected deterministic replay over a substantially broader
historical sample before any controlled strategy optimization.

M019 is a **validation** milestone. It must determine whether the descriptive
patterns seen in Sep 1–24 persist, weaken, reverse, or vary across different
market regimes.

Do not tune the strategy in response to M019 results.

## Preserve exactly

Keep the accepted M018 semantics and production configuration:

- symbols:
  EURUSD, EURJPY, GBPUSD, GBPJPY, USDJPY;
- position size: 0.1;
- stochastic: 21 / 7 / 7;
- trend filter: off;
- RSI filter: off;
- higher-TF filter: off;
- EMA: 7;
- ATR: 14 on M5;
- SL: 1 × ATR;
- TP: 2 × ATR;
- M018 wrong-side initial-TP guard;
- monotonic trailing-stop semantics;
- no forced end-of-data liquidation;
- tick-derived historical Ask where available;
- account-currency historical conversion semantics;
- explicit commission/slippage assumptions unchanged.

Do not invent unavailable broker costs.

## Historical scope

The exact M019 validation interval is now fixed as:

`2026-06-23T00:00:00Z` through `2026-09-25T00:00:00Z`

The initial June 1 candidate was rejected by the pre-export coverage probe:
all five symbols had M5/M15 history and tick samples back to June 1, but common
M1 history began only around June 22 05:29–05:33 UTC. June 23 00:00 UTC is the
first clean full-day boundary after common M1 availability.

The accepted M019 window therefore covers late June, July, August, and Sep
1–24 across all five production symbols. Use those calendar subperiods for
descriptive stability comparisons; do not select or discard periods based on
profitability.

Before export, verify required M1, native M5, native M15, and tick-derived Ask
coverage exists for each symbol.

The immutable broader dataset must also prove that its Sep 1–24 overlapping
M1/M5/M15/Ask data is identical to the accepted M016 dataset before replay
evidence is trusted.

Use only read-only historical MT5 access.

## Required validation sequence

1. verify branch/worktree safety and accepted M018 starting SHA;
2. define the exact broader UTC window;
3. export or assemble a versioned immutable dataset with manifest/integrity
   checks;
4. verify row coverage by symbol/timeframe;
5. run the unchanged corrected strategy twice;
6. require byte-identical deterministic reports;
7. run deterministic diagnostics on the broader dataset;
8. summarize aggregate and per-symbol results;
9. compare periods/regimes without changing strategy behavior;
10. run full native and Wine suites;
11. record exact implementation/evidence SHAs and limitations.

## Required analysis

At minimum compare:

- aggregate P/L and drawdown;
- per-symbol trade count, hit rate, and P/L;
- BUY versus SELL payoff;
- spread distribution and tail behavior;
- UTC entry buckets;
- stop-loss versus take-profit exits;
- initial protection and trailing activity;
- account-currency conversion routes;
- loss clustering;
- drawdown episodes;
- subperiod/regime stability.

The goal is not to select a winning filter. The goal is to discover which M017
and M018 observations are stable enough to justify later controlled
experiments.

## Regression requirements

M019 must retain focused M018 protection tests proving:

- no BUY initial TP is at/below its fill;
- no SELL initial TP is at/above its fill;
- ordinary current-price TP semantics are preserved when the target is already
  valid.

Any broader-history infrastructure added must remain deterministic and must not
change production strategy semantics.

## Prohibited during M019

Do not:

- tune stochastic settings;
- enable trend/RSI/higher-TF filters;
- disable or rank symbols;
- add session filters;
- add spread filters;
- change position size;
- change ATR period or multipliers;
- optimize trailing;
- choose settings based on broader-history performance;
- invent commission/slippage/swap;
- enable real MT5 trading;
- place, modify, or close real orders.

If M019 uncovers another genuine implementation defect, stop optimization work,
prove it with deterministic evidence, and treat the correction as a separately
documented defect before continuing.

## Exit condition

M019 is complete only when the broader real-data replay is reproducible,
diagnosed, and documented well enough to define M020 controlled experiments
without using the Sep 1–24 window as the sole evidence base.
