# Milestone 019 — Broader-History Validation

Status: **IN PROGRESS**

Date started: 2026-09-25

Starting closeout SHA:

`94c031a852751973e3f7541cfbb7ebf636844223`

Accepted M018 implementation SHA:

`fb03bc197d60d5d7b5b218a86288811f72ec4f60`

## Objective

Validate the corrected deterministic replay across several months of real MT5
history before any strategy optimization.

M019 must preserve the accepted M018 execution semantics and current strategy
configuration.

## Exact historical window

Chosen UTC interval:

`2026-06-01T00:00:00Z` through `2026-09-25T00:00:00Z`

This includes:

- June 2026;
- July 2026;
- August 2026;
- Sep 1 through the end of Sep 24 UTC.

The end boundary exactly matches the accepted M016/M018 dataset end so the
Sep 1–24 overlap can be checked against the previously accepted immutable
dataset.

Planned subperiod comparison:

- 2026-06;
- 2026-07;
- 2026-08;
- 2026-09 through Sep 24.

These are descriptive calendar subperiods, not preselected profitable regimes.

## Symbols and required data

All five production symbols remain required:

- EURUSD
- EURJPY
- GBPUSD
- GBPJPY
- USDJPY

Required history:

- M1 Bid-side bars;
- native M5 bars;
- native M15 bars;
- tick-derived Ask M1;
- symbol execution metadata;
- account currency for historical P/L conversion.

Historical MT5 access remains read-only.

## Pre-export gate

Before writing the broader dataset:

1. verify the exact branch/worktree state;
2. probe M1/M5/M15 availability across the requested interval;
3. probe tick-history availability at distributed checkpoints across the
   interval for every symbol;
4. do not export if required history is absent.

The full export must then prove complete M1/Ask alignment and manifest
integrity.

## Dataset acceptance

Planned immutable dataset directory:

`backtest_data/broader-history-20260601-20260925`

After export:

- load through the existing manifest/checksum validator;
- require all five symbols;
- require M1, native M5, native M15;
- require tick-derived Ask rows to align one-for-one with exported M1 rows;
- compare the Sep 1–24 overlap with the accepted M016 dataset;
- require the overlapping M1/M5/M15/Ask frames to be identical before broader
  replay evidence is trusted.

## Replay acceptance

Run the unchanged corrected strategy twice over the exact broader dataset.

Require:

- byte-identical ordinary baseline reports;
- byte-identical diagnostic reports;
- zero wrong-side initial TP violations;
- zero negative-P/L take-profit exits;
- zero remaining unexplained semantic drift;
- no new strategy-reporting artifacts.

## Required analysis

Record:

- aggregate P/L and drawdown;
- per-symbol result;
- BUY/SELL result;
- entry-spread distribution;
- UTC entry buckets;
- exit reasons;
- protection/trailing activity;
- account-currency conversion routes;
- loss clustering;
- deepest drawdown episodes;
- June/July/August/Sep subperiod results.

These observations are evidence for M020 experiment design only. M019 does not
enable, disable, rank, or tune any strategy component.

## Prohibited

No strategy/filter tuning, spread/session filters, symbol removal, ATR changes,
position-size changes, invented broker costs, or real MT5 order actions.
