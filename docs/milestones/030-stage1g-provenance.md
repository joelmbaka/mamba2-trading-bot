# M030 Stage 1G — exporter and native-history provenance investigation

Date: 2026-11-12
Status: **READ-ONLY INVESTIGATION ACCEPTED; NATIVE CLOCK/DATA PARITY UNPROVEN**
Inspected `scalping-recovery` at `3f1adcccf462c8f1fe91c504b2173c275b8dd13d` (clean, equal to origin, ahead/behind 0/0).

## Exporter provenance

`mamba2/backtest/mt5_dataset.py` calls MT5 `copy_rates_range()` with UTC-aware Python datetimes, labels timestamps with `pd.to_datetime(time, unit="s", utc=True)`, and uses `copy_ticks_range()` to derive Ask. It can request history synchronization using `copy_rates_from_pos()` and `copy_ticks_from()`. This documents the exporter mapping and manifest's `bar_open_utc` claim; it is **not independent proof** that an isolated MT5 tester will use identical native bars, ticks, or historic server-local time.

Canonical manifest `backtest_data/m022-history-inventory-tick-m1-v2/manifest.json`: SHA-256 `cfaf3d130eb8fc2abf2e467e43cc5bba735df711ebb8bc9766e865713ba4065b`; MetaQuotes-Demo; export `2026-09-26T11:09:54.037447Z`; requested `2025-08-25T00:00Z` through `2026-09-25T00:00Z`. M1/Ask 405,283 rows, first 2025-08-25 00:03 UTC; M5 81,036 rows, first 2025-08-25 00:00 UTC; 2026-09-10 1,440 M1 and 288 M5 rows. These are source claims.

## Terminal evidence

Original terminal `/home/joel/.local/share/mamba2-mt5-wine1121/app/logs/20261112.log` contains authorization/access-point/build messages but no independently paired UTC and historical server-local candle timestamp. `app/config/terminal.ini` reports `LastBuildTester=6316` and `ProgramBuild=6230` but no historic UTC offset. Account identifiers were not reported.

Read-only local EURUSD cache inventory:

| File | Size | SHA-256 |
| --- | ---: | --- |
| `history/EURUSD/cache/M1.hc` | 1,263,074 B | `ffa5b9ff285f176ac411d3fd97f70429b2ab001fb51b7cc87f43c2df0751afed` |
| `history/EURUSD/cache/M5.hc` | 250,994 B | `5ee6fdd079e7458e24ca8531091900573cec865f269a6c7395e46090a1120250` |
| `history/EURUSD/2026.hcc` | 1,313,328 B | `3f95e4e48cf4888a63535bb0531ad313f5e5fa4948b4312089b298998fa54331` |
| `ticks/EURUSD/ticks.dat` | 37,692 B | `cc6ee0f1702233f8ae82048e472814b2ce26314e385aa0cd0b69741455cad19f` |

Available offline utilities (`file`, `strings`, `xxd`, `hexdump`, `objdump`, `readelf`, `7z`, `sqlite3`, Python) did not provide a documented reliable `.hc`/`.hcc`/`ticks.dat` decoder or verified timestamp index. Cache metadata cannot establish native bar coverage or real ticks.

## Conclusion

No independently verified historic MetaQuotes-Demo server-to-UTC offset. No proof cached native M1/M5 bars include complete canonical source prefixes or share exact OHLC. No validation of native tick sequence. Do not guess offset, substitute another history dataset, or relax the original strategy's EMA first-source seed.

## Proposed Stage 1H — standalone no-order clock/bar probe (source only)

Design and separately authorize implementation of a new independent tester-only MQL5 probe (do not weaken `M030_DecisionProbe.mq5` fail-closed UTC input requirements). New probe must:
1. Refuse any non-Strategy-Tester context, lock EURUSD and frozen research interval, require explicit server-date envelope broad enough to include **all plausible offsets** rather than infer an offset.
2. Never trade, connect to a broker, initialize an account, download data, use the original terminal/prefix, or alter native history.
3. Export *raw* tester server timestamp, completed M1/M5 bar open, native OHLC, timeframe, actual tester clock observation, and source/run metadata; never label raw server times as UTC.
4. Report first/last available bar, count, missing/duplicate/stale candles, exact tester build/config and no-data cases. Do **not** claim full historical first-prefix coverage from a short 2026 sample.
5. Strictly fail closed on unavailable source rows; cap output file sizes, protect against overwrite, and avoid outputting credentials or account information.
6. Include an offline Python comparator over candidate server-to-UTC offsets, matching *both* native M1 and M5 OHLC/timestamp sequences. Require a **unique and sufficiently complete** mapping with zero unexplained source differences, clear observed coverage, and independent dataset hashes. Never choose an offset from market hours, Kenya timezone, or filename metadata. Handle potential DST transitions explicitly; a single constant offset may be insufficient for the full 2025–2026 history.
7. Maintain no-order separation from strategy calculation. Source-only implementation, synthetic comparator tests, and disposable MetaEditor compile must each be reviewed before a **separately authorized**, isolated, network-disabled decision-free tester diagnostic.

A hard operational blocker remains: a fresh isolated tester without account data may have **no usable native bars**. No cached history can be assumed portable without a documented safe provisioning method. If no bars can be exposed offline and without copying account data, return a blocker; do not connect a broker or fetch data to make the test pass.

No terminal, Wine, MetaEditor, Strategy Tester, account access, data download, new files or historical replay occurred in Stage 1G.
