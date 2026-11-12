"""Single-variable causal spread treatment for M020-D."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from config import config
from mamba2.crew.atr_manager import ATRManager
from mamba2.crew.position_manager import PositionManager
from mamba2.strategy.triple_cross import StochasticTripleTFStrategy

from .baseline import build_baseline_report, write_baseline_report
from .broker import ExecutionCostModel
from .diagnostics import (
    DiagnosticHistoricalBroker,
    build_diagnostic_report,
    write_diagnostic_report,
)
from .feed import ReplayFeed
from .mt5_dataset import load_mt5_dataset
from .runner import PortfolioBacktestRunner


M020_D_MAX_DECISION_SPREAD_POINTS = 10.0


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _iso_utc(value: Any) -> str | None:
    if value is None:
        return None
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.isoformat().replace("+00:00", "Z")


class DecisionSpreadFilterBroker(DiagnosticHistoricalBroker):
    """Reject only new orders whose causal decision spread exceeds 10 points."""

    def __init__(self, *args, max_spread_points: float = 10.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_spread_points = float(max_spread_points)
        self.rejected_orders: list[dict[str, Any]] = []
        self.accepted_decision_spreads: dict[int, dict[str, Any]] = {}

    def _decision_snapshot(self, symbol: str) -> dict[str, Any] | None:
        tick = self.symbol_info_tick(symbol)
        if tick is None:
            return None
        bid = float(tick["bid"])
        ask = float(tick["ask"])
        point = float(self.get_point_size(symbol))
        spread_points = (
            round((ask - bid) / point, 10)
            if point > 0
            else None
        )
        return {
            "timestamp_utc": _iso_utc(self.feed.current_time),
            "bid": bid,
            "ask": ask,
            "spread_price": ask - bid,
            "spread_points": spread_points,
        }

    def order_send(self, request: dict[str, Any]) -> dict[str, Any]:
        symbol = str(request["symbol"])
        snapshot = self._decision_snapshot(symbol)
        if (
            snapshot is not None
            and snapshot["spread_points"] is not None
            and float(snapshot["spread_points"]) > self.max_spread_points
        ):
            self.rejected_orders.append(
                {
                    "symbol": symbol,
                    "side": "BUY" if int(request.get("type", 0)) == 0 else "SELL",
                    **snapshot,
                }
            )
            return {
                "retcode": 1,
                "deal": 0,
                "order": 0,
                "price": 0.0,
                "comment": (
                    "M020-D experiment rejected decision-time spread "
                    f">{self.max_spread_points:g} points"
                ),
            }

        result = super().order_send(request)
        order_id = result.get("order")
        if order_id is not None and snapshot is not None:
            self.accepted_decision_spreads[int(order_id)] = snapshot
        return result


def _monthly_trade_stats(trades: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for trade in trades:
        month = pd.Timestamp(trade["entry_time_utc"]).strftime("%Y-%m")
        grouped[month].append(trade)

    return {
        month: {
            "closed_trades": len(rows),
            "wins": sum(row["outcome"] == "win" for row in rows),
            "losses": sum(row["outcome"] == "loss" for row in rows),
            "flats": sum(row["outcome"] == "flat" for row in rows),
            "net_realized_pl": sum(
                float(row["net_realized_pl"]) for row in rows
            ),
        }
        for month, rows in sorted(grouped.items())
    }


def _accepted_spread_stats(
    trades: Sequence[Mapping[str, Any]],
    accepted: Mapping[int, Mapping[str, Any]],
) -> dict[str, Any]:
    rows = []
    violations = []
    for trade in trades:
        order_id = int(trade["order_id"])
        decision = accepted.get(order_id)
        if decision is None:
            continue
        spread = decision.get("spread_points")
        row = {
            "order_id": order_id,
            "position_ticket": int(trade["position_ticket"]),
            "symbol": trade["symbol"],
            "side": trade["side"],
            "entry_time_utc": trade["entry_time_utc"],
            "decision_time_utc": decision["timestamp_utc"],
            "decision_spread_points": spread,
            "outcome": trade["outcome"],
            "net_realized_pl": float(trade["net_realized_pl"]),
        }
        rows.append(row)
        if (
            spread is not None
            and float(spread) > M020_D_MAX_DECISION_SPREAD_POINTS
        ):
            violations.append(row)

    return {
        "closed_trade_rows_with_decision_spread": len(rows),
        "accepted_spread_violation_count": len(violations),
        "accepted_spread_violations": violations,
        "maximum_accepted_decision_spread_points": (
            max(
                float(row["decision_spread_points"])
                for row in rows
                if row["decision_spread_points"] is not None
            )
            if rows
            else None
        ),
    }


def run_m020d_treatment(
    manifest_path: str | Path,
    *,
    baseline_output: str | Path,
    diagnostic_output: str | Path,
    evidence_output: str | Path,
    starting_balance: float = 10_000.0,
) -> dict[str, Any]:
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
    broker = DecisionSpreadFilterBroker(
        feed,
        balance=starting_balance,
        symbol_metadata=dataset.symbol_metadata,
        account_currency=dataset.account_currency,
        execution_costs=execution_costs,
        max_spread_points=M020_D_MAX_DECISION_SPREAD_POINTS,
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
    baseline_path = write_baseline_report(
        baseline_report,
        baseline_output,
    )

    diagnostic_report = build_diagnostic_report(
        baseline_report=baseline_report,
        broker=broker,
        result=result,
    )
    baseline_sha = _sha256_path(baseline_path)
    diagnostic_report["source_baseline_sha256"] = baseline_sha
    diagnostic_path = write_diagnostic_report(
        diagnostic_report,
        diagnostic_output,
    )

    trades = diagnostic_report.get("trades", [])
    spread_gate = _accepted_spread_stats(
        trades,
        broker.accepted_decision_spreads,
    )
    evidence = {
        "experiment_id": "M020-D",
        "hypothesis": (
            "New entries submitted when observable decision-time spread is "
            "greater than 10 points are a persistently harmful exposure."
        ),
        "strategy_behavior_changed": True,
        "treatment": {
            "behavior": "reject new order submission only",
            "decision_time_spread_operator": ">",
            "decision_time_spread_threshold_points": (
                M020_D_MAX_DECISION_SPREAD_POINTS
            ),
            "m020_a_session_filter_stacked": False,
        },
        "baseline_sha256": baseline_sha,
        "diagnostic_sha256": _sha256_path(diagnostic_path),
        "aggregate": baseline_report["aggregate"],
        "per_symbol": baseline_report.get("per_symbol"),
        "by_entry_month": _monthly_trade_stats(trades),
        "analysis": {
            "by_symbol": diagnostic_report["analysis"].get("by_symbol"),
            "by_side": diagnostic_report["analysis"].get("by_side"),
            "by_exit_reason": diagnostic_report["analysis"].get(
                "by_exit_reason"
            ),
            "spread_by_outcome": diagnostic_report["analysis"].get(
                "spread_by_outcome"
            ),
        },
        "rejected_order_count": len(broker.rejected_orders),
        "rejected_orders": broker.rejected_orders,
        **spread_gate,
    }

    evidence_path = Path(evidence_output)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "ok": spread_gate["accepted_spread_violation_count"] == 0,
        "experiment_id": "M020-D",
        "baseline_path": str(baseline_path),
        "baseline_sha256": baseline_sha,
        "diagnostic_path": str(diagnostic_path),
        "diagnostic_sha256": _sha256_path(diagnostic_path),
        "evidence_path": str(evidence_path),
        "evidence_sha256": _sha256_path(evidence_path),
        "aggregate": baseline_report["aggregate"],
        "rejected_order_count": len(broker.rejected_orders),
        **spread_gate,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the single-variable M020-D decision-spread treatment."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--baseline-output", required=True)
    parser.add_argument("--diagnostic-output", required=True)
    parser.add_argument("--evidence-output", required=True)
    parser.add_argument("--starting-balance", type=float, default=10_000.0)
    args = parser.parse_args(argv)

    result = run_m020d_treatment(
        args.manifest,
        baseline_output=args.baseline_output,
        diagnostic_output=args.diagnostic_output,
        evidence_output=args.evidence_output,
        starting_balance=args.starting_balance,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
