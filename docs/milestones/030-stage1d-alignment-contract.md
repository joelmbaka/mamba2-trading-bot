# M030 Stage 1D — independent M1/M5 alignment source checkpoint

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **SOURCE CHANGES COMMITTED; SYNTHETIC TESTS AND MQL5 RECOMPILATION REQUIRED**

## Changes

- `mql5/M030_DecisionProbe.mq5`: replaces single `SourceHistoryStart` with **two fail-closed server-local first-bar inputs**: `M1SourceStartServer` and `M5SourceStartServer`. Both default to 0 (invalid). Requires `VerifiedServerUtcOffsetMinutes`, default 99999 (invalid), before converting frozen UTC comparison boundaries to historical server clock.
- `GetBars()` reads from each explicit timeframe origin, verifies the first bar exactly equals that origin and enforces chronological completed bars; refuses missing or stale latest completed M1/M5 bars. No fallback date or truncation to fit. A missing prefix stops the probe.
- Optional `EmitBarAudit` produces `BarAuditOutputName` CSV of every M1/M5 bar in the **first decision's completed prefix**. Fields are run ID, symbol, timeframe, server bar-open and OHLC. Default disabled; refuses an already-existing audit filename, just as decision CSV output refuses replacement. Outputs must be hashed/archived before any later runs.
- `mamba2/backtest/m030_bar_alignment.py` independently validates MT5 bar audit against trusted UTC-indexed, hash-verified **native M1 and M5** expected prefixes. Rejects missing/unordered/duplicate rows, source timestamp differences and OHLC differences, with first-mismatch evidence. Exact price equality is default; no rounding forgiveness without documented price source precision.
- `mamba2/backtest/m030_mt5_import.py` now rejects both incomplete and stale M5 candle references, including the 5-minute boundary convention.
- `tests/test_m030_parity.py` adds synthetic independent-start, mismatch, missing-prefix and duplicate audit cases.

## Important evidence gap and implementation caution

**These changes have not been executed or compiled in this source-only stage.** Stage 1B-II's previously successful EX5 is **stale** and cannot be used as evidence of compilation for this revised EA. The historical MetaEditor exit status 1 despite 0 errors/warnings remains known.

The 2025-08-to-2026-09 first-source window contains ~389k M1 and ~77k M5 bars before September 10. The no-order probe currently retrieves and calculates full historical prefixes on every new M1 boundary, which may be **computationally prohibitive** in the tester. Do not authorize a full-day run until bounded performance/causal-caching and complete-prefix preservation are separately designed and verified. No short warm-up window may be substituted merely for speed, because that changes EMA initialization. Optional full prefix audit can also generate large CSV files. Disc capacity, max-bars availability, and MT5 CopyRates history constraints require a separate feasibility check.

Timestamp offset remains **unproven** by Stage 1C. Merely setting the offset input is not independent verification. Native tester candle equality must be established through audit; a correct candidate-offset parameter is not proof by itself. MT5 chart/tester clock and exporter UTC claims must be independently reconciled.

The source CSV and MQL5 probe have no simulated trade functionality; order/fill/protection/exit parity remains unproven. No live or demo trading, broker access, historical tester operation or Python economic replay authorized.

## Next Codex validation — test and compiler only

Once explicitly scoped:
1. Verify clean/synchronized `scalping-recovery` and exact current GitHub HEAD, `AGENTS.md`, `docs/NEXT_TASK.md`, this checkpoint and `docs/BACKTEST_SEMANTICS.md`.
2. Run `PYTHONPATH=. ./.venv/bin/pytest tests/test_m030_parity.py -q` and relevant regression tests, report counts/tracebacks and syntax validation.
3. Compile **this revised** MQL5 EA in a new, verified disposable Wine prefix and copied MetaEditor application, reusing the safe Stage 1B-II isolation protocol. Do not reuse the old EX5 or original app/prefix; document compiler log, source/output SHA-256, errors/warnings and process-status anomaly.
4. Inspect estimated cost of full-prefix retraversal and propose performance-safe implementation. Do **not** launch tester/backtest or shorten history.
5. No repo source edits by Codex, no MetaQuotes account information, no real or simulated orders, no `local-control`.

After test/compile acceptance, ChatGPT should address performance feasibility and exact historical clock provenance before a decision-only tester run.
