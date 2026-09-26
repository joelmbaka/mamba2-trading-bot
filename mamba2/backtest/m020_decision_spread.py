"""Causal decision-time spread diagnostics for M020-C."""

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
from .m020_diagnostics import PERCENTILES, SPREAD_BANDS, _spread_band
from .mt5_dataset import load_mt5_dataset
from .runner import PortfolioBacktestRunner


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


class DecisionSpreadDiagnosticBroker(DiagnosticHistoricalBroker):
    """Record only causal bid/ask information at order submission time."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.decision_spreads: dict[int, dict[str, Any]] = {}

    def order_send(self, request: dict[str, Any]) -> dict[str, Any]:
        symbol = str(request["symbol"])
        current = self.feed.current_time
        tick = self.symbol_info_tick(symbol)
        snapshot = None
        if tick is not None:
            bid = float(tick["bid"])
            ask = float(tick["ask"])
            point = float(self.get_point_size(symbol))
            snapshot = {
                "timestamp_utc": _iso_utc(current),
                "bid": bid,
                "ask": ask,
                "spread_price": ask - bid,
                "spread_points": (
                    round((ask - bid) / point, 10)
                    if point > 0
                    else None
                ),
            }

        result = super().order_send(request)
        order_id = result.get("order")
        if order_id is not None and snapshot is not None:
            self.decision_spreads[int(order_id)] = snapshot
        return result


def _decision_spread(row: Mapping[str, Any]) -> float | None:
    value = row.get("decision_spread_points")
    return None if value is None else float(value)


def _stats(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    spreads = [
        spread
        for row in rows
        if (spread := _decision_spread(row)) is not None
    ]
    return {
        "closed_trades": len(rows),
        "wins": sum(row["outcome"] == "win" for row in rows),
        "losses": sum(row["outcome"] == "loss" for row in rows),
        "flats": sum(row["outcome"] == "flat" for row in rows),
        "net_realized_pl": sum(
            float(row["net_realized_pl"]) for row in rows
        ),
        "decision_spread_points": {
            "count": len(spreads),
            "mean": sum(spreads) / len(spreads) if spreads else None,
            "minimum": min(spreads) if spreads else None,
            "maximum": max(spreads) if spreads else None,
        },
    }


def _group_by_decision_band(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        spread = _decision_spread(row)
        if spread is not None:
            grouped[_spread_band(spread)].append(row)
    return {
        label: _stats(grouped.get(label, []))
        for label, _lower, _upper in SPREAD_BANDS
    }


def _nested_band_breakdown(
    rows: Sequence[Mapping[str, Any]],
    key,
) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(key(row))].append(row)
    return {
        name: _group_by_decision_band(group)
        for name, group in sorted(grouped.items())
    }


def _percentiles(values: Sequence[float]) -> dict[str, float | None]:
    if not values:
        return {
            f"p{percentile:02d}": None
            for percentile in PERCENTILES
        }
    series = pd.Series(values, dtype="float64")
    return {
        f"p{percentile:02d}": float(
            series.quantile(
                percentile / 100.0,
                interpolation="linear",
            )
        )
        for percentile in PERCENTILES
    }


def build_decision_spread_report(
    diagnostic_report: Mapping[str, Any],
    decision_spreads: Mapping[int, Mapping[str, Any]],
) -> dict[str, Any]:
    rows = []
    for trade in diagnostic_report.get("trades", []):
        order_id = int(trade["order_id"])
        decision = decision_spreads.get(order_id)
        if decision is None:
            continue
        decision_value = decision.get("spread_points")
        fill = trade.get("entry_spread") or {}
        fill_value = fill.get("spread_points")
        rows.append(
            {
                "order_id": order_id,
                "position_ticket": int(trade["position_ticket"]),
                "symbol": trade["symbol"],
                "side": trade["side"],
                "submission_time_utc": decision["timestamp_utc"],
                "decision_bid": decision["bid"],
                "decision_ask": decision["ask"],
                "decision_spread_points": decision_value,
                "decision_spread_band": (
                    _spread_band(float(decision_value))
                    if decision_value is not None
                    else None
                ),
                "fill_time_utc": trade["entry_time_utc"],
                "fill_spread_points": fill_value,
                "fill_spread_band": (
                    _spread_band(float(fill_value))
                    if fill_value is not None
                    else None
                ),
                "outcome": trade["outcome"],
                "net_realized_pl": float(trade["net_realized_pl"]),
            }
        )

    decision_values = [
        float(row["decision_spread_points"])
        for row in rows
        if row["decision_spread_points"] is not None
    ]
    fill_values = [
        float(row["fill_spread_points"])
        for row in rows
        if row["fill_spread_points"] is not None
    ]

    transitions: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for row in rows:
        decision_band = row["decision_spread_band"]
        fill_band = row["fill_spread_band"]
        if decision_band is not None and fill_band is not None:
            transitions[decision_band][fill_band] += 1

    paired = [
        (
            float(row["decision_spread_points"]),
            float(row["fill_spread_points"]),
        )
        for row in rows
        if (
            row["decision_spread_points"] is not None
            and row["fill_spread_points"] is not None
        )
    ]
    correlation = None
    if len(paired) >= 2:
        frame = pd.DataFrame(paired, columns=["decision", "fill"])
        correlation = float(frame["decision"].corr(frame["fill"]))

    return {
        "diagnostic_id": "M020-C",
        "strategy_behavior_changed": False,
        "decision_spread_semantics": (
            "broker bid/ask visible at order submission from the latest "
            "completed causal M1 bar"
        ),
        "fill_spread_semantics": (
            "bid/ask on the next M1 execution bar used for historical fill"
        ),
        "spread_band_definition": [
            {
                "label": label,
                "lower_exclusive": lower,
                "upper_inclusive": upper,
            }
            for label, lower, upper in SPREAD_BANDS
        ],
        "reconciliation": {
            "diagnostic_trade_rows": len(
                diagnostic_report.get("trades", [])
            ),
            "decision_spread_rows": len(rows),
            "missing_decision_spread_rows": (
                len(diagnostic_report.get("trades", [])) - len(rows)
            ),
        },
        "decision_spread_percentiles": _percentiles(decision_values),
        "fill_spread_percentiles": _percentiles(fill_values),
        "decision_fill_pearson_correlation": correlation,
        "by_decision_spread_band": _group_by_decision_band(rows),
        "decision_to_fill_band_transitions": {
            decision: {
                fill: counts[fill]
                for fill in sorted(counts)
            }
            for decision, counts in sorted(transitions.items())
        },
        "by_symbol_and_decision_spread_band": _nested_band_breakdown(
            rows,
            lambda row: row["symbol"],
        ),
        "by_side_and_decision_spread_band": _nested_band_breakdown(
            rows,
            lambda row: row["side"],
        ),
        "by_entry_month_and_decision_spread_band": _nested_band_breakdown(
            rows,
            lambda row: pd.Timestamp(
                row["fill_time_utc"]
            ).strftime("%Y-%m"),
        ),
        "rows": rows,
    }


def run_m020c_decision_spread(
    manifest_path: str | Path,
    *,
    baseline_output: str | Path,
    diagnostic_output: str | Path,
    output: str | Path,
    expected_baseline_sha256: str,
    expected_diagnostic_sha256: str,
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
    broker = DecisionSpreadDiagnosticBroker(
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
    baseline_sha = _sha256_path(baseline_path)
    if baseline_sha != expected_baseline_sha256:
        return {
            "ok": False,
            "reason": "M020-C changed accepted M019 baseline bytes",
            "baseline_sha256": baseline_sha,
            "expected_baseline_sha256": expected_baseline_sha256,
        }

    diagnostic_report = build_diagnostic_report(
        baseline_report=baseline_report,
        broker=broker,
        result=result,
    )
    diagnostic_report["source_baseline_sha256"] = baseline_sha
    diagnostic_path = write_diagnostic_report(
        diagnostic_report,
        diagnostic_output,
    )
    diagnostic_sha = _sha256_path(diagnostic_path)
    if diagnostic_sha != expected_diagnostic_sha256:
        return {
            "ok": False,
            "reason": "M020-C changed accepted M019 diagnostic bytes",
            "baseline_sha256": baseline_sha,
            "diagnostic_sha256": diagnostic_sha,
            "expected_diagnostic_sha256": expected_diagnostic_sha256,
        }

    report = build_decision_spread_report(
        diagnostic_report,
        broker.decision_spreads,
    )
    report["source_baseline_sha256"] = baseline_sha
    report["source_diagnostic_sha256"] = diagnostic_sha

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "ok": True,
        "diagnostic_id": "M020-C",
        "strategy_behavior_changed": False,
        "baseline_sha256": baseline_sha,
        "diagnostic_sha256": diagnostic_sha,
        "output": str(output_path),
        "output_sha256": _sha256_path(output_path),
        "reconciliation": report["reconciliation"],
        "decision_spread_percentiles": report[
            "decision_spread_percentiles"
        ],
        "fill_spread_percentiles": report["fill_spread_percentiles"],
        "decision_fill_pearson_correlation": report[
            "decision_fill_pearson_correlation"
        ],
        "by_decision_spread_band": report[
            "by_decision_spread_band"
        ],
        "decision_to_fill_band_transitions": report[
            "decision_to_fill_band_transitions"
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run causal M020-C decision-time spread diagnostics."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--baseline-output", required=True)
    parser.add_argument("--diagnostic-output", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--expected-baseline-sha256", required=True)
    parser.add_argument("--expected-diagnostic-sha256", required=True)
    parser.add_argument("--starting-balance", type=float, default=10_000.0)
    args = parser.parse_args(argv)

    result = run_m020c_decision_spread(
        args.manifest,
        baseline_output=args.baseline_output,
        diagnostic_output=args.diagnostic_output,
        output=args.output,
        expected_baseline_sha256=args.expected_baseline_sha256,
        expected_diagnostic_sha256=args.expected_diagnostic_sha256,
        starting_balance=args.starting_balance,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
