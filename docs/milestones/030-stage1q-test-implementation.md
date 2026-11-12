# M030 Stage 1Q — deterministic production signals and indicator boundaries

Date: 2026-11-12
Status: **GITHUB SOURCE TESTS COMMITTED; NOT YET RUN BY CODEX**

## Source-only implementation

- `tests/test_triple_cross_condition_semantics.py` now exercises the real async `mamba2.strategy.triple_cross.StochasticTripleTFStrategy.evaluate` with **ten M1 stochastic observations** for BUY and SELL, an early oversold K=10 / overbought K=90, final two K/D values staying in the desired order (no final-bar fresh crossover), directional M5 K/D and valid EMA/bullish or bearish candle. Removing only the earlier extreme must prevent submission. Order type, size 0.1, initial SL/TP=0 (deferred attachment) are checked. All broker methods are synthetic mocks; reporting disabled.
- `tests/test_m030_stage1q_boundaries.py` exercises `observe_candidate` directly with the same ten-value BUY/SELL and earlier-extreme deletion cases; expects ENTRY_CONDITIONS or NO_SIGNAL. Uses synthetic UTC-indexed feed and mocked indicators/ATR/EMA, without account/trades.
- Same file tests public `get_stochastic` with deterministic non-flat OHLC at exactly 34 and 35 bars for 21/7/7 (None / finite K&D).
- Same file checks public `get_moving_average` EMA7 complete first-source seeded recurrence against Pandas `ewm(adjust=False)`, and deliberately shortened distinct first-close prefix with **positive divergence** (>0.05) instead of an always-true assertion.
- Same file checks public `get_atr` ATR14: current API 14-bar `0.0` sentinel, 15-bar rolling arithmetic of explicit prior-close gap-sensitive TR values over rows 1–14.
- `tests/test_m030_incremental_contract.py` had the tautological `abs(...)>=0` removed and now points to the discriminatory public-API EMA test.

**No** strategy, indicator, broker, runner or production configuration code changed. No historical dataset or native MT5 files changed. No MT5, Wine, MetaEditor or Strategy Tester execution; no broker access, historical economic replay or order calls occurred.

## Review before validation

Codex should ensure the new strategy tests use existing config defaults and callable interface correctly; compare `mamba2.strategy.triple_cross` (singular `strategy` path). Confirm synthetic ten-series logic is not a fresh crossover assumption and the public ATR API sentinel is `0.0`, not None. A test failure should lead to evidence, not an unreviewed production-strategy change.

## Next validation gate

Run targeted `PYTHONPATH=. ./.venv/bin/pytest tests/test_triple_cross_condition_semantics.py tests/test_m030_stage1q_boundaries.py tests/test_m030_incremental_contract.py -q`, plus existing stochastic/ATR/EMA, M030 parity and relevant regression suites and syntax checks. Return counts, exact failures, file hashes/paths and status of source protection. Codex must not silently edit source.

Only after Stage 1Q tests pass should Stage 1R be considered for full ordered M030 lifecycle stream and real strategy runner position-blocking integration.

## Unproven

Python correctness tests do not establish independent native MT5 historical server-to-UTC mapping, source OHLC/tick identity, tester execution, broker-specific fills/costs, economic parity or profitability. Standalone account-free MT5 environment remains blocked by Stage 1O STOP.
