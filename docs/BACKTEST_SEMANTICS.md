# Accepted Backtest Semantics

Changes to this contract require an explicit milestone and tests.

## Bar timing

MT5 timestamps are bar-open timestamps.

For M1, source bar 10:00 becomes completed/visible at replay 10:01. A strategy decision at 10:01 may use the completed 10:00 candle and fill from the 10:01 execution open, but the 10:01 high/low/close remain unavailable until 10:02.

M5/M15 bars become visible only after their entire interval completes.

## Portfolio replay order

One shared feed/broker/account:

1. `broker.advance()` — expose boundary, completed-bar exits, mark positions, settle older pending orders.
2. `ATRManager.refresh_once()`.
3. Evaluate strategies in order:
   - EURUSD
   - EURJPY
   - GBPUSD
   - GBPJPY
   - USDJPY
4. After each strategy, settle a same-boundary submitted order when an execution bar exists.
5. `PositionManager.update_once()` once globally.

Open/pending state blocks only the same symbol.

## Spread

Historical MT5 OHLC is Bid-side.

- BUY entry: Ask
- SELL entry: Bid
- BUY mark/exit: Bid
- SELL mark/exit: Ask

Tick-derived Ask M1 is preferred; bar-spread Ask is fallback.

## Account currency

P/L is converted from quote currency using historical replay prices from available conversion pairs only. No current/web FX rates.

## Costs

Explicit model supports commission-per-lot-per-side and adverse slippage points. Defaults are zero because actual broker rules are not yet proven. Swap is not modeled.

## End of data

No implicit force liquidation. Report realized balance, unrealized P/L, equity, and remaining positions separately.

## Strategy defaults

- Stochastic: 21 / 7 / 7
- Trend: off
- RSI: off
- Higher-TF: off
- EMA: 7
- Position size: 0.1

## ATR/protection

- ATR: 14 on M5
- SL multiplier: 1.0
- TP multiplier: 2.0

Initial missing protection is installed when positive ATR is available.

Existing near-target protected positions are monotonic:
- BUY candidate SL must be strictly above current SL.
- SELL candidate SL must be strictly below current SL.
- Rejected SL changes do not move TP independently.

## Known limitations

- stop-first if both SL and TP are touched inside one OHLC candle;
- no leverage/margin model;
- no swap/overnight model;
- unknown actual commission/slippage;
- Ask sidecar summarizes ticks to M1 rather than retaining every tick timestamp.
