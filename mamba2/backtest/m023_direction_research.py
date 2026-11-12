"""M023 Stage-A causal direction research.

This module is research-only. It keeps the accepted P2-08 strategy parameters
and replay semantics fixed, changes only new-entry direction eligibility, and
is mechanically limited to the already-seen 225-date research partition.
Historical holdout execution is not exposed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, median
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
from .mt5_dataset import LoadedHistoricalDataset, load_mt5_dataset
from .parameter_research import (
    COST_CONTRACT,
    M022_SOURCE_MANIFEST_SHA256,
    Phase1Parameters,
    ResearchBoundaryReplayFeed,
    _canonical_json_sha256,
    _datetime_index_sha256,
    _iso,
    _sha256_path,
    _slice_frame,
    _strict_common_boundary_clock,
    _temporary_research_config,
    _tp_safety,
    _utc,
)
from .runner import PortfolioBacktestRunner


M023_STAGE_A_START_UTC = "2025-08-25T00:00:00Z"
M023_STAGE_A_END_EXCLUSIVE_UTC = "2026-07-08T00:00:00Z"
M023_STAGE_A_TRADING_DATE_COUNT = 225
M023_STAGE_A_DATE_LIST_SHA256 = (
    "50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0"
)

M023_STAGE_A_FOLDS: tuple[tuple[str, str, str, str], ...] = (
    (
        "F1",
        "2025-08-25",
        "2025-10-24",
        "bccecd70357df71e85fbd7ce1d0f329fc6d866998c0fe3ad899290b6d0ed0f8e",
    ),
    (
        "F2",
        "2025-10-27",
        "2025-12-29",
        "4f6344e3ae75c51e48d176d0b85c743666cf34c4cfe7b05731d7d40a58d17a8b",
    ),
    (
        "F3",
        "2025-12-30",
        "2026-03-03",
        "6c51d75e0d585649821d3105e3e1d1b2c485fa34e70348041d1b137b26485d4f",
    ),
    (
        "F4",
        "2026-03-04",
        "2026-05-05",
        "f0e758dfdf722747aacc277fdd9c09b0ab9035415978369aaec97b6f1ed807ec",
    ),
    (
        "F5",
        "2026-05-06",
        "2026-07-07",
        "1df4395f28637370920957a3ae2af3eb5fc75b5d4255918e29d42fcd14073292",
    ),
)

P2_08_PARAMETERS = Phase1Parameters(
    stochastic_k_period=21,
    stochastic_d_period=7,
    stochastic_slowing=7,
    oversold_level=20.0,
    overbought_level=80.0,
    ema_period=7,
    decision_spread_max_points=None,
    atr_sl_multiplier=1.5,
    atr_tp_multiplier=3.0,
    block_00_04_utc=False,
)

STAGE_A_DIRECTIONS: Mapping[str, str] = {
    "D-R": "BOTH",
    "D-S": "SELL",
    "D-B": "BUY",
}


@dataclass(frozen=True)
class StageADirectionArm:
    arm_id: str
    direction: str
    parameters: Phase1Parameters = P2_08_PARAMETERS

    def __post_init__(self) -> None:
        expected = STAGE_A_DIRECTIONS.get(self.arm_id)
        if expected is None or expected != self.direction:
            raise ValueError("arm is outside the frozen M023 Stage-A matrix")


class DirectionFilterBrokerProxy:
    """Suppress only disallowed new entry requests."""

    RESEARCH_REJECT_CODE = 10031

    def __init__(self, broker: Any, *, allowed_direction: str):
        if allowed_direction not in {"BOTH", "SELL", "BUY"}:
            raise ValueError("unsupported Stage-A direction")
        self.broker = broker
        self.allowed_direction = allowed_direction
        self.rejections = 0
        self.rejected_by_side = {"BUY": 0, "SELL": 0}
        self.passed_by_side = {"BUY": 0, "SELL": 0}

    @staticmethod
    def _side(request: Mapping[str, Any]) -> str:
        order_type = int(request.get("type", 0))
        if order_type == 0:
            return "BUY"
        if order_type == 1:
            return "SELL"
        raise ValueError(f"unsupported entry order type: {order_type}")

    def order_send(self, request: dict[str, Any]) -> dict[str, Any]:
        side = self._side(request)
        allowed = (
            self.allowed_direction == "BOTH"
            or side == self.allowed_direction
        )
        if not allowed:
            self.rejections += 1
            self.rejected_by_side[side] += 1
            return {
                "retcode": self.RESEARCH_REJECT_CODE,
                "order": 0,
                "price": float(request.get("price", 0.0)),
                "comment": (
                    f"M023 Stage-A direction rejection: {side} "
                    f"not allowed by {self.allowed_direction}"
                ),
            }

        self.passed_by_side[side] += 1
        return self.broker.order_send(request)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.broker, name)


class DirectionStrategyWrapper:
    """Expose only a direction-filtered broker to one research strategy."""

    def __init__(self, strategy: Any, proxy: DirectionFilterBrokerProxy):
        self.strategy = strategy
        self.proxy = proxy
        self.symbol = strategy.symbol

    async def evaluate(self, market: dict[str, Any]) -> None:
        await self.strategy.evaluate({**market, "broker": self.proxy})


def stage_a_arm(arm_id: str) -> StageADirectionArm:
    try:
        direction = STAGE_A_DIRECTIONS[arm_id]
    except KeyError as exc:
        raise ValueError("arm is outside the frozen M023 Stage-A matrix") from exc
    return StageADirectionArm(arm_id=arm_id, direction=direction)


def _date_list_sha256(dates: Sequence[str]) -> str:
    payload = ("\n".join(dates) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require_stage_a_range(start_utc: str, end_exclusive_utc: str) -> None:
    if (
        start_utc != M023_STAGE_A_START_UTC
        or end_exclusive_utc != M023_STAGE_A_END_EXCLUSIVE_UTC
    ):
        raise ValueError(
            "M023 Stage A permits only the frozen 225-date seen-research "
            "partition; historical holdout is unavailable"
        )


def slice_stage_a_dataset(
    dataset: LoadedHistoricalDataset,
) -> tuple[LoadedHistoricalDataset, pd.DatetimeIndex, list[str], list[dict[str, Any]]]:
    """Slice exact seen research data and verify dates/folds prospectively."""

    _require_stage_a_range(
        M023_STAGE_A_START_UTC,
        M023_STAGE_A_END_EXCLUSIVE_UTC,
    )
    start = _utc(M023_STAGE_A_START_UTC)
    end = _utc(M023_STAGE_A_END_EXCLUSIVE_UTC)

    m1 = {
        symbol: _slice_frame(frame, start=start, end=end)
        for symbol, frame in dataset.m1_bars.items()
    }
    ask = {
        symbol: _slice_frame(frame, start=start, end=end)
        for symbol, frame in dataset.ask_m1_bars.items()
    }
    native = {
        symbol: {
            timeframe: _slice_frame(frame, start=start, end=end)
            for timeframe, frame in frames.items()
        }
        for symbol, frames in dataset.native_timeframe_bars.items()
    }

    for symbol in m1:
        if symbol not in ask or not m1[symbol].index.equals(ask[symbol].index):
            raise ValueError(f"M023 Stage-A Bid/Ask M1 mismatch for {symbol}")

    boundary_clock = _strict_common_boundary_clock(
        m1,
        ask,
        end_exclusive=end,
    )
    dates = list(
        dict.fromkeys(
            timestamp.date().isoformat()
            for timestamp in boundary_clock
            if timestamp < end
        )
    )
    if len(dates) != M023_STAGE_A_TRADING_DATE_COUNT:
        raise ValueError(
            "M023 Stage-A trading-date count changed: "
            f"{len(dates)} != {M023_STAGE_A_TRADING_DATE_COUNT}"
        )
    date_sha = _date_list_sha256(dates)
    if date_sha != M023_STAGE_A_DATE_LIST_SHA256:
        raise ValueError(
            "M023 Stage-A date-list SHA changed: "
            f"{date_sha} != {M023_STAGE_A_DATE_LIST_SHA256}"
        )

    folds: list[dict[str, Any]] = []
    for index, (label, first, last, expected_sha) in enumerate(
        M023_STAGE_A_FOLDS
    ):
        chunk = dates[index * 45 : (index + 1) * 45]
        observed_sha = _date_list_sha256(chunk)
        if (
            len(chunk) != 45
            or chunk[0] != first
            or chunk[-1] != last
            or observed_sha != expected_sha
        ):
            raise ValueError(f"M023 Stage-A fold {label} changed")
        folds.append(
            {
                "label": label,
                "first_date": first,
                "last_date": last,
                "trading_dates": 45,
                "date_list_sha256": observed_sha,
                "dates": chunk,
            }
        )

    manifest = dict(dataset.manifest)
    manifest["requested_range"] = {
        "from_utc": M023_STAGE_A_START_UTC,
        "to_utc": M023_STAGE_A_END_EXCLUSIVE_UTC,
    }
    manifest["m023_stage"] = "A"
    manifest["m023_stage_a_seen_research_only"] = True
    manifest["m023_stage_a_date_list_sha256"] = date_sha
    manifest["m023_stage_a_trading_dates"] = len(dates)
    manifest["m023_strict_common_boundary_clock"] = True
    manifest["m023_full_symbol_m1_preserved"] = True
    manifest["m023_replay_boundary_count"] = int(len(boundary_clock))
    manifest["m023_replay_boundary_first_utc"] = _iso(boundary_clock[0])
    manifest["m023_replay_boundary_last_utc"] = _iso(boundary_clock[-1])
    manifest["m023_replay_boundary_sha256"] = _datetime_index_sha256(
        boundary_clock
    )

    sliced = LoadedHistoricalDataset(
        m1_bars=m1,
        native_timeframe_bars=native,
        ask_m1_bars=ask,
        symbol_metadata=dataset.symbol_metadata,
        account_currency=dataset.account_currency,
        manifest=manifest,
    )
    return sliced, boundary_clock, dates, folds


def _partition_metadata(
    *,
    manifest_path: Path,
    dataset: LoadedHistoricalDataset,
    dates: Sequence[str],
    folds: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    source_sha = _sha256_path(manifest_path)
    if source_sha != M022_SOURCE_MANIFEST_SHA256:
        raise ValueError(
            "accepted M022 source manifest changed: "
            f"{source_sha} != {M022_SOURCE_MANIFEST_SHA256}"
        )
    specification = {
        "source_manifest_sha256": source_sha,
        "start_utc": M023_STAGE_A_START_UTC,
        "end_exclusive_utc": M023_STAGE_A_END_EXCLUSIVE_UTC,
        "trading_dates": len(dates),
        "date_list_sha256": _date_list_sha256(dates),
        "strict_common_boundary_clock": bool(
            dataset.manifest.get("m023_strict_common_boundary_clock")
        ),
        "full_symbol_m1_preserved": bool(
            dataset.manifest.get("m023_full_symbol_m1_preserved")
        ),
        "replay_boundary_count": int(
            dataset.manifest.get("m023_replay_boundary_count", 0)
        ),
        "replay_boundary_first_utc": dataset.manifest.get(
            "m023_replay_boundary_first_utc"
        ),
        "replay_boundary_last_utc": dataset.manifest.get(
            "m023_replay_boundary_last_utc"
        ),
        "replay_boundary_sha256": dataset.manifest.get(
            "m023_replay_boundary_sha256"
        ),
        "folds": [
            {
                key: value
                for key, value in fold.items()
                if key != "dates"
            }
            for fold in folds
        ],
    }
    return {
        **specification,
        "partition_spec_sha256": _canonical_json_sha256(specification),
    }


def _entry_timestamp(trade: Mapping[str, Any]) -> pd.Timestamp:
    value = pd.Timestamp(str(trade["entry_time_utc"]))
    if value.tzinfo is None:
        return value.tz_localize("UTC")
    return value.tz_convert("UTC")


def _trade_stats(trades: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(trades)
    pls = [float(row.get("net_realized_pl", 0.0)) for row in rows]
    wins = sum(value > 0 for value in pls)
    losses = sum(value < 0 for value in pls)
    flats = len(rows) - wins - losses
    nonflat = wins + losses
    spreads = [
        float(row["entry_spread"]["spread_points"])
        for row in rows
        if (row.get("entry_spread") or {}).get("spread_points") is not None
    ]
    symbols: dict[str, Any] = {}
    for symbol in sorted({str(row["symbol"]) for row in rows}):
        symbol_rows = [row for row in rows if str(row["symbol"]) == symbol]
        symbol_pls = [
            float(row.get("net_realized_pl", 0.0))
            for row in symbol_rows
        ]
        symbols[symbol] = {
            "closed_trades": len(symbol_rows),
            "net_realized_pl": float(sum(symbol_pls)),
            "mean_trade_pl": mean(symbol_pls) if symbol_pls else None,
        }
    return {
        "closed_trades": len(rows),
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "win_rate_nonflat_pct": (
            (wins / nonflat) * 100.0 if nonflat else None
        ),
        "net_realized_pl": float(sum(pls)),
        "mean_trade_pl": mean(pls) if pls else None,
        "median_trade_pl": median(pls) if pls else None,
        "entry_spread_points": {
            "count": len(spreads),
            "mean": mean(spreads) if spreads else None,
            "median": median(spreads) if spreads else None,
        },
        "per_symbol": symbols,
    }


def _stage_a_breakdowns(
    trades: Sequence[Mapping[str, Any]],
    folds: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = list(trades)

    fold_rows: dict[str, Any] = {}
    for fold in folds:
        allowed = set(fold["dates"])
        subset = [
            row
            for row in rows
            if _entry_timestamp(row).date().isoformat() in allowed
        ]
        fold_rows[str(fold["label"])] = _trade_stats(subset)

    weekly: dict[str, Any] = {}
    week_labels = sorted(
        {
            (
                _entry_timestamp(row).isocalendar().year,
                _entry_timestamp(row).isocalendar().week,
            )
            for row in rows
        }
    )
    for year, week in week_labels:
        label = f"{year}-W{week:02d}"
        subset = []
        for row in rows:
            stamp = _entry_timestamp(row).isocalendar()
            if stamp.year == year and stamp.week == week:
                subset.append(row)
        weekly[label] = _trade_stats(subset)

    active = []
    off_hours = []
    for row in rows:
        eat = _entry_timestamp(row).tz_convert("Africa/Nairobi")
        if 8 <= eat.hour <= 20:
            active.append(row)
        else:
            off_hours.append(row)

    return {
        "overall": _trade_stats(rows),
        "folds": fold_rows,
        "iso_weeks": weekly,
        "eat_active": {
            **_trade_stats(active),
            "hours": "08:00-20:59 Africa/Nairobi",
            "fold_mean_trade_pl": {
                fold["label"]: _trade_stats(
                    [
                        row
                        for row in active
                        if _entry_timestamp(row).date().isoformat()
                        in set(fold["dates"])
                    ]
                )["mean_trade_pl"]
                for fold in folds
            },
        },
        "eat_off_hours": {
            **_trade_stats(off_hours),
            "hours": "21:00-07:59 Africa/Nairobi",
            "fold_mean_trade_pl": {
                fold["label"]: _trade_stats(
                    [
                        row
                        for row in off_hours
                        if _entry_timestamp(row).date().isoformat()
                        in set(fold["dates"])
                    ]
                )["mean_trade_pl"]
                for fold in folds
            },
        },
    }


def _stage_a_metadata(
    *,
    arm: StageADirectionArm,
    partition: Mapping[str, Any],
    proxy: DirectionFilterBrokerProxy,
) -> dict[str, Any]:
    parameter_payload = asdict(arm.parameters)
    return {
        "milestone": "M023",
        "stage": "A",
        "experiment_id": f"M023-A-{arm.arm_id}",
        "arm_id": arm.arm_id,
        "direction": arm.direction,
        "new_entry_eligibility_only": True,
        "parameters": parameter_payload,
        "parameters_sha256": _canonical_json_sha256(parameter_payload),
        "partition": dict(partition),
        "cost_contract": COST_CONTRACT,
        "session": "all-hours",
        "m15_signal_enabled": False,
        "position_size": 0.1,
        "direction_filter": {
            "rejections_total": proxy.rejections,
            "rejected_by_side": dict(proxy.rejected_by_side),
            "passed_by_side": dict(proxy.passed_by_side),
        },
    }


def _run_stage_a_arm(
    manifest_path: str | Path,
    *,
    arm: StageADirectionArm,
    starting_balance: float = 10_000.0,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if not math.isfinite(starting_balance) or starting_balance <= 0:
        raise ValueError("starting_balance must be finite and positive")

    manifest_file = Path(manifest_path)
    full_dataset = load_mt5_dataset(manifest_file)
    dataset, boundary_clock, dates, folds = slice_stage_a_dataset(full_dataset)
    partition = _partition_metadata(
        manifest_path=manifest_file,
        dataset=dataset,
        dates=dates,
        folds=folds,
    )
    if (
        _datetime_index_sha256(boundary_clock)
        != partition["replay_boundary_sha256"]
    ):
        raise ValueError("M023 Stage-A replay boundary clock hash changed")

    symbols = tuple(config.symbols)
    if float(config.position_size) != 0.1:
        raise ValueError("M023 Stage-A position size must remain exactly 0.1")
    if bool(getattr(config, "use_higher_tf", False)):
        raise ValueError("M023 Stage A requires M15/higher-TF signal disabled")

    with _temporary_research_config(arm.parameters):
        feed = ResearchBoundaryReplayFeed(
            dataset.m1_bars,
            native_timeframe_bars=dataset.native_timeframe_bars,
            ask_m1_bars=dataset.ask_m1_bars,
            boundary_clock=boundary_clock,
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
            balance=float(starting_balance),
            symbol_metadata=dataset.symbol_metadata,
            account_currency=dataset.account_currency,
            execution_costs=execution_costs,
        )
        proxy = DirectionFilterBrokerProxy(
            broker,
            allowed_direction=arm.direction,
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

        strategies = []
        for symbol in symbols:
            strategy = StochasticTripleTFStrategy(
                symbol,
                stochastic_k_period=21,
                stochastic_d_period=7,
                stochastic_slowing=7,
                oversold_level=20.0,
                overbought_level=80.0,
                ema_period=7,
            )
            strategies.append(DirectionStrategyWrapper(strategy, proxy))

        runner = PortfolioBacktestRunner(
            feed,
            broker,
            strategies,
            position_manager=position_manager,
            atr_manager=atr_manager,
            strategy_reporting_enabled=False,
        )
        result = runner.run()
        baseline = build_baseline_report(
            dataset=dataset,
            result=result,
            broker=broker,
            starting_balance=float(starting_balance),
        )
        metadata = _stage_a_metadata(
            arm=arm,
            partition=partition,
            proxy=proxy,
        )
        baseline["research"] = metadata
        baseline["cost_assumptions"]["m023_contract"] = COST_CONTRACT
        baseline["cost_assumptions"]["historical_spread"] = (
            "native Bid M1 + tick-derived Ask M1"
        )
        baseline["configuration"]["m1_boundaries"] = {
            "oversold": 20.0,
            "overbought": 80.0,
        }
        baseline["configuration"]["ema_entry_period"] = 7
        baseline["configuration"]["decision_spread_max_points"] = None
        baseline["configuration"]["session_filter"] = "all-hours"
        baseline["configuration"]["entry_direction"] = arm.direction
        baseline["configuration"]["m15_signal_enabled"] = False

        diagnostic = build_diagnostic_report(
            baseline_report=baseline,
            broker=broker,
            result=result,
        )
        diagnostic["research"] = metadata

    trades = diagnostic["trades"]
    breakdowns = _stage_a_breakdowns(trades, folds)
    aggregate = baseline["aggregate"]
    per_symbol = {}
    for symbol in symbols:
        base = dict(baseline["per_symbol"][symbol])
        detail = breakdowns["overall"]["per_symbol"].get(
            symbol,
            {
                "closed_trades": 0,
                "net_realized_pl": 0.0,
                "mean_trade_pl": None,
            },
        )
        base["mean_trade_pl"] = detail["mean_trade_pl"]
        per_symbol[symbol] = base

    side_rows = diagnostic["analysis"]["by_side"]
    accepted_buy = int(proxy.passed_by_side["BUY"])
    accepted_sell = int(proxy.passed_by_side["SELL"])
    direction_invariants = {
        "buy_accepted_entries": accepted_buy,
        "sell_accepted_entries": accepted_sell,
        "opposite_side_accepted_entries": (
            accepted_buy
            if arm.direction == "SELL"
            else accepted_sell
            if arm.direction == "BUY"
            else 0
        ),
    }

    summary = {
        "milestone": "M023",
        "stage": "A",
        "experiment_id": f"M023-A-{arm.arm_id}",
        "arm_id": arm.arm_id,
        "direction": arm.direction,
        "parameters": asdict(arm.parameters),
        "partition": partition,
        "cost_contract": COST_CONTRACT,
        "aggregate": aggregate,
        "per_symbol": per_symbol,
        "by_side": side_rows,
        "folds": breakdowns["folds"],
        "iso_weeks": breakdowns["iso_weeks"],
        "eat_active": breakdowns["eat_active"],
        "eat_off_hours": breakdowns["eat_off_hours"],
        "direction_filter": metadata["direction_filter"],
        "direction_invariants": direction_invariants,
        "entry_spread_diagnostics": {
            "overall": breakdowns["overall"]["entry_spread_points"],
            "by_outcome": diagnostic["analysis"]["spread_by_outcome"],
        },
        "exit_type_diagnostics": diagnostic["analysis"]["by_exit_reason"],
        "tp_safety": _tp_safety(diagnostic),
        "remaining_positions": baseline["remaining_positions"],
        "source_date_replay_hashes": {
            "source_manifest_sha256": partition["source_manifest_sha256"],
            "date_list_sha256": partition["date_list_sha256"],
            "partition_spec_sha256": partition["partition_spec_sha256"],
            "replay_boundary_sha256": partition["replay_boundary_sha256"],
        },
        "safety": {
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
            "session_filter_applied": False,
            "weekday_filter_applied": False,
        },
    }
    return baseline, diagnostic, summary


def write_summary(report: Mapping[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def run_stage_a_pair(
    manifest_path: str | Path,
    *,
    arm_id: str,
    output_dir: str | Path,
    starting_balance: float = 10_000.0,
) -> dict[str, Any]:
    """Run deterministic A/B for one exact Stage-A arm only."""

    arm = stage_a_arm(arm_id)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    runs = []
    for label in ("a", "b"):
        baseline, diagnostic, summary = _run_stage_a_arm(
            manifest_path,
            arm=arm,
            starting_balance=starting_balance,
        )
        prefix = f"M023-A-{arm.arm_id}-{label}"
        baseline_path = write_baseline_report(
            baseline,
            root / f"{prefix}-baseline.json",
        )
        baseline_sha = _sha256_path(baseline_path)
        diagnostic["source_baseline_sha256"] = baseline_sha
        diagnostic_path = write_diagnostic_report(
            diagnostic,
            root / f"{prefix}-diagnostic.json",
        )
        summary_path = write_summary(
            summary,
            root / f"{prefix}-summary.json",
        )
        runs.append(
            {
                "label": label,
                "baseline_path": str(baseline_path),
                "baseline_sha256": baseline_sha,
                "diagnostic_path": str(diagnostic_path),
                "diagnostic_sha256": _sha256_path(diagnostic_path),
                "summary_path": str(summary_path),
                "summary_sha256": _sha256_path(summary_path),
                "summary": summary,
            }
        )

    deterministic = all(
        runs[0][field] == runs[1][field]
        for field in (
            "baseline_sha256",
            "diagnostic_sha256",
            "summary_sha256",
        )
    )
    return {
        "ok": bool(deterministic),
        "milestone": "M023",
        "stage": "A",
        "arm_id": arm.arm_id,
        "direction": arm.direction,
        "parameters": asdict(arm.parameters),
        "deterministic": deterministic,
        "a": runs[0],
        "b": runs[1],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one frozen M023 Stage-A causal direction arm pair."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--arm",
        choices=tuple(STAGE_A_DIRECTIONS),
        required=True,
    )
    parser.add_argument("--starting-balance", type=float, default=10_000.0)
    args = parser.parse_args(argv)

    result = run_stage_a_pair(
        args.manifest,
        arm_id=args.arm,
        output_dir=args.output_dir,
        starting_balance=args.starting_balance,
    )
    compact = {
        "ok": result["ok"],
        "milestone": result["milestone"],
        "stage": result["stage"],
        "arm_id": result["arm_id"],
        "direction": result["direction"],
        "parameters": result["parameters"],
        "deterministic": result["deterministic"],
        "baseline_sha256": result["a"]["baseline_sha256"],
        "diagnostic_sha256": result["a"]["diagnostic_sha256"],
        "summary_sha256": result["a"]["summary_sha256"],
        "summary_path": result["a"]["summary_path"],
    }
    print(json.dumps(compact, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
