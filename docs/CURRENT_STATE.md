# Current State

Last updated: 2026-09-25

## Latest accepted implementation milestone

**018 — Proven-defect review and correction**

Accepted implementation SHA:

`fb03bc197d60d5d7b5b218a86288811f72ec4f60`

Base M017 closeout SHA:

`8a8886acad74e9dcff0ee2d2d2ee596eee95f7f0`

## M018 validation

Implementation validation:

- full native suite: **175 passed, 2 skipped**
- full Wine suite: **175 passed, 2 skipped**
- Wine Python: **3.10.11 AMD64**
- Wine NumPy: **2.2.1**
- Wine MetaTrader5: **5.0.6180**
- Wine pytest: **9.1.1**
- pre-accept repository checks: PASS

Corrected real-data acceptance command:

`mamba2-m018-corrected-diagnostic-pair-20260925-1520`

Corrected baseline A/B:

- byte-for-byte identical
- SHA-256:
  `e33a5400f70494356d12faebbb1e2588bd2075769da5539e9c6584dc88cedcca`

Corrected diagnostic A/B:

- byte-for-byte identical
- SHA-256:
  `1497db0918bac89c8d10224745db4a522492ac577e845bfc1731450c39e3dda7`

Semantic gates:

- wrong-side initial TP violations: **0**
- negative-P/L take-profit exits: **0**
- remaining open positions: **0**
- new strategy-reporting artifacts: **0**

## Proven defect and accepted semantic correction

M017 exposed three negative-P/L take-profit exits. M018 reconstructed all three
and proved that large spreads could cause an initial ATR take-profit target to
land on the loss side of the actual fill.

The defect came from deriving initial TP only from `price_current`.

Accepted correction:

- initial SL remains current-price-based;
- ordinary initial TP remains current-price-based;
- BUY TP is re-anchored to `price_open + 2 × ATR` only if the ordinary TP
  would be at or below the BUY fill;
- SELL TP is re-anchored to `price_open - 2 × ATR` only if the ordinary TP
  would be at or above the SELL fill;
- trailing semantics are unchanged;
- ATR settings are unchanged;
- strategy parameters are unchanged.

This correction applies to the shared production/historical position-management
path, but M018 performed no real MT5 order action.

See `docs/milestones/018-proven-defect-review.md` for the complete record.

## Corrected accepted baseline window

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

Corrected aggregate:

- accepted orders / closed trades: **1,389 / 1,389**
- wins / losses / flats: **580 / 808 / 1**
- non-flat win rate: **41.78674351585015%**
- ending realized balance/equity: **USD 9,785.824347114009**
- net realized P/L: **USD -214.17565288599144**
- maximum equity drawdown:
  **USD 400.156643608565 / 3.9953123082355586%**

Accepted M016 comparison reference:

- report SHA-256:
  `d73a86c8af9063a5831f38131bc9e9a7fdc956971cb0b65971cf1709b6509f6a`
- net realized P/L: **USD -268.54299014546086**

M018 changed net P/L by **+USD 54.36733725946942** as an observed consequence
of correcting invalid initial targets. This is not treated as strategy
optimization or evidence of future profitability.

## Remaining descriptive evidence

Extreme historical spread tails were verified against the exported Bid/Ask
data and adjacent minutes. M018 found no evidence that replay invented them, so
no spread filter was added.

After correction, side payoff asymmetry remains:

- BUY: 673 trades, USD -307.2632966290044
- SELL: 716 trades, USD +93.08764374302802

UTC performance also remains uneven, including negative 00:00–03:59 and
12:00–15:59 buckets.

These remain hypotheses for broader-history validation and later controlled
experiments. They are not additional proven implementation defects.

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

Allowed workflows include repository checks, native/Wine validation, read-only
historical export, paired baseline execution, paired diagnostic execution, and
the fixed M018 corrected diagnostic acceptance pair.

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

**019 — Broader-history validation**

Expand the corrected deterministic replay to several months and multiple market
regimes before any strategy/filter optimization.

M019 must preserve M018 execution semantics and current strategy parameters.
