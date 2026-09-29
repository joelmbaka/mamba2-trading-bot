"""M024 one-shot historical-holdout replay for H-UJ.

This module is intentionally limited to the single prospectively frozen H-UJ
candidate. It requires the accepted metadata-only readiness artifact and exact
frozen readiness hashes before it can construct any economic replay.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict
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
    DirectionFilterBrokerProxy,
    DirectionStrategyWrapper,
    P2_08_PARAMETERS,
    _date_list_sha256,
    _stage_a_breakdowns,
)
from .m024_holdout_readiness import (
    M024_HOLDOUT_BLOCK_SIZE,
    M024_HOLDOUT_END_EXCLUSIVE_UTC,
    M024_HOLDOUT_START_UTC,
    M024_HOLDOUT_SYMBOLS,
    M024_HOLDOUT_TRADING_DATES,
    _slice_holdout_metadata,
)
from .mt5_dataset import LoadedHistoricalDataset, load_mt5_dataset
from .parameter_research import (
    COST_CONTRACT,
    M022_SOURCE_MANIFEST_SHA256,
    ResearchBoundaryReplayFeed,
    _canonical_json_sha256,
    _datetime_index_sha256,
    _sha256_path,
    _temporary_research_config,
    _tp_safety,
)
from .runner import PortfolioBacktestRunner


M024_HOLDOUT_CANDIDATE = "H-UJ"
M024_ACCEPTED_READINESS_SHA256 = (
    "85852452d61db9447e8935ddc05e2f8e41889aa3ae168b3cc2a76ab26ceedb2e"
)
M024_ACCEPTED_DATE_LIST_SHA256 = (
    "5d71d3ed67e5ae50f7e515f765e99a4887336e8a0d3659c62836d79dfe484af4"
)
M024_ACCEPTED_REPLAY_SHA256 = (
    "945c9961af7ce58e3b54223f0b8c10eb216e3dbfdf687ac002ef27b18197fab7"
)
M024_ACCEPTED_PARTITION_SPEC_SHA256 = (
    "2fac9ab123f1ed173a51aab2cccb42368937e9373b4937a94fd421a89a49cb70"
)
M024_ACCEPTED_BLOCK_SHA256 = {
    "H1": "35cd428dd20dc965aa6e1479a28c73ad66329a1e64d188c1a6e16df25f7b260d",
    "H2": "eb2dfda09cf52320eeb83aac9175713fb45a8b32a330e5b29168f5cd1bc9ae19",
    "H3": "c57086b4e23affa9125f3ff4b4b9eb0352cf7bd5b45b45d7efdf865d984f9359",
}


def load_accepted_readiness(path: str | Path) -> dict[str, Any]:
    readiness_path = Path(path)
    if not readiness_path.is_file():
        raise FileNotFoundError("accepted M024 holdout readiness artifact required")
    observed_sha = _sha256_path(readiness_path)
    if observed_sha != M024_ACCEPTED_READINESS_SHA256:
        raise ValueError("M024 holdout readiness artifact SHA changed")

    report = json.loads(readiness_path.read_text(encoding="utf-8"))
    partition = report.get("partition") or {}
    blocks = partition.get("blocks") or []
    safety = report.get("safety") or {}

    checks = {
        "readiness_only": report.get("readiness_only") is True,
        "economics_false": report.get("economics_computed") is False,
        "ready": report.get("ready") is True,
        "partition_spec": report.get("partition_spec_sha256")
        == M024_ACCEPTED_PARTITION_SPEC_SHA256,
        "source_manifest": partition.get("source_manifest_sha256")
        == M022_SOURCE_MANIFEST_SHA256,
        "start": partition.get("start_utc") == M024_HOLDOUT_START_UTC,
        "end": partition.get("end_exclusive_utc")
        == M024_HOLDOUT_END_EXCLUSIVE_UTC,
        "dates": int(partition.get("trading_dates", 0))
        == M024_HOLDOUT_TRADING_DATES,
        "date_sha": partition.get("date_list_sha256")
        == M024_ACCEPTED_DATE_LIST_SHA256,
        "replay_sha": partition.get("replay_boundary_sha256")
        == M024_ACCEPTED_REPLAY_SHA256,
        "blocks": len(blocks) == 3
        and all(
            row.get("date_list_sha256")
            == M024_ACCEPTED_BLOCK_SHA256.get(str(row.get("label")))
            and int(row.get("trading_dates", 0)) == M024_HOLDOUT_BLOCK_SIZE
            for row in blocks
        ),
        "pl_not_computed": safety.get("pl_computed") is False,
        "trades_not_computed": safety.get("trades_computed") is False,
        "m021_unused": safety.get("m021_post_cutoff_outcomes_used") is False,
        "m025_unused": safety.get("m025_outcomes_used") is False,
        "real_order_unused": safety.get("real_order_api_called") is False,
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"M024 accepted readiness invariant drift: {failed}")
    return report


def _holdout_dataset(
    full: LoadedHistoricalDataset,
    readiness: Mapping[str, Any],
) -> tuple[
    LoadedHistoricalDataset,
    Any,
    list[str],
    list[dict[str, Any]],
]:
    m1, ask, native, boundary_clock, dates = _slice_holdout_metadata(full)
    date_sha = _date_list_sha256(dates)
    replay_sha = _datetime_index_sha256(boundary_clock)
    partition = readiness["partition"]
    if date_sha != M024_ACCEPTED_DATE_LIST_SHA256:
        raise ValueError("M024 holdout date-list SHA changed before economics")
    if replay_sha != M024_ACCEPTED_REPLAY_SHA256:
        raise ValueError("M024 holdout replay SHA changed before economics")
    if date_sha != partition["date_list_sha256"]:
        raise ValueError("M024 holdout date list no longer matches readiness")
    if replay_sha != partition["replay_boundary_sha256"]:
        raise ValueError("M024 holdout replay clock no longer matches readiness")

    blocks: list[dict[str, Any]] = []
    for index, label in enumerate(("H1", "H2", "H3")):
        chunk = dates[
            index * M024_HOLDOUT_BLOCK_SIZE :
            (index + 1) * M024_HOLDOUT_BLOCK_SIZE
        ]
        observed = _date_list_sha256(chunk)
        if observed != M024_ACCEPTED_BLOCK_SHA256[label]:
            raise ValueError(f"M024 holdout block {label} SHA changed")
        blocks.append(
            {
                "label": label,
                "first_date": chunk[0],
                "last_date": chunk[-1],
                "trading_dates": len(chunk),
                "date_list_sha256": observed,
                "dates": list(chunk),
            }
        )

    manifest = dict(full.manifest)
    manifest["requested_range"] = {
        "from_utc": M024_HOLDOUT_START_UTC,
        "to_utc": M024_HOLDOUT_END_EXCLUSIVE_UTC,
    }
    manifest["m024_holdout"] = True
    manifest["m024_holdout_date_list_sha256"] = date_sha
    manifest["m024_holdout_replay_boundary_sha256"] = replay_sha
    manifest["m024_holdout_readiness_sha256"] = M024_ACCEPTED_READINESS_SHA256

    sliced = LoadedHistoricalDataset(
        m1_bars=m1,
        native_timeframe_bars=native,
        ask_m1_bars=ask,
        symbol_metadata=full.symbol_metadata,
        account_currency=full.account_currency,
        manifest=manifest,
    )
    return sliced, boundary_clock, dates, blocks


def _entry_date_counts(trades: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in trades:
        value = str(row["entry_time_utc"])
        date = value[:10]
        counts[date] = counts.get(date, 0) + 1
    return dict(sorted(counts.items()))


def _run_h_uj(
    manifest_path: str | Path,
    readiness_path: str | Path,
    *,
    starting_balance: float = 10_000.0,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if not math.isfinite(starting_balance) or starting_balance <= 0:
        raise ValueError("starting_balance must be finite and positive")

    readiness = load_accepted_readiness(readiness_path)
    manifest_file = Path(manifest_path)
    if _sha256_path(manifest_file) != M022_SOURCE_MANIFEST_SHA256:
        raise ValueError("accepted M022 source manifest SHA changed")

    full = load_mt5_dataset(manifest_file)
    dataset, boundary_clock, dates, blocks = _holdout_dataset(full, readiness)

    if tuple(config.symbols) != tuple(M024_HOLDOUT_SYMBOLS):
        raise ValueError("M024 holdout requires exact all-five config universe")
    if float(config.position_size) != 0.1:
        raise ValueError("M024 holdout position size must remain exactly 0.1")
    if bool(getattr(config, "use_higher_tf", False)):
        raise ValueError("M024 holdout requires M15/higher-TF signal disabled")

    with _temporary_research_config(P2_08_PARAMETERS):
        feed = ResearchBoundaryReplayFeed(
            dataset.m1_bars,
            native_timeframe_bars=dataset.native_timeframe_bars,
            ask_m1_bars=dataset.ask_m1_bars,
            boundary_clock=boundary_clock,
        )
        broker = DiagnosticHistoricalBroker(
            feed,
            balance=float(starting_balance),
            symbol_metadata=dataset.symbol_metadata,
            account_currency=dataset.account_currency,
            execution_costs={
                symbol: ExecutionCostModel(
                    commission_per_lot_per_side=0.0,
                    slippage_points=0.0,
                )
                for symbol in M024_HOLDOUT_SYMBOLS
            },
        )
        proxy = DirectionFilterBrokerProxy(broker, allowed_direction="BUY")
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

        strategy = StochasticTripleTFStrategy(
            "USDJPY",
            stochastic_k_period=21,
            stochastic_d_period=7,
            stochastic_slowing=7,
            oversold_level=20.0,
            overbought_level=80.0,
            ema_period=7,
        )
        wrapped = DirectionStrategyWrapper(strategy, proxy)

        runner = PortfolioBacktestRunner(
            feed,
            broker,
            [wrapped],
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
            "checkpoint": "historical-holdout",
            "candidate": M024_HOLDOUT_CANDIDATE,
            "strategy_symbols": ["USDJPY"],
            "market_data_symbols": list(M024_HOLDOUT_SYMBOLS),
            "direction": "BUY",
            "session": "all-hours",
            "m15_signal_enabled": False,
            "position_size": 0.1,
            "parameters": asdict(P2_08_PARAMETERS),
            "parameters_sha256": _canonical_json_sha256(
                asdict(P2_08_PARAMETERS)
            ),
            "cost_contract": COST_CONTRACT,
            "readiness_artifact_sha256": M024_ACCEPTED_READINESS_SHA256,
        }
        baseline["research"] = metadata
        diagnostic = build_diagnostic_report(
            baseline_report=baseline,
            broker=broker,
            result=result,
        )
        diagnostic["research"] = metadata

    trades = diagnostic["trades"]
    breakdowns = _stage_a_breakdowns(trades, blocks)
    symbol_counts = {
        symbol: sum(str(row.get("symbol")) == symbol for row in trades)
        for symbol in M024_HOLDOUT_SYMBOLS
    }
    excluded_count = sum(
        count for symbol, count in symbol_counts.items() if symbol != "USDJPY"
    )

    summary = {
        "milestone": "M024",
        "checkpoint": "historical-holdout",
        "candidate": M024_HOLDOUT_CANDIDATE,
        "strategy_symbols": ["USDJPY"],
        "market_data_symbols": list(M024_HOLDOUT_SYMBOLS),
        "direction": "BUY",
        "session": "all-hours",
        "m15_signal_enabled": False,
        "position_size": 0.1,
        "parameters": asdict(P2_08_PARAMETERS),
        "cost_contract": COST_CONTRACT,
        "readiness": {
            "artifact_sha256": M024_ACCEPTED_READINESS_SHA256,
            "partition_spec_sha256": M024_ACCEPTED_PARTITION_SPEC_SHA256,
            "date_list_sha256": M024_ACCEPTED_DATE_LIST_SHA256,
            "replay_boundary_sha256": M024_ACCEPTED_REPLAY_SHA256,
            "block_sha256": dict(M024_ACCEPTED_BLOCK_SHA256),
        },
        "partition": {
            "start_utc": M024_HOLDOUT_START_UTC,
            "end_exclusive_utc": M024_HOLDOUT_END_EXCLUSIVE_UTC,
            "trading_dates": len(dates),
            "date_list_sha256": _date_list_sha256(dates),
            "replay_boundary_count": len(boundary_clock),
            "replay_boundary_sha256": _datetime_index_sha256(boundary_clock),
            "blocks": [
                {key: value for key, value in block.items() if key != "dates"}
                for block in blocks
            ],
        },
        "aggregate": baseline["aggregate"],
        "per_symbol": baseline["per_symbol"],
        "blocks": breakdowns["folds"],
        "iso_weeks": breakdowns["iso_weeks"],
        "trading_date_counts": _entry_date_counts(trades),
        "direction_invariants": {
            "buy_accepted_entries": int(proxy.passed_by_side["BUY"]),
            "sell_accepted_entries": int(proxy.passed_by_side["SELL"]),
        },
        "symbol_invariants": {
            "closed_trade_rows_by_symbol": symbol_counts,
            "excluded_symbol_closed_trade_rows": excluded_count,
        },
        "tp_safety": _tp_safety(diagnostic),
        "remaining_positions": baseline["remaining_positions"],
        "safety": {
            "historical_holdout_economic_data_used": True,
            "m021_post_cutoff_data_used": False,
            "m025_outcomes_used": False,
            "real_order_api_called": False,
            "session_filter_applied": False,
            "weekday_filter_applied": False,
            "market_data_universe_reduced": False,
        },
    }
    return baseline, diagnostic, summary


def _write_json(report: Mapping[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def run_holdout_pair(
    manifest_path: str | Path,
    readiness_path: str | Path,
    *,
    output_dir: str | Path,
    starting_balance: float = 10_000.0,
) -> dict[str, Any]:
    # Readiness is deliberately validated before the source dataset is loaded.
    load_accepted_readiness(readiness_path)

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    runs = []
    for label in ("a", "b"):
        baseline, diagnostic, summary = _run_h_uj(
            manifest_path,
            readiness_path,
            starting_balance=starting_balance,
        )
        prefix = f"M024-H-UJ-{label}"
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
        summary_path = _write_json(
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
        runs[0][key] == runs[1][key]
        for key in (
            "baseline_sha256",
            "diagnostic_sha256",
            "summary_sha256",
        )
    )
    return {
        "ok": deterministic,
        "candidate": M024_HOLDOUT_CANDIDATE,
        "deterministic": deterministic,
        "a": runs[0],
        "b": runs[1],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the single frozen M024 H-UJ holdout A/B pair."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--readiness", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--starting-balance", type=float, default=10_000.0)
    args = parser.parse_args(argv)

    result = run_holdout_pair(
        args.manifest,
        args.readiness,
        output_dir=args.output_dir,
        starting_balance=args.starting_balance,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
