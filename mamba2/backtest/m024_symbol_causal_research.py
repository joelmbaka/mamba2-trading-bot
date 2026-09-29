"""M024 Stage-2 causal symbol-specialization research.

Research-only runner. The market-data universe remains all five accepted FX
pairs for replay timing and account-currency conversion. Only the strategy
instantiation universe changes between C-R and C-UJ.

Historical holdout execution is intentionally unavailable.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

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
    M023_STAGE_A_DATE_LIST_SHA256,
    M023_STAGE_A_END_EXCLUSIVE_UTC,
    M023_STAGE_A_FOLDS,
    M023_STAGE_A_START_UTC,
    M023_STAGE_A_TRADING_DATE_COUNT,
    P2_08_PARAMETERS,
    DirectionFilterBrokerProxy,
    DirectionStrategyWrapper,
    _partition_metadata,
    _stage_a_breakdowns,
    slice_stage_a_dataset,
)
from .mt5_dataset import load_mt5_dataset
from .parameter_research import (
    COST_CONTRACT,
    M022_SOURCE_MANIFEST_SHA256,
    ResearchBoundaryReplayFeed,
    _canonical_json_sha256,
    _datetime_index_sha256,
    _sha256_path,
    _tp_safety,
)
from .runner import PortfolioBacktestRunner


M024_STAGE2_START_UTC = M023_STAGE_A_START_UTC
M024_STAGE2_END_EXCLUSIVE_UTC = M023_STAGE_A_END_EXCLUSIVE_UTC
M024_STAGE2_TRADING_DATE_COUNT = M023_STAGE_A_TRADING_DATE_COUNT
M024_STAGE2_DATE_LIST_SHA256 = M023_STAGE_A_DATE_LIST_SHA256
M024_STAGE2_FOLDS = M023_STAGE_A_FOLDS
M024_MARKET_DATA_SYMBOLS = (
    "EURUSD",
    "EURJPY",
    "GBPUSD",
    "GBPJPY",
    "USDJPY",
)
M024_STAGE2_ARMS: Mapping[str, tuple[str, ...]] = {
    "C-R": M024_MARKET_DATA_SYMBOLS,
    "C-UJ": ("USDJPY",),
}


@dataclass(frozen=True)
class Stage2SymbolArm:
    arm_id: str
    strategy_symbols: tuple[str, ...]

    def __post_init__(self) -> None:
        expected = M024_STAGE2_ARMS.get(self.arm_id)
        if expected is None or tuple(self.strategy_symbols) != tuple(expected):
            raise ValueError("arm is outside the frozen M024 Stage-2 matrix")


def stage2_arm(arm_id: str) -> Stage2SymbolArm:
    try:
        symbols = M024_STAGE2_ARMS[arm_id]
    except KeyError as exc:
        raise ValueError("arm is outside the frozen M024 Stage-2 matrix") from exc
    return Stage2SymbolArm(arm_id=arm_id, strategy_symbols=tuple(symbols))


def _require_market_data_universe(dataset: Any) -> None:
    observed_m1 = tuple(sorted(dataset.m1_bars))
    observed_ask = tuple(sorted(dataset.ask_m1_bars))
    expected = tuple(sorted(M024_MARKET_DATA_SYMBOLS))
    if observed_m1 != expected:
        raise ValueError(
            f"M024 Stage 2 market-data M1 universe changed: {observed_m1}"
        )
    if observed_ask != expected:
        raise ValueError(
            f"M024 Stage 2 market-data Ask universe changed: {observed_ask}"
        )


def _symbol_entry_counts(trades: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {symbol: 0 for symbol in M024_MARKET_DATA_SYMBOLS}
    for row in trades:
        symbol = str(row.get("symbol"))
        if symbol not in counts:
            raise ValueError(f"unexpected M024 trade symbol: {symbol}")
        counts[symbol] += 1
    return counts


def _run_stage2_arm(
    manifest_path: str | Path,
    *,
    arm: Stage2SymbolArm,
    starting_balance: float = 10_000.0,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if not math.isfinite(starting_balance) or starting_balance <= 0:
        raise ValueError("starting_balance must be finite and positive")

    manifest_file = Path(manifest_path)
    full_dataset = load_mt5_dataset(manifest_file)
    dataset, boundary_clock, dates, folds = slice_stage_a_dataset(full_dataset)
    _require_market_data_universe(dataset)

    partition = _partition_metadata(
        manifest_path=manifest_file,
        dataset=dataset,
        dates=dates,
        folds=folds,
    )
    if partition["source_manifest_sha256"] != M022_SOURCE_MANIFEST_SHA256:
        raise ValueError("M024 Stage 2 source manifest changed")
    if partition["start_utc"] != M024_STAGE2_START_UTC:
        raise ValueError("M024 Stage 2 start changed")
    if partition["end_exclusive_utc"] != M024_STAGE2_END_EXCLUSIVE_UTC:
        raise ValueError("M024 Stage 2 end changed")
    if int(partition["trading_dates"]) != M024_STAGE2_TRADING_DATE_COUNT:
        raise ValueError("M024 Stage 2 trading-date count changed")
    if partition["date_list_sha256"] != M024_STAGE2_DATE_LIST_SHA256:
        raise ValueError("M024 Stage 2 date-list SHA changed")
    if _datetime_index_sha256(boundary_clock) != partition["replay_boundary_sha256"]:
        raise ValueError("M024 Stage 2 replay-boundary SHA changed")

    configured_symbols = tuple(config.symbols)
    if tuple(configured_symbols) != M024_MARKET_DATA_SYMBOLS:
        raise ValueError(
            "M024 Stage 2 requires the exact accepted all-five config universe"
        )
    if float(config.position_size) != 0.1:
        raise ValueError("M024 Stage 2 position size must remain exactly 0.1")
    if bool(getattr(config, "use_higher_tf", False)):
        raise ValueError("M024 Stage 2 requires M15/higher-TF signal disabled")

    from .parameter_research import _temporary_research_config

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
            for symbol in M024_MARKET_DATA_SYMBOLS
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
        for symbol in arm.strategy_symbols:
            strategy = StochasticTripleTFStrategy(
                symbol,
                stochastic_k_period=21,
                stochastic_d_period=7,
                stochastic_slowing=7,
                oversold_level=20.0,
                overbought_level=80.0,
                ema_period=7,
            )
            strategies.append(
                DirectionStrategyWrapper(strategy, direction_proxy)
            )

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

        metadata = {
            "milestone": "M024",
            "stage": "2",
            "experiment_id": f"M024-S2-{arm.arm_id}",
            "arm_id": arm.arm_id,
            "direction": "BUY",
            "strategy_symbols": list(arm.strategy_symbols),
            "market_data_symbols": list(M024_MARKET_DATA_SYMBOLS),
            "parameters": asdict(P2_08_PARAMETERS),
            "parameters_sha256": _canonical_json_sha256(
                asdict(P2_08_PARAMETERS)
            ),
            "partition": dict(partition),
            "cost_contract": COST_CONTRACT,
            "session": "all-hours",
            "m15_signal_enabled": False,
            "position_size": 0.1,
        }
        baseline["research"] = metadata
        baseline["cost_assumptions"]["m024_contract"] = COST_CONTRACT
        baseline["configuration"]["m1_boundaries"] = {
            "oversold": 20.0,
            "overbought": 80.0,
        }
        baseline["configuration"]["ema_entry_period"] = 7
        baseline["configuration"]["decision_spread_max_points"] = None
        baseline["configuration"]["session_filter"] = "all-hours"
        baseline["configuration"]["entry_direction"] = "BUY"
        baseline["configuration"]["m15_signal_enabled"] = False
        baseline["configuration"]["strategy_symbols"] = list(
            arm.strategy_symbols
        )
        baseline["configuration"]["market_data_symbols"] = list(
            M024_MARKET_DATA_SYMBOLS
        )

        diagnostic = build_diagnostic_report(
            baseline_report=baseline,
            broker=broker,
            result=result,
        )
        diagnostic["research"] = metadata

    trades = diagnostic["trades"]
    breakdowns = _stage_a_breakdowns(trades, folds)
    entry_counts = _symbol_entry_counts(trades)
    excluded = tuple(
        symbol
        for symbol in M024_MARKET_DATA_SYMBOLS
        if symbol not in arm.strategy_symbols
    )
    excluded_entries = sum(entry_counts[symbol] for symbol in excluded)

    per_symbol = {}
    for symbol in M024_MARKET_DATA_SYMBOLS:
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
        "milestone": "M024",
        "stage": "2",
        "experiment_id": f"M024-S2-{arm.arm_id}",
        "arm_id": arm.arm_id,
        "direction": "BUY",
        "parameters": asdict(P2_08_PARAMETERS),
        "partition": partition,
        "cost_contract": COST_CONTRACT,
        "strategy_symbols": list(arm.strategy_symbols),
        "market_data_symbols": list(M024_MARKET_DATA_SYMBOLS),
        "aggregate": baseline["aggregate"],
        "per_symbol": per_symbol,
        "folds": breakdowns["folds"],
        "iso_weeks": breakdowns["iso_weeks"],
        "direction_filter": {
            "rejections_total": direction_proxy.rejections,
            "rejected_by_side": dict(direction_proxy.rejected_by_side),
            "passed_by_side": dict(direction_proxy.passed_by_side),
        },
        "direction_invariants": {
            "buy_accepted_entries": int(direction_proxy.passed_by_side["BUY"]),
            "sell_accepted_entries": int(direction_proxy.passed_by_side["SELL"]),
        },
        "symbol_invariants": {
            "strategy_symbols": list(arm.strategy_symbols),
            "market_data_symbols": list(M024_MARKET_DATA_SYMBOLS),
            "excluded_strategy_symbols": list(excluded),
            "closed_trade_rows_by_symbol": entry_counts,
            "excluded_symbol_closed_trade_rows": excluded_entries,
        },
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
            "m025_outcomes_used": False,
            "real_order_api_called": False,
            "session_filter_applied": False,
            "weekday_filter_applied": False,
            "market_data_universe_reduced": False,
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


def run_stage2_pair(
    manifest_path: str | Path,
    *,
    arm_id: str,
    output_dir: str | Path,
    starting_balance: float = 10_000.0,
) -> dict[str, Any]:
    arm = stage2_arm(arm_id)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    runs = []

    for label in ("a", "b"):
        baseline, diagnostic, summary = _run_stage2_arm(
            manifest_path,
            arm=arm,
            starting_balance=starting_balance,
        )
        prefix = f"M024-S2-{arm.arm_id}-{label}"
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
        "milestone": "M024",
        "stage": "2",
        "arm_id": arm.arm_id,
        "strategy_symbols": list(arm.strategy_symbols),
        "market_data_symbols": list(M024_MARKET_DATA_SYMBOLS),
        "deterministic": deterministic,
        "a": runs[0],
        "b": runs[1],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one frozen M024 Stage-2 causal symbol arm pair."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--arm",
        choices=tuple(M024_STAGE2_ARMS),
        required=True,
    )
    parser.add_argument("--starting-balance", type=float, default=10_000.0)
    args = parser.parse_args(argv)

    result = run_stage2_pair(
        args.manifest,
        arm_id=args.arm,
        output_dir=args.output_dir,
        starting_balance=args.starting_balance,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
