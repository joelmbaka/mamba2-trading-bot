# Milestone 019 — Broader-History Validation

Status: **ACCEPTED**

Date started: 2026-09-25

Date accepted: 2026-09-25

Starting closeout SHA:

`94c031a852751973e3f7541cfbb7ebf636844223`

Accepted M019 implementation SHA:

`94a74211175d0f1db7e4c00cb3ab1f8ca1f286bb`

Accepted M018 implementation SHA:

`fb03bc197d60d5d7b5b218a86288811f72ec4f60`

## Objective

Validate the corrected deterministic replay across several months of real MT5
history before any strategy optimization, while preserving M018 execution
semantics and the unchanged production strategy configuration.

## Accepted historical window

UTC interval:

`2026-06-23T00:00:00Z` through `2026-09-25T00:00:00Z`

The original June 1 candidate was rejected because common retained M1 history
for all five symbols did not begin until around June 22. June 23 00:00 UTC is
the first clean full-day boundary after common M1 availability.

The window contains:

- June 23–30, 2026;
- July 2026;
- August 2026;
- Sep 1 through the end of Sep 24 UTC.

## Dataset acceptance

Immutable dataset:

`backtest_data/broader-history-20260623-20260925/manifest.json`

Manifest schema: **2**

Account currency: **USD**

| Symbol | M1 | Ask M1 | M5 | M15 |
|---|---:|---:|---:|---:|
| EURUSD | 97,914 | 97,914 | 19,584 | 6,528 |
| EURJPY | 97,914 | 97,914 | 19,584 | 6,528 |
| GBPUSD | 97,911 | 97,911 | 19,584 | 6,528 |
| GBPJPY | 97,911 | 97,911 | 19,584 | 6,528 |
| USDJPY | 97,910 | 97,910 | 19,584 | 6,528 |

Acceptance properties:

- Ask M1 aligns one-for-one with Bid-side M1 for every symbol;
- native M5 and M15 coverage is present;
- manifest/checksum loading passed;
- the Sep 1–24 overlap is identical to the accepted M016 dataset for M1, M5,
  M15, and tick-derived Ask M1.

The broader MT5 export required opt-in deterministic seven-day rate chunking
because large M1 range requests did not return the full retained history.
Default exporter behavior remains unchanged when chunking is not requested.

## Replay performance infrastructure

The first broader replay exposed repeated copying of increasingly large visible
historical DataFrames.

M019 added replay-only performance infrastructure:

- direct causal lookup for `ReplayFeed.current_bar`;
- replay-only causal visible-rate views;
- replay-only immutable source hooks for causal indicator caching;
- stochastic cache on replay source history;
- ATR cache on replay source history;
- replay-only moving-average and strategy reads;
- replay-only ATRManager reads.

Public `get_rates()` copy-returning behavior remains unchanged. Production/live
rate fetchers remain on their previous code path. No strategy parameter was
changed.

Parity tests verify cached/optimized reads against the ordinary causal visible
history.

## Final implementation validation

At accepted implementation SHA
`94a74211175d0f1db7e4c00cb3ab1f8ca1f286bb`:

- native: **179 passed, 2 skipped**
- Wine: **179 passed, 2 skipped**
- Wine Python: **3.10.11 AMD64**
- Wine NumPy: **2.2.1**
- Wine MetaTrader5: **5.0.6180**
- Wine pytest: **9.1.1**

## M018 semantic preservation gate

Command:

`mamba2-m019-m018-regression-current-head-20260925-2016`

The accepted Sep 1–24 dataset was replayed twice through the optimized M019
code.

Baseline:

- A/B byte-identical: **PASS**
- A SHA:
  `e33a5400f70494356d12faebbb1e2588bd2075769da5539e9c6584dc88cedcca`
- B SHA:
  `e33a5400f70494356d12faebbb1e2588bd2075769da5539e9c6584dc88cedcca`
- exact accepted M018 SHA preserved: **PASS**

Diagnostics:

- A/B byte-identical: **PASS**
- A SHA:
  `1497db0918bac89c8d10224745db4a522492ac577e845bfc1731450c39e3dda7`
- B SHA:
  `1497db0918bac89c8d10224745db4a522492ac577e845bfc1731450c39e3dda7`
- exact accepted M018 SHA preserved: **PASS**

This is the critical proof that replay optimization did not alter the accepted
M018 Sep behavior.

## Final broader replay acceptance

Command:

`mamba2-m019-final-broader-pair-20260925-2022`

Baseline:

- A/B byte-identical: **PASS**
- SHA-256:
  `114df816acf9900e9255a89c4ab203aab40ea56d898c19b25c7be29d6403d983`

Diagnostics:

- A/B byte-identical: **PASS**
- SHA-256:
  `84c474e3e10ebb36eb05b80bbef7726161858cd8fa18b986e2cf7515c121aba8`

Semantic gates:

- wrong-side initial TP violations: **0**
- negative-P/L take-profit exits: **0**
- new strategy-reporting artifacts: **0**
- remaining open positions: **0**

The final optimized broader hashes are also exactly equal to the earlier
pre-optimization broader pair hashes. This extends semantic-parity evidence
across the complete M019 window.

## Aggregate result

Cost label:

`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO`

Actual commission, slippage, and swap are not proven and are not modeled.

- accepted orders / closed trades: **4,922 / 4,922**
- wins / losses / flats: **1,899 / 3,020 / 3**
- non-flat win rate: **38.60540760317138%**
- starting balance: **USD 10,000**
- ending realized balance/equity: **USD 8,283.392367997667**
- net realized P/L: **USD -1,716.607632002333**
- largest closed gain: **USD 61.37692445619354**
- largest closed loss: **USD -26.566478053355354**
- maximum equity drawdown:
  **USD 1,929.6969567926317 / 19.214803229083717%**

## Per-symbol result

| Symbol | Trades | Wins | Losses | Non-flat win rate | Net P/L |
|---|---:|---:|---:|---:|---:|
| EURJPY | 954 | 388 | 565 | 40.7135% | USD +113.69332714418455 |
| EURUSD | 994 | 400 | 593 | 40.2820% | USD -301.59285714284704 |
| GBPJPY | 1,001 | 327 | 674 | 32.6673% | USD -930.0206586449655 |
| GBPUSD | 947 | 382 | 564 | 40.3805% | USD -423.3857142857603 |
| USDJPY | 1,026 | 402 | 624 | 39.1813% | USD -175.301729072955 |

GBPJPY contributed the largest symbol loss, but the remaining four symbols
still sum to approximately **USD -786.5869733573676**. The negative aggregate
is therefore not solely a one-symbol effect.

## Calendar subperiods

Grouped by entry month:

| Entry period | Trades | Wins | Losses | Flats | Net P/L | Mean spread | Median | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Jun 23–30 | 401 | 150 | 251 | 0 | USD -170.12248532167797 | 6.7207 | 2 | 203 |
| July | 1,604 | 614 | 990 | 0 | USD -637.4843772180006 | 6.7350 | 2 | 225 |
| August | 1,523 | 554 | 967 | 2 | USD -674.9506208103498 | 4.8877 | 2 | 182 |
| Sep 1–24 | 1,394 | 581 | 812 | 1 | USD -234.0501486523148 | 5.5330 | 2 | 300 |

All four calendar entry subperiods were negative.

The Sep entry-period result is not expected to equal the isolated M018 Sep
replay because the broader replay enters September with account/position state
formed during June–August. Exact isolated-Sep semantic parity is established
separately by the M018 regression gate above.

## BUY versus SELL

| Side | Trades | Wins | Losses | Flats | Net P/L | Mean entry spread |
|---|---:|---:|---:|---:|---:|---:|
| BUY | 2,213 | 885 | 1,327 | 1 | USD -762.8500941221877 | 5.2174 |
| SELL | 2,709 | 1,014 | 1,693 | 2 | USD -953.7575378801578 | 6.3156 |

The Sep-only M018 observation was BUY negative / SELL positive. The broader
sample has both sides negative. Therefore side asymmetry is not stable enough
to justify disabling one side.

## UTC entry buckets

| UTC bucket | Trades | Wins | Losses | Flats | Net P/L | Mean spread | Median | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 00:00–03:59 | 842 | 260 | 582 | 0 | USD -839.9216322911675 | 19.8990 | 4 | 300 |
| 04:00–07:59 | 805 | 313 | 491 | 1 | USD -337.05684303269584 | 2.9975 | 2 | 15 |
| 08:00–11:59 | 899 | 371 | 527 | 1 | USD -14.593607221385962 | 2.6719 | 1 | 17 |
| 12:00–15:59 | 804 | 328 | 475 | 1 | USD -169.74405332670088 | 2.7637 | 2 | 30 |
| 16:00–19:59 | 799 | 346 | 453 | 0 | USD -35.04135197819057 | 2.5845 | 2 | 14 |
| 20:00–23:59 | 773 | 281 | 492 | 0 | USD -320.25014415220096 | 3.6197 | 2 | 70 |

The 00:00–03:59 UTC bucket is the strongest persistent descriptive weakness.
It was negative in M018 and is strongly negative here, while also carrying a
much wider spread distribution. The data does not by itself establish whether
session timing, spread tails, symbol mix, or another regime feature is causal.

## Spread evidence

By eventual outcome:

- losses: 3,020 entries, mean **7.070529801324503**, median **2**, max **300**
- wins: 1,899 entries, mean **3.843601895734597**, median **2**, max **211**
- flats: 3 entries, mean/median/max **1**

The shared median but materially different mean/max indicates tail exposure
rather than a simple uniform spread shift. This is descriptive evidence only;
M019 does not add a spread filter.

## Exit and protection behavior

Stop-loss exits:

- **4,715** trades
- wins / losses / flats: **1,692 / 3,020 / 3**
- net P/L: **USD -3,530.797379799249**

Take-profit exits:

- **207** trades
- wins / losses: **207 / 0**
- net P/L: **USD +1,814.1897477968992**

Protection:

- trades with initial protection: **4,922**
- trades with trailing: **2,090**
- total trailing modifications: **3,531**
- trailing modifications on eventual wins: **3,209**
- trailing modifications on eventual losses: **319**
- trailing modifications on flats: **3**

The M018 wrong-side target correction remains clean on the broader sample.

## Conversion routes

- `JPY->USD:USDJPY:direct`: **2,980 trades**, net
  **USD -991.6290605737348**
- `USD->USD:none`: **1,941 trades**, net
  **USD -724.9785714286061**
- `JPY->USD:none`: **1 flat trade**, zero P/L

No unexpected multi-leg conversion route appeared.

## Loss clustering and drawdown

- loss streak count: **994**
- maximum consecutive losses: **22**
- maximum streak:
  `2026-08-11T00:01:00Z` to `2026-08-11T05:01:00Z`
- maximum-streak P/L: **USD -62.40904494615151**
- drawdown episodes: **17**

Deepest drawdown:

- peak equity: **USD 10,042.761998581507**
- peak: `2026-06-23T16:49:00Z`
- trough equity: **USD 8,113.0650417888755**
- trough: `2026-09-04T16:43:00Z`
- drawdown: **USD 1,929.6969567926317 / 19.214803229083717%**
- recovered by dataset end: **no**

## FACTS established by M019

1. The broader strategy result is negative and the drawdown is materially
   larger than in the isolated Sep baseline.
2. The loss is present in every calendar entry subperiod.
3. Four of five symbols are negative; GBPJPY is the largest contributor but is
   not the sole source of aggregate loss.
4. Both BUY and SELL are negative over the broader sample. Sep-only SELL
   profitability is not stable.
5. 00:00–03:59 UTC remains negative and has unusually wide spread exposure.
6. Losses have wider mean/tail entry spreads than wins, while both have median
   spread 2 points.
7. The M018 initial-TP semantic correction remains clean over the broader
   sample.
8. Replay optimization preserves accepted results exactly on both the M018
   window and the full M019 window.

## HYPOTHESES for controlled experiments

M019 does not convert observations directly into strategy changes.

The first justified M020 hypothesis is:

> Blocking new entries during 00:00–03:59 UTC may improve the strategy's
> risk/return behavior without altering position management or other signal
> logic.

This must be tested as one treatment only. A spread filter is a separate
hypothesis and must not be stacked into the same experiment.

Symbol exclusion, side exclusion, ATR/trailing changes, stochastic tuning, and
position-size changes are not authorized by M019.

## Limitations intentionally preserved

- actual commission is unproven;
- actual slippage is unproven;
- swap is unmodeled;
- the broader window begins at retained common M1 availability, not an arbitrary
  earlier date;
- M019 is historical replay evidence, not forward/live validation;
- same-dataset temporal slices are stability checks, not pristine unseen
  holdouts.

No real MT5 order was placed, modified, or closed during M019.
