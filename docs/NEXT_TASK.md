# Next Task — M031 Stage 2 one-day Python baseline CLI (source-only implementation)

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1 INPUT SEAL ACCEPTED; CLI NOT YET IMPLEMENTED; NO HISTORICAL RUN AUTHORIZED**

## Objective and blocking gate

Build a reproducible, **fail-closed one-day Python baseline** for subsequent independently authored LEAN or supported MT5 tester comparison of the **exact same canonical source**. User requires independent same-input indicator/signal and then trade-model parity *before* mass Python backtesting or tuning. No profit or deployment claim follows from source-only unit tests.

Stage 1 seal: `docs/milestones/031-stage1-full-prefix-seal.md`; see also `docs/milestones/031-independent-engine-parity-gate.md` and `docs/BACKTEST_SEMANTICS.md`.

## Critical input rules

- Source `backtest_data/m022-history-inventory-tick-m1-v2/`: manifest `cfaf3d130eb8fc2abf2e467e43cc5bba735df711ebb8bc9766e865713ba4065b`, M1 `19a3a92141989e9d1ed174447e43ada627c13ed8b3cef39d800a07d587fdc2fe`, M1 Ask `7cca2326ead010df7dcc38fdbd787ec051804ce7145b4645325ea9f67ca0548c`, M5 `c8dc043c301531b11452a95273bd2fceec8f7ca933d99c5d7338d3f4ab2bb2e9`; assert hashes **before** any evaluation.
- Frozen source M1 interval `[2026-09-10T00:00:00Z,2026-09-11T00:00:00Z)`, 1440 M1 and 288 M5 rows. Full preceding prefix is required to reproduce first-source EMA7 seed and all indicator states: 389447 M1 and 77868 canonical M5 bars prior to the sample.
- The 288 frozen-day M1→M5 OHLC aggregations match native-source M5. **The full warm-up cannot be reconstructed identically from M1**: 151 incomplete/missing five-M1 buckets, 83 derived-only M5 buckets, and 3 comparable OHLC mismatches. **Use original canonical M5 as native input for ALL prefix/sample M5 calculations**. Source-specific spread/tick volume differ even on day; never substitute M1-derived M5 ancillary data.
- M1 Ask CSV is minute-aggregated and cannot prove raw ticks. Keep Ask, Bid, spread and cost assumptions explicit; do not invent native spread, tick order or broker behavior.

## Stage 2 source-only task

1. Verify clean synchronized `scalping-recovery`, read `AGENTS.md`, `docs/NEXT_TASK.md`, `docs/BACKTEST_SEMANTICS.md`, Stage 1 seal, and existing replay/runner, M030 observer/parity schema, dataset integrity loader and tests.
2. **Implement** a narrowly bounded module `mamba2/backtest/m031_single_day_baseline.py` with CLI `--manifest`, `--m1`, `--m1-ask`, `--m5`, `--symbol EURUSD`, `--start`, `--end`, `--output-dir`, `--fail-on-input-mismatch`. Prefer existing checksum-aware loaders; reject missing, modified or unexpected source hashes, ambiguous timestamps, incomplete selected-day M1/M5/Ask, and reused output directory. No original source file changes.
3. Explicitly distinguish **source-bar time** from **decision boundary time**: M1 bar opened at T is available only at T+1 minute. If the source-day window is `[Sep10 00:00, Sep11 00:00)`, its 1440 completed-M1 decision boundaries are `Sep10 00:01` through `Sep11 00:00` inclusive; the next half-open decision interval is `[Sep10 00:01, Sep11 00:01)`. Resolve M5 completion, 00:00 day turnover and any next-bar order execution without lookahead, state exact inclusive/exclusive boundaries and what happens to unclosed positions at end-of-run. Do not silently compare source-row count to a differently timed event window.
4. Use **full original M1 and canonical M5 source prefixes** for indicator seeding. Treat the selected day as a **flat-start trading evaluation**, unless a separately approved pre-start trading warmup is specified. Pre-start history is **indicator warmup only**, not months of trades. Do not mutate original `ReplayFeed` source or bypass private state unsafely; design safe clock fast-forward/immutable prefix handling with focused tests.
5. Collect `input_manifest.json`, `indicator_trace.jsonl` (all eligible decision boundaries including ones where strategy is blocked, clearly marked observation-only), `events.jsonl` from actual `m030.events.v1` runtime producers (no fabricated blocked SIGNALs), and `summary.json` (counts, unresolved positions, explicitly modeled costs; no profitability judgment). Append no uncontrolled artifacts/logs; output only into fresh scratch directory and refuse overwrite.
6. Freeze M5/M1 stochastic(21,7,7), last-ten %K extreme **without a fresh crossover requirement**, EMA7 first-source seed, M5 ATR14, deferred SL/TP, position/pending blocking, Bid/Ask assumptions, no unknown costs silently substituted. Keep actual production strategy/indicator/position behavior unchanged. Any new observation instrumentation must be separate and observation-only.
7. Add **synthetic input-integrity, calendar-gap, bar-open/decision-boundary, full-prefix seed and output-schema tests** using tiny fake CSV fixtures and no historical economic backtest. Do not yet invoke the new CLI on frozen EURUSD history. Report exact code/test changes and static checks to allow a subsequent authorized validation and one-day run.
8. Separately outline the independently authored LEAN adapter contract. No LEAN install, Docker pull or cloud upload in this stage.

## Explicit prohibitions

No actual frozen-day or mass historical economic replay, no tuning/optimization, Wine/MT5/MetaEditor/Strategy Tester, broker connection, market-data download/cloud upload, LEAN/Docker pull/install, live/paper orders, source dataset modification, original MT5 state access, force push/reset/new branch or local-control.

## After implementation

First validate source-only CLI with focused synthetic tests. Then **separately scope one frozen-day run** with persisted hashes and traces. Independently compare to a LEAN or properly isolated MT5 implementation using the **identical canonical M1/M5/Ask** inputs, full warmup and explicit signal/cost model. Mass Python research/tuning remains blocked until explained/no-unexplained cross-engine eligible decision differences.
