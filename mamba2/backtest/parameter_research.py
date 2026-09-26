"""M022 deterministic parameter-research harness.

This module is research-only.  It reuses the accepted replay broker, position
manager, diagnostics, and production strategy while keeping M022's chronological
partitions and parameter grids explicit.

Phase-1 callers must use the development partition only.  Validation and
historical holdout remain mechanically unavailable through the Phase-1 CLI.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

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
from .mt5_dataset import LoadedHistoricalDataset, load_mt5_dataset
from .runner import PortfolioBacktestRunner


M022_SOURCE_MANIFEST_SHA256 = (
    "143274a42cd5a1904202fa86a045d8b6fb61561709e1d8f305ded1a9b6ba1558"
)
M022_COMMON_TRADING_DATES_SHA256 = (
    "2efcd016d0d346036a33415e794903b5fea86ad610519fbda056ceb2c94feac5"
)

M022_PARTITIONS: Mapping[str, tuple[str, str, int]] = {
    "development": (
        "2025-08-25T00:00:00Z",
        "2026-04-21T00:00:00Z",
        169,
    ),
    "validation": (
        "2026-04-21T00:00:00Z",
        "2026-07-08T00:00:00Z",
        56,
    ),
    "historical_holdout": (
        "2026-07-08T00:00:00Z",
        "2026-09-25T00:00:00Z",
        57,
    ),
}

REFERENCE_STOCHASTIC = (21, 7, 7)
REFERENCE_BOUNDARIES = (20.0, 80.0)
REFERENCE_EMA_PERIOD = 7
REFERENCE_ATR = (1.0, 2.0)

PHASE1_STOCHASTIC_TUPLES = (
    (9, 3, 3),
    (10, 4, 4),
    (10, 6, 6),
    (14, 3, 3),
    (14, 5, 5),
    (14, 7, 7),
    (21, 5, 5),
    (21, 7, 7),
    (28, 7, 7),
)
PHASE1_BOUNDARIES = ((15.0, 85.0), (20.0, 80.0), (25.0, 75.0))
PHASE1_EMA_PERIODS = (5, 7, 9, 12)
PHASE1_SPREAD_POINTS = (None, 5.0, 8.0, 10.0, 12.0, 15.0)
PHASE1_ATR_SL = (0.75, 1.0, 1.25, 1.5)
PHASE1_ATR_TP = (1.0, 1.5, 2.0, 2.5, 3.0)
PHASE1_SESSION_VARIANTS = ("all-hours", "block-00-04-utc")

COST_CONTRACT = (
    "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
    "SWAP-UNMODELED"
)


@dataclass(frozen=True)
class Phase1Parameters:
    """One fully specified M022 Phase-1 arm."""

    stochastic_k_period: int = 21
    stochastic_d_period: int = 7
    stochastic_slowing: int = 7
    oversold_level: float = 20.0
    overbought_level: float = 80.0
    ema_period: int = 7
    decision_spread_max_points: float | None = None
    atr_sl_multiplier: float = 1.0
    atr_tp_multiplier: float = 2.0
    block_00_04_utc: bool = False

    def __post_init__(self) -> None:
        if min(
            self.stochastic_k_period,
            self.stochastic_d_period,
            self.stochastic_slowing,
            self.ema_period,
        ) < 1:
            raise ValueError("period parameters must be positive")
        if not 0 <= self.oversold_level < self.overbought_level <= 100:
            raise ValueError("stochastic boundaries are invalid")
        if (
            self.decision_spread_max_points is not None
            and self.decision_spread_max_points < 0
        ):
            raise ValueError("decision spread threshold cannot be negative")
        if self.atr_sl_multiplier <= 0 or self.atr_tp_multiplier <= 0:
            raise ValueError("ATR multipliers must be positive")


@dataclass(frozen=True)
class Phase1Arm:
    """Metadata + parameterization for one controlled Phase-1 arm."""

    experiment_id: str
    family: str
    value_label: str
    parameters: Phase1Parameters


class DecisionSpreadBrokerProxy:
    """Reject new orders using only decision-time observable Bid/Ask."""

    RESEARCH_REJECT_CODE = 10030

    def __init__(self, broker: Any, *, max_points: float):
        self.broker = broker
        self.max_points = float(max_points)
        self.rejections = 0
        self.accepted_checks = 0
        self.observations: list[dict[str, Any]] = []

    def order_send(self, request: dict[str, Any]) -> dict[str, Any]:
        symbol = str(request.get("symbol") or "")
        tick = self.broker.symbol_info_tick(symbol)
        point = float(self.broker.get_point_size(symbol))
        bid = float(tick["bid"])
        ask = float(tick["ask"])
        spread_points = (ask - bid) / point if point > 0 else math.inf
        rejected = spread_points > self.max_points
        self.observations.append(
            {
                "symbol": symbol,
                "bid": bid,
                "ask": ask,
                "spread_points": spread_points,
                "rejected": rejected,
            }
        )
        if rejected:
            self.rejections += 1
            return {
                "retcode": self.RESEARCH_REJECT_CODE,
                "order": 0,
                "price": float(request.get("price", 0.0)),
                "comment": (
                    "M022 research decision-spread rejection "
                    f"({spread_points:.10f} > {self.max_points:.10f})"
                ),
            }
        self.accepted_checks += 1
        return self.broker.order_send(request)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.broker, name)


class ResearchStrategyWrapper:
    """Apply optional session/spread filters without changing production code."""

    def __init__(
        self,
        strategy: Any,
        *,
        block_00_04_utc: bool,
        decision_spread_max_points: float | None,
    ):
        self.strategy = strategy
        self.symbol = strategy.symbol
        self.block_00_04_utc = bool(block_00_04_utc)
        self.decision_spread_max_points = decision_spread_max_points
        self.blocked_evaluation_boundaries = 0
        self.spread_rejections = 0
        self.spread_accepted_checks = 0

    @staticmethod
    def _utc_timestamp(value: Any) -> pd.Timestamp:
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
        return timestamp.tz_convert("UTC")

    async def evaluate(self, market: dict[str, Any]) -> None:
        current = getattr(market["rate_fetcher"], "current_time", None)
        if self.block_00_04_utc and current is not None:
            if self._utc_timestamp(current).hour < 4:
                self.blocked_evaluation_boundaries += 1
                return

        if self.decision_spread_max_points is None:
            await self.strategy.evaluate(market)
            return

        proxy = DecisionSpreadBrokerProxy(
            market["broker"],
            max_points=float(self.decision_spread_max_points),
        )
        await self.strategy.evaluate({**market, "broker": proxy})
        self.spread_rejections += proxy.rejections
        self.spread_accepted_checks += proxy.accepted_checks


def _utc(value: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _iso(value: str | pd.Timestamp) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _datetime_index_sha256(index: pd.DatetimeIndex) -> str:
    payload = "\n".join(_iso(value) for value in index).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _strict_common_boundary_clock(
    m1_bars: Mapping[str, pd.DataFrame],
    ask_m1_bars: Mapping[str, pd.DataFrame],
    *,
    end_exclusive: pd.Timestamp,
) -> pd.DatetimeIndex:
    """Return replay boundaries with same-boundary data for every symbol.

    Each interior boundary T requires both the completed M1 open T-1 and the
    execution M1 open T to exist for every Bid/Ask symbol. The partition-close
    boundary is retained when T-1 is common so the final scored M1 bar can be
    processed without introducing an out-of-partition execution bar.
    """

    common_opens: pd.DatetimeIndex | None = None
    for symbol in sorted(m1_bars):
        if symbol not in ask_m1_bars:
            raise ValueError(f"missing Ask M1 history for {symbol}")
        symbol_opens = m1_bars[symbol].index.intersection(
            ask_m1_bars[symbol].index
        )
        common_opens = (
            symbol_opens
            if common_opens is None
            else common_opens.intersection(symbol_opens)
        )

    if common_opens is None or common_opens.empty:
        raise ValueError("M022 partition has no common Bid/Ask M1 opens")
    common_opens = common_opens.sort_values()

    one_minute = pd.Timedelta(minutes=1)
    interior = common_opens.intersection(common_opens + one_minute)
    boundary_clock = interior.sort_values()

    final_completed_open = end_exclusive - one_minute
    if final_completed_open in common_opens:
        boundary_clock = boundary_clock.union(
            pd.DatetimeIndex([end_exclusive])
        ).sort_values()

    if boundary_clock.empty:
        raise ValueError("M022 partition has no strict common replay boundaries")
    return boundary_clock


class ResearchBoundaryReplayFeed(ReplayFeed):
    """Replay full symbol histories on a prevalidated research boundary clock."""

    def __init__(
        self,
        bars: Mapping[str, pd.DataFrame],
        *,
        native_timeframe_bars: Mapping[
            str, Mapping[str | int, pd.DataFrame]
        ] | None,
        ask_m1_bars: Mapping[str, pd.DataFrame],
        boundary_clock: pd.DatetimeIndex,
    ):
        super().__init__(
            bars,
            native_timeframe_bars=native_timeframe_bars,
            ask_m1_bars=ask_m1_bars,
        )
        clock = pd.DatetimeIndex(
            pd.to_datetime(boundary_clock, utc=True),
            name="time",
        )
        if clock.empty:
            raise ValueError("research boundary clock cannot be empty")
        if clock.has_duplicates or not clock.is_monotonic_increasing:
            raise ValueError(
                "research boundary clock must be unique and chronological"
            )
        self._timeline = clock
        self._position = -1


def _slice_frame(
    frame: pd.DataFrame,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    sliced = frame.loc[(frame.index >= start) & (frame.index < end)].copy()
    if sliced.empty:
        raise ValueError(
            f"partition slice produced no rows for {_iso(start)} -> {_iso(end)}"
        )
    return sliced


def slice_dataset(
    dataset: LoadedHistoricalDataset,
    *,
    partition: str,
) -> LoadedHistoricalDataset:
    """Return a strict in-memory dataset view with no post-partition bars."""

    if partition not in M022_PARTITIONS:
        raise ValueError(f"unknown M022 partition: {partition}")
    start_raw, end_raw, _count = M022_PARTITIONS[partition]
    start = _utc(start_raw)
    end = _utc(end_raw)

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
            raise ValueError(
                f"partition Bid/Ask M1 index mismatch for {symbol}"
            )

    # Preserve every genuine per-symbol M1 bar for stochastic/EMA/ATR state.
    # Only the portfolio replay clock is synchronized. This keeps the accepted
    # same-boundary currency-conversion rule without forward-filling sparse
    # conversion data or deleting legitimate signal-history bars.
    boundary_clock = _strict_common_boundary_clock(
        m1,
        ask,
        end_exclusive=end,
    )

    manifest = dict(dataset.manifest)
    manifest["requested_range"] = {
        "from_utc": _iso(start),
        "to_utc": _iso(end),
    }
    manifest["m022_partition"] = partition
    manifest["m022_source_manifest_sha256"] = M022_SOURCE_MANIFEST_SHA256
    manifest["m022_strict_common_boundary_clock"] = True
    manifest["m022_full_symbol_m1_preserved"] = True
    manifest["m022_replay_boundary_count"] = int(len(boundary_clock))
    manifest["m022_replay_boundary_first_utc"] = _iso(boundary_clock[0])
    manifest["m022_replay_boundary_last_utc"] = _iso(boundary_clock[-1])
    manifest["m022_replay_boundary_sha256"] = _datetime_index_sha256(
        boundary_clock
    )

    return LoadedHistoricalDataset(
        m1_bars=m1,
        native_timeframe_bars=native,
        ask_m1_bars=ask,
        symbol_metadata=dataset.symbol_metadata,
        account_currency=dataset.account_currency,
        manifest=manifest,
    )


@contextlib.contextmanager
def _temporary_research_config(
    parameters: Phase1Parameters,
) -> Iterator[None]:
    """Temporarily expose research values to accepted replay components."""

    names = (
        "stochastic_k_period",
        "stochastic_d_period",
        "stochastic_slowing",
        "atr_sl_multiplier",
        "atr_tp_multiplier",
    )
    original = {name: getattr(config, name) for name in names}
    try:
        config.stochastic_k_period = int(parameters.stochastic_k_period)
        config.stochastic_d_period = int(parameters.stochastic_d_period)
        config.stochastic_slowing = int(parameters.stochastic_slowing)
        config.atr_sl_multiplier = float(parameters.atr_sl_multiplier)
        config.atr_tp_multiplier = float(parameters.atr_tp_multiplier)
        yield
    finally:
        for name, value in original.items():
            setattr(config, name, value)


def _partition_metadata(
    *,
    manifest_path: Path,
    partition: str,
    dataset: LoadedHistoricalDataset,
) -> dict[str, Any]:
    start, end, count = M022_PARTITIONS[partition]
    source_manifest_sha = _sha256_path(manifest_path)
    if source_manifest_sha != M022_SOURCE_MANIFEST_SHA256:
        raise ValueError(
            "M022 source manifest hash changed: "
            f"{source_manifest_sha} != {M022_SOURCE_MANIFEST_SHA256}"
        )
    specification = {
        "source_manifest_sha256": source_manifest_sha,
        "common_trading_dates_sha256": M022_COMMON_TRADING_DATES_SHA256,
        "partition": partition,
        "start_utc": start,
        "end_exclusive_utc": end,
        "common_trading_dates": count,
        "strict_common_boundary_clock": bool(
            dataset.manifest.get("m022_strict_common_boundary_clock")
        ),
        "full_symbol_m1_preserved": bool(
            dataset.manifest.get("m022_full_symbol_m1_preserved")
        ),
        "replay_boundary_count": int(
            dataset.manifest.get("m022_replay_boundary_count", 0)
        ),
        "replay_boundary_first_utc": dataset.manifest.get(
            "m022_replay_boundary_first_utc"
        ),
        "replay_boundary_last_utc": dataset.manifest.get(
            "m022_replay_boundary_last_utc"
        ),
        "replay_boundary_sha256": dataset.manifest.get(
            "m022_replay_boundary_sha256"
        ),
    }
    return {
        **specification,
        "partition_spec_sha256": _canonical_json_sha256(specification),
    }


def _tp_safety(diagnostic_report: Mapping[str, Any]) -> dict[str, int]:
    trades = diagnostic_report.get("trades", [])
    negative_take_profit_exits = sum(
        row.get("exit_reason") == "take_profit"
        and float(row.get("net_realized_pl", 0.0)) < 0
        for row in trades
    )
    wrong_side_initial_targets = 0
    for row in trades:
        protection = row.get("initial_protection")
        if not protection:
            continue
        entry = float(row["entry_price"])
        tp_value = protection.get("applied_tp", protection.get("new_tp"))
        if tp_value is None:
            continue
        tp = float(tp_value)
        side = str(row["side"]).upper()
        if (side == "BUY" and tp <= entry) or (side == "SELL" and tp >= entry):
            wrong_side_initial_targets += 1
    return {
        "negative_pl_take_profit_exits": int(negative_take_profit_exits),
        "wrong_side_initial_tp": int(wrong_side_initial_targets),
    }


def _research_metadata(
    *,
    arm: Phase1Arm,
    partition: Mapping[str, Any],
    wrappers: Sequence[ResearchStrategyWrapper],
) -> dict[str, Any]:
    parameter_payload = asdict(arm.parameters)
    return {
        "milestone": "M022",
        "phase": 1,
        "experiment_id": arm.experiment_id,
        "family": arm.family,
        "value_label": arm.value_label,
        "parameters": parameter_payload,
        "parameters_sha256": _canonical_json_sha256(parameter_payload),
        "partition": dict(partition),
        "cost_contract": COST_CONTRACT,
        "rejections": {
            "decision_spread": int(
                sum(wrapper.spread_rejections for wrapper in wrappers)
            ),
            "session_evaluation_boundaries": int(
                sum(
                    wrapper.blocked_evaluation_boundaries
                    for wrapper in wrappers
                )
            ),
        },
    }


def run_phase1_arm(
    manifest_path: str | Path,
    *,
    arm: Phase1Arm,
    partition: str = "development",
    starting_balance: float = 10_000.0,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run one M022 arm on a strict partition.

    Phase 1 is intentionally restricted to development.  Validation/holdout
    execution requires a later, separately frozen shortlist workflow.
    """

    if partition != "development":
        raise ValueError(
            "Phase-1 arm runner is development-only; validation/holdout remain closed"
        )
    manifest_file = Path(manifest_path)
    full_dataset = load_mt5_dataset(manifest_file)
    dataset = slice_dataset(full_dataset, partition=partition)
    partition_meta = _partition_metadata(
        manifest_path=manifest_file,
        partition=partition,
        dataset=dataset,
    )
    symbols = tuple(config.symbols)

    wrappers: list[ResearchStrategyWrapper] = []
    with _temporary_research_config(arm.parameters):
        end_exclusive = _utc(M022_PARTITIONS[partition][1])
        boundary_clock = _strict_common_boundary_clock(
            dataset.m1_bars,
            dataset.ask_m1_bars,
            end_exclusive=end_exclusive,
        )
        if (
            _datetime_index_sha256(boundary_clock)
            != partition_meta["replay_boundary_sha256"]
        ):
            raise ValueError("M022 replay boundary clock hash changed")
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
                stochastic_k_period=arm.parameters.stochastic_k_period,
                stochastic_d_period=arm.parameters.stochastic_d_period,
                stochastic_slowing=arm.parameters.stochastic_slowing,
                oversold_level=arm.parameters.oversold_level,
                overbought_level=arm.parameters.overbought_level,
                ema_period=arm.parameters.ema_period,
            )
            wrapper = ResearchStrategyWrapper(
                strategy,
                block_00_04_utc=arm.parameters.block_00_04_utc,
                decision_spread_max_points=(
                    arm.parameters.decision_spread_max_points
                ),
            )
            wrappers.append(wrapper)
            strategies.append(wrapper)

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
            starting_balance=float(starting_balance),
        )
        metadata = _research_metadata(
            arm=arm,
            partition=partition_meta,
            wrappers=wrappers,
        )
        baseline_report["research"] = metadata
        baseline_report["cost_assumptions"]["m022_contract"] = COST_CONTRACT
        baseline_report["cost_assumptions"]["historical_spread"] = (
            "native Bid M1 + tick-derived Ask M1"
        )
        baseline_report["configuration"]["m1_boundaries"] = {
            "oversold": float(arm.parameters.oversold_level),
            "overbought": float(arm.parameters.overbought_level),
        }
        baseline_report["configuration"]["ema_entry_period"] = int(
            arm.parameters.ema_period
        )
        baseline_report["configuration"]["decision_spread_max_points"] = (
            None
            if arm.parameters.decision_spread_max_points is None
            else float(arm.parameters.decision_spread_max_points)
        )
        baseline_report["configuration"]["block_00_04_utc"] = bool(
            arm.parameters.block_00_04_utc
        )

        diagnostic_report = build_diagnostic_report(
            baseline_report=baseline_report,
            broker=broker,
            result=result,
        )
        diagnostic_report["research"] = metadata

    analysis = diagnostic_report["analysis"]
    aggregate = baseline_report["aggregate"]
    summary = {
        "experiment_id": arm.experiment_id,
        "family": arm.family,
        "value_label": arm.value_label,
        "parameters": asdict(arm.parameters),
        "partition": partition_meta,
        "cost_contract": COST_CONTRACT,
        "aggregate": aggregate,
        "per_symbol": baseline_report["per_symbol"],
        "by_side": analysis["by_side"],
        "by_entry_utc_bucket": analysis["by_entry_utc_bucket"],
        "protection": analysis["protection"],
        "rejections": baseline_report["research"]["rejections"],
        "tp_safety": _tp_safety(diagnostic_report),
        "remaining_positions": baseline_report["remaining_positions"],
    }
    return baseline_report, diagnostic_report, summary


def write_summary(report: Mapping[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def run_phase1_pair(
    manifest_path: str | Path,
    *,
    arm: Phase1Arm,
    output_dir: str | Path,
    starting_balance: float = 10_000.0,
) -> dict[str, Any]:
    """Run deterministic A/B copies of one arm and require byte identity."""

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    runs = []
    for label in ("a", "b"):
        baseline, diagnostic, summary = run_phase1_arm(
            manifest_path,
            arm=arm,
            partition="development",
            starting_balance=starting_balance,
        )
        baseline_path = write_baseline_report(
            baseline,
            root / f"{arm.experiment_id}-{label}-baseline.json",
        )
        baseline_sha = _sha256_path(baseline_path)
        diagnostic["source_baseline_sha256"] = baseline_sha
        diagnostic_path = write_diagnostic_report(
            diagnostic,
            root / f"{arm.experiment_id}-{label}-diagnostic.json",
        )
        summary_path = write_summary(
            summary,
            root / f"{arm.experiment_id}-{label}-summary.json",
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
        "experiment_id": arm.experiment_id,
        "family": arm.family,
        "value_label": arm.value_label,
        "parameters": asdict(arm.parameters),
        "partition": "development",
        "deterministic": deterministic,
        "a": runs[0],
        "b": runs[1],
    }


def stochastic_arm(k: int, d: int, slowing: int) -> Phase1Arm:
    params = Phase1Parameters(
        stochastic_k_period=int(k),
        stochastic_d_period=int(d),
        stochastic_slowing=int(slowing),
    )
    return Phase1Arm(
        experiment_id=f"M022-P1-STOCH-{k}-{d}-{slowing}",
        family="stochastic",
        value_label=f"{k}/{d}/{slowing}",
        parameters=params,
    )


def reference_arm() -> Phase1Arm:
    return Phase1Arm(
        experiment_id="M022-P1-REFERENCE",
        family="reference",
        value_label="21/7/7-20/80-ema7-no-spread-gate-atr1x2-all-hours",
        parameters=Phase1Parameters(),
    )


def boundary_arm(oversold: float, overbought: float) -> Phase1Arm:
    pair = (float(oversold), float(overbought))
    if pair not in PHASE1_BOUNDARIES:
        raise ValueError("boundary pair is outside the frozen M022 grid")
    params = Phase1Parameters(
        oversold_level=pair[0],
        overbought_level=pair[1],
    )
    return Phase1Arm(
        experiment_id=f"M022-P1-BOUND-{int(pair[0])}-{int(pair[1])}",
        family="boundaries",
        value_label=f"{int(pair[0])}/{int(pair[1])}",
        parameters=params,
    )


def ema_arm(period: int) -> Phase1Arm:
    period = int(period)
    if period not in PHASE1_EMA_PERIODS:
        raise ValueError("EMA period is outside the frozen M022 grid")
    params = Phase1Parameters(ema_period=period)
    return Phase1Arm(
        experiment_id=f"M022-P1-EMA-{period}",
        family="ema",
        value_label=str(period),
        parameters=params,
    )


def spread_arm(max_points: float | None) -> Phase1Arm:
    normalized = None if max_points is None else float(max_points)
    if normalized not in PHASE1_SPREAD_POINTS:
        raise ValueError("spread threshold is outside the frozen M022 grid")
    params = Phase1Parameters(decision_spread_max_points=normalized)
    label = "none" if normalized is None else f"{normalized:g}"
    return Phase1Arm(
        experiment_id=f"M022-P1-SPREAD-{label}",
        family="spread",
        value_label=label,
        parameters=params,
    )


def atr_sl_arm(multiplier: float) -> Phase1Arm:
    multiplier = float(multiplier)
    if multiplier not in PHASE1_ATR_SL:
        raise ValueError("ATR SL multiplier is outside the frozen M022 grid")
    params = Phase1Parameters(atr_sl_multiplier=multiplier)
    return Phase1Arm(
        experiment_id=f"M022-P1-ATR-SL-{multiplier:g}",
        family="atr-sl",
        value_label=f"{multiplier:g}",
        parameters=params,
    )


def atr_tp_arm(multiplier: float) -> Phase1Arm:
    multiplier = float(multiplier)
    if multiplier not in PHASE1_ATR_TP:
        raise ValueError("ATR TP multiplier is outside the frozen M022 grid")
    params = Phase1Parameters(atr_tp_multiplier=multiplier)
    return Phase1Arm(
        experiment_id=f"M022-P1-ATR-TP-{multiplier:g}",
        family="atr-tp",
        value_label=f"{multiplier:g}",
        parameters=params,
    )


def session_arm(variant: str) -> Phase1Arm:
    if variant not in PHASE1_SESSION_VARIANTS:
        raise ValueError("session variant is outside the frozen M022 grid")
    params = Phase1Parameters(
        block_00_04_utc=variant == "block-00-04-utc"
    )
    return Phase1Arm(
        experiment_id=(
            "M022-P1-SESSION-ALL"
            if variant == "all-hours"
            else "M022-P1-SESSION-BLOCK-00-04"
        ),
        family="session",
        value_label=variant,
        parameters=params,
    )


def _require_value(args: argparse.Namespace, description: str) -> str:
    if not args.value:
        raise ValueError(f"{args.family} family requires --value {description}")
    return args.value


def _arm_from_cli(args: argparse.Namespace) -> Phase1Arm:
    if args.family == "reference":
        return reference_arm()

    if args.family == "stochastic":
        raw = _require_value(args, "K/D/S")
        parts = tuple(int(item) for item in raw.split("/"))
        if len(parts) != 3:
            raise ValueError("stochastic --value must be K/D/S")
        if parts not in PHASE1_STOCHASTIC_TUPLES:
            raise ValueError("stochastic tuple is outside the frozen M022 grid")
        return stochastic_arm(*parts)

    if args.family == "boundaries":
        raw = _require_value(args, "LOW/HIGH")
        parts = tuple(float(item) for item in raw.split("/"))
        if len(parts) != 2:
            raise ValueError("boundaries --value must be LOW/HIGH")
        return boundary_arm(*parts)

    if args.family == "ema":
        return ema_arm(int(_require_value(args, "PERIOD")))

    if args.family == "spread":
        raw = _require_value(args, "none|POINTS").strip().lower()
        return spread_arm(None if raw == "none" else float(raw))

    if args.family == "atr-sl":
        return atr_sl_arm(float(_require_value(args, "MULTIPLIER")))

    if args.family == "atr-tp":
        return atr_tp_arm(float(_require_value(args, "MULTIPLIER")))

    if args.family == "session":
        return session_arm(_require_value(args, "VARIANT"))

    raise ValueError(f"unsupported Phase-1 family: {args.family}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic M022 Phase-1 development-only arm pairs."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--family",
        choices=(
            "reference",
            "stochastic",
            "boundaries",
            "ema",
            "spread",
            "atr-sl",
            "atr-tp",
            "session",
        ),
        required=True,
    )
    parser.add_argument("--value")
    parser.add_argument("--starting-balance", type=float, default=10_000.0)
    args = parser.parse_args(argv)

    arm = _arm_from_cli(args)
    result = run_phase1_pair(
        args.manifest,
        arm=arm,
        output_dir=args.output_dir,
        starting_balance=args.starting_balance,
    )
    compact = {
        "ok": result["ok"],
        "experiment_id": result["experiment_id"],
        "family": result["family"],
        "value_label": result["value_label"],
        "parameters": result["parameters"],
        "partition": result["partition"],
        "deterministic": result["deterministic"],
        "baseline_sha256": result["a"]["baseline_sha256"],
        "diagnostic_sha256": result["a"]["diagnostic_sha256"],
        "summary_sha256": result["a"]["summary_sha256"],
        "summary": result["a"]["summary"],
    }
    print(json.dumps(compact, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
