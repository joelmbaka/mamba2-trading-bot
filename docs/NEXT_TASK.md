# Next Authorized Task — M030 Stage 1F tester/data readiness preflight (read-only)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1E INCREMENTAL ENGINE VALIDATED AND COMPILED; NO TESTER RUN AUTHORIZED**

## Accepted evidence

Codex verified Stage 1E incremental MQL5 EA source and synthetic validation: **39 focused Python tests passed**, **45 regressions passed**, syntax checks passed. The revised observation-only EA was compiled in a newly initialized isolated Wine 11.21 prefix with MetaEditor build 6316: **0 errors, 0 warnings**, EX5 SHA-256 `ea46dcb09e4bbc77fdb6b764918ab38c2b269909ae4520459ea7261c131609b4`; source SHA-256 `125c0f44cb2118a5ce74d5c8165fdb78c2a17e1dcb64351043f16e168f20e35f`. Exit code 1 is a previously observed CLI anomaly, but compiler output is explicit. Original terminal PID 71219 untouched. Full report: `docs/milestones/030-stage1eii-compile-acceptance.md`.

## Next bounded Codex task

**Read-only** inspect availability/readiness for an isolated no-order decision-only Strategy Tester configuration, but do not execute it:
1. Verify clean synced `scalping-recovery` branch and read Stage 1C provenance, 1E-II compile acceptance, and source-level guards.
2. Identify exact installed tester build, existing history/cache coverage evidence, and whether full earliest M1 (2025-08-25 00:03 UTC) and M5 (2025-08-25 00:00 UTC) bar prefixes can be supplied without downloads. Distinguish manifest claims from actual terminal-cache proof; do not assume a source alignment.
3. Seek independent historical server-to-UTC clock evidence for MetaQuotes-Demo. Do not guess a UTC offset; the EA must remain fail-closed on unknown clock.
4. Inspect feasibility of isolated tester inputs and safe immutable CSV evidence output paths (including large optional prefix audit), without copying account profiles or launching MT5. Do not start tester, MetaEditor, Wine, broker connection or Python backtest in this gate.
5. Return exact paths, build/version evidence, interval coverage proof or gaps, input readiness, time offset evidence, remaining blockers, and proposed *separately authorized* diagnostic procedure.

## Prohibited

No live/demo broker login, tester/terminal launch, historical replay, order calls (including simulated), data downloads, installs, changes to original MT5 app or Wine prefix, production strategy changes, optimization, reset/rebase/force-push/new branch, or local-control.

## Following decision

If enough clock and history evidence exists, propose an isolated **decision-only** tester step with no-order EA and frozen EURUSD 2026-09-10 UTC sample for explicit later authorization. If not, design a provenance-preserving alignment path before any tester execution.

## References

- `AGENTS.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/milestones/030-stage1c-data-provenance.md`
- `docs/milestones/030-stage1e-incremental-engine.md`
- `docs/milestones/030-stage1eii-compile-acceptance.md`
