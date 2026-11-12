# M030 Stage 1P — read-only Python correctness and tracing gap audit

Date: 2026-11-12
Status: **AUDIT ACCEPTED; NO TESTS RUN OR SOURCE CHANGED BY CODEX**

## Repository and scope

Codex verified clean synchronized `scalping-recovery` at `bb000f9e44af2a771a3932961839c4430b625d93`, ahead/behind 0/0. No Wine, MT5/Tester, historical replay, Python tests, broker session or source edits.

## Already tested

- Completed M1/M5 bar visibility, aggregation, and incomplete-bar exclusion: `mamba2/backtest/feed.py:148-162,216-248,306-359`; `tests/test_backtest_foundation.py:40-74` and integration tests.
- Stochastic 21/7/7 basic arithmetic: `mamba2/indicators/stochastic.py:7-58`, `tests/test_stochastic_indicator.py:48-110`.
- Indicator cached-vector equivalence: `tests/test_replay_indicator_cache.py:149-163`, `tests/test_m030_incremental_contract.py`.
- Portfolio position/pending-order blocking in runner with *synthetic repeating strategies*: `mamba2/backtest/runner.py:99-121` and `tests/test_backtest_strategy_lifecycle.py:146-170,266-307`.
- SL/TP modification, stop-first/target/gap semantics, trailing: `mamba2/backtest/position_manager.py:72-194`, `mamba2/backtest/broker.py:388-460`, `tests/test_position_manager_trailing_semantics.py`, `tests/test_backtest_execution.py`.
- M030 event schema and first-difference comparator: `mamba2/backtest/m030_parity.py:15-155`, `tests/test_m030_parity.py`.

These are deterministic Python-level semantics, not actual native MT5 parity.

## Highest-priority gaps

### P0 — production ten-candle extreme vs fresh crossover

`mamba2/strategies/triple_cross.py:216-220,345-350` detects any earlier M1 stochastic extreme in its recent entry window (BUY: any K below oversold; SELL: any K above overbought). `mamba2/backtest/m030_signal_observer.py:57-64` mirrors this. Existing mocked examples use only two stochastic values, and a separate incremental-vector test does not prove *actual strategy/observer* decisions.

Add synthetic **ten-value** real observer/strategy tests: previous extreme + latest K/D relation without fresh latest crossover should still allow BUY/SELL if all other rules pass. Alter only earlier extreme to assert `NO_SIGNAL`. Avoid changing strategy or indicator formulas.

### P0 — indicator seed and warm-up boundaries

`get_stochastic()` requires 35 visible rates for 21/7/7 (`stochastic.py:191-196`). Assert <35 unavailable, 35 valid, and no strategy decision on insufficient history. EMA `ewm(span=7, adjust=False)` begins with first source close (`moving_average.py:71-75,140-147`). Replace tautological `abs(current-wrong_short_seed)>=0` in `tests/test_m030_incremental_contract.py:64-70` with a deliberately divergent causal vector and a **positive lower bound**. ATR14 rolling TR in `mamba2/indicators/atr.py:5-16` needs 15 rates under the public API; assert 14 unavailable per accepted contract, 15 equal explicit gap-sensitive true-range computation. Use synthetic data only.

### P1 — ordered M030 signal-to-fill lifecycle

Event schema `m030_parity.py:15-24` supports `M1_CLOSE,SIGNAL,SUBMIT,FILL,SLTP_MODIFY,EXIT,REJECT,ACCOUNT`. Producers in `broker.py:219-264,304-367,388-409,497-503`, `runner.py:128-150` are not validated as one event stream. Note `broker.advance()` processes previous exits/marks/fills **before** runner emits the new boundary's `M1_CLOSE`, and same-boundary submission/fill/SLTP can occur later in runner. Add single deterministic fill/SLTP/exit test checking timestamps, source bars and order. Decide whether `REJECT`/`ACCOUNT` are intentionally unproduced; do not invent emitters.

### P1 — production strategy + runner position blocking

Existing blocking tests use `RepeatingStrategy`, not `triple_cross.py`. With deterministic mocked indicators, assert a second genuine signal while position open does **not** submit a second order through the runner. The strategy itself has no direct open-position guard; the runner does.

### P2 — trace quality

Connect SLTP and exit updates to M030 emitted event fields/order, direct observer reasons (`INSUFFICIENT_HISTORY,MISSING_EMA,EMA_CANDLE_FILTER,ENTRY_CONDITIONS`), native M5 preference without claiming native MT5 parity.

## Decision and next task

Stage 1Q: **source-only synthetic production-signal and indicator boundary tests**. Prioritize P0; do not silently change strategy semantics, entry criteria, source dataset or real trading code. If a test exposes a contradiction, report the exact frozen contract before any production change. Stage 1R may later address P1 lifecycle integration after separately reviewing results.

Native MetaQuotes-Demo historical UTC offset, native M1/M5 OHLC and ticks, tester execution, broker spreads/fills, position semantics and economic parity remain unverified. Standalone MT5 launcher path stays closed under the Stage 1O STOP decision.
