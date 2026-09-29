"""M023 Stage-B causal BUY-only session research.

Research-only session entry filters over the already-seen 225-date sample.
Production strategy/defaults are unchanged. Historical holdout execution is
not exposed.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path
from typing import Any, Mapping, Sequence
from zoneinfo import TZPATH, ZoneInfo

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
from .m023_direction_research import (
    P2_08_PARAMETERS,
    DirectionFilterBrokerProxy,
    DirectionStrategyWrapper,
    _partition_metadata,
    _stage_a_breakdowns,
    _tp_safety,
    slice_stage_a_dataset,
)
from .mt5_dataset import load_mt5_dataset
from .parameter_research import COST_CONTRACT, ResearchBoundaryReplayFeed, _sha256_path
from .runner import PortfolioBacktestRunner


EAT = ZoneInfo("Africa/Nairobi")


@dataclass(frozen=True)
class StageBSession:
    arm_id: str
    label: str
    start_hour: int | None
    end_hour: int | None

    @property
    def all_hours(self) -> bool:
        return self.start_hour is None and self.end_hour is None

    def allows(self, timestamp: Any) -> bool:
        if self.all_hours:
            return True
        if timestamp is None:
            raise ValueError("Stage-B session check requires replay timestamp")
        localized = timestamp.tz_convert(EAT)
        return bool(self.start_hour <= localized.hour <= self.end_hour)

    @property
    def duration_hours(self) -> int:
        if self.all_hours:
            return 24
        return int(self.end_hour - self.start_hour + 1)


STAGE_B_SESSIONS: Mapping[str, StageBSession] = {
    "S-R": StageBSession("S-R", "ALL-HOURS", None, None),
    "S-ACTIVE": StageBSession("S-ACTIVE", "EAT-ACTIVE", 8, 20),
    "S-MORNING": StageBSession("S-MORNING", "EAT-MORNING", 8, 11),
    "S-MIDDAY": StageBSession("S-MIDDAY", "EAT-MIDDAY", 12, 14),
    "S-AFTERNOON": StageBSession("S-AFTERNOON", "EAT-AFTERNOON", 15, 17),
}


class SessionFilterBrokerProxy:
    """Suppress only new BUY entries outside the frozen Stage-B session."""

    RESEARCH_REJECT_CODE = 10032

    def __init__(
        self,
        direction_proxy: DirectionFilterBrokerProxy,
        *,
        feed: Any,
        session: StageBSession,
    ):
        self.direction_proxy = direction_proxy
        self.feed = feed
        self.session = session
        self.rejections = 0
        self.passed = 0

    def order_send(self, request: dict[str, Any]) -> dict[str, Any]:
        side = DirectionFilterBrokerProxy._side(request)
        # Direction remains BUY-only independently of session membership.
        if side != "BUY":
            return self.direction_proxy.order_send(request)

        if not self.session.allows(self.feed.current_time):
            self.rejections += 1
            return {
                "retcode": self.RESEARCH_REJECT_CODE,
                "order": 0,
                "price": float(request.get("price", 0.0)),
                "comment": (
                    f"M023 Stage-B session rejection: BUY outside "
                    f"{self.session.label}"
                ),
            }

        self.passed += 1
        return self.direction_proxy.order_send(request)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.direction_proxy, name)


class SessionStrategyWrapper:
    """Expose the session+BUY-only broker only to strategy entry evaluation."""

    def __init__(self, strategy: Any, proxy: SessionFilterBrokerProxy):
        self.strategy = strategy
        self.proxy = proxy
        self.symbol = strategy.symbol

    async def evaluate(self, market: dict[str, Any]) -> None:
        await self.strategy.evaluate({**market, "broker": self.proxy})


def stage_b_session(arm_id: str) -> StageBSession:
    try:
        return STAGE_B_SESSIONS[arm_id]
    except KeyError as exc:
        raise ValueError("arm is outside the frozen M023 Stage-B matrix") from exc


def _tzdata_version() -> str | None:
    try:
        return metadata.version("tzdata")
    except metadata.PackageNotFoundError:
        return None


def _session_filter_trades(
    trades: Sequence[Mapping[str, Any]],
    session: StageBSession,
) -> list[Mapping[str, Any]]:
    if session.all_hours:
        return list(trades)
    rows = []
    for row in trades:
        import pandas as pd

        timestamp = pd.Timestamp(str(row["entry_time_utc"]))
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        if session.allows(timestamp):
            rows.append(row)
    return rows


def _reference_windows(
    trades: Sequence[Mapping[str, Any]],
    folds: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Descriptive S-R same-window slices for representation denominators."""

    result = {}
    for arm_id in ("S-ACTIVE", "S-MORNING", "S-MIDDAY", "S-AFTERNOON"):
        session = stage_b_session(arm_id)
        sliced = _session_filter_trades(trades, session)
        breakdown = _stage_a_breakdowns(sliced, folds)
        result[arm_id] = {
            "session": {
                "label": session.label,
                "timezone": "Africa/Nairobi",
                "start_hour": session.start_hour,
                "end_hour": session.end_hour,
                "duration_hours": session.duration_hours,
            },
            "overall": breakdown["overall"],
            "folds": breakdown["folds"],
            "iso_weeks": breakdown["iso_weeks"],
        }
    return result


def _run_stage_b_arm(
    manifest_path: str | Path,
    *,
    arm_id: str,
    starting_balance: float = 10_000.0,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if not math.isfinite(starting_balance) or starting_balance <= 0:
        raise ValueError("starting_balance must be finite and positive")

    session = stage_b_session(arm_id)
    manifest_file = Path(manifest_path)
    full_dataset = load_mt5_dataset(manifest_file)
    dataset, boundary_clock, dates, folds = slice_stage_a_dataset(full_dataset)
    partition = _partition_metadata(
        manifest_path=manifest_file,
        dataset=dataset,
        dates=dates,
        folds=folds,
    )

    if float(config.position_size) != 0.1:
        raise ValueError("M023 Stage-B position size must remain exactly 0.1")
    if bool(getattr(config, "use_higher_tf", False)):
        raise ValueError("M023 Stage B requires M15/higher-TF signal disabled")

    from .m023_direction_research import _temporary_research_config

    symbols = tuple(config.symbols)
    with _temporary_research_config(P2_08_PARAMETERS):
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
        direction_proxy = DirectionFilterBrokerProxy(
            broker,
            allowed_direction="BUY",
        )
        session_proxy = SessionFilterBrokerProxy(
            direction_proxy,
            feed=feed,
            session=session,
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
            strategies.append(SessionStrategyWrapper(strategy, session_proxy))

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

        session_metadata = {
            "milestone": "M023",
            "stage": "B",
            "experiment_id": f"M023-B-{arm_id}",
            "arm_id": arm_id,
            "direction": "BUY",
            "parameters": asdict(P2_08_PARAMETERS),
            "partition": partition,
            "cost_contract": COST_CONTRACT,
            "session": {
                "label": session.label,
                "timezone": "Africa/Nairobi",
                "start_hour": session.start_hour,
                "end_hour": session.end_hour,
                "duration_hours": session.duration_hours,
                "new_entry_eligibility_only": True,
            },
            "timezone_runtime": {
                "python": sys.version.split()[0],
                "implementation": sys.implementation.name,
                "zoneinfo_module": "stdlib zoneinfo",
                "tzpath": [str(path) for path in TZPATH],
                "tzdata_package_version": _tzdata_version(),
            },
            "direction_filter": {
                "rejections_total": direction_proxy.rejections,
                "rejected_by_side": dict(direction_proxy.rejected_by_side),
                "passed_by_side": dict(direction_proxy.passed_by_side),
            },
            "session_filter": {
                "rejections_total": session_proxy.rejections,
                "passed_buy_entries": session_proxy.passed,
            },
            "m15_signal_enabled": False,
            "position_size": 0.1,
        }
        baseline["research"] = session_metadata
        baseline["cost_assumptions"]["m023_contract"] = COST_CONTRACT
        baseline["configuration"]["m1_boundaries"] = {
            "oversold": 20.0,
            "overbought": 80.0,
        }
        baseline["configuration"]["ema_entry_period"] = 7
        baseline["configuration"]["decision_spread_max_points"] = None
        baseline["configuration"]["session_filter"] = session.label
        baseline["configuration"]["entry_direction"] = "BUY"
        baseline["configuration"]["m15_signal_enabled"] = False

        diagnostic = build_diagnostic_report(
            baseline_report=baseline,
            broker=broker,
            result=result,
        )
        diagnostic["research"] = session_metadata

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

    summary = {
        "milestone": "M023",
        "stage": "B",
        "experiment_id": f"M023-B-{arm_id}",
        "arm_id": arm_id,
        "direction": "BUY",
        "parameters": asdict(P2_08_PARAMETERS),
        "partition": partition,
        "cost_contract": COST_CONTRACT,
        "session": session_metadata["session"],
        "timezone_runtime": session_metadata["timezone_runtime"],
        "aggregate": aggregate,
        "overall": breakdowns["overall"],
        "per_symbol": per_symbol,
        "folds": breakdowns["folds"],
        "iso_weeks": breakdowns["iso_weeks"],
        "eat_active": breakdowns["eat_active"],
        "eat_off_hours": breakdowns["eat_off_hours"],
        "direction_filter": session_metadata["direction_filter"],
        "session_filter": session_metadata["session_filter"],
        "direction_invariants": {
            "buy_accepted_entries": int(direction_proxy.passed_by_side["BUY"]),
            "sell_accepted_entries": int(direction_proxy.passed_by_side["SELL"]),
        },
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
        "reference_windows": (
            _reference_windows(trades, folds) if arm_id == "S-R" else None
        ),
        "safety": {
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
            "weekday_filter_applied": False,
            "m15_signal_enabled": False,
            "forced_session_end_close": False,
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


def run_stage_b_pair(
    manifest_path: str | Path,
    *,
    arm_id: str,
    output_dir: str | Path,
    starting_balance: float = 10_000.0,
) -> dict[str, Any]:
    stage_b_session(arm_id)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    runs = []
    for label in ("a", "b"):
        baseline, diagnostic, summary = _run_stage_b_arm(
            manifest_path,
            arm_id=arm_id,
            starting_balance=starting_balance,
        )
        prefix = f"M023-B-{arm_id}-{label}"
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
                "baseline_sha256": baseline_sha,
                "diagnostic_sha256": _sha256_path(diagnostic_path),
                "summary_sha256": _sha256_path(summary_path),
                "summary_path": str(summary_path),
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
        "stage": "B",
        "arm_id": arm_id,
        "session": asdict(stage_b_session(arm_id)),
        "deterministic": deterministic,
        "a": runs[0],
        "b": runs[1],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one frozen M023 Stage-B BUY-only session arm pair."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--arm",
        choices=tuple(STAGE_B_SESSIONS),
        required=True,
    )
    parser.add_argument("--starting-balance", type=float, default=10_000.0)
    args = parser.parse_args(argv)

    result = run_stage_b_pair(
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
        "session": result["session"],
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
