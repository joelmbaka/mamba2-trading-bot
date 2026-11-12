# Next Authorized Task — M030 Stage 1R synthetic lifecycle test validation

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1R TEST SOURCE COMMITTED; VALIDATION NOT YET PERFORMED**

## Prior evidence

Stage 1Q validated **64 focused passing, 92 related regressions passing, 1 known legacy skip, 119 Python files syntax-parsed**, no failures. Tests show original ten-candle extreme/no-fresh-crossover, stochastic 34/35, EMA first-source seed and ATR14 14-bar `0.0` / 15-bar gap semantics.

Stage 1R read-only Codex audit mapped event sequence, real strategy guard, and schema-only REJECT/ACCOUNT. ChatGPT committed only new **synthetic tests** in `tests/test_m030_stage1r_lifecycle.py`, fully described in `docs/milestones/030-stage1r-test-implementation.md`.

## Stage 1R test-only implementation

- One-shot positive-ATR BUY trace checks `M1_CLOSE(10:01) → SIGNAL → SUBMIT → FILL → SLTP_MODIFY`, then `EXIT(10:02) → M1_CLOSE(10:02) → SIGNAL`. HistoricalBroker's exit on completed 10:01 bar occurs **before** the current boundary's close event. Test asserts UTC milliseconds, source bar open, fill from execution open, old SL/TP=0, new ATR-derived SL/TP, stop_loss reason and IDs.
- Real production `StochasticTripleTFStrategy` plus real runner, broker and manager: after first eligible submission fills, no further evaluation/submission while position open; synthetic stochastic/EMA and reporting mocks only, no ATR protection.
- Sparse EURUSD 10:00, 10:01, 10:04 and GBPUSD clock: **real strategy** first eligible at 10:02 because it needs two completed M1 candles; queued order remains unfilled at 10:03 and settles at 10:04 before blocking another evaluation. `SIGNAL` is intentionally absent for blocked candidates.
- `REJECT` and `ACCOUNT` remain schema-only, not runtime-produced. No production code changed.

## Next bounded Codex validation

1. Verify clean synchronized branch, read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, this file and Stage 1R implementation milestone.
2. Run `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_m030_stage1r_lifecycle.py tests/test_m030_stage1q_boundaries.py tests/test_triple_cross_condition_semantics.py tests/test_backtest_strategy_lifecycle.py tests/test_m030_parity.py`; add relevant focused and broad regression suites (synthetic in-memory tests only) and Python syntax audit.
3. Inspect exact event timestamps/bar-source fields and fills. In particular: a bar opening 10:01 is NOT completed until 10:02; earliest real entry with two completed M1 bars is 10:02; no synthesized blocked SIGNALs.
4. Report exact passed/failed/skipped counts, precise traceback and source lines for discrepancies. **Do not patch files locally**; return failure evidence for separate GitHub source-only corrections.
5. Verify original terminal/PID, native market history and source dataset remain untouched; no file artifacts emitted.

## Prohibited

No historical economic replay or performance optimization, Wine/MT5/MetaEditor/Strategy Tester, broker login or account-history copies, downloads, simulated/live trades outside deterministic mocked synthetic broker tests, installs, local source edits, reset/force-push/new branches or local-control.

## Following gate

Only after Stage 1R tests pass may we evaluate remaining deterministic trace-contract gaps and stop/revisit native MT5 parity based on **new evidence**, not another empty terminal attempt. Native server UTC offset, independent OHLC/ticks and broker fills remain unverified.
