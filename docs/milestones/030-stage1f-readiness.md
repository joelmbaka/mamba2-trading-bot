# M030 Stage 1F — tester/data readiness audit

Date: 2026-11-12
Status: **READ-ONLY PREFLIGHT COMPLETE; NO TESTER EXECUTION AUTHORIZED**
Repository `scalping-recovery` at `71a47bdcd84d940ce9a86375611e84aa70dee3f4`, equal to origin, clean (ahead/behind 0/0).

## MT5 and compiler provenance

Installed terminal `/home/joel/.local/share/mamba2-mt5-wine1121/app/terminal64.exe`, agent `app/metatester64.exe`, MetaEditor `app/MetaEditor64.exe`.
`app/config/terminal.ini` reports `LastBuildTester=6316`, a configuration record rather than confirmation of a launched tester. Agent PE32+ x64 SHA-256 `d3ecb15e12e8918f80a8c531984b5a4ee6f2606ddf03504d8ec2514e7f110a49`. Original terminal PID 71219 remained running/untouched.

Prior Stage 1E compilation: no-order EX5 SHA-256 `ea46dcb09e4bbc77fdb6b764918ab38c2b269909ae4520459ea7261c131609b4`, MetaEditor 6316, 0 errors, 0 warnings; prior Python tests 39 focused plus 45 regressions passed. No tester run has validated this binary.

## Canonical research export

Directory `backtest_data/m022-history-inventory-tick-m1-v2/`; manifest SHA-256 `cfaf3d130eb8fc2abf2e467e43cc5bba735df711ebb8bc9766e865713ba4065b`.
Source claims MetaTrader5 / MetaQuotes-Demo, bar-open UTC.

| File | Rows | Claimed range | SHA-256 |
| --- | ---: | --- | --- |
| EURUSD_M1.csv | 405,283 | 2025-08-25 00:03 to 2026-09-24 23:59 UTC | `19a3a92141989e9d1ed174447e43ada627c13ed8b3cef39d800a07d587fdc2fe` |
| EURUSD_M1_ask.csv | 405,283 | same | `7cca2326ead010df7dcc38fdbd787ec051804ce7145b4645325ea9f67ca0548c` |
| EURUSD_M5.csv | 81,036 | 2025-08-25 00:00 to 2026-09-24 23:55 UTC | `c8dc043c301531b11452a95273bd2fceec8f7ca933d99c5d7338d3f4ab2bb2e9` |

Frozen EURUSD Sep 10 2026 UTC sample: 1,440 M1, 288 M5. Pre-sample prefixes: 389,447 M1 and 77,868 M5. Exporter metadata/hashes do not independently establish native tester history identity or MT5 server offset.

## Opaque original terminal cache

- `app/bases/MetaQuotes-Demo/history/EURUSD/cache/M1.hc`: 1,263,074 bytes, SHA-256 `ffa5b9ff285f176ac411d3fd97f70429b2ab001fb51b7cc87f43c2df0751afed`.
- `app/bases/MetaQuotes-Demo/history/EURUSD/cache/M5.hc`: 250,994 bytes, SHA-256 `5ee6fdd079e7458e24ca8531091900573cec865f269a6c7395e46090a1120250`.
- `app/bases/MetaQuotes-Demo/history/EURUSD/2026.hcc`: 1,313,328 bytes, SHA-256 `3f95e4e48cf4888a63535bb0531ad313f5e5fa4948b4312089b298998fa54331`.
- `app/bases/MetaQuotes-Demo/ticks/EURUSD/ticks.dat`: 37,692 bytes, SHA-256 `cc6ee0f1702233f8ae82048e472814b2ce26314e385aa0cd0b69741455cad19f`.

Presence, file size, hashes and timestamps are **not proof** of UTC clock mapping, required source-prefix coverage, native OHLC parity or raw tick completeness.

`app/Tester/` and `app/MQL5/Profiles/Tester/` exist but are empty. No existing M030 .set configuration.

## Open gates

1. Historical MetaQuotes-Demo server-to-UTC mapping is not independently established. Do not use Kenya's local time or guess zero/+2/+3; historical mapping may vary.
2. Native MT5 cache content, earliest available M1/M5 bars, and exact source identity are not proven without an independently validated safe decode/export mechanism.
3. The existing compiled EA requires both exact full native history prefixes and verified server offset and will fail closed without them.
4. Repository CSV data cannot be asserted as a native tester dataset. Any controlled custom-symbol import would constitute a separate explicit data-provisioning experiment, not independent native-tick parity.
5. Original terminal and account/config/history must stay untouched. Strategy Tester, simulated/live orders, broker access, data downloads, new installs and original-app modification are forbidden at this stage.

## Next narrow gate: Stage 1G provenance feasibility

Conduct **read-only** investigation of the original exporter source and manifests, existing MT5 timestamps in logs/config or offline metadata, and known safe decoder/exporter mechanisms. Determine whether the historical server offset can be established without a terminal/broker session. Evaluate whether native cached EURUSD bar prefixes are demonstrably available offline. Distinguish evidence from hypotheses and declare blockers if inconclusive.

Do not invent a timestamp, silently reduce EMA warm-up, change dataset, run tester, or connect broker to make the gate pass. If no non-invasive proof exists, propose a *separately authorized*, isolated **no-order bar/time discovery protocol** that does not treat unknown server time as verified, rather than issuing fictitious tester inputs. No execution is authorized by this document.
