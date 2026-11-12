# M030 Stage 1R — deterministic lifecycle validation acceptance

Date: 2026-11-12
Status: **STAGE 1R PASSED — SYNTHETIC PYTHON LIFECYCLE ONLY**

## Repository and validation evidence

Codex checked a clean, synchronized `scalping-recovery` at `04e72c59b1dab2aafc815414555f65e36470ad98` (ahead/behind 0/0). No source files modified locally.

- Prescribed focused Stage 1R suite: **59 passed**.
- Related deterministic synthetic regression suite: **109 passed, 1 skipped**.
- **0 failures**.
- Syntax: **120 Python files parsed successfully**.
- Known legacy skip: `tests/test_stochastic_triple_tf.py:4` references removed `mamba2.strategy.stochastic_triple_tf`, while current production strategy lives at `mamba2.strategy.triple_cross`. Do not misrepresent skipped legacy test as a pass.

## Verified in `tests/test_m030_stage1r_lifecycle.py`

- One deterministic BUY: `M1_CLOSE → SIGNAL → SUBMIT → FILL → SLTP_MODIFY`; completed-bar exit precedes next replay boundary's `M1_CLOSE`.
- Source M1 bar open and event UTC timestamp are correctly distinguished; same-boundary fill uses execution-bar **open**, not a future completed bar.
- Initial order SL/TP zero; real position manager attaches synthetic ATR-derived protection. Stop-loss exit uses expected reason and shared request/position IDs.
- Real `StochasticTripleTFStrategy.evaluate` is integrated with real `BacktestRunner`, `HistoricalBroker` and `PositionManager` under mocked indicators. With an open EURUSD position, no second strategy evaluation/submission occurs; with a queued EURUSD order and a sparse execution timeline, no duplicate submission occurs until/after the original fills.
- When the guard blocks evaluation, no `SIGNAL` event is emitted. This is a current observability limitation by design, not evidence of whether a candidate signal otherwise existed.
- `REJECT` and `ACCOUNT` remain schema-supported but without production event producers; do not infer broker rejections are emitted.

## Constraints and evidence level

All tests are in-memory synthetic tests, not historical trading performance research. No Wine, native MT5, MetaEditor, Strategy Tester, broker access, orders, live funds, downloads, package installation, local-control or historical market replay occurred.

Stage 1Q previously passed 64 focused tests and 92 related regression tests (one legacy skip), and syntax auditing of 119 files, validating frozen signal semantics and indicator boundaries. Synthetic correctness of specified cases is not exhaustive mathematical verification and does **not** demonstrate native M1/M5 candle/tick identity, historical MetaQuotes-Demo server-to-UTC mapping, MQL5 runtime parity, broker fills/spread/slippage or P/L reliability.

## Decision

Stage 1R is accepted. Do not expand into unbounded synthetic-testing phases by default. Use a final **M030 Stage 1S readiness/evidence review** to classify each frozen strategy contract and unresolved external dependency, choose a well-defined next independent evidence source, or explicitly leave native parity blocked. No Strategy Tester or historical economic evaluation is authorized by passing these synthetic tests.
