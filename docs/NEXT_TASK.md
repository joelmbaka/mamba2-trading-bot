# Next Task — M031 Stage 0 same-data independent-engine feasibility (read-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **M031 PREPARATION ONLY — CROSS-ENGINE REPRODUCTION REQUIRED BEFORE MASS PYTHON BACKTESTS/TUNING**

## Why this task

After Stage 1S concluded that frozen M030 Python deterministic semantics were tested but independent native MT5 parity and economics remained unresolved, the user agreed to study historical performance **only with an explicit independent comparison gate**. The same frozen EURUSD Python-tested period must be reproduced in MT5 **or** a genuinely independent web-based engine **before** any mass Python evaluation or strategy fine-tuning.

See: `docs/milestones/031-independent-engine-parity-gate.md`. This is **not** authorization to execute a backtest, connect a broker, download/upload data or alter the original MT5 environment.

## Initial platform findings requiring scrutiny

Official MetaTrader 5 documentation supports custom financial symbols built from imported M1 rates/ticks and tested using Strategy Tester; higher timeframes are normally generated from imported M1. That is a *documented feature*, not proof a safe standalone account-free terminal can start under Wine. The previously tested isolated blank MT5 build 6316 exited; repeated startup attempts and undocumented standalone tester invocation remain prohibited under M030 Stage 1O.

QuantConnect LEAN cloud provides a possible second execution engine with user-defined external datasets, but its object storage and licensing restrictions, CSV OHLC loader and export limitations require feasibility review before any sign-up, paid tier, upload or algorithm execution. TradingView provider data is not an independent *same-input* comparison unless all source M1 and M5 rows can be matched.

## Next bounded Codex read-only task — M031 Stage 0

1. Verify clean synchronized `scalping-recovery`. Read `AGENTS.md`, `docs/NEXT_TASK.md`, `docs/BACKTEST_SEMANTICS.md`, `docs/milestones/030-stage1s-readiness-decision.md` and `docs/milestones/031-independent-engine-parity-gate.md`.
2. Inspect frozen source manifests and checksum evidence, timestamps and M1/M5 normalization/derived M5 behavior for the UTC interval `2026-09-10 00:00` to `2026-09-11 00:00` plus full warm-up. Determine whether MT5 M1-to-M5 aggregation can match the frozen independent M5 dataset; do **not** assume equality. Read-only inspection, no backtest/replay.
3. Inspect existing M030 observer/exporter, MQL5 probes, entry/position semantics and trace schema. Design a canonical same-input comparison of indicator outputs, per-M1 candidate decisions, submissions/fills/SLTP/exits and source bar times, with explicit tolerances and a STOP on unexplained mismatches.
4. Evaluate documentation evidence for MT5 custom symbol import/tester in a **newly isolated, no-account, no-network** hypothetical runtime and for a QuantConnect custom-CSV cloud project. Distinguish documented capabilities from locally verified startup viability; spell out data input/output, costs, privacy, source time zone, synthetic ticks and spread/slippage limitations.
5. Propose exactly one evidence-based next authorization gate: a bounded Python frozen-day baseline, if inputs/data lineage verified, and an independent no-order decision test design, or formal stop if impossible. No mass backtests or optimization before approved independent comparison.

## Prohibited

Do not run tests, Python historical performance simulations, Wine/MT5/MetaEditor/Strategy Tester, undocumented tester agents, connect any broker, copy original terminal credentials/profiles/history, import/alter data, upload sensitive data to cloud, install packages, run real/paper orders, optimize/tune, edit repository locally, reset/force-push/create branch or use local-control. Read-only audit only.

## M030 remains paused

Python deterministic synthetic strategy/indicator/event semantics have passed focused tests; native MetaQuotes-Demo raw timestamp, independent M1/M5 OHLC and tick identity, execution parity and profitability are **unproven**. Imported custom-symbol data can test platform semantics on *our* data but **cannot independently certify original broker historical data provenance**.
