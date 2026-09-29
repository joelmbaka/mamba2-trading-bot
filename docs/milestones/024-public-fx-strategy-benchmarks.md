# Milestone 024 — Public FX Strategy Benchmarks

Status: **PROTOCOL FROZEN — IMPLEMENTATION/DATA GATE ONLY; NO ECONOMIC RESULTS AUTHORIZED**

Protocol date: 2026-09-29

Branch:

`public-strategy-benchmarks`

Base commit:

`7047d5ff3fd4c74163b62f2142742a124462bb7d`

M024 is intentionally independent of M023. It must not read, branch from, tune
against, or otherwise use M023 outcomes. M021 remains frozen and untouched.

## Objective

Implement public, literature-defined FX benchmark strategies beside Mamba2 so
future research can ask whether the existing strategy adds value relative to
simple documented anomalies.

M024 is not a search for a profitable parameter combination. Strategy
definitions are fixed from published research before any M024 economic result is
inspected.

## Frozen benchmark families

### B1 — MOP-TSMOM-12-1

Source definition: Moskowitz, Ooi, and Pedersen (2012), Time Series Momentum.

Frozen mechanics:

- formation horizon: **12 months**;
- holding/rebalance horizon: **1 month**;
- direction: long when the instrument's trailing 12-month excess return is
  positive, short when negative;
- per-instrument ex-ante annualized volatility target: **40%**;
- volatility estimator: exponentially weighted lagged squared **daily** returns;
- annualization scalar: **261**;
- EWMA decay: `delta = 60 / 61`, matching a 60-day center of mass;
- the volatility estimate at time `t` may use information only through
  `t-1`.

Publication-faithful execution requires an excess-return/forward-compatible
currency return series. A spot-price-only implementation must be labelled
**TSMOM SPOT PROXY**, never silently presented as the paper's exact futures or
forward strategy.

No alternate lookback, holding period, target volatility, or volatility
estimator is authorized in M024.

### B2 — MSSS-CURRENCY-MOMENTUM

Source definition: Menkhoff, Sarno, Schmeling, and Schrimpf (2012), Currency
Momentum Strategies.

Frozen benchmark variants:

- **MOM(1,1)**;
- **MOM(6,1)**;
- **MOM(12,1)**.

Frozen mechanics:

- month-end formation;
- rank currencies by lagged currency **excess return** over the fixed formation
  horizon;
- split the available cross-section into **six** deterministic portfolios;
- long the highest-return portfolio;
- short the lowest-return portfolio;
- holding period: **1 month**;
- equal weight currencies inside each extreme portfolio;
- rebalance monthly.

No formation horizon other than 1, 6, or 12 months is authorized in M024.

Publication-faithful economics require monthly spot and one-month forward data
(or an equivalent directly observed excess-return series) and a sufficiently
broad currency cross-section. The existing five Mamba2 symbols are not a valid
six-portfolio currency universe and must fail the data gate.

### B3 — HML-FX-CARRY

Source definition: the standard carry construction used by
Lustig/Verifier collaborators: sort currencies on the one-month forward
discount or corresponding short-term interest-rate differential.

Frozen mechanics:

- month-end sort;
- **six** deterministic portfolios;
- short the lowest-carry portfolio;
- long the highest-carry portfolio;
- equal weight currencies inside each extreme portfolio;
- hold/rebalance monthly.

No price-only substitute for carry is permitted. Carry economics require
observed one-month forward discounts or corresponding short-term rate
differentials.

### B4 — MAMBA-M020D-SNAPSHOT

The internal comparator is frozen now, before M023 completes:

- stochastic: 21 / 7 / 7;
- boundaries: 20 / 80;
- EMA: 7;
- ATR: 14 on M5;
- ATR SL/TP: 1.0 / 2.0;
- decision-time spread rule: reject new submissions only when spread is
  **>10 points**;
- all hours;
- both BUY and SELL.

This comparator is the accepted M020-D research candidate, not a claim that it
is production-safe or profitable. M023 outcomes may later be reported
separately but may not replace this frozen M024 comparator.

## Data sufficiency gates

Before any benchmark economics:

### TSMOM

Require:

- daily observations with deterministic calendar handling;
- at least **5 complete years** of usable history after cleaning;
- at least 12 months of pre-signal history before the first eligible trade;
- no forward filling across missing trading observations;
- explicit source, timezone/calendar, instrument convention, and hashes.

A 10+ year dataset is preferred, but M024 mechanically blocks only below five
complete years.

### Cross-sectional momentum and carry

Require:

- at least **12 distinct foreign currencies versus one common base currency**
  at every evaluated month;
- monthly spot observations;
- monthly one-month forward observations or directly observed excess returns;
- carry additionally requires observed forward discount / short-rate
  differential;
- at least **5 complete years** after the common-universe gate;
- deterministic treatment of missing currencies and ties;
- bid/ask or other transaction-cost inputs must be separately labelled; costs
  may not be invented.

The current five-symbol MT5 universe must be classified **INSUFFICIENT** for
B2/B3.

## Stage 1 authorization

Stage 1 may only:

1. implement deterministic pure benchmark-signal/portfolio machinery;
2. implement data-audit and sufficiency gates;
3. add synthetic/unit tests for no-lookahead, exact parameter constants,
   deterministic ranking, and data-gate refusal;
4. add a spot-proxy label/path for TSMOM without running economic research;
5. preserve all M019/M020/M021/M022 behavior and artifacts.

Stage 1 must not:

- run benchmark economics on historical market data;
- inspect M022 historical holdout for M024;
- inspect M021 post-cutoff data;
- read M023 results;
- source-select or parameter-select based on profitability;
- add local-control economic actions;
- merge to main;
- deploy;
- enable or place real MT5 orders.

## Stage 1 acceptance

Stage 1 closes only when:

- exact public benchmark constants are regression-tested;
- future-data mutation cannot change earlier TSMOM volatility/signals;
- six-portfolio momentum and carry ranking is deterministic;
- insufficient universe/history fails before economic calculation;
- current five-symbol universe is explicitly rejected for B2/B3;
- no existing production strategy defaults change;
- full native tests pass.

Only after Stage 1 acceptance may a separate, prospectively frozen data-source
inventory gate be authorized.
