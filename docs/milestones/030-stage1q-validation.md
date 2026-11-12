# M030 Stage 1Q — focused synthetic validation accepted

Date: 2026-11-12
Status: **VALIDATED — NO PRODUCTION STRATEGY MODIFICATIONS**

## Source version and reproducibility

Codex checked clean synchronized `scalping-recovery` at `2b320c75908fb06d04019372fbff16645e350f97` with 0 ahead/behind and no local changes.

- Focused Stage 1Q suite: **64 passed**, no failures.
- Related regression suite: **92 passed, 1 skipped**, no failures.
- Python syntax audit: **119 files successfully parsed**.
- Known skip: `tests/test_stochastic_triple_tf.py:4` references the removed legacy module `mamba2.strategy.stochastic_triple_tf`; it does not constitute a Stage 1Q regression.

## Verified Stage 1Q behavior

- `tests/test_triple_cross_condition_semantics.py:513-572` calls the real `mamba2.strategy.triple_cross.StochasticTripleTFStrategy.evaluate`: full 10-point M1 %K history; earlier oversold or overbought extreme enables correct BUY/SELL under valid final K/D, M5 direction and EMA/candle condition, even with **no fresh final-bar crossover**. Removing only the older extreme prevents order submission. Broker and reporting are mocked. Initial SL and TP remain production zero values.
- `tests/test_m030_stage1q_boundaries.py:39-83` calls actual `mamba2.backtest.m030_signal_observer.observe_candidate`; checks signal reason ENTRY_CONDITIONS versus NO_SIGNAL after historical extreme is removed.
- Stochastic (21,7,7): 34-bar insufficient data and 35-bar first eligible result.
- EMA7: first-source `ewm(adjust=False)` causal seed, and truncated prefix produces a **strictly positive divergence >0.05** on a synthetic vector.
- ATR14: preserves current public-API 14-bar `0.0` sentinel; verifies 15-bar availability and exact gap-sensitive rolling true-range mean.
- `tests/test_m030_incremental_contract.py`: tautological `abs(...) >= 0` assertion replaced by a discriminatory separate test.

No Wine, MetaEditor, MT5 terminal, Strategy Tester, historical replay, broker, downloads, package installs or local-control. No production strategy/indicator/broker code or historical datasets changed.

## Next decision

**Proceed only to Stage 1R source/test read-only integration planning**: inspect M030 event production (`M1_CLOSE`, `SIGNAL`, `SUBMIT`, `FILL`, `SLTP_MODIFY`, `EXIT`) and real production strategy position/pending-order guard under `BacktestRunner`. Identify exact deterministic, no-market-data fixtures and expected event timestamps/order (particularly `broker.advance()` before current `M1_CLOSE`, then same-boundary submit/fill and deferred SL/TP). Keep `REJECT` and `ACCOUNT` schema coverage distinctions explicit; do not add undocumented producers.

Do not execute a historical economic replay or modify a production strategy just to satisfy event tests. Native MT5 time, OHLC, tick, broker fill or strategy parity remain unproven, and standalone account-free tester path remains STOPPED by Stage 1O.
