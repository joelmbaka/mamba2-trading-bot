# Mamba2 Project Plan

## Goal

Make historical results trustworthy enough to guide strategy development without simulator defects distorting conclusions.

## Completed foundation

1. deterministic OHLC replay;
2. strategy runner/adapter;
3. execution lifecycle, positions, and ledger;
4. MT5 bar-open timing;
5. native runtime and read-only MT5 history exporter;
6. production ATR/position lifecycle;
7. spread-aware Bid/Ask execution;
8. account-currency P/L conversion;
9. explicit execution-cost model;
10. strategy condition semantics;
11. shared-account five-symbol portfolio replay;
12. deterministic baseline reporting;
13. monotonic trailing-stop semantics;
14. runtime cache sanitization.

Exact SHAs are in `MILESTONES.md`.

## Current operations milestone

Build durable agent handoff and safe local-control before long-running baseline work.

## Next analytical sequence

### 15 — First real baseline
Run Sep 1–24, 2026 across all five production symbols, unchanged strategy.

### 16 — Baseline diagnosis
Inspect trade-by-trade evidence: symbol, side, session, spread, ATR/trailing, conversion, and loss clustering. Do not optimize yet.

### 17 — Proven-defect corrections
Fix only issues demonstrated by evidence, rerun the exact same dataset, compare before/after.

### 18 — Broader-history validation
Expand to several months and multiple market regimes.

### 19 — Controlled experiments
One strategy/filter change at a time with preserved baseline and separate validation periods.

### 20 — Paper/live validation
Compare replay assumptions against forward behavior before increasing live risk.

## Principles

- Correctness before profitability.
- One semantic change per milestone.
- Reproducible acceptance record after every milestone.
- Never invent unavailable broker costs.
- Never silently change production behavior.
