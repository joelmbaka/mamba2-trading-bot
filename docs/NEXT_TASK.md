# Next Authorized Task — M030 Stage 1C no-trade data alignment preflight

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **ISOLATED NO-ORDER MQL5 COMPILATION ACCEPTED; READ-ONLY DATA PROVENANCE NEXT**

## Accepted prior results

- Python synthetic tests 10 passed; relevant regressions 45 passed; Python syntax passed.
- Stage 1B-I established necessity and feasibility of disposable compiler isolation.
- Stage 1B-II reported successful compilation of `mql5/M030_DecisionProbe.mq5` under independent disposable Wine prefix/app with MetaEditor 5.0.0.6316, 0 errors and 0 warnings. Source SHA-256 `16d5dd992d8183074d0c7795661e4891aca4ff52a103fa11ad8786929b886ba6`; EX5 SHA-256 `392a6cb6f71893a5cb24a2da0a730120da98d18baadfebbf44030fb74522308c`. Process exit code 1 is an unresolved reporting anomaly; preserve the compiler log and executable evidence. Original running terminal unchanged. See `docs/milestones/030-stage1bii-compiler-validation.md`.

## Immediate next gate — Stage 1C

Before any tester or historical replay, Codex should perform only separately instructed read-only offline data-provenance checks:
1. Check clean/synchronized `scalping-recovery`, read M030 contract.
2. Inventory existing repository EURUSD M1/M5/Ask datasets and manifests: file hashes, source server, exact first/last UTC rows and warm-up span, sample completeness, timezone declarations and tick export provenance. **Do not inspect historical trading P/L.**
3. Read-only inspect the known EURUSD MT5 cache metadata and timestamps without launching MT5, Wine, MetaEditor or Strategy Tester. Do not mutate originals or interpret a cached binary as a proven complete real-tick source unless independently decoded and validated.
4. Determine whether an explicit historical MT5 server-to-UTC offset can be independently established from available metadata. No inference from user's Kenya timezone or speculative offsets.
5. Identify the exact common initial M1 and M5 source bar used for EMA and stochastic warm-up and whether the EA's copied-history approach can reproduce the Python historical prefix. Report any mismatch instead of silently trimming inputs.
6. Provide machine-readable data inventory where feasible but do not create/write files under this read-only preflight. Return source paths, hashes, row counts, UTC identity, missing coverage and blockers.

## Boundaries

Stage 1C is **not** authorization to launch a tester, download/repair market data, initialize a broker, run a historical Python backtest, create orders (even simulated), install packages, change strategy calculations or overwrite old data. Workstation execution belongs only to Codex, not local-control or local-control-results. GitHub remains the source editing control plane. No new branches.

## Next decision

Evaluate data identity and clock evidence before authorizing isolated no-trade MT5 decision-only Strategy Tester operation. Full trade execution comparison remains a separate later gate.

## References

- `AGENTS.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/milestones/030-scalping-parity-audit.md`
- `docs/milestones/030-stage1a-source-checkpoint.md`
- `docs/milestones/030-stage1b-validation.md`
- `docs/milestones/030-stage1bi-isolation-preflight.md`
- `docs/milestones/030-stage1bii-compiler-validation.md`
