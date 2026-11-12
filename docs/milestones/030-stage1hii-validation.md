# M030 Stage 1H-II — canonical epoch adapter validation accepted

Date: 2026-11-12
Status: **PYTHON FORMAT FIX VERIFIED; ISOLATED MT5 HISTORY ACCESS STILL UNPROVEN**

## Repository and tests

Codex validated clean synchronized `scalping-recovery` at `c0a7d2259a5e10a3518603ee119d244577466f9b` (ahead/behind `0/0`; no source/data modifications).

- Focused M030 tests: **49 passed**.
- Relevant regressions: **59 passed**.
- Python syntax checks: passed.
- New canonical reader accepts original integer Unix epoch-second `time` values only with explicitly selected `reference_timestamp_format="unix_seconds_utc"`; default ISO-8601 mode correctly rejects canonical files, preventing silent format inference.

## Frozen canonical dataset evidence

Directory: `backtest_data/m022-history-inventory-tick-m1-v2/` (existing immutable source).

| File | SHA-256 | First full-file bar (claimed UTC) | Frozen 2026-09-10 UTC bars | Frozen last |
| --- | --- | --- | ---: | --- |
| `EURUSD_M1.csv` | `19a3a92141989e9d1ed174447e43ada627c13ed8b3cef39d800a07d587fdc2fe` | 2025-08-25 00:03 | 1,440 from 00:00 | 23:59 |
| `EURUSD_M5.csv` | `c8dc043c301531b11452a95273bd2fceec8f7ca933d99c5d7338d3f4ab2bb2e9` | 2025-08-25 00:00 | 288 from 00:00 | 23:55 |

Exporter `bar_open_utc` semantics remain an exporter claim, not independently verified MT5 historical server clock provenance.

## No-order independent probe

`mql5/M030_ClockBarProbe.mq5` SHA-256 `9b6b4782402c0eea268ccea8325ca81bf03b0e265054d58904c598137834a2fe` unchanged from the independently compiled source (Stage 1H-I: isolated MetaEditor 6316, 0 errors/warnings, EX5 SHA-256 `59cf2288212bc8d215b32f23a7bda89c9faf25dbcd486706999ad5251c5f2496`). No need for recompilation solely because Python adapter changed.

No Wine, MetaEditor, MT5 or Strategy Tester launched during Stage 1H-II. Original MT5 PID 71219 remained alone. No broker access, data imports/downloads, historical replay, order operation, installation, original-file modification or local-control.

## Remaining blocker: offline isolated history provisioning

A freshly copied tester/terminal with no account profiles may have no native EURUSD M1/M5 history; the opaque original `.hc`, `.hcc`, `ticks.dat` cannot independently prove requested coverage or compatibility. Their mere presence does not justify copying original terminal state or assuming parity. The network must be blocked externally; MQL5 no-order source alone cannot enforce this.

## Next gate — Stage 1I offline tester provisioning feasibility (read-only)

Codex should review existing MT5 tester/cache documentation and layout, and inspect original history *non-sensitive data file classification* and disposable environment requirements **read-only**, without copying any files or running Wine/MT5/Tester. Determine whether strictly market-data-only content could be provisioned in a **separate** offline isolated terminal (no account/profile/config/log/history mutation of original). Consider whether the tester automatically requires terminal authentication, network synchronization, or history download. Report source-grounded evidence and a proposed fail-closed offline data-discovery protocol.

If independent MT5 native history cannot be made accessible offline without account state/network activity, declare a blocker rather than guessing clock offsets, simulating native history, or silently replacing canonical input. Any copying, provisioning, terminal/tester execution or network namespace changes must be separately authorized.

Do not claim any historic UTC/server offset, native tick parity, full warm-up parity, economic parity or profitability from this result.
