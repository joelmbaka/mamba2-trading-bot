# Next Authorized Task — M030 Stage 1A Parity Harness

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1A SOURCE IMPLEMENTATION AUTHORIZED — LOCAL EXECUTION / BACKTEST NOT AUTHORIZED**

## Current boundary

Stage 0 source audit and Codex read-only runtime preflight completed. The operator's latest handoff selects the next implementation milestone after Stage 0 and prohibits automatic MT5 backtests. Implement **Stage 1A independent Python/MQL5 parity harness** under `docs/milestones/030-stage1a-parity-harness.md`, preserving `docs/milestones/030-scalping-parity-audit.md` as the Stage 0 record.

Start at reported clean, synchronized `scalping-recovery` commit `c36296c3fe3c74d82e50d30164595f78e9351bee`, but check the GitHub branch head before every write and do not overwrite newer changes. No new branch.

## Work now permitted for ChatGPT on GitHub

- Implement opt-in Python event ledger, independent MQL5 test-only EA, versioned manifest/schema, first-divergence comparator, synthetic fixtures and test cases, Codex execution guide.
- Preserve original M5/M1 signal, 21/7/7 stochastic, EMA7, M5 ATR14 (simple TR average), 0.1 lot, SL1×/TP2×ATR and current stop/trailing timing; no optional M020-D filter applied to this frozen baseline.
- Freeze EURUSD 2026-09-10 UTC as initial sample, with pre-roll. Do not silently substitute a date based on economics.
- Prefer isolated instrumentation rather than intrusive refactors; economic outputs must be unchanged when tracing is disabled.
- Document all assumptions and outstanding availability/precision issues.

## Still not authorized

- Any local commands, tests, MetaEditor compile, MT5 GUI operations or Python/MT5 backtest without a separately scoped Codex instruction and execution authorization.
- Any broker login/init, real or demo account trading, external history fetch, installs, strategy optimization, changes to production strategy semantics or monthly paper scheduling.
- Any MQL5 simulated order outside isolated Strategy Tester. Test EA default must be no-order, fail-closed outside tester.

## Next gate

After source implementation, request Codex Stage 1B **compile + synthetic validation + read-only tester readiness**, with exact paths, build evidence, tests and blockers. Only after reviewing Stage 1B may the operator authorize Stage 2 one-day historical Python replay and isolated MT5 visual Strategy Tester simulated orders.

## References

- `AGENTS.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/WORKFLOW.md`
- `docs/milestones/030-scalping-parity-audit.md`
- `docs/milestones/030-stage1a-parity-harness.md`
