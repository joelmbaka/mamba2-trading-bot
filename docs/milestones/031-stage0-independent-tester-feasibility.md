# M031 Stage 0 — same-input independent tester feasibility audit accepted

Date: 2026-11-12
Status: **READ-ONLY AUDIT COMPLETE; FROZEN-DAY BASELINE, LEAN PROVISIONING AND NATIVE TESTER NOT YET AUTHORIZED**

## Repository and scope

Codex reported a clean, synchronized `scalping-recovery` at `72be46ed333753db51020e455f329145c0e804fd`, ahead/behind `0/0`. No tests, historical replay, Wine, MT5/Strategy Tester, broker, uploads/downloads, package installation or file modifications occurred.

## Immutable source evidence

Source directory: `backtest_data/m022-history-inventory-tick-m1-v2/`.

Manifest SHA-256: `cfaf3d130eb8fc2abf2e467e43cc5bba735df711ebb8bc9766e865713ba4065b`.

| Artifact | Total rows | First bar UTC | Last bar UTC | SHA-256 |
| --- | ---: | --- | --- | --- |
| `EURUSD_M1.csv` | 405,283 | 2025-08-25 00:03 | 2026-09-24 23:59 | `19a3a92141989e9d1ed174447e43ada627c13ed8b3cef39d800a07d587fdc2fe` |
| `EURUSD_M1_ask.csv` | 405,283 | 2025-08-25 00:03 | 2026-09-24 23:59 | `7cca2326ead010df7dcc38fdbd787ec051804ce7145b4645325ea9f67ca0548c` |
| `EURUSD_M5.csv` | 81,036 | 2025-08-25 00:00 | 2026-09-24 23:55 | `c8dc043c301531b11452a95273bd2fceec8f7ca933d99c5d7338d3f4ab2bb2e9` |

Frozen UTC period `[2026-09-10T00:00:00Z, 2026-09-11T00:00:00Z)`: 1,440 M1 bars and 288 M5 bars. Every M5 period has five complete M1 bars. **All 288 derived M1→M5 OHLC bars match canonical M5 OHLC**, but tick-volume and spread fields mismatch on **all 288**. This proves price OHLC aggregation for the sampled day only. It does *not* prove full-record equality, full earlier warm-up prefix equality, raw native tick provenance, executable Ask/spread identity or economic parity.

Different `native-m1-v3` M1 export hash with the same M5 export hash confirms the importance of pinning complete source provenance, not inferring it from filenames. Canonical `time` is integer Unix seconds with explicitly UTC interpretation; that interpretation does not independently verify original MT5 server clock.

## Platform assessment

- MT5 official custom-symbol feature supports imported historical M1 prices and ticks and Strategy Tester use: https://www.metatrader5.com/en/terminal/help/trading_advanced/custom_instruments and https://www.mql5.com/en/docs/customsymbols . This is documentation of platform capability, **not proof that the present account-free MT5/Wine sandbox can remain running**.
- Tester can synchronize missing history and generate ticks depending on mode; this complicates safe isolation and execution parity: https://www.mql5.com/en/docs/runtime/testing .
- QuantConnect LEAN custom data is supported via `PythonData`/`BaseData`, `Reader`/`GetSource` and `AddData`; market-hours and execution mechanics for custom securities must be explicit: https://www.quantconnect.com/docs/v2/writing-algorithms/importing-data/streaming-data/custom-securities/key-concepts .
- Local `lean` and `dotnet` are absent; Docker present but no LEAN images cached; no LEAN adapter in repository. Provisioning, Docker pulls, cloud account creation and uploads were **not authorized or executed**.

## Cross-engine parity gate

1. Pin hashes, source-path identity, source row counts, complete full-prefix warmup, bar-open timestamps, clock/UTC interpretation, Ask sidecar, and assumed execution costs before any run. On any mismatch, STOP.
2. Key every event by symbol, decision UTC boundary, completed M1 source UTC open and completed M5 UTC open. Do not align by row position.
3. Compare actual OHLC exact decimal values; M1/M5 stochastic K/D, EMA7, ATR14 with initial absolute tolerance `1e-9` subject to explicit float representation/rounding review, plus warmup availability. Differences must be investigated rather than dismissed.
4. Require exact BUY/SELL/NONE decisions and reason codes on every eligible boundary, including last-ten M1 stochastic extreme **without fresh crossover**, EMA/candle filter and M5 directional confirmation. An unexplained difference fails signal parity.
5. Compare order submission, fills, SLTP modification and exits using event order, source times, volume, side, prices and request/position correspondence. Runtime-generated numeric ticket IDs need not match.
6. Full economic P/L equality is **not** meaningful without matched tick/Ask, spread, slippage, commission, swap, conversion, margin and stop/TP intrabar path. `REJECT`/`ACCOUNT` are currently schema-only; suppressed candidate signals have no `SIGNAL` log while position or order blocks.
7. One bounded Python baseline on the frozen day can establish a canonical output once sealed, but cannot validate itself independently. Cross-engine 100% decision parity is a precondition to mass Python backtests and tuning. No optimization on the same evaluation holdout.

## Next bounded activity

**M031 Stage 1 — read-only input seal and executable comparison specification**, using existing immutable files. Verify the exact matching day M1/M5 OHLC and test whether all source warmup bars required for K/D, EMA and ATR also match or require explicit native M5 input rather than M1 aggregation. Check source hashes, Ask sidecar coverage, timestamps and requirements without running historical replay or changing data. Specify an independently authored LEAN adapter architecture that handles same input and market-hours/clock behavior; do not claim it is already executable. Return a complete single-day baseline command/output contract and an explicit list of permissions needed for a bounded Python baseline and an isolated LEAN Docker pull/run. Do not provision or run either yet.

The final comparison approval is **not** authorization to perform historical testing or MT5/LEAN execution; obtain separate task scope. Native MT5 historical UTC/source identity remains blocked by Stage 1O/1S.
