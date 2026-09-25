# Next Authorized Task

## Milestone 016 — First real five-symbol baseline

Repository operations/local-control are accepted.

Before executing the baseline:

1. fast-forward `main` to the accepted repository-operations closeout;
2. fast-forward existing `backtest-first-baseline` from main;
3. verify clean worktree/divergence 0/0;
4. do not change strategy or replay semantics.

## Historical window

Run the current production strategy unchanged:

- From: `2026-09-01T00:00:00Z`
- To: `2026-09-25T00:00:00Z`

This covers Sep 1 through the end of Sep 24 UTC and avoids partial Sep 25 data.

## Symbols

- EURUSD
- EURJPY
- GBPUSD
- GBPJPY
- USDJPY

## Dataset

Require:

- M1
- native M5
- native M15
- tick-derived Ask M1
- verified manifest/checksums

Historical MT5 access is read-only.

## Shared runtime

Exactly one:

- ReplayFeed
- HistoricalBroker/shared account
- ATRManager
- PositionManager
- PortfolioBacktestRunner

Five production `StochasticTripleTFStrategy` instances in configured symbol order.

## Strategy configuration

Do not optimize.

Keep:

- position size: 0.1
- stochastic: 21 / 7 / 7
- trend filter: off
- RSI filter: off
- higher-TF filter: off
- EMA: 7
- ATR: period 14, M5
- ATR SL multiplier: 1.0
- ATR TP multiplier: 2.0
- monotonic trailing-stop semantics

## Costs

Use historical tick-derived Bid/Ask spread.

Explicit assumptions:

- commission = 0
- configured slippage = 0

Report label:

`SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO`

Do not describe results as fully net of actual broker costs.

## End of data

No forced liquidation.

Report realized balance, unrealized P/L, equity, and remaining positions separately.

## Determinism gate

Run the exact baseline twice.

Require report A and report B to be byte-for-byte identical with the same SHA-256.

If determinism fails, stop and fix the replay/reporting defect before interpreting performance.

## Output required

Report:

- replay boundaries;
- accepted orders total/per symbol;
- closed trades total/per symbol;
- remaining positions;
- starting balance;
- ending realized balance;
- ending unrealized P/L;
- ending equity;
- gross realized P/L;
- commission;
- net realized P/L;
- wins/losses/flats;
- non-flat win rate;
- largest closed gain/loss;
- maximum shared-account equity drawdown absolute/percent;
- per-symbol orders/trades/wins/losses/net realized P/L.

Do not rank symbols.

## Prohibited during milestone 016

Do not:

- change thresholds;
- tune parameters;
- disable a losing symbol;
- enable filters;
- change position size;
- change ATR;
- change trailing;
- change spread/accounting/cost semantics;
- force-close end-of-data positions.

This milestone measures the current strategy as it exists.
