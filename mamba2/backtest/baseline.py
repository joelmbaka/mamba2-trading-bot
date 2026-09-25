"""Reproducible reporting for the accepted shared-account replay engine."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from config import config
from mamba2.crew.atr_manager import ATRManager
from mamba2.crew.position_manager import PositionManager
from mamba2.strategy.triple_cross import StochasticTripleTFStrategy

from .broker import ExecutionCostModel, HistoricalBroker
from .feed import ReplayFeed
from .mt5_dataset import DatasetIntegrityError, LoadedHistoricalDataset, load_mt5_dataset
from .runner import PortfolioBacktestResult, PortfolioBacktestRunner


COST_ASSUMPTION_LABEL = (
    "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO"
)


def _iso_utc(value: Any) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.isoformat().replace("+00:00", "Z")


def _validate_baseline_dataset(
    dataset: LoadedHistoricalDataset,
    symbols: Sequence[str],
) -> None:
    for symbol in symbols:
        if symbol not in dataset.m1_bars:
            raise DatasetIntegrityError(
                f"baseline dataset is missing M1 history for {symbol}"
            )
        native = dataset.native_timeframe_bars.get(symbol, {})
        for timeframe in ("M5", "M15"):
            if timeframe not in native:
                raise DatasetIntegrityError(
                    f"baseline dataset is missing native {timeframe} "
                    f"history for {symbol}"
                )
        ask = dataset.ask_m1_bars.get(symbol)
        if ask is None:
            raise DatasetIntegrityError(
                f"baseline dataset is missing tick-derived Ask M1 for {symbol}"
            )
        ask_manifest = dataset.manifest.get("symbols", {}).get(
            symbol,
            {},
        ).get("ask_m1", {})
        if ask_manifest.get("source") != "copy_ticks_range":
            raise DatasetIntegrityError(
                f"baseline Ask M1 is not tick-derived for {symbol}"
            )
        if not ask.index.equals(dataset.m1_bars[symbol].index):
            raise DatasetIntegrityError(
                f"baseline dataset has incomplete Ask M1 coverage for {symbol}"
            )


def _config_snapshot() -> dict[str, Any]:
    return {
        "symbols": list(config.symbols),
        "position_size": float(config.position_size),
        "trend_filter_enabled": bool(config.ENABLE_TREND_CONDITION),
        "rsi_filter_enabled": bool(config.ENABLE_RSI_CONDITION),
        "higher_tf_filter_enabled": bool(config.use_higher_tf),
        "stochastic_timeframes": dict(config.stochastic_timeframes),
        "stochastic_parameters": {
            "k_period": int(config.stochastic_k_period),
            "d_period": int(config.stochastic_d_period),
            "slowing": int(config.stochastic_slowing),
        },
        "atr_period": int(config.atr_period),
        "atr_timeframe": str(config.atr_timeframe),
        "atr_sl_multiplier": float(config.atr_sl_multiplier),
        "atr_tp_multiplier": float(config.atr_tp_multiplier),
    }


def _equity_curve(
    result: PortfolioBacktestResult,
) -> list[dict[str, Any]]:
    return [
        {
            "timestamp": _iso_utc(sample["timestamp"]),
            "balance": float(sample["balance"]),
            "realized_profit": float(sample["realized_profit"]),
            "unrealized_profit": float(sample["unrealized_profit"]),
            "equity": float(sample["equity"]),
            "commission_paid": float(sample["commission_paid"]),
        }
        for sample in result.account_snapshots
    ]


def _maximum_drawdown(
    curve: Sequence[Mapping[str, Any]],
    *,
    starting_equity: float,
) -> tuple[float, float]:
    peak = float(starting_equity)
    maximum = 0.0
    maximum_pct = 0.0
    for sample in curve:
        equity = float(sample["equity"])
        if equity > peak:
            peak = equity
        drawdown = peak - equity
        drawdown_pct = drawdown / peak if peak > 0 else 0.0
        if drawdown > maximum:
            maximum = drawdown
        if drawdown_pct > maximum_pct:
            maximum_pct = drawdown_pct
    return maximum, maximum_pct * 100.0


def _remaining_positions(
    result: PortfolioBacktestResult,
    symbols: Sequence[str],
) -> list[dict[str, Any]]:
    remaining: list[dict[str, Any]] = []
    for symbol in symbols:
        for position in result.open_positions_by_symbol.get(symbol, []):
            remaining.append(
                {
                    "symbol": symbol,
                    "side": "buy" if int(position["type"]) == 0 else "sell",
                    "volume": float(position["volume"]),
                    "open_time_utc": _iso_utc(
                        pd.Timestamp(int(position["time"]), unit="s", tz="UTC")
                    ),
                    "open_price": float(position["price_open"]),
                    "current_price": float(position["price_current"]),
                    "sl": float(position["sl"]),
                    "tp": float(position["tp"]),
                    "unrealized_pl": float(position["profit"]),
                }
            )
    return remaining


def build_baseline_report(
    *,
    dataset: LoadedHistoricalDataset,
    result: PortfolioBacktestResult,
    broker: HistoricalBroker,
    starting_balance: float,
) -> dict[str, Any]:
    """Build a deterministic account-level report from a completed replay."""

    symbols = tuple(config.symbols)
    trades = list(broker.closed_trades)
    final = result.final_account or broker.account_info()
    curve = _equity_curve(result)
    max_drawdown, max_drawdown_pct = _maximum_drawdown(
        curve,
        starting_equity=starting_balance,
    )

    wins = [trade for trade in trades if trade.realized_pl > 0]
    losses = [trade for trade in trades if trade.realized_pl < 0]
    flats = [trade for trade in trades if trade.realized_pl == 0]
    nonflat = len(wins) + len(losses)

    per_symbol: dict[str, Any] = {}
    for symbol in symbols:
        symbol_trades = [trade for trade in trades if trade.symbol == symbol]
        symbol_open = result.open_positions_by_symbol.get(symbol, [])
        open_entry_commission = sum(
            float(position.get("entry_commission", 0.0))
            for position in symbol_open
        )
        per_symbol[symbol] = {
            "accepted_orders": int(
                result.accepted_order_count_by_symbol.get(symbol, 0)
            ),
            "closed_trades": len(symbol_trades),
            "wins": sum(trade.realized_pl > 0 for trade in symbol_trades),
            "losses": sum(trade.realized_pl < 0 for trade in symbol_trades),
            "net_realized_pl": float(
                sum(trade.realized_pl for trade in symbol_trades)
                - open_entry_commission
            ),
            "remaining_open_positions": len(symbol_open),
        }

    remaining = _remaining_positions(result, symbols)
    requested_range = dataset.manifest.get("requested_range", {})
    gross_realized = float(sum(trade.gross_realized_pl for trade in trades))
    commission = float(final.get("commission_paid", 0.0))
    net_realized = float(final["balance"]) - float(starting_balance)

    report = {
        "report_schema_version": 1,
        "dataset": {
            "schema_version": dataset.manifest.get("schema_version"),
            "source": dataset.manifest.get("source"),
            "timestamp_semantics": dataset.manifest.get("timestamp_semantics"),
            "start_utc": requested_range.get("from_utc"),
            "end_utc": requested_range.get("to_utc"),
            "account_currency": dataset.account_currency,
            "symbols": list(symbols),
        },
        "configuration": _config_snapshot(),
        "cost_assumptions": {
            "label": COST_ASSUMPTION_LABEL,
            "historical_spread": "tick-derived Bid/Ask",
            "commission_per_lot_per_side": 0.0,
            "configured_slippage_points": 0.0,
        },
        "aggregate": {
            "global_replay_boundaries": int(result.evaluations),
            "accepted_orders": int(result.accepted_order_count),
            "closed_trades": len(trades),
            "remaining_open_positions": len(remaining),
            "starting_balance": float(starting_balance),
            "ending_realized_balance": float(final["balance"]),
            "ending_unrealized_pl": float(final["unrealized_profit"]),
            "ending_equity": float(final["equity"]),
            "gross_realized_pl": gross_realized,
            "commission": commission,
            "net_realized_pl": net_realized,
            "winning_closed_trades": len(wins),
            "losing_closed_trades": len(losses),
            "flat_closed_trades": len(flats),
            "win_rate_nonflat_pct": (
                (len(wins) / nonflat) * 100.0 if nonflat else None
            ),
            "largest_closed_trade_gain": (
                max(trade.realized_pl for trade in wins) if wins else None
            ),
            "largest_closed_trade_loss": (
                min(trade.realized_pl for trade in losses) if losses else None
            ),
            "maximum_equity_drawdown": max_drawdown,
            "maximum_equity_drawdown_pct": max_drawdown_pct,
        },
        "per_symbol": per_symbol,
        "remaining_positions": remaining,
        "equity_curve": curve,
    }
    return report


def run_baseline(
    manifest_path: str | Path,
    *,
    starting_balance: float = 10_000.0,
    max_steps: int | None = None,
) -> dict[str, Any]:
    """Run the production strategy portfolio with explicit zero execution costs."""

    starting_balance = float(starting_balance)
    if not math.isfinite(starting_balance) or starting_balance <= 0:
        raise ValueError("starting_balance must be finite and positive")
    if max_steps is not None and max_steps < 1:
        raise ValueError("max_steps must be at least 1 when provided")

    dataset = load_mt5_dataset(manifest_path)
    symbols = tuple(config.symbols)
    _validate_baseline_dataset(dataset, symbols)

    feed = ReplayFeed(
        dataset.m1_bars,
        native_timeframe_bars=dataset.native_timeframe_bars,
        ask_m1_bars=dataset.ask_m1_bars,
    )
    execution_costs = {
        symbol: ExecutionCostModel(
            commission_per_lot_per_side=0.0,
            slippage_points=0.0,
        )
        for symbol in symbols
    }
    broker = HistoricalBroker(
        feed,
        balance=starting_balance,
        symbol_metadata=dataset.symbol_metadata,
        account_currency=dataset.account_currency,
        execution_costs=execution_costs,
    )
    atr_manager = ATRManager(feed)
    position_manager = PositionManager(
        broker,
        atr_manager=atr_manager,
        rates_fetcher=feed,
    )
    strategies = [
        StochasticTripleTFStrategy(symbol)
        for symbol in symbols
    ]
    runner = PortfolioBacktestRunner(
        feed,
        broker,
        strategies,
        position_manager=position_manager,
        atr_manager=atr_manager,
        strategy_reporting_enabled=False,
    )
    result = runner.run(max_steps=max_steps)
    return build_baseline_report(
        dataset=dataset,
        result=result,
        broker=broker,
        starting_balance=starting_balance,
    )


def write_baseline_report(
    report: Mapping[str, Any],
    path: str | Path,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def format_baseline_summary(report: Mapping[str, Any]) -> str:
    aggregate = report["aggregate"]
    return (
        f"boundaries={aggregate['global_replay_boundaries']} "
        f"orders={aggregate['accepted_orders']} "
        f"closed={aggregate['closed_trades']} "
        f"open={aggregate['remaining_open_positions']} "
        f"balance={aggregate['ending_realized_balance']:.2f} "
        f"equity={aggregate['ending_equity']:.2f} "
        f"max_dd={aggregate['maximum_equity_drawdown']:.2f} "
        f"({aggregate['maximum_equity_drawdown_pct']:.2f}%)"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a deterministic five-symbol historical baseline."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--starting-balance", type=float, default=10_000.0)
    parser.add_argument("--max-steps", type=int)
    args = parser.parse_args(argv)

    report = run_baseline(
        args.manifest,
        starting_balance=args.starting_balance,
        max_steps=args.max_steps,
    )
    output = write_baseline_report(report, args.output)
    print(format_baseline_summary(report))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
