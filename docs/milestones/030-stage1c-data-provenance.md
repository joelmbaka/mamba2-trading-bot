# M030 Stage 1C — historical market-data provenance audit

Date: 2026-11-12
Status: **READ-ONLY INVENTORY ACCEPTED; CROSS-ENGINE DATA IDENTITY UNPROVEN**
Inspected repository HEAD: `ceaf94be2826d324f48434ea813f2270ae36fecb` (`scalping-recovery`, clean, origin synchronized 0/0).

## Canonical dataset

`backtest_data/m022-history-inventory-tick-m1-v2/manifest.json`

Manifest SHA-256: `cfaf3d130eb8fc2abf2e467e43cc5bba735df711ebb8bc9766e865713ba4065b`.

Manifest claims MetaTrader5 / MetaQuotes-Demo, exporter version `[500,6215,"25 Sep 2026"]`, `bar_open_utc`, requested range `[2025-08-25T00:00Z, 2026-09-25T00:00Z)`, Ask generated from `copy_ticks_range(COPY_TICKS_ALL)`, 41,003,938 valid Ask ticks, zero missing Ask M1 rows. **Raw tick sequence is not retained.** Exporter UTC label is not independent proof of the installed tester's server time.

| File (within canonical directory) | Rows | First claimed UTC open | Last claimed UTC open | SHA-256 |
| --- | ---: | --- | --- | --- |
| `EURUSD_M1.csv` | 405,283 | 2025-08-25 00:03 | 2026-09-24 23:59 | `19a3a92141989e9d1ed174447e43ada627c13ed8b3cef39d800a07d587fdc2fe` |
| `EURUSD_M1_ask.csv` | 405,283 | 2025-08-25 00:03 | 2026-09-24 23:59 | `7cca2326ead010df7dcc38fdbd787ec051804ce7145b4645325ea9f67ca0548c` |
| `EURUSD_M5.csv` | 81,036 | 2025-08-25 00:00 | 2026-09-24 23:55 | `c8dc043c301531b11452a95273bd2fceec8f7ca933d99c5d7338d3f4ab2bb2e9` |

Frozen evaluation interval is `[2026-09-10T00:00Z, 2026-09-11T00:00Z)`. M1: 1,440; Ask M1: 1,440; M5: 288; none missing in the observed sample. Before the sample: M1/Ask 389,447 rows; M5 77,868. Last pre-sample M1/Ask bar: Sep 9 23:59 UTC; M5: Sep 9 23:55 UTC. Warm-up is ample in *row count*, not yet proof that MT5 or the MQL5 EA sees identical source rows.

## Crucial clarification — independent timeframe histories

The earliest M1 bar is 2025-08-25 00:03 while the earliest M5 bar is 2025-08-25 00:00. **This is not itself an invalid dataset, nor a requirement to drop the first M5 bars.** The two timeframes have independent native history. M1 EMA and M1 stochastic must start at their own precise shared M1 source-history origin; M5 stochastic and M5 ATR must start at their own precise shared M5 origin. Reconciliation requires per-timeframe equality between engines (timestamps, OHLC and indicator seeds), not equality between M1 and M5's earliest timestamp.

The MQL5 diagnostic EA currently has *one* `SourceHistoryStart` and uses range-based `CopyRates`. This cannot prove complete exact first-bar parity or account for each timeframe's first source timestamp; a later source revision should use explicit per-timeframe first-source identifiers and assert them, reject missing bars and record prefix hashes before claiming indicator equality. No live strategy mathematics or economics changes are authorized. The alternative `first-baseline-20260901-20260925` dataset is **not** a drop-in replacement because it has different warm-up history.

## Existing MetaTrader data objects

Read-only observations:

- `/home/joel/.local/share/mamba2-mt5-wine1121/app/bases/MetaQuotes-Demo/history/EURUSD/2026.hcc`: 1,313,328 bytes; SHA-256 `3f95e4e48cf4888a63535bb0531ad313f5e5fa4948b4312089b298998fa54331`.
- `.../history/EURUSD/cache/M5.hc`: 250,994 bytes (hash not supplied).
- `.../ticks/EURUSD/ticks.dat`: 37,692 bytes; SHA-256 `cc6ee0f1702233f8ae82048e472814b2ce26314e385aa0cd0b69741455cad19f`.
- Older legacy .mt5 history cache also exists.

These files' sizes, hashes and mtime are not evidence of September 10 data coverage, identical M1/M5 candles or real-tick completeness. No independent historical MetaQuotes-Demo server UTC offset was found.

## Explicit blockers

1. MT5 historical M1/M5/tick coverage and broker clock offset are unknown; do not infer from exporter `bar_open_utc` or Kenya's local timezone.
2. Historical tick counts do not establish the original tick sequence or a matched real-tick replay.
3. The MQL5 EA's source seed, CopyRates range semantics and source M1/M5 prefix parity have not been verified.
4. Position blocking differs between the no-order tester probe and the Python trading runner.
5. No cross-engine decision stream has yet been produced, and neither Python/MT5 execution nor economics parity is demonstrated.

## Next gate — Stage 1D: source-only alignment contract, then no-trade tester readiness

First update the diagnostic **tester-only** source, importer and synthetic tests on GitHub to explicitly encode two independent history starts, strict per-timeframe bar identity, non-UTC server-clock ambiguity and warm-up exclusion. Require a deterministic comparison artifact that can reject differences by timestamp before comparing numeric indicators. Do not modify strategy execution semantics. Codex separately validates and compiles in a disposable isolated environment.

Only after passing this source and compiler gate may a *separately authorized* isolated **decision-only** MT5 tester run be planned to learn actual bar coverage/offset; no simulated trade orders. Retain September 10 as frozen candidate and do not substitute dates opportunistically.

No trading, MT5 backtest, broker connectivity, installing dependencies, or source-data mutation was performed in Stage 1C.
