# M030 Stage 1R — deterministic lifecycle integration tests (source-only)

Date: 2026-11-12
Status: **GITHUB TEST CODE COMMITTED; NOT YET EXECUTED/VALIDATED**

## Accepted Stage 1R read-only findings

Codex reviewed clean synchronized branch `3f297ce81d942a122466c5ac2440c090abd67058` and identified `HistoricalBroker.advance()` ordering of feed advance → completed-bar exits → position marks → queued fills, before `BacktestRunner.run_async()` emits `M1_CLOSE`, refreshes ATR, evaluates an unblocked candidate and strategy, settles same-boundary submissions, then runs position management.

Runtime observability has `M1_CLOSE,SIGNAL,SUBMIT,FILL,SLTP_MODIFY,EXIT` producers. `REJECT` and `ACCOUNT` remain schema-only. When a position or pending order blocks a symbol, the runner does **not** call the observer and does **not** emit a suppressed `SIGNAL`. This is a known observability limitation, not a test failure.

## GitHub source-only implementation

Added `tests/test_m030_stage1r_lifecycle.py`, containing:

1. **One-shot in-memory lifecycle trace** with actual `ReplayFeed`, `HistoricalBroker`, `BacktestRunner`, `PositionManager` and `EventSink`. A stub with deterministic positive ATR 0.0004 drives one deferred SL/TP attachment. Source bar 10:00 closes at boundary 10:01; one BUY order fills from execution open of source bar 10:01 with no spread, then the newly protected stop is touched in that 10:01 bar. At boundary 10:02, `EXIT` **precedes** `M1_CLOSE`. Assert precise timestamp/source-open fields, initial SL/TP zero, modification old/new values, fill/open price, linkage IDs and exit reason. Because the one-shot strategy is again eligible after exit, a fresh `SIGNAL` appears at the next boundary without a second order; event-list expectations reflect this actual semantics.
2. **Real production strategy open-position guard**: actual `mamba2.strategy.triple_cross.StochasticTripleTFStrategy.evaluate()` through real runner/broker/manager, mocked indicator outputs and isolated reporting method. First boundary sees only one completed M1 bar and cannot submit; second has two, so strategy submits an accepted order, fills at execution bar, and subsequent valid opportunities must not trigger `strategy.evaluate` or a second order. No ATR, so the position remains open.
3. **Real production strategy pending-order guard**: EURUSD M1 source at 10:00 and 10:01 (two completed candles available at 10:02), then none until 10:04; GBPUSD provides global clock. The real strategy can submit at 10:02 but no 10:02 execution bar is available; pending at 10:03 blocks observer and strategy, then fills in `broker.advance()` at 10:04 before guard. Exactly one SUBMIT/FILL and two prior SIGNALs; no suppressed-signal invention. This corrects the read-only proposal's 10:01 first-entry premise, which was incompatible with the real strategy's requirement for two completed candles.

## Constraints

Only test code was added. Production strategy/indicators/runner/broker/position management and source datasets remain unchanged. No GitHub source code was executed in this stage, so tests **must be validated**. Native MT5 account-free tester path remains stopped; no independent server-clock/ohlc/tick parity or broker execution evidence.

## Next Codex validation gate

1. Verify clean synchronized branch and inspect `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md` and this milestone.
2. Run focused synthetic `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_m030_stage1r_lifecycle.py tests/test_m030_stage1q_boundaries.py tests/test_triple_cross_condition_semantics.py tests/test_backtest_strategy_lifecycle.py tests/test_m030_parity.py`, then relevant regressions and syntax checks.
3. Return exact counts and failure traces, especially if the event order, original zero SL/TP, 10:02 stop, or 10:04 pending fill diverges from current production semantics. Check no writes/artifacts; report rather than patch code locally. Do not claim execution or validation until this gate is complete.
4. If tests fail, propose only reviewed GitHub *test-fixture* corrections. Changes to frozen trading behavior require a separate explicit decision.

No Python historical economic backtest, Wine/MT5/MetaEditor/Tester, broker/network actions, simulated/live trades beyond deterministic in-memory synthetic broker tests, installs, repo reset, force-push or local-control.
