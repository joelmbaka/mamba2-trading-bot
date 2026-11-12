# M030 Stage 1D — Codex validation and performance blocker

Date: 2026-11-12
Repository: `scalping-recovery` at `f878cbd65389ae4f1ccb490ecbfd3af93bba96ca`; clean, origin synchronized, ahead/behind `0/0`.

## Validation accepted

- `PYTHONPATH=. ./.venv/bin/pytest tests/test_m030_parity.py -q`: **13 passed**.
- Relevant execution, portfolio, strategy and indicator regressions: **45 passed**.
- Python `py_compile` for M030/runner/broker/test modules passed.
- Disposable MetaEditor 5.0.0.6316 compiled revised no-order `M030_DecisionProbe.mq5`: **0 errors, 0 warnings**, 602 ms; EX5 produced.
- Compilation command returned status `1` despite clean MetaEditor log, as in previous stage. Preserve this anomaly.
- Source SHA-256: `e916a427a2812d6544aaebb184ff398c81565fe6349749a34d9f07f8198a579d`.
- EX5 SHA-256: `dd019f9769c66b229b31b81ffe1bf9a0ac619dd3d4f01a6f4f2e5f1272d374a1`.
- Disposable root: `/tmp/mamba2-m030-stage1d.1SilW3`; fresh `wine-prefix/drive_c/M030MetaEditorApp`, without Z: or user-folder host mappings and without trading/account/history/config/common data. Original MT5 PID `71219` remained untouched.
- No tester, broker, replay, trades, installs, downloads or local-control used.

## Blocking complexity

The observation EA presently repeats **full-prefix CopyRates and indicator recomputation** each M1 boundary. Before the frozen sample, canonical data has approximately 389,000 M1 bars and 78,000 M5 bars. For 1,440 boundaries, Codex estimated ~19 billion inner-loop operations before overhead; this is an *analytical estimate, not a runtime benchmark*. Optional first-bar audit exports approximately 467,000 OHLC rows. Therefore **do not authorize the MT5 tester yet**.

## Next implementation — M030 Stage 1E incremental causal engine

ChatGPT performs source-only GitHub changes on existing `scalping-recovery`:
1. Initialize indicator state once from the **full independently seeded M1 and M5 histories**; refuse unavailable first bars, unknown server offset, unverified timestamp alignment or unsupported history count.
2. As each completed M1 (or new completed M5) bar appears, advance stochastic (21/7/7), EMA(7) and rolling true-range ATR(14) using causal incremental state, preserving warm-up conventions and recent-ten-extremes behavior; do not substitute short pre-roll or full recompute per minute.
3. Maintain *strict* monotonic, no-gap/duplicate, current-vs-completed bar checks; a timestamp discontinuity should fail closed rather than silently bridge.
4. Keep optional OHLC audit independent of incremental evaluation, evidence filenames immutable, server-to-UTC conversion explicitly verified and decision-only order-free safety.
5. Add synthetic Python reference fixtures comparing incremental vectors to the original full-prefix calculations at many boundaries, including stochastic warm-up, EMA seed, M5 rollovers, missing bars and chronology.
6. Source review then separate Codex focused tests and isolated MetaEditor compilation. No MT5 tester execution or historical Python replay without subsequent authorization.

### Unresolved after source optimization

Native MT5 cache coverage, source OHLC equality, actual historical server-to-UTC offset, real tick sequence, broker costs, position-blocking equivalence, and end-to-end execution parity are all unknown. Test passing does **not** establish profitability or signal parity.
