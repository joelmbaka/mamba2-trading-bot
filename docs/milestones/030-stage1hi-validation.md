# M030 Stage 1H-I — validation and canonical epoch-second adapter

Date: 2026-11-12
Status: **INITIAL VALIDATION ACCEPTED; FORMAT ADAPTER CHANGES UNTESTED**

## Codex report at cfa0bc7ac4eea21f32be279e13c8eab35f628194

- Clean synchronized `scalping-recovery`, no local source modifications.
- **46 focused tests passed**, **59 relevant regressions passed**, Python syntax passed.
- Standalone `mql5/M030_ClockBarProbe.mq5` static safety: tester-only `MQL_TESTER`, EURUSD, no trade/order/account APIs, shift-1 completed M1/M5 and server-local timestamps, failures on missing bars, timestamp gaps and row cap, bounded seven-day envelope and 20,000 records maximum.
- Isolated no-order MetaEditor 5.0.0.6316 compiled **0 errors, 0 warnings**, 464 ms; EX5 produced. Wine CLI returned status `1` (the recurring MetaEditor exit-code caveat).
- Original/copy source SHA-256: `9b6b4782402c0eea268ccea8325ca81bf03b0e265054d58904c598137834a2fe`.
- EX5 SHA-256: `59cf2288212bc8d215b32f23a7bda89c9faf25dbcd486706999ad5251c5f2496`.
- MetaEditor binary SHA-256: `f9de90562ff98540278f16eb0d803a0392fd3be7a8fb6ad918817345507f2fc3`.
- Disposable root `/tmp/mamba2-m030-stage1h-i.DyxSFT`, initialized `wineboot -u` exit 0; `Z:` and broad user folder symlinks removed, EX5/inputs/output confined inside disposable copy, no process remnants and original MT5 PID 71219 untouched.
- No terminal/tester, broker session, downloads, historical replay, orders, installs or local-control.

## Discovered CSV incompatibility

Codex read actual local canonical files: `EURUSD_M1.csv` and `EURUSD_M5.csv` contain integer Unix epoch-second values under `time`, not ISO-8601 text. Original offline `m030_clock_discovery.py` expected ISO-8601 UTC strings, so it would have rejected those original files.

## GitHub adapter changes after the validated commit

The comparator now supports `reference_timestamp_format="unix_seconds_utc"` **only when explicitly requested**, and only for a `time` column containing integer Unix epoch seconds aligned to a minute. Default is still `"iso8601_utc"`, so ordinary fixtures remain strict. The comparator reads source files without rewriting them; existing SHA-256 pins remain in force. The exporter UTC interpretation is documented as a claim to test against raw server observations, not independently established truth.

New synthetic fixtures test accepted UTC epoch seconds, format declarations, invalid fractional seconds and non-minute-aligned epochs.

**The new adapter and test changes are not yet independently tested by Codex.** The previously compiled MQL5 EX5 remains valid because its source was not modified; no recompilation of that EA is required merely for Python format support.

## Remaining readiness blockers

1. No verified native MT5 cache coverage or full history prefix and no proven historical UTC/server clock mapping. The new probe itself is not allowed to run yet.
2. A copied terminal/tester with no account profiles may have no native bars; a separate read-only isolation and offline-data provisioning feasibility plan is necessary.
3. A unique one-day M1+M5 OHLC match proves only that day's timestamp/bar alignment, **not** the entire 2025–2026 EMA warm-up, raw tick provenance or trade parity.
4. The standalone probe uses `FILE_COMMON`; evidence must be confined by a physically isolated prefix and immutable run-specific filenames. OS network blocking must be independently verified before any separately approved tester run.
5. Synthetic tests do not yet use the actual canonical CSVs; a separately authorized local **read-only reference parser compatibility check** should first verify proper format parsing against known hashes/row counts and that the sample still contains 1,440 M1 and 288 M5 rows, without generating trades or touching MT5.

## Next narrow gate — Stage 1H-II Python adapter validation

Codex validates new synthetic tests plus canonical CSV reader against the known SHA-256 file hashes, without creating any CSV or running a Strategy Tester. Report specific failures and source-format edge cases; do not edit source locally. Do not treat this as authority to provision/launch MT5.
