# Next Authorized Task — M030 Stage 1D independent data-alignment contract

Date: 2026-11-12
Branch: `scalping-recovery`
Status: **STAGE 1C READ-ONLY PROVENANCE AUDIT ACCEPTED; SOURCE ALIGNMENT REPAIR NEXT**

## Accepted Stage 1C evidence

Codex inspected the canonical `backtest_data/m022-history-inventory-tick-m1-v2/` MetaQuotes-Demo export without modifying data or opening the terminal/tester. EURUSD Sep 10, 2026 UTC contains M1=1,440, Ask M1=1,440, M5=288 complete bars. The canonical M1/Ask first source bar is 2025-08-25 00:03 UTC; the native M5 source starts 2025-08-25 00:00 UTC. These different origins are valid **per-timeframe warm-up starts**; both engines must agree within each timeframe, not artificially synchronize M1 start with M5 start. Raw ticks were not preserved; MT5 caches cannot yet prove coverage or historical server clock offset. See `docs/milestones/030-stage1c-data-provenance.md` for hashes, row counts and unresolved risks.

Prior gates: 10 focused + 45 regression tests passed; independent no-order EA compiled with MetaEditor build 6316, zero errors/warnings and a generated EX5. CLI returned code 1 despite a successful log; note the anomaly. No tester execution.

## Next source work (ChatGPT GitHub only)

1. Revise `mql5/M030_DecisionProbe.mq5` as necessary to explicitly assert **separate M1 and M5 source origins**, correct `CopyRates` closed-bar ordering and startup seeds, and fail closed if the exact frozen history prefix is unavailable. Do not silently trim or shift warm-up data.
2. Capture or verify per-timeframe bar timestamps/OHLC using a deterministic export schema and manifest with independent source hash and time-zone declarations. MQL5 server timestamps are not assumed UTC.
3. Strengthen Python importer and synthetic tests to reject missing/duplicate/misaligned M1/M5 identities and unverified offset assumptions.
4. Document exact Codex source validation and disposable compilation instructions. Preserve original strategy semantics and all historical data. No new branch.

## Runtime boundaries

Stage 1D GitHub source work only; Codex tests/compile require a distinct bounded instruction and report. Do **not** automatically launch MT5 or its Strategy Tester, run a historical Python backtest, connect a broker, download/replace historical data, submit simulated/real orders, optimize strategy, install packages, or use `local-control`/`local-control-results`.

## Subsequent decision

After Stage 1D source validation and isolated compile, decide whether to authorize a *decision-only* MT5 tester session in an isolated environment to establish actual broker cache data coverage and clock alignment. No order-capable EA or economic parity is authorized at this stage.

## References

- `AGENTS.md`
- `docs/BACKTEST_SEMANTICS.md`
- `docs/milestones/030-stage1a-parity-harness.md`
- `docs/milestones/030-stage1bii-compiler-validation.md`
- `docs/milestones/030-stage1c-data-provenance.md`
