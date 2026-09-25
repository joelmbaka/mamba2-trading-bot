# Next Authorized Task

## Milestone 020 — Controlled experiments

Milestone 019 is accepted.

Accepted M019 implementation SHA:

`94a74211175d0f1db7e4c00cb3ab1f8ca1f286bb`

Accepted broader baseline SHA-256:

`114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`

Accepted broader diagnostic SHA-256:

`84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`

Branch:

`backtest-controlled-experiments`

## Objective

Build a controlled experiment workflow and test exactly one explicitly stated
strategy/filter hypothesis at a time against the accepted M019 strategy.

M020 is not a parameter search and is not permission to stack filters.

## Control

The control is the accepted M019 strategy unchanged:

- five production symbols;
- position size 0.1;
- stochastic 21 / 7 / 7;
- trend filter off;
- RSI filter off;
- higher-TF filter off;
- EMA 7;
- ATR 14 on M5;
- SL 1 × ATR;
- TP 2 × ATR;
- M018 wrong-side initial-TP guard;
- current monotonic trailing semantics;
- no forced end-of-data liquidation;
- tick-derived historical Ask;
- account-currency conversion semantics;
- current explicit cost assumptions.

Control replay must reproduce the accepted M019 artifacts before a treatment is
interpreted.

## First authorized hypothesis — M020-A

**Hypothesis:** new entries opened during `00:00–03:59 UTC` are a persistently
harmful exposure worth testing as a single session filter.

Why this is justified for experiment, not yet for adoption:

- M018 Sep-only evidence already showed this UTC bucket negative;
- M019 broader evidence shows 842 entries and
  **USD -839.9216322911675** net P/L in the bucket;
- its mean entry spread was **19.899049881235154 points**, materially above the
  other fixed UTC buckets;
- the observation may still be confounded by symbol mix, spread tails, and
  market regime.

## Treatment

Change exactly one thing:

- reject **new entry signals** whose replay decision/fill entry time falls in
  `00:00:00 <= UTC time < 04:00:00`.

Do not:

- close an already-open position because the clock enters the blocked session;
- add a spread threshold;
- remove a symbol;
- disable BUY or SELL;
- alter ATR, SL, TP, trailing, position size, stochastic, EMA, RSI, or trend
  behavior;
- change replay/execution semantics;
- alter historical conversion or cost assumptions.

## Experiment framework requirements

Before interpreting treatment results:

1. define a deterministic control/treatment runner;
2. use the same immutable M019 dataset for both arms;
3. require repeated A/B determinism for control and treatment;
4. require the control to reproduce the accepted M019 baseline/diagnostic
   hashes;
5. record one experiment definition and one treatment change;
6. compare aggregate P/L, drawdown, trade count, win/loss payoff, per-symbol
   behavior, side behavior, and calendar subperiod stability;
7. report the treatment effect separately for late June, July, August, and
   Sep 1–24;
8. report whether an apparent gain is concentrated in one symbol or one
   subperiod;
9. document rejected or inconclusive experiments as well as promising ones.

Do not accept a treatment merely because aggregate P/L improves.

## Overfitting guard

M019 has already exposed the overall broader result, so no slice of this same
dataset should be described as a pristine unseen holdout.

Use temporal slices as stability checks only. Do not tune a treatment on one
slice and then silently reuse the same slice as independent validation.

A later milestone must use genuinely later data/paper-forward evidence before a
strategy change is promoted toward live risk.

## Safety

Historical MT5 access remains read-only. Never enable real trading or place,
modify, or close a real MT5 order during M020.
