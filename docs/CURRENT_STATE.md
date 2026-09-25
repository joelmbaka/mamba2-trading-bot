# Current State

Last updated: 2026-09-25

## Accepted state

- Accepted main SHA: `40536d96c6ac2119fca3c2cfec92dad889e7c878`
- Latest accepted milestone: **Runtime cache sanitization**
- Native suite at acceptance: **165 passed, 2 skipped**
- Wine suite at acceptance: **165 passed, 2 skipped**
- `bot_cache.json`: untracked
- `icon.png`: tracked and unchanged

## Current operations work

- Operations branch: `repo-ops-foundation`
- Base: accepted main `40536d96c6ac2119fca3c2cfec92dad889e7c878`
- Purpose: durable docs/agent handoff, safe ChatGPT ↔ local-machine control, and removal of proven dead/generated repository clutter.

## Baseline branch

`backtest-first-baseline` exists at the accepted main SHA and is intentionally untouched until repository operations are accepted.

## Current production/backtest settings

- Symbols: EURUSD, EURJPY, GBPUSD, GBPJPY, USDJPY
- Position size: 0.1
- Stochastic: 21 / 7 / 7
- Trend filter: off
- RSI filter: off
- Higher-TF filter: off
- EMA: 7
- ATR: period 14, M5
- ATR SL multiplier: 1.0
- ATR TP multiplier: 2.0
- Existing BUY stops only move upward.
- Existing SELL stops only move downward.
- End-of-data does not force-liquidate.
- Historical spread uses tick-derived Ask where available.
- Unknown real commission/slippage must not be invented.

## Next

Complete repository-operations/local-control setup, then return to `backtest-first-baseline`.

## Code cleanup audit

See `docs/CODE_CLEANUP.md`. This operations branch removes only proven dead scaffolding/generated artifacts plus the stale SciPy dependency; behavioral cleanup candidates remain deferred.
