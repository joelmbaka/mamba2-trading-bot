# Mamba2 Project Plan

## Goal

Make historical results trustworthy enough to guide strategy development
without simulator defects distorting conclusions.

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
14. runtime cache sanitization;
15. repository operations foundation;
16. first real five-symbol baseline;
17. deterministic baseline diagnosis;
18. proven wrong-side initial-TP defect correction;
19. broader-history validation with replay-performance parity.

Exact SHAs are in `MILESTONES.md`.

## Current analytical sequence

### 16 — First real baseline — COMPLETE

Sep 1–24, 2026 across all five production symbols, unchanged strategy. The
accepted report is recorded in
`docs/milestones/016-first-real-baseline.md`.

### 17 — Baseline diagnosis — COMPLETE

Trade-level deterministic evidence identified spread tails, side/session
asymmetry, drawdown structure, and three negative-P/L take-profit exits without
changing strategy behavior.

### 18 — Proven-defect corrections — COMPLETE

The anomalous take-profit exits proved a real initial-target placement defect
under sufficiently wide spreads. The narrow correction prevents an initial TP
from crossing to the loss side of the actual fill while preserving normal
current-price TP, SL, and trailing semantics.

### 19 — Broader-history validation — COMPLETE

The corrected strategy was replayed from June 23 through Sep 24 across all five
symbols. The final optimized implementation reproduced both the accepted M018
Sep artifacts and the earlier whole-window broader artifacts exactly.

The broader result was negative across late June, July, August, and Sep 1–24.
Four of five symbols were negative. Both BUY and SELL were negative, so the
short-window profitable-SELL observation did not persist. The 00:00–03:59 UTC
entry bucket remained the strongest persistent descriptive weakness and also
carried unusually wide spread exposure.

No strategy filter was adopted in M019.

### 20 — Controlled experiments — NEXT

Build a deterministic control/treatment framework and test one strategy/filter
change at a time.

The first authorized experiment is M020-A: block new entries during
00:00–03:59 UTC only. Do not combine this with a spread, symbol, side, ATR,
trailing, stochastic, or position-size change.

### 21 — Paper/live validation

Compare replay assumptions against genuinely later forward behavior before
increasing live risk.

## Principles

- Correctness before profitability.
- One deliberate treatment per controlled experiment.
- Reproducible acceptance record after every milestone.
- Never invent unavailable broker costs.
- Never silently change production behavior.
- Broader validation before optimization.
- Same-dataset temporal slices are stability checks, not pristine holdouts.
