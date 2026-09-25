"""Deterministic trade-level diagnostics for the accepted baseline replay.

This module is intentionally observational.  DiagnosticHistoricalBroker
inherits the accepted HistoricalBroker execution semantics and records immutable
facts around successful broker actions.  The diagnostic runner rebuilds the
ordinary baseline report with the inherited broker and can require byte-for-byte
identity with an accepted M016 report before its evidence is trusted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Callable, Mapping, Sequence

import pandas as pd

from config import config
from mamba2.crew.atr_manager import ATRManager
from mamba2.crew.position_manager import PositionManager
from mamba2.strategy.triple_cross import StochasticTripleTFStrategy

from .baseline import build_baseline_report, write_baseline_report
from .broker import (
    AccountCurrencyConversionError,
    ExecutionCostModel,
    HistoricalBroker,
)
from .feed import ReplayFeed
from .mt5_dataset import load_mt5_dataset
from .runner import PortfolioBacktestRunner


def _iso_utc(value: Any) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.isoformat().replace("+00:00", "Z")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    return numeric if math.isfinite(numeric) else None


def _utc_bucket(timestamp: str, *, hours: int = 4) -> str:
    hour = pd.Timestamp(timestamp).hour
    start = (hour // hours) * hours
    end = start + hours - 1
    return f"{start:02d}:00-{end:02d}:59 UTC"


class DiagnosticHistoricalBroker(HistoricalBroker):
    """HistoricalBroker with append-only observational evidence."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._diagnostic_entries: dict[int, dict[str, Any]] = {}
        self._diagnostic_modifications: dict[int, list[dict[str, Any]]] = (
            defaultdict(list)
        )
        self._diagnostic_exits: dict[int, dict[str, Any]] = {}
        self._diagnostic_atr_manager: ATRManager | None = None
        self._diagnostic_atr_timeframe: str | None = None

    def attach_atr_manager(
        self,
        manager: ATRManager,
        *,
        timeframe: str,
    ) -> None:
        self._diagnostic_atr_manager = manager
        self._diagnostic_atr_timeframe = str(timeframe)

    def _spread_snapshot(
        self,
        symbol: str,
        *,
        phase: str,
        field: str,
    ) -> dict[str, Any] | None:
        if phase == "execution":
            bid_bar = self.feed.execution_bar(symbol)
            ask_bar = self.feed.execution_ask_bar(symbol)
        elif phase == "completed":
            bid_bar = self.feed.completed_bar(symbol)
            ask_bar = self.feed.completed_ask_bar(symbol)
        elif phase == "current":
            bid_bar = self.feed.current_bar(symbol)
            ask_bar = self.feed.current_ask_bar(symbol)
        else:
            raise ValueError(f"unsupported diagnostic spread phase: {phase}")

        if bid_bar is None:
            return None

        bid = self._bid_price(bid_bar, field)
        ask = self._ask_price(
            symbol,
            bid_bar,
            field,
            ask_bar=ask_bar,
        )
        point = self.get_point_size(symbol)
        spread_price = ask - bid
        return {
            "phase": phase,
            "field": field,
            "bid": bid,
            "ask": ask,
            "spread_price": spread_price,
            "spread_points": (
                round(spread_price / point, 10) if point > 0 else None
            ),
            "ask_source": "tick-derived" if ask_bar is not None else "bar-spread",
        }

    def _trace_conversion_leg(
        self,
        amount: float,
        *,
        from_currency: str,
        to_currency: str,
        phase: str,
        field: str,
    ) -> tuple[float, dict[str, Any]]:
        symbol, orientation = self._conversion_pair(
            from_currency,
            to_currency,
        )
        bid_bar, ask_bar = self._conversion_bar(symbol, phase=phase)
        bid = self._bid_price(bid_bar, field)
        ask = self._ask_price(
            symbol,
            bid_bar,
            field,
            ask_bar=ask_bar,
        )
        if bid <= 0 or ask <= 0:
            raise AccountCurrencyConversionError(
                f"invalid conversion price for {symbol}"
            )

        if orientation == "direct":
            rate = ask if amount > 0 else bid
            result = amount / rate
            operation = "divide"
        else:
            rate = bid if amount > 0 else ask
            result = amount * rate
            operation = "multiply"

        return result, {
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "symbol": symbol,
            "orientation": orientation,
            "phase": phase,
            "field": field,
            "bid": bid,
            "ask": ask,
            "applied_rate": rate,
            "operation": operation,
            "input_amount": amount,
            "output_amount": result,
            "ask_source": "tick-derived" if ask_bar is not None else "bar-spread",
        }

    def _trace_conversion(
        self,
        amount: float,
        *,
        quote_currency: str,
        phase: str,
        field: str,
    ) -> dict[str, Any]:
        quote = quote_currency.upper()
        account = self.account_currency
        base = {
            "required": bool(amount != 0.0 and quote != account),
            "from_currency": quote,
            "to_currency": account,
            "input_amount": amount,
            "phase": phase,
            "field": field,
            "legs": [],
        }

        if amount == 0.0 or quote == account:
            return {
                **base,
                "route_type": "none",
                "route_label": f"{quote}->{account}:none",
                "output_amount": amount,
            }
        if not quote:
            return {
                **base,
                "route_type": "error",
                "route_label": "missing-quote-currency",
                "output_amount": None,
                "error": "position quote currency is missing",
            }

        direct_error = None
        try:
            output, leg = self._trace_conversion_leg(
                amount,
                from_currency=quote,
                to_currency=account,
                phase=phase,
                field=field,
            )
            return {
                **base,
                "route_type": "direct",
                "route_label": (
                    f"{quote}->{account}:{leg['symbol']}:{leg['orientation']}"
                ),
                "output_amount": output,
                "legs": [leg],
            }
        except AccountCurrencyConversionError as exc:
            direct_error = str(exc)

        for intermediate in self._conversion_intermediates(
            from_currency=quote,
            to_currency=account,
        ):
            try:
                first_output, first = self._trace_conversion_leg(
                    amount,
                    from_currency=quote,
                    to_currency=intermediate,
                    phase=phase,
                    field=field,
                )
                output, second = self._trace_conversion_leg(
                    first_output,
                    from_currency=intermediate,
                    to_currency=account,
                    phase=phase,
                    field=field,
                )
                return {
                    **base,
                    "route_type": "two_leg",
                    "route_label": (
                        f"{quote}->{intermediate}->{account}:"
                        f"{first['symbol']}:{first['orientation']}+"
                        f"{second['symbol']}:{second['orientation']}"
                    ),
                    "output_amount": output,
                    "legs": [first, second],
                }
            except AccountCurrencyConversionError:
                continue

        return {
            **base,
            "route_type": "error",
            "route_label": f"{quote}->{account}:unavailable",
            "output_amount": None,
            "legs": [],
            "error": direct_error,
        }

    def _fill_pending(self) -> None:
        before = {position["ticket"] for position in self._positions}
        super()._fill_pending()
        current = self.feed.current_time
        if current is None:
            return

        for position in self._positions:
            ticket = int(position["ticket"])
            if ticket in before or ticket in self._diagnostic_entries:
                continue

            symbol = position["symbol"]
            _base, quote = self._symbol_currencies(symbol)
            quote_pl = self._calculate_quote_pl(
                position,
                float(position["price_current"]),
            )
            conversion = self._trace_conversion(
                quote_pl,
                quote_currency=quote,
                phase="execution",
                field="open",
            )
            self._diagnostic_entries[ticket] = {
                "timestamp_utc": _iso_utc(current),
                "price": float(position["price_open"]),
                "market_price_after_fill": float(position["price_current"]),
                "spread": self._spread_snapshot(
                    symbol,
                    phase="execution",
                    field="open",
                ),
                "quote_currency": quote,
                "mark_to_market_quote_pl": quote_pl,
                "mark_to_market_conversion": conversion,
                "initial_sl": float(position["sl"]),
                "initial_tp": float(position["tp"]),
            }

    async def order_modify(
        self,
        ticket: int,
        sl: float = 0.0,
        tp: float = 0.0,
    ):
        before = self.position_get_ticket(ticket)
        current = self.feed.current_time
        atr = None
        if (
            before is not None
            and self._diagnostic_atr_manager is not None
        ):
            atr = self._diagnostic_atr_manager.get_atr(
                before["symbol"],
                self._diagnostic_atr_timeframe or "M5",
            )

        result = await super().order_modify(ticket=ticket, sl=sl, tp=tp)
        if (
            before is not None
            and result
            and result.get("retcode") in {0, 10009}
        ):
            after = self.position_get_ticket(ticket)
            self._diagnostic_modifications[ticket].append(
                {
                    "timestamp_utc": (
                        _iso_utc(current) if current is not None else None
                    ),
                    "kind": (
                        "initial_protection"
                        if float(before["sl"]) == 0.0
                        or float(before["tp"]) == 0.0
                        else "trailing"
                    ),
                    "current_price": float(before["price_current"]),
                    "atr": _safe_float(atr),
                    "old_sl": float(before["sl"]),
                    "old_tp": float(before["tp"]),
                    "new_sl": float(sl),
                    "new_tp": float(tp),
                    "applied_sl": (
                        float(after["sl"]) if after is not None else None
                    ),
                    "applied_tp": (
                        float(after["tp"]) if after is not None else None
                    ),
                }
            )
        return result

    def _close_position(
        self,
        position: dict[str, Any],
        price: float,
        reason: str,
        *,
        conversion_phase: str,
        conversion_field: str,
    ) -> None:
        ticket = int(position["ticket"])
        current = self.feed.current_time
        symbol = position["symbol"]
        _base, quote = self._symbol_currencies(symbol)
        quote_pl = self._calculate_quote_pl(position, float(price))
        conversion = self._trace_conversion(
            quote_pl,
            quote_currency=quote,
            phase=conversion_phase,
            field=conversion_field,
        )
        exit_evidence = {
            "timestamp_utc": (
                _iso_utc(current) if current is not None else None
            ),
            "reason": reason,
            "price": float(price),
            "final_sl": float(position["sl"]),
            "final_tp": float(position["tp"]),
            "quote_currency": quote,
            "gross_quote_pl": quote_pl,
            "conversion": conversion,
            "spread_open": self._spread_snapshot(
                symbol,
                phase=conversion_phase,
                field="open",
            ),
            "spread_close": self._spread_snapshot(
                symbol,
                phase=conversion_phase,
                field="close",
            ),
        }
        super()._close_position(
            position,
            price,
            reason,
            conversion_phase=conversion_phase,
            conversion_field=conversion_field,
        )
        self._diagnostic_exits[ticket] = exit_evidence

    def trade_diagnostics(self) -> list[dict[str, Any]]:
        rows = []
        for trade in self.closed_trades:
            ticket = int(trade.position_ticket)
            entry = self._diagnostic_entries.get(ticket, {})
            modifications = list(
                self._diagnostic_modifications.get(ticket, [])
            )
            exit_evidence = self._diagnostic_exits.get(ticket, {})
            entry_time = _iso_utc(
                pd.Timestamp(int(trade.open_time), unit="s", tz="UTC")
            )
            exit_time = _iso_utc(
                pd.Timestamp(int(trade.close_time), unit="s", tz="UTC")
            )
            initial_protection = next(
                (
                    event
                    for event in modifications
                    if event["kind"] == "initial_protection"
                ),
                None,
            )
            trailing = [
                event for event in modifications if event["kind"] == "trailing"
            ]
            outcome = (
                "win"
                if trade.realized_pl > 0
                else "loss"
                if trade.realized_pl < 0
                else "flat"
            )
            rows.append(
                {
                    "order_id": int(trade.order_id),
                    "position_ticket": ticket,
                    "symbol": trade.symbol,
                    "side": "BUY" if int(trade.side) == 0 else "SELL",
                    "volume": float(trade.volume),
                    "entry_time_utc": entry_time,
                    "entry_utc_hour": pd.Timestamp(entry_time).hour,
                    "entry_utc_bucket": _utc_bucket(entry_time),
                    "entry_price": float(trade.open_price),
                    "exit_time_utc": exit_time,
                    "exit_utc_hour": pd.Timestamp(exit_time).hour,
                    "exit_utc_bucket": _utc_bucket(exit_time),
                    "exit_price": float(trade.close_price),
                    "exit_reason": trade.exit_reason,
                    "outcome": outcome,
                    "gross_realized_pl": float(trade.gross_realized_pl),
                    "commission": float(trade.commission),
                    "net_realized_pl": float(trade.realized_pl),
                    "entry_spread": entry.get("spread"),
                    "entry_mark_to_market_conversion": entry.get(
                        "mark_to_market_conversion"
                    ),
                    "initial_protection": initial_protection,
                    "trailing_modifications": trailing,
                    "protection_modification_count": len(modifications),
                    "trailing_modification_count": len(trailing),
                    "exit_spread_open": exit_evidence.get("spread_open"),
                    "exit_spread_close": exit_evidence.get("spread_close"),
                    "exit_conversion": exit_evidence.get("conversion"),
                    "final_sl": exit_evidence.get("final_sl"),
                    "final_tp": exit_evidence.get("final_tp"),
                }
            )
        return rows


def _numeric_summary(values: Sequence[float]) -> dict[str, Any]:
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
        }
    return {
        "count": len(clean),
        "mean": sum(clean) / len(clean),
        "median": median(clean),
        "minimum": min(clean),
        "maximum": max(clean),
    }


def _group_trade_stats(
    trades: Sequence[Mapping[str, Any]],
    key: str,
) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for trade in trades:
        grouped[str(trade[key])].append(trade)

    output = {}
    for name in sorted(grouped):
        rows = grouped[name]
        entry_spreads = [
            row.get("entry_spread", {}).get("spread_points")
            for row in rows
            if row.get("entry_spread")
        ]
        initial_atr = [
            row.get("initial_protection", {}).get("atr")
            for row in rows
            if row.get("initial_protection")
            and row.get("initial_protection", {}).get("atr") is not None
        ]
        output[name] = {
            "closed_trades": len(rows),
            "wins": sum(row["outcome"] == "win" for row in rows),
            "losses": sum(row["outcome"] == "loss" for row in rows),
            "flats": sum(row["outcome"] == "flat" for row in rows),
            "net_realized_pl": sum(
                float(row["net_realized_pl"]) for row in rows
            ),
            "gross_realized_pl": sum(
                float(row["gross_realized_pl"]) for row in rows
            ),
            "entry_spread_points": _numeric_summary(entry_spreads),
            "initial_atr": _numeric_summary(initial_atr),
            "trades_with_trailing": sum(
                int(row["trailing_modification_count"]) > 0
                for row in rows
            ),
            "trailing_modifications": sum(
                int(row["trailing_modification_count"]) for row in rows
            ),
        }
    return output


def _spread_by_outcome(
    trades: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    grouped = defaultdict(list)
    for trade in trades:
        spread = trade.get("entry_spread")
        if spread and spread.get("spread_points") is not None:
            grouped[trade["outcome"]].append(spread["spread_points"])
    return {
        outcome: _numeric_summary(grouped.get(outcome, []))
        for outcome in ("win", "loss", "flat")
    }


def _conversion_stats(
    trades: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for trade in trades:
        trace = trade.get("exit_conversion") or {}
        label = trace.get("route_label", "unknown")
        grouped[label].append(trade)
    return {
        label: {
            "closed_trades": len(rows),
            "wins": sum(row["outcome"] == "win" for row in rows),
            "losses": sum(row["outcome"] == "loss" for row in rows),
            "flats": sum(row["outcome"] == "flat" for row in rows),
            "net_realized_pl": sum(
                float(row["net_realized_pl"]) for row in rows
            ),
        }
        for label, rows in sorted(grouped.items())
    }


def _loss_streaks(
    trades: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    ordered = sorted(
        trades,
        key=lambda row: (
            row["exit_time_utc"],
            int(row["position_ticket"]),
        ),
    )
    streaks = []
    current = []

    def flush() -> None:
        nonlocal current
        if current:
            streaks.append(
                {
                    "start_exit_time_utc": current[0]["exit_time_utc"],
                    "end_exit_time_utc": current[-1]["exit_time_utc"],
                    "count": len(current),
                    "net_realized_pl": sum(
                        float(row["net_realized_pl"]) for row in current
                    ),
                    "tickets": [
                        int(row["position_ticket"]) for row in current
                    ],
                }
            )
            current = []

    for trade in ordered:
        if trade["outcome"] == "loss":
            current.append(trade)
        else:
            flush()
    flush()

    counts = Counter(streak["count"] for streak in streaks)
    maximum = max(streaks, key=lambda item: item["count"], default=None)
    return {
        "loss_streak_count": len(streaks),
        "streak_length_distribution": {
            str(length): counts[length] for length in sorted(counts)
        },
        "maximum_consecutive_losses": (
            maximum["count"] if maximum is not None else 0
        ),
        "maximum_loss_streak": maximum,
        "streaks": streaks,
    }


def _drawdown_episodes(
    curve: Sequence[Mapping[str, Any]],
    *,
    starting_equity: float,
) -> list[dict[str, Any]]:
    peak_equity = float(starting_equity)
    peak_time = curve[0]["timestamp"] if curve else None
    episode = None
    episodes = []

    for sample in curve:
        timestamp = sample["timestamp"]
        equity = float(sample["equity"])
        if equity >= peak_equity:
            if episode is not None:
                episode["recovery_time_utc"] = timestamp
                episode["recovered"] = True
                episodes.append(episode)
                episode = None
            peak_equity = equity
            peak_time = timestamp
            continue

        drawdown = peak_equity - equity
        drawdown_pct = (
            (drawdown / peak_equity) * 100.0 if peak_equity > 0 else 0.0
        )
        if episode is None:
            episode = {
                "peak_time_utc": peak_time,
                "peak_equity": peak_equity,
                "trough_time_utc": timestamp,
                "trough_equity": equity,
                "maximum_drawdown": drawdown,
                "maximum_drawdown_pct": drawdown_pct,
                "recovery_time_utc": None,
                "recovered": False,
            }
        elif drawdown > episode["maximum_drawdown"]:
            episode["trough_time_utc"] = timestamp
            episode["trough_equity"] = equity
            episode["maximum_drawdown"] = drawdown
            episode["maximum_drawdown_pct"] = drawdown_pct

    if episode is not None:
        episodes.append(episode)

    return episodes


def build_diagnostic_report(
    *,
    baseline_report: Mapping[str, Any],
    broker: DiagnosticHistoricalBroker,
    result,
    accepted_baseline_sha256: str | None = None,
) -> dict[str, Any]:
    trades = broker.trade_diagnostics()
    curve = baseline_report.get("equity_curve", [])
    drawdowns = _drawdown_episodes(
        curve,
        starting_equity=float(
            baseline_report["aggregate"]["starting_balance"]
        ),
    )
    deepest = sorted(
        drawdowns,
        key=lambda row: (
            -float(row["maximum_drawdown"]),
            str(row["peak_time_utc"]),
        ),
    )[:10]

    return {
        "diagnostic_schema_version": 1,
        "source_baseline_sha256": accepted_baseline_sha256,
        "dataset": baseline_report["dataset"],
        "configuration": baseline_report["configuration"],
        "cost_assumptions": baseline_report["cost_assumptions"],
        "reconciliation": {
            "accepted_orders": baseline_report["aggregate"][
                "accepted_orders"
            ],
            "closed_trades": baseline_report["aggregate"]["closed_trades"],
            "remaining_open_positions": baseline_report["aggregate"][
                "remaining_open_positions"
            ],
            "ending_realized_balance": baseline_report["aggregate"][
                "ending_realized_balance"
            ],
            "ending_equity": baseline_report["aggregate"]["ending_equity"],
            "net_realized_pl": baseline_report["aggregate"][
                "net_realized_pl"
            ],
            "diagnostic_trade_rows": len(trades),
        },
        "analysis": {
            "by_symbol": _group_trade_stats(trades, "symbol"),
            "by_side": _group_trade_stats(trades, "side"),
            "by_entry_utc_bucket": _group_trade_stats(
                trades,
                "entry_utc_bucket",
            ),
            "by_exit_reason": _group_trade_stats(trades, "exit_reason"),
            "spread_by_outcome": _spread_by_outcome(trades),
            "conversion_routes": _conversion_stats(trades),
            "protection": {
                "trades_with_initial_protection": sum(
                    trade["initial_protection"] is not None
                    for trade in trades
                ),
                "trades_with_trailing": sum(
                    int(trade["trailing_modification_count"]) > 0
                    for trade in trades
                ),
                "total_trailing_modifications": sum(
                    int(trade["trailing_modification_count"])
                    for trade in trades
                ),
                "trailing_modifications_by_outcome": {
                    outcome: sum(
                        int(trade["trailing_modification_count"])
                        for trade in trades
                        if trade["outcome"] == outcome
                    )
                    for outcome in ("win", "loss", "flat")
                },
            },
            "loss_clustering": _loss_streaks(trades),
            "drawdown_episode_count": len(drawdowns),
            "deepest_drawdown_episodes": deepest,
        },
        "trades": trades,
    }


def run_diagnostic_baseline(
    manifest_path: str | Path,
    *,
    starting_balance: float = 10_000.0,
    strategy_transform: Callable[[Any], Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    dataset = load_mt5_dataset(manifest_path)
    symbols = tuple(config.symbols)

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
    broker = DiagnosticHistoricalBroker(
        feed,
        balance=starting_balance,
        symbol_metadata=dataset.symbol_metadata,
        account_currency=dataset.account_currency,
        execution_costs=execution_costs,
    )
    atr_manager = ATRManager(feed)
    broker.attach_atr_manager(
        atr_manager,
        timeframe=str(config.atr_timeframe),
    )
    position_manager = PositionManager(
        broker,
        atr_manager=atr_manager,
        rates_fetcher=feed,
    )
    strategies = [
        StochasticTripleTFStrategy(symbol)
        for symbol in symbols
    ]
    if strategy_transform is not None:
        strategies = [
            strategy_transform(strategy)
            for strategy in strategies
        ]
    runner = PortfolioBacktestRunner(
        feed,
        broker,
        strategies,
        position_manager=position_manager,
        atr_manager=atr_manager,
        strategy_reporting_enabled=False,
    )
    result = runner.run()
    baseline_report = build_baseline_report(
        dataset=dataset,
        result=result,
        broker=broker,
        starting_balance=starting_balance,
    )
    diagnostic_report = build_diagnostic_report(
        baseline_report=baseline_report,
        broker=broker,
        result=result,
    )
    return baseline_report, diagnostic_report


def write_diagnostic_report(
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


def _compact_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    analysis = report["analysis"]
    return {
        "reconciliation": report["reconciliation"],
        "by_symbol": analysis["by_symbol"],
        "by_side": analysis["by_side"],
        "by_entry_utc_bucket": analysis["by_entry_utc_bucket"],
        "by_exit_reason": analysis["by_exit_reason"],
        "spread_by_outcome": analysis["spread_by_outcome"],
        "conversion_routes": analysis["conversion_routes"],
        "protection": analysis["protection"],
        "loss_clustering": {
            key: value
            for key, value in analysis["loss_clustering"].items()
            if key != "streaks"
        },
        "drawdown_episode_count": analysis["drawdown_episode_count"],
        "deepest_drawdown_episodes": analysis[
            "deepest_drawdown_episodes"
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic trade-level baseline diagnostics."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--baseline-output", required=True)
    parser.add_argument("--expected-baseline-report")
    parser.add_argument("--starting-balance", type=float, default=10_000.0)
    args = parser.parse_args(argv)

    baseline_report, diagnostic_report = run_diagnostic_baseline(
        args.manifest,
        starting_balance=args.starting_balance,
    )
    baseline_path = write_baseline_report(
        baseline_report,
        args.baseline_output,
    )
    baseline_bytes = baseline_path.read_bytes()
    baseline_sha = _sha256_bytes(baseline_bytes)

    expected_sha = None
    identical = None
    if args.expected_baseline_report:
        expected = Path(args.expected_baseline_report)
        expected_bytes = expected.read_bytes()
        expected_sha = _sha256_bytes(expected_bytes)
        identical = baseline_bytes == expected_bytes
        if not identical:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "reason": "diagnostic replay changed accepted baseline",
                        "baseline_sha256": baseline_sha,
                        "expected_sha256": expected_sha,
                    },
                    sort_keys=True,
                )
            )
            return 2

    diagnostic_report["source_baseline_sha256"] = (
        expected_sha or baseline_sha
    )
    diagnostic_path = write_diagnostic_report(
        diagnostic_report,
        args.output,
    )
    payload = {
        "ok": True,
        "baseline_sha256": baseline_sha,
        "expected_baseline_sha256": expected_sha,
        "baseline_identical": identical,
        "diagnostic_sha256": _sha256_path(diagnostic_path),
        "summary": _compact_summary(diagnostic_report),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
