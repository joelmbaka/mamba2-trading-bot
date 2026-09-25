# Milestone 020 — Controlled Experiments

Status: **IN PROGRESS**

Date started: 2026-09-25

Accepted M019 closeout base:

`927d90c656b6846603d338987bf67e6928499966`

Accepted M019 implementation SHA:

`94a74211175d0f1db7e4c00cb3ab1f8ca1f286bb`

Branch:

`backtest-controlled-experiments`

## Purpose

Test one explicitly stated hypothesis at a time against the accepted M019
control without turning the broader historical dataset into an unconstrained
parameter search.

No strategy behavior may change until an experiment definition is documented.

## Immutable control

The control is the accepted M019 strategy and replay semantics unchanged.

Required control artifacts:

- baseline SHA-256:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`
- diagnostic SHA-256:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`

The experiment harness must reproduce the accepted control before treatment
results are interpreted.

## M020-A — first authorized experiment

### Hypothesis

New entries during `00:00–03:59 UTC` are a persistently harmful exposure.

This hypothesis is justified for testing because:

- the fixed bucket was negative in the accepted Sep-only evidence;
- the broader M019 bucket contains 842 trades and
  **USD -839.9216322911675** net realized P/L;
- its mean entry spread is **19.899049881235154 points**, much wider than the
  other fixed UTC buckets;
- the relationship can still be confounded by spread tails, symbol mix, and
  market regime.

The observation is not yet an accepted strategy change.

### Control

Accepted M019 strategy unchanged.

### Treatment

Change exactly one behavior:

- suppress **new entries** when the entry decision/fill time is
  `00:00:00 <= UTC time < 04:00:00`.

Positions already open before or during the blocked interval continue through
the unchanged position-management path.

### Must remain constant

- immutable M019 dataset;
- five symbols;
- replay timing and execution semantics;
- tick-derived historical Ask;
- account-currency conversion;
- position size 0.1;
- stochastic 21 / 7 / 7;
- trend/RSI/higher-TF flags;
- EMA 7;
- ATR 14 M5;
- SL 1 × ATR;
- TP 2 × ATR;
- M018 wrong-side initial-TP guard;
- trailing semantics;
- end-of-data behavior;
- explicit cost assumptions.

Do not add a spread threshold, symbol filter, side filter, or second strategy
change to M020-A.

## Experiment framework design

The framework must produce deterministic paired control/treatment evidence.

For each experiment:

1. identify an immutable experiment ID and exact hypothesis;
2. run the accepted control without strategy mutation;
3. run one treatment;
4. repeat each arm and require deterministic artifacts;
5. verify the control matches the accepted M019 hashes;
6. record treatment artifact hashes;
7. compare aggregate result and maximum drawdown;
8. compare per-symbol result and trade count;
9. compare BUY/SELL behavior;
10. compare late-June, July, August, and Sep 1–24 behavior;
11. report win/loss payoff and exit reasons;
12. report spread exposure and any changed trade population;
13. record whether the observed treatment effect is concentrated in one symbol
    or one subperiod;
14. document the experiment even when it is rejected or inconclusive.

## Overfitting rule

No result is accepted merely because aggregate P/L improves.

The existing June–September dataset has already been inspected in M019, so its
calendar slices are stability checks rather than pristine holdouts. Do not tune
on one slice and call another already-inspected slice independent validation.

A later milestone must use genuinely later paper/forward evidence before an
experimental strategy change is promoted toward live risk.

## Safety

Historical MT5 access remains read-only.

Never:

- enable real MT5 trading;
- place a real order;
- modify a real order;
- close a real position;
- invent commission, slippage, or swap;
- change accepted replay semantics silently;
- stack multiple strategy treatments into one experiment.

## Initial implementation task

Build the experiment harness first. It must prove the accepted M019 control is
unchanged before M020-A treatment code is evaluated.
