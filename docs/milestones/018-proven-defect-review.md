# Milestone 018 — Proven-Defect Review and Correction

Status: **ACCEPTED**

Date: 2026-09-25

Accepted implementation SHA:

`fb03bc197d60d5d7b5b218a86288811f72ec4f60`

Base M017 closeout SHA entering M018:

`8a8886acad74e9dcff0ee2d2d2ee596eee95f7f0`

## Objective

Use the accepted M017 trade-level evidence to prove or disprove implementation
defects before any strategy optimization.

M018 was not allowed to tune strategy parameters, add symbol/session/spread
filters, change position size, alter ATR multipliers, invent broker costs, or
perform real MT5 trading.

## Proven defect

M017 found three take-profit exits with negative realized P/L.

Trade reconstruction proved that all three were SELL positions entered during
large historical spreads:

- EURJPY ticket 379: fill 179.332, initial TP 179.50057142857145, entry spread
  211 points;
- USDJPY ticket 381: fill 154.317, initial TP 154.39457142857142, entry spread
  113 points;
- GBPJPY ticket 1312: fill 209.502, initial TP 209.62442857142858, entry spread
  229 points.

For each position, the initial SELL TP was above the actual fill. Reaching that
TP therefore produced a loss even though the exit reason was take-profit.

The cause was deterministic: initial ATR protection in
`PositionManager` used `price_current` for both SL and TP. For a SELL
position, `price_current` is the closing-side Ask. When spread exceeded the
2×ATR TP distance, the current-price-derived TP could cross above
`price_open`.

This was a position-management defect, not a legitimate strategy outcome.

## Narrow correction

The accepted correction deliberately preserves existing semantics whenever the
target remains valid:

- initial SL remains based on `price_current`;
- the ordinary initial TP remains based on `price_current`;
- for BUY only, if that TP would be at or below `price_open`, TP is instead
  anchored to `price_open + 2 × ATR`;
- for SELL only, if that TP would be at or above `price_open`, TP is instead
  anchored to `price_open - 2 × ATR`;
- existing trailing-stop behavior is unchanged;
- ATR period and multipliers are unchanged;
- production strategy configuration is unchanged.

The formal broker position shape already exposes `price_open`, including the
real MT5 adapter, historical broker, and test doubles.

Focused regression coverage proves that a wide-spread BUY or SELL initial TP
cannot be placed on the loss side of its fill while ordinary current-price TP
semantics remain unchanged.

## Changed application paths

Relative to the accepted M017 closeout:

- `mamba2/crew/position_manager.py`
- `tests/test_backtest_strategy_lifecycle.py`
- `tests/test_position_manager_trailing_semantics.py`

No strategy configuration file changed.

## Validation

At accepted implementation SHA
`fb03bc197d60d5d7b5b218a86288811f72ec4f60`:

- full native suite: **175 passed, 2 skipped**
- full Wine suite: **175 passed, 2 skipped**
- Wine Python: **3.10.11 AMD64**
- Wine NumPy: **2.2.1**
- Wine MetaTrader5: **5.0.6180**
- Wine pytest: **9.1.1**
- pre-accept repository checks: PASS

The exact accepted M016 dataset was then replayed twice through the corrected
diagnostic path.

Acceptance command:

`mamba2-m018-corrected-diagnostic-pair-20260925-1520`

## Corrected replay determinism

Corrected ordinary baseline A and B were byte-for-byte identical.

Corrected baseline SHA-256:

`e33a5400f70494356d12faebbb1e2588bd2075769da5539e9c6584dc88cedcca`

Corrected diagnostic A and B were byte-for-byte identical.

Corrected diagnostic SHA-256:

`1497db0918bac89c8d10224745db4a522492ac577e845bfc1731450c39e3dda7`

The accepted M016 baseline SHA-256 remained the comparison reference:

`d73a86c8af9063a5831f38131bc9e9a7fdc956971cb0b65971cf1709b6509f6a`

The corrected baseline is intentionally different because a proven execution
semantic defect was fixed.

## Semantic acceptance gates

The corrected deterministic replay produced:

- initial TP direction violations: **0**
- negative-P/L take-profit exits: **0**
- new strategy-reporting artifacts: **0**
- remaining open positions: **0**

Take-profit exits after correction:

- **52 total**
- **52 wins**
- **0 losses**
- net realized P/L: **USD 467.37687269437953**

All **1,389 / 1,389** closed trades received initial protection.

## Corrected aggregate result

Exact Sep 1–24 UTC corrected replay:

- accepted orders: **1,389**
- closed trades: **1,389**
- wins: **580**
- losses: **808**
- flats: **1**
- non-flat win rate: **41.78674351585015%**
- ending realized balance/equity: **USD 9,785.824347114009**
- net realized P/L: **USD -214.17565288599144**
- gross realized P/L: **USD -214.1756528859763**
- commission: **USD 0**
- largest closed gain: **USD 35.041524659453856**
- largest closed loss: **USD -26.566478053355354**
- maximum equity drawdown: **USD 400.156643608565 /
  3.9953123082355586%**

Compared with accepted M016:

- accepted/closed trades: **-4**
- wins: **+1**
- losses: **-5**
- ending equity/net P/L: **+USD 54.36733725946942**
- maximum drawdown: unchanged

The P/L improvement is an observed consequence of correcting the invalid
initial targets. It is **not** treated as evidence of strategy optimization or
future profitability.

Because position lifetime can change after correcting a target, downstream
entry availability can also change; therefore the aggregate difference is not
assumed to equal only the direct P/L of the three originally anomalous trades.

## Corrected per-symbol result

| Symbol | Trades | Wins | Losses | Flats | Net realized P/L (USD) |
|---|---:|---:|---:|---:|---:|
| EURUSD | 271 | 123 | 148 | 0 | 14.79285714287349 |
| EURJPY | 281 | 127 | 154 | 0 | 32.52718286401407 |
| GBPUSD | 265 | 111 | 153 | 1 | 1.2928571428561284 |
| GBPJPY | 281 | 105 | 176 | 0 | -106.16419797088078 |
| USDJPY | 291 | 114 | 177 | 0 | -156.62435206483926 |

The same short window remains materially negative overall and must not be used
as a broad profitability claim.

## Extreme-spread investigation

M018 inspected the largest M017 entry-spread tails against the exported
tick-derived Ask/Bid data and adjacent M1 minutes.

The large spreads are present in the accepted historical data rather than being
created by the replay:

- EURJPY 300 points around Sep 14 00:01 UTC, with adjacent broad widening;
- USDJPY 113 points at Sep 8 00:01 UTC;
- GBPJPY 229 points at Sep 24 00:28 UTC, with surrounding widened minutes;
- GBPUSD 56 points at Sep 3 00:36 UTC, also visible in adjacent minutes;
- EURUSD 18 points at Sep 3 00:01 UTC.

M018 therefore does **not** add a spread filter or rewrite the exported data.

## Payoff/session observations after correction

The corrected replay still shows a material side payoff difference:

- BUY: 673 trades, 282 wins / 391 losses, USD -307.2632966290044
- SELL: 716 trades, 298 wins / 417 losses / 1 flat,
  USD +93.08764374302802

The hit rates remain similar while payoff differs. No additional implementation
defect was proven from this asymmetry.

UTC buckets remain descriptive rather than causal:

- 00:00–03:59 UTC: USD -114.90206901432626
- 12:00–15:59 UTC: USD -133.82873588314456
- 16:00–19:59 UTC: USD +73.59878495540866

Spread, symbol mix, volatility, and market regime remain confounded. No session
filter is authorized by M018.

## Limitations intentionally unresolved

- this is still only Sep 1–24, 2026;
- actual historical commission is unknown and remains zero rather than invented;
- historical slippage is unknown and remains zero;
- swap remains unmodeled;
- margin/leverage remains unmodeled;
- OHLC stop-first ambiguity remains unchanged;
- observed symbol, side, spread, session, clustering, and drawdown effects are
  not yet validated across broader market regimes;
- no real MT5 order was placed, modified, or closed.

## Next authorized milestone

**019 — Broader-history validation**

Expand the now-corrected deterministic baseline across several months and
multiple market regimes before any strategy/filter optimization.

M019 must preserve the corrected execution semantics and strategy parameters.
It is a validation milestone, not a tuning milestone.
