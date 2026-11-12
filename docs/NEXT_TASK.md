# Next Authorized Task — M030 Stage 1R lifecycle integration audit (read-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1Q VALIDATED; STAGE 1R INTEGRATION TEST DESIGN NEXT**

## Accepted Stage 1Q

Codex verified clean synchronized `scalping-recovery` at `2b320c75908fb06d04019372fbff16645e350f97`. **64 focused tests passed; 92 related regression tests passed, 1 known legacy skip; 119 Python files parsed; no failures**. Real production BUY/SELL ten-candle historical extreme (no fresh K/D crossover), M030 observer reasons, stochastic 34/35 warmup, EMA first-source seed and ATR14 14-bar zero sentinel / 15-bar gap TR boundary verified using synthetic fixtures. Full acceptance: `docs/milestones/030-stage1q-validation.md`. No production strategy implementation changed.

## Immediate task after separate Codex instruction — Stage 1R read-only test design

1. Confirm branch clean and synchronized. Read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, Stage 1P gap audit, Stage 1Q validation and this file.
2. Inspect `mamba2/backtest/runner.py`, `broker.py`, `position_manager.py`, `m030_parity.py`, M030 observer, production `mamba2/strategy/triple_cross.py` and existing deterministic lifecycle tests.
3. Map exact invocation/event order for `broker.advance()`, `M1_CLOSE`, `SIGNAL`, `SUBMIT`, `FILL`, `SLTP_MODIFY`, `EXIT` across at least one synthetic entry, deferred SL/TP attachment, and exit. Distinguish event chronology (including source bar and timestamp) from the misleading assumption that every event always follows that simple listed order. Include same-boundary fill and prior-exit-before-new-M1_CLOSE cases.
4. Design concrete tests integrating **real production strategy** with `BacktestRunner` and synthetic mocks/feeds to prove an open position or pending order prevents another submitted order, even when a second candidate signal exists. If complete real strategy setup is infeasible, document exact minimal injectable interfaces and limitations.
5. Review schema-only `REJECT` and `ACCOUNT` kinds; report whether intentionally absent and avoid inventing event producers. Identify existing traces available for blocked signals.
6. Return precise file/line test plan, helper fixtures, expected ordering, any suspicious discrepancy and verification gates. **Do not change files or run any tests/replay locally** at this stage.

## Prohibitions

No real or synthetic historical economic replay, Wine/MT5/MetaEditor/Strategy Tester start, broker connection, external market-data access, simulated/live orders beyond test-design mocked calls, production strategy tuning, package installs, original terminal/history copy/modifications, repository edits/branches/force-push/reset or local-control.

## Later gate

Source-only GitHub test implementation and focused synthetic tests follow read-only Stage 1R review. Native MT5 server UTC offset, native tick/bar history, tester execution and economic parity remain explicitly unverified and the standalone MT5 route paused.
