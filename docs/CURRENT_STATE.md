# Current State

Last updated: 2026-09-25

## Latest accepted implementation milestone

**015 — Repository operations foundation**

Accepted implementation SHA:

`32da1d846960cbc2b196da1c2f8c8a8561a5c322`

Validation:

- core local-control validation: **73 passed**
- full native suite: **164 passed, 2 skipped**
- full Wine suite: **164 passed, 2 skipped**
- Wine Python: **3.10.11 AMD64**
- Wine NumPy: **2.2.1**
- Wine MetaTrader5: **5.0.6180**
- Wine pytest: **9.1.1**
- repository checks: PASS
- worktree: clean
- divergence: 0/0
- `bot_cache.json`: untracked
- `icon.png`: tracked and unchanged

The test count decreased from 165 to 164 because the obsolete TraderClient scaffold and its standalone test were intentionally removed.

## Durable handoff now available

A fresh ChatGPT or Codex session must start with:

1. `AGENTS.md`
2. `docs/CURRENT_STATE.md`
3. `docs/NEXT_TASK.md`
4. `docs/BACKTEST_SEMANTICS.md`
5. `docs/WORKFLOW.md`
6. `docs/MILESTONES.md`

## Local control

Permanent branches:

- `local-control`
- `local-control-results`

Installed workstation service:

`chatgpt-mamba2-local-agent.service`

Validated capabilities:

- status
- safe FF-only sync
- safe branch switch
- repository checks
- runtime discovery/version checks
- core tests
- full native tests
- full Wine tests
- fixed pinned Wine-test-environment recovery

No arbitrary shell action is exposed.

## Cleanup completed

See `docs/CODE_CLEANUP.md`.

Removed proven dead/generated clutter including:

- tracked runtime logs/analytics;
- empty placeholders;
- unused MACD/support-resistance modules;
- obsolete TraderClient/example scaffold;
- unused MT5 diagnostic;
- stale broker README;
- unused private strategy helper;
- direct SciPy dependency.

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

## Next milestone

**016 — First real five-symbol baseline**

Branch:

`backtest-first-baseline`

The branch must first be fast-forwarded to the accepted repository-operations closeout from `main`.

No strategy optimization is authorized before the baseline is reproduced twice identically.
