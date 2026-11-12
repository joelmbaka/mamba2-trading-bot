# Next Authorized Task — M030 Stage 1S closure/readiness evidence matrix (read-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGES 1Q/1R SYNTHETIC PYTHON TESTS PASSED; NATIVE MT5 PARITY BLOCKED**

## Accepted verification

Stage 1Q: 64 focused tests passed; related regressions 92 passed, 1 known legacy skip; 119 Python syntax files parsed. Real production ten-M1-candle extreme BUY/SELL without fresh crossover, Stochastic 34/35 warm-up, first-source EMA7 and ATR14 public 0.0 vs 15-row gap TR tested.

Stage 1R: 59 focused tests passed; 109 related deterministic regressions passed, 1 known legacy skip; 120 Python files syntax-parsed; zero failures. Real replay broker/position manager event ordering `M1_CLOSE,SIGNAL,SUBMIT,FILL,SLTP_MODIFY`, prior completed-bar `EXIT` before new `M1_CLOSE`, same-boundary execution open, deferred ATR protection and production strategy pending/open position guards. See `docs/milestones/030-stage1r-validation.md` and Stage 1Q validation milestone.

Original MQL5 diagnostics compiled, but native MT5 startup was short-lived without account/server state and neither a supported offline tester nor history-portability path was found. Stage 1O specifically STOPPED additional account-free blank-terminal retries. Historical MetaQuotes-Demo UTC offset, native M1/M5 OHLC and ticks, MT5 tester decision/fill parity and broker costs remain unverified. The frozen UTC sample remains 2026-09-10; source exporter UTC interpretation is not independent historical broker clock verification.

## Next bounded Codex task — Stage 1S read-only decision

1. Verify clean synchronized branch. Read `AGENTS.md`, `docs/BACKTEST_SEMANTICS.md`, `docs/NEXT_TASK.md`, M030 milestone, Stage 1O STOP, Stage 1Q/1R validations, M030 probes and source/test design summaries as necessary.
2. Produce a single **read-only M030 evidence matrix** separating: (a) frozen strategy/indicator calculations, (b) Python causal feed and signal decisions, (c) synthetic broker/execution and trace ordering, (d) MQL5 source compilation, (e) independently established native MT5 timestamps, M1/M5 OHLC and tick history, (f) native tester decision/execution parity, and (g) economic performance/broker execution.
3. For each, name exact verified evidence, remaining uncertainties and an objective pass/fail gate. Do not treat overlapping test suites' pass counts as independent distinct test totals, do not overstate synthetic proof, and do not conflate original historical source exporter timestamp interpretation with broker-clock proof.
4. Identify whether any *new* supported and privacy-preserving native data/time source is available **without** copying account material or connecting to broker. If none, recommend explicit native-parity STOP, with alternatives and required evidence to reopen. No speculative MT5 processes.
5. Recommend a single focused next action in one of two forms: evidence-backed source-only work, or formal closure/pause of M030 awaiting independent native evidence. Any historical **economic** test, broker/tick study or native tester must be separately authorized.
6. Report findings and citations to repo paths/lines, and identify any known schema-only `REJECT`/`ACCOUNT` events and blocked candidate observability limitations.

## Prohibited

No code edits, tests, historical replay, Wine/MT5/MetaEditor/Strategy Tester startup, native history/account data copying, broker connection, downloads, simulated/live orders, optimization or performance claims, package installs, new branches/force-push/reset or local-control.

## Decision after Stage 1S

Use the evidence matrix to decide whether to close Python deterministic correctness submilestone while keeping **native MT5 parity unresolved**; do not bypass the native MT5 and economic validation requirements by relabeling Python tests as trading readiness.
