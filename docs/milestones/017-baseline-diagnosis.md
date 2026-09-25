# Milestone 017 — Baseline Diagnosis

Status: **ACCEPTED**

Date: 2026-09-25

Accepted implementation SHA:

`e653ba87df2ff1e8afbad5704f9a8d81428d7b27`

Base M016 closeout SHA entering M017:

`0f22c342ae0ae6beae34fb11462fbf55eddded40`

## Objective

Explain the accepted M016 result with deterministic trade-level evidence before
changing strategy behavior.

M017 does not optimize or change:

- strategy thresholds;
- stochastic parameters;
- filter enablement;
- position size;
- ATR settings;
- trailing semantics;
- Bid/Ask spread semantics;
- account-currency conversion semantics;
- explicit commission/slippage assumptions;
- end-of-data behavior.

## Diagnostic implementation

M017 adds a separate observational replay path:

- `mamba2/backtest/diagnostics.py`
- `tests/test_backtest_diagnostics.py`

`DiagnosticHistoricalBroker` inherits the accepted `HistoricalBroker`
execution behavior and records append-only evidence around successful fills,
protection changes, exits, spreads, and conversion routes.

The ordinary M016 baseline report is rebuilt from the diagnostic replay and is
required to remain byte-for-byte identical to the accepted M016 report before
diagnostic evidence is trusted.

## Evidence captured per closed trade

Where applicable, the deterministic diagnostic artifact records:

- order ID;
- position ticket;
- symbol;
- BUY/SELL side;
- volume;
- entry UTC timestamp and price;
- exit UTC timestamp and price;
- exit reason;
- gross realized P/L;
- commission;
- net realized P/L;
- entry historical Bid/Ask spread;
- exit historical Bid/Ask spread;
- initial ATR protection state;
- successful trailing-stop modifications;
- final SL/TP;
- account-currency conversion route and historical prices;
- UTC entry hour and four-hour session bucket.

## Validation

At implementation SHA
`e653ba87df2ff1e8afbad5704f9a8d81428d7b27`:

- full native: **173 passed, 2 skipped**
- full Wine: **173 passed, 2 skipped**
- Wine Python: **3.10.11 AMD64**
- Wine NumPy: **2.2.1**
- Wine MetaTrader5: **5.0.6180**
- Wine pytest: **9.1.1**

The real diagnostic acceptance action then ran the complete M016 replay twice.

## Non-interference gate

Accepted M016 baseline SHA-256:

`d73a86c8af9063a5831f38131bc9e9a7fdc956971cb0b65971cf1709b6509f6a`

Both diagnostic replays regenerated the ordinary baseline report with exactly
that SHA-256.

Reconciliation remained exactly:

- accepted orders: **1,393**
- closed trades: **1,393**
- diagnostic trade rows: **1,393**
- remaining positions: **0**
- ending realized balance: **USD 9,731.45700985454**
- ending equity: **USD 9,731.45700985454**
- net realized P/L: **USD -268.54299014546086**

No new strategy-reporting artifacts were created.

## Diagnostic determinism

Diagnostic A and Diagnostic B were byte-for-byte identical.

SHA-256:

`edf01f4a1f936d386e618faa65fb9a7afb65fff6ae7ae9b4373c35692ced987a`

## Findings

These are descriptive findings from the accepted Sep 1–24 window. They are not
strategy recommendations and do not establish broader-regime robustness.

### Symbol evidence

| Symbol | Trades | Wins | Losses | Flats | Non-flat win rate | Net realized P/L (USD) |
|---|---:|---:|---:|---:|---:|---:|
| EURUSD | 271 | 123 | 148 | 0 | 45.39% | 14.79285714287349 |
| EURJPY | 283 | 126 | 157 | 0 | 44.52% | 9.06763705593736 |
| GBPUSD | 265 | 111 | 153 | 1 | 42.05% | 1.2928571428561284 |
| GBPJPY | 283 | 105 | 178 | 0 | 37.10% | -133.3473684763957 |
| USDJPY | 291 | 114 | 177 | 0 | 39.18% | -160.34897301071814 |

The total loss is concentrated in the negative P/L from GBPJPY and USDJPY in
this window. EURUSD, EURJPY, and GBPUSD are slightly positive or approximately
flat over the same period.

This is descriptive only; M017 does not disable or rank symbols.

### BUY versus SELL

| Side | Trades | Wins | Losses | Flats | Non-flat win rate | Net realized P/L (USD) |
|---|---:|---:|---:|---:|---:|---:|
| BUY | 676 | 282 | 394 | 0 | 41.72% | -330.9923055212326 |
| SELL | 717 | 297 | 419 | 1 | 41.48% | 62.44931537578547 |

The hit rates are almost the same, but realized P/L is materially different.
Therefore the BUY/SELL difference in this window is not explained merely by a
different win frequency; payoff size/path must be investigated before any
strategy conclusion is made.

### UTC entry-time buckets

| Entry UTC | Trades | Wins | Losses | Flats | Net realized P/L (USD) | Mean entry spread (points) |
|---|---:|---:|---:|---:|---:|---:|
| 00:00–03:59 | 227 | 76 | 151 | 0 | -169.2694062737969 | 19.140969162995596 |
| 04:00–07:59 | 235 | 98 | 136 | 1 | -23.0714937373522 | 3.0170212765957447 |
| 08:00–11:59 | 259 | 119 | 140 | 0 | 8.248817033652632 | 2.7258687258687258 |
| 12:00–15:59 | 250 | 98 | 152 | 0 | -133.82873588314456 | 2.716 |
| 16:00–19:59 | 217 | 108 | 109 | 0 | 73.59878495540866 | 2.8202764976958523 |
| 20:00–23:59 | 205 | 80 | 125 | 0 | -24.22095624021479 | 4.058536585365854 |

The 00:00–03:59 UTC bucket combines the weakest hit rate with the largest spread
tail. The 12:00–15:59 UTC bucket is also materially negative despite ordinary
median spread levels. Session, symbol mix, volatility, and spread therefore
remain confounded and must not be converted directly into a session filter.

### Exit reasons

- stop-loss exits: **1,339**
  - wins: 528
  - losses: 810
  - flats: 1
  - net realized P/L: **USD -711.7839706704057**
- take-profit exits: **54**
  - wins: 51
  - losses: 3
  - flats: 0
  - net realized P/L: **USD 443.2409805249587**

A stop-loss exit is not synonymous with a losing trade because monotonic
trailing can move SL into profit. There were 528 profitable stop-loss exits.

The three negative-P/L take-profit exits are an evidence-backed anomaly for
M018 investigation. M017 does not assume they are a defect; price path,
spread, trailing TP movement, and conversion must be checked trade-by-trade.

### Spread evidence

Entry spread by final outcome:

- winning trades: mean **3.538860103626943 points**, median **2**
- losing trades: mean **7.174661746617466 points**, median **2**
- flat trade: **1 point**

The equal median but materially larger loss-side mean indicates that the
difference is concentrated in spread tails rather than a uniformly higher
spread on all losing trades.

Observed extreme entry-spread maxima include:

- EURJPY: 300 points
- GBPJPY: 229 points
- USDJPY: 113 points
- GBPUSD: 56 points
- EURUSD: 18 points

Those tails are evidence to inspect in M018. M017 does not yet establish
whether they are valid historical market conditions, exporter/data artifacts,
or simply expensive but correctly modeled fills.

### ATR/protection/trailing evidence

- trades receiving initial protection: **1,393 / 1,393**
- trades with at least one successful trailing modification: **619**
- total successful trailing modifications: **1,093**
- trailing modifications associated with eventual wins: **1,019**
- trailing modifications associated with eventual losses: **73**
- trailing modifications associated with the flat trade: **1**

By exit reason:

- stop-loss trades with trailing: **601**
- take-profit trades with trailing: **18**

The majority of trailing activity ultimately exits through the stop path,
which is consistent with the presence of many profitable stop-loss exits.
M017 finds no evidence that initial protection was missing.

### Account-currency conversion evidence

Realized exits used:

- `JPY->USD:USDJPY:direct`: **857 trades**, net
  **USD -284.6287044311765**
- `USD->USD:none`: **536 trades**, net
  **USD 16.085714285729626**

No realized exit in this accepted replay required the sparse two-leg conversion
fallback. Therefore the realized negative result on JPY-quoted trades cannot be
attributed to the M016 two-leg fallback itself.

This grouping is confounded with symbol set and must not be interpreted as
evidence that currency conversion causes losses.

### Loss clustering

- distinct loss streaks: **287**
- maximum consecutive losses: **17**
- maximum streak window:
  `2026-09-18T22:10:00Z` through `2026-09-21T04:14:00Z`
- maximum-streak net realized P/L:
  **USD -83.84457684161302**

Longer streaks also occurred, including lengths 10, 11, 14, and 15. Losses are
therefore temporally clustered rather than independently distributed through
the window.

The maximum streak spans a weekend boundary, so its wall-clock duration must
not be interpreted as continuous market exposure.

### Drawdown structure

Eight equity drawdown episodes were identified.

The deepest episode:

- peak equity: **USD 10,015.653664513784**
- peak: `2026-09-01T03:24:00Z`
- trough equity: **USD 9,615.497020905219**
- trough: `2026-09-04T16:43:00Z`
- maximum drawdown: **USD 400.156643608565 / 3.9953123082355586%**
- recovered: **yes**
- recovery: `2026-09-10T19:35:00Z`

A later episode:

- peak equity: **USD 10,039.652256508334**
- peak: `2026-09-10T20:02:00Z`
- trough equity: **USD 9,727.210391770168**
- trough: `2026-09-24T20:18:00Z`
- maximum drawdown: **USD 312.44186473816626 / 3.112078553673229%**
- recovered by end of data: **no**

The accepted window therefore contains a deep early drawdown that fully
recovered, followed by a second sustained drawdown that remained open at the
end of the period.

## Evidence-backed M018 investigation targets

M017 authorizes investigation, not immediate parameter changes, for:

1. the three take-profit exits with negative realized P/L;
2. extreme spread-tail entries, especially the 300/229/113-point JPY cases;
3. the BUY-versus-SELL payoff asymmetry despite almost identical hit rates;
4. concentration of losses in 00:00–03:59 and 12:00–15:59 UTC after controlling
   for symbol mix, spread, and volatility;
5. long loss streaks and the two major drawdown regimes;
6. whether any protection/trailing event ordering is causally associated with
   the anomalies above.

A correction is allowed in M018 only if deterministic trade-level evidence
proves an implementation/replay defect. Otherwise the observation remains a
strategy hypothesis for later controlled experiments.

## Limitations

- this remains one Sep 1–24, 2026 historical window;
- actual broker commission remains unknown and is not invented;
- actual historical slippage remains unknown and is configured as zero;
- swap remains unmodeled;
- margin/leverage remains unmodeled;
- OHLC stop-first ambiguity remains unchanged;
- spread/session/symbol effects are correlated and not causal estimates;
- M017 does not optimize or claim production profitability.

## Next authorized milestone

**018 — Proven-defect review and corrections**

Start from the accepted M017 evidence. Prove or disprove the documented
anomalies first. Change replay/implementation behavior only when a defect is
demonstrated, then rerun the exact M016 dataset and compare against the accepted
baseline.

Do not begin controlled strategy optimization during M018.
