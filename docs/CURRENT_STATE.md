# Current State

Last updated: 2026-09-25

## Latest accepted implementation milestone

**017 — Baseline diagnosis**

Accepted implementation SHA:

`e653ba87df2ff1e8afbad5704f9a8d81428d7b27`

Validation:

- full native suite: **173 passed, 2 skipped**
- full Wine suite: **173 passed, 2 skipped**
- Wine Python: **3.10.11 AMD64**
- Wine NumPy: **2.2.1**
- Wine MetaTrader5: **5.0.6180**
- Wine pytest: **9.1.1**
- M017 diagnostic pair: PASS
- repository checks: required at closeout

Diagnostic determinism:

- diagnostic A and B: byte-for-byte identical
- diagnostic SHA-256:
  `edf01f4a1f936d386e618faa65fb9a7afb65fff6ae7ae9b4373c35692ced987a`

Non-interference:

- accepted M016 report SHA-256 remained:
  `d73a86c8af9063a5831f38131bc9e9a7fdc956971cb0b65971cf1709b6509f6a`
- both M017 diagnostic replays regenerated exactly that baseline report
- accepted orders / closed trades: **1,393 / 1,393**
- remaining positions: **0**
- ending realized balance/equity: **USD 9,731.45700985454**
- net realized P/L: **USD -268.54299014546086**
- no new strategy-reporting artifacts

## Accepted baseline window

Historical window:

`2026-09-01T00:00:00Z` through `2026-09-25T00:00:00Z`

This covers Sep 1 through the end of Sep 24 UTC.

Symbols:

- EURUSD
- EURJPY
- GBPUSD
- GBPJPY
- USDJPY

Dataset:

- M1
- native M5
- native M15
- tick-derived Ask M1
- account currency USD
- verified manifest/integrity

Cost label:

`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO`

Actual commission, slippage, and swap remain unproven/unmodeled and must not be
invented.

## M017 accepted diagnosis

The accepted 24-day baseline result is not explained by one uniform low hit
rate.

### Symbol

- EURUSD: 271 trades, 123 wins / 148 losses, USD +14.79285714287349
- EURJPY: 283 trades, 126 wins / 157 losses, USD +9.06763705593736
- GBPUSD: 265 trades, 111 wins / 153 losses / 1 flat, USD +1.2928571428561284
- GBPJPY: 283 trades, 105 wins / 178 losses, USD -133.3473684763957
- USDJPY: 291 trades, 114 wins / 177 losses, USD -160.34897301071814

### Side

BUY and SELL non-flat win rates are almost identical:

- BUY: 41.72%, USD -330.9923055212326
- SELL: 41.48%, USD +62.44931537578547

Therefore the side difference is a payoff/path issue in this window, not merely
a hit-rate difference.

### UTC entry buckets

Materially negative buckets:

- 00:00–03:59 UTC: USD -169.2694062737969
- 12:00–15:59 UTC: USD -133.82873588314456

Positive bucket:

- 16:00–19:59 UTC: USD +73.59878495540866

Do not convert these observations directly into time filters: symbol mix,
spread, and volatility are confounded.

### Exit/protection

- stop-loss exits: 1,339
  - 528 profitable
  - 810 losing
  - 1 flat
- take-profit exits: 54
  - 51 profitable
  - 3 losing

All 1,393 trades received initial protection.

- trades with successful trailing: 619
- successful trailing modifications: 1,093
- modifications associated with eventual wins: 1,019
- modifications associated with eventual losses: 73
- modifications associated with flat: 1

The 3 negative-P/L take-profit exits are an M018 investigation target, not yet
a proven defect.

### Spread

Entry spread:

- wins: mean 3.538860103626943 points, median 2
- losses: mean 7.174661746617466 points, median 2

The difference is concentrated in the tails.

Observed entry-spread maxima:

- EURJPY 300 points
- GBPJPY 229
- USDJPY 113
- GBPUSD 56
- EURUSD 18

Extreme spread cases must be inspected before any spread filter is considered.

### Conversion

Realized exits used:

- JPY→USD through direct USDJPY: 857 trades, USD -284.6287044311765
- USD→USD, no conversion: 536 trades, USD +16.085714285729626

No realized exit required the M016 two-leg sparse-conversion fallback.
Therefore the realized negative JPY result is not attributable to that fallback
itself.

### Loss clustering

- distinct loss streaks: 287
- maximum consecutive losses: 17
- maximum streak:
  `2026-09-18T22:10:00Z` to `2026-09-21T04:14:00Z`
- streak P/L: USD -83.84457684161302

The interval spans a weekend boundary and is not continuous market exposure.

### Drawdowns

Deepest:

- peak: USD 10,015.653664513784 at `2026-09-01T03:24:00Z`
- trough: USD 9,615.497020905219 at `2026-09-04T16:43:00Z`
- drawdown: USD 400.156643608565 / 3.9953123082355586%
- recovered: `2026-09-10T19:35:00Z`

Later sustained episode:

- peak: USD 10,039.652256508334 at `2026-09-10T20:02:00Z`
- trough: USD 9,727.210391770168 at `2026-09-24T20:18:00Z`
- drawdown: USD 312.44186473816626 / 3.112078553673229%
- not recovered by end of data

See `docs/milestones/017-baseline-diagnosis.md` for the complete accepted
record.

## Durable handoff

A fresh ChatGPT or Codex session must start with:

1. `AGENTS.md`
2. `docs/CURRENT_STATE.md`
3. `docs/NEXT_TASK.md`
4. `docs/BACKTEST_SEMANTICS.md`
5. `docs/WORKFLOW.md`
6. `docs/MILESTONES.md`

## Local control

Permanent branches:

- `local-control`
- `local-control-results`

Installed workstation service:

`chatgpt-mamba2-local-agent.service`

Validated actions include repository checks, runtime discovery, native/Wine
tests, read-only baseline export, baseline cleanup, paired baseline execution,
and paired M017 diagnostic execution.

No arbitrary shell action is exposed.

## Current production/backtest settings

- Symbols: EURUSD, EURJPY, GBPUSD, GBPJPY, USDJPY
- Position size: 0.1
- Stochastic: 21 / 7 / 7
- Trend filter: off
- RSI filter: off
- Higher-TF filter: off
- EMA: 7
- ATR: period 14, M5
- ATR SL multiplier: 1.0
- ATR TP multiplier: 2.0
- Existing BUY stops only move upward.
- Existing SELL stops only move downward.
- End-of-data does not force-liquidate.
- Historical spread uses tick-derived Ask where available.

## Next milestone

**018 — Proven-defect review and corrections**

Start from the accepted M017 trade-level evidence.

Investigate documented anomalies first. Change replay/implementation behavior
only when a defect is proven. Do not optimize strategy parameters during M018.
