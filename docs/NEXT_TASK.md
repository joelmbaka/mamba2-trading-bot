# Next Authorized Task — M030 Stage 1H standalone native clock/bar discovery probe

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1G PROVENANCE INSPECTION ACCEPTED; SOURCE-ONLY DIAGNOSTIC DESIGN NEXT**

## Evidence

Codex inspected `mamba2/backtest/mt5_dataset.py`: exporter requests UTC-aware Python MT5 bars/ticks and labels `time` values as UTC. This proves the exporter transformation, but not an independent native MT5 historical server-to-UTC offset or native OHLC equality. Original terminal log/config and opaque EURUSD .hc/.hcc/ticks.dat metadata do not prove an offset, history coverage or tick identity. Local source/MT5 environment unchanged. Full evidence: `docs/milestones/030-stage1g-provenance.md`.

Stage 1E prior validation: 39 focused + 45 regression tests passed, no-order incremental EA compiled independently with 0 errors and 0 warnings. **That existing EA remains blocked** on unknown historical server offset and source-prefix identity.

## Next source work for ChatGPT on GitHub

Prepare **M030 Stage 1H** as a separate tester-only, no-order, no-account MQL5 *bar/time discovery probe* plus offline Python comparator:
- Do not change original strategy, its historical dataset, or weaken the existing `M030_DecisionProbe.mq5` UTC-offset fail-closed input.
- Probe uses explicit broad server-date envelope instead of a presumed UTC offset. Export raw tester server times, completed native M1/M5 OHLC, per-timeframe coverage and missing-data diagnostics; don't mislabel raw server times as UTC.
- Protect immutable output paths; ensure bounded CSV output, dedicated run identity, fail-closed startup/no-data checks.
- Offline comparator tests all documented candidate offsets, matches both native M1 and M5 bars to immutable canonical dataset by shifted timestamps and raw OHLC, and reports unique vs ambiguous/no mapping; preserve source hashes. A DST-changing offset may require segmented windows and must not be silently flattened.
- Document that a fresh isolated MT5 tester can lack native market history and may require future separately approved safe data provisioning; no network/broker access allowed by this task.
- Add synthetic tests; no tester execution during source development. Hand off to a separate Codex isolated MetaEditor compile and tests before proposing any decision-only tester run.

## Not authorized

Do not run Python historical replay, Strategy Tester, Wine/MT5 broker, real or simulated orders, download/import market data, install packages, modify original MT5 prefix/app or native history, change production strategy, optimize economics, or use `local-control`. Stay on `scalping-recovery` without branch proliferation.

## Following gate

Review independent source/tests/compile and data availability; only then decide whether a separately authorized **isolated decision-free, network-blocked tester discovery** can produce evidence without modifying original terminal/account state. Missing native bars are a blocker, not a reason to guess the offset.
