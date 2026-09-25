# Milestone 016 — First Real Five-Symbol Baseline

Status: **ACCEPTED**

Date: 2026-09-25

Accepted implementation SHA:

`4d8a15937f461c0e39d434be6639bfde83698d7f`

Base docs-closeout SHA entering M016:

`af1abb120848ab1c5accb528bf67551f6a882ef5`

## Objective

Measure the current production strategy exactly as it exists before any optimization.

No strategy threshold, filter, position-size, ATR, trailing, spread, explicit-cost, or end-of-data setting was optimized for this result.

## Historical window

`2026-09-01T00:00:00Z` through `2026-09-25T00:00:00Z`.

This covers September 1 through the end of September 24 UTC.

## Symbols

Configured strategy order:

1. EURUSD
2. EURJPY
3. GBPUSD
4. GBPJPY
5. USDJPY

## Verified dataset

Account currency: USD.

| Symbol | M1 rows | Tick-derived Ask M1 | Native M5 | Native M15 |
|---|---:|---:|---:|---:|
| EURUSD | 25,916 | 25,916 | 5,184 | 1,728 |
| EURJPY | 25,916 | 25,916 | 5,184 | 1,728 |
| GBPUSD | 25,915 | 25,915 | 5,184 | 1,728 |
| GBPJPY | 25,914 | 25,914 | 5,184 | 1,728 |
| USDJPY | 25,913 | 25,913 | 5,184 | 1,728 |

The manifest loaded successfully through the native integrity verifier. The dataset was cleanly re-exported after a sparse-conversion diagnostic and reproduced the same row counts.

Historical MT5 access remained read-only.

## Strategy/configuration

Unchanged baseline configuration:

- position size: 0.1
- stochastic K/D/slowing: 21 / 7 / 7
- trend filter: off
- RSI filter: off
- higher-timeframe filter: off
- stochastic entry/trading/higher timeframes: M1 / M5 / M15
- EMA: 7
- ATR period/timeframe: 14 / M5
- ATR SL multiplier: 1.0
- ATR TP multiplier: 2.0
- monotonic trailing-stop semantics
- no forced liquidation at end of data

Costs:

- historical tick-derived Bid/Ask spread included;
- explicit commission: 0;
- configured slippage: 0;
- swap: not modeled.

Required report label:

`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO`

The result is not described as fully net of actual broker costs.

## Real-data defects discovered before acceptance

### 1. Replay scalability

The first long attempt demonstrated that repeatedly recalculating full visible stochastic and ATR history at every replay boundary made the 24-day five-symbol baseline impractically slow.

Accepted correction:

- ReplayFeed visible-history lookup uses prefix-efficient index search;
- ReplayFeed exposes immutable static source history only through a replay-specific indicator hook;
- stochastic and ATR may precompute their existing arithmetic once against immutable replay source history;
- every returned value is sliced back to the currently visible causal prefix;
- production/live rate fetchers do not use this caching path.

Regression coverage proves exact cached-vs-legacy output parity.

### 2. Sparse same-boundary FX conversion

The first optimized real run reached `2026-09-14T00:01:00Z` and failed because a JPY-denominated position required USD conversion while USDJPY had no execution bar at that exact minute.

Coverage diagnosis showed USDJPY absent where:

- EURJPY had `2026-09-14 00:00Z`;
- EURJPY had `2026-09-14 00:01Z`;
- EURJPY and GBPJPY had `2026-09-14 00:07Z`.

A clean re-export reproduced the dataset row counts, so the gap was not treated as a transient first-load artifact.

The accepted correction preserves same-boundary historical conversion:

1. prefer a direct/inverse same-boundary conversion pair;
2. if that pair has no bar on the required replay phase, permit a deterministic two-leg route only when both legs have historical Bid/Ask data on that same boundary;
3. apply Bid/Ask independently on each leg;
4. never use a prior bar, future bar, current/web rate, or invented price.

Tests prove execution-time fallback, completed-bar fallback, direct-route preference, and the existing no-future-price rule.

## Changed implementation paths

Net changes from the M016 starting SHA:

- `mamba2/backtest/broker.py`
- `mamba2/backtest/feed.py`
- `mamba2/indicators/atr.py`
- `mamba2/indicators/stochastic.py`
- `tests/test_backtest_account_currency.py`
- `tests/test_replay_indicator_cache.py`

A temporary local-dataset diagnostic test was added and then removed during investigation; it is not present in the accepted tree.

## Validation

At implementation SHA `4d8a15937f461c0e39d434be6639bfde83698d7f`:

- full native: **169 passed, 2 skipped**
- full Wine: **169 passed, 2 skipped**
- Wine Python: **3.10.11 AMD64**
- Wine NumPy: **2.2.1**
- Wine MetaTrader5: **5.0.6180**
- Wine pytest: **9.1.1**
- repository checks: PASS
- worktree: clean
- divergence: 0/0
- `bot_cache.json`: untracked
- `icon.png`: tracked and unchanged

## Determinism acceptance

Command:

`first_baseline_run_pair`

Report A:

`backtest_data/first-baseline-20260901-20260925/report-a.json`

Report B:

`backtest_data/first-baseline-20260901-20260925/report-b.json`

Result:

- byte-for-byte identical: **PASS**
- report A SHA-256: `d73a86c8af9063a5831f38131bc9e9a7fdc956971cb0b65971cf1709b6509f6a`
- report B SHA-256: `d73a86c8af9063a5831f38131bc9e9a7fdc956971cb0b65971cf1709b6509f6a`
- new strategy artifacts created: none

## Accepted aggregate result

- replay boundaries: **25,916**
- accepted orders: **1,393**
- closed trades: **1,393**
- remaining positions: **0**
- starting balance: **USD 10,000.00**
- ending realized balance: **USD 9,731.45700985454**
- ending unrealized P/L: **USD 0.00**
- ending equity: **USD 9,731.45700985454**
- gross realized P/L: **USD -268.54299014544677**
- commission: **USD 0.00**
- net realized P/L: **USD -268.54299014546086**
- wins: **579**
- losses: **813**
- flats: **1**
- non-flat win rate: **41.5948275862069%**
- largest closed gain: **USD 35.041524659453856**
- largest closed loss: **USD -26.566478053355354**
- maximum shared-account equity drawdown: **USD 400.156643608565**
- maximum shared-account equity drawdown: **3.9953123082355586%**

The minute floating-point difference between summed gross realized P/L and balance-derived net realized P/L is approximately (1.4 	imes 10^{-11}) USD; explicit commission is zero.

## Per-symbol result

No ranking is implied.

| Symbol | Orders | Closed trades | Wins | Losses | Flats | Net realized P/L (USD) |
|---|---:|---:|---:|---:|---:|---:|
| EURUSD | 271 | 271 | 123 | 148 | 0 | 14.79285714287349 |
| EURJPY | 283 | 283 | 126 | 157 | 0 | 9.06763705593736 |
| GBPUSD | 265 | 265 | 111 | 153 | 1 | 1.2928571428561284 |
| GBPJPY | 283 | 283 | 105 | 178 | 0 | -133.3473684763957 |
| USDJPY | 291 | 291 | 114 | 177 | 0 | -160.34897301071814 |

## Limitations intentionally unresolved

- actual broker commission is unknown and therefore not invented;
- actual historical execution slippage is unknown and therefore configured as zero;
- swap/overnight financing is not modeled;
- no leverage/margin model;
- OHLC ambiguity remains stop-first when both SL and TP are touched inside one bar;
- tick-derived Ask is summarized to M1, not retained as every tick timestamp;
- this is one 24-day historical window and is not evidence of broader-regime robustness.

## Next authorized milestone

**017 — Baseline diagnosis**

Use the exact accepted baseline as evidence. Add deterministic trade-level diagnostics and analyze symbol, side, time/session, spread, ATR/trailing, conversion route, loss clustering, and drawdown episodes.

Do not optimize during M017.
