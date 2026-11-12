# M030 — PAUSED after Stage 1S evidence assessment

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **PYTHON DETERMINISTIC SEMANTICS VALIDATED FOR TESTED SCOPE; NATIVE MT5 PARITY AND ECONOMIC PERFORMANCE UNRESOLVED**

## Stage 1S decision

Codex reviewed clean synchronized branch `46c4cf1ae0b9e49889861f5e2e600a52c9bac898` read-only. No independent native MetaQuotes-Demo raw historical clock, M1/M5 OHLC, native tick/Ask, offline tester execution or broker cost/fill parity was available. The account-free blank terminal repeatedly shut down for an unknown reason; unsupported standalone tester-agent invocation is not authorized. The Stage 1S decision and evidence matrix are preserved at `docs/milestones/030-stage1s-readiness-decision.md`.

Prior Stage 1Q: 64 focused tests passed, 92 related regressions passed with one known legacy skip, 119 Python files parsed; real strategy ten-K extreme/no-fresh-crossover entry, indicator warmup, EMA7 seed, ATR14 boundaries.

Prior Stage 1R: 59 focused tests passed; 109 synthetic regressions passed with one known legacy skip, 120 Python files parsed; correct deterministic causal source-bar timing, signal/order/fill/SLTP/exit sequence and real strategy pending/open position guard. Test totals are separate suite counts with potential overlap; **do not add them as distinct tests**.

No production trading rules, source dataset or historical broker offset changed.

## No active M030 execution task

**PAUSE** rather than manufacturing a Stage 1T. Do not ask Codex to repeat blank MT5 terminal startup, invoke undocumented `metatester64.exe`, copy original account/server/history state, or endlessly add synthetic tests without a new diagnosed contract gap.

M030 may reopen only when a material, independently verifiable capability is provided:
- documented account-free offline native MT5 tester/history interface;
- independently captured and UTC-anchored native raw M1/M5/ticks plus full causal prefixes and provenance;
- or separately approved privacy-preserving native tester workflow with reproducible no-order probe traces.

On receipt of new evidence, the **first** action is a read-only source/provenance and privacy-risk assessment, not automatically starting a tester. Preserve frozen EURUSD sample 2026-09-10 and checksum pinned canonical dataset.

## Not yet approved

Historical **economic** backtest, new broker connections, market data downloads/imports, simulated/paper/live trades, strategy tuning, original MT5 state changes, Wine/MetaEditor/Strategy Tester execution, and local-control. Python semantics are validated within their synthetic scope, **not** independent native MT5 or real-broker parity, profit or deployment readiness.

## Next user decision

Await genuinely new evidence or separately scoped authorization for a different task. M030 itself is parked at Stage 1S.
