"""M024 metadata-only historical-holdout readiness.

This module is intentionally non-economic. It may load and slice the accepted
historical dataset to prove coverage, exact dates, and replay-clock integrity,
but it does not construct a broker, strategy, order, trade, or P/L report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from .m023_direction_research import _date_list_sha256
from .mt5_dataset import LoadedHistoricalDataset, load_mt5_dataset
from .parameter_research import (
    M022_PARTITIONS,
    M022_SOURCE_MANIFEST_SHA256,
    _canonical_json_sha256,
    _datetime_index_sha256,
    _sha256_path,
    _slice_frame,
    _strict_common_boundary_clock,
    _utc,
)


M024_HOLDOUT_START_UTC = "2026-07-08T00:00:00Z"
M024_HOLDOUT_END_EXCLUSIVE_UTC = "2026-09-25T00:00:00Z"
M024_HOLDOUT_TRADING_DATES = 57
M024_HOLDOUT_BLOCK_SIZE = 19
M024_HOLDOUT_SYMBOLS = (
    "EURUSD",
    "EURJPY",
    "GBPUSD",
    "GBPJPY",
    "USDJPY",
)


def _iso(timestamp: pd.Timestamp) -> str:
    return timestamp.isoformat().replace("+00:00", "Z")


def _require_manifest_range(manifest: Mapping[str, Any]) -> None:
    requested = manifest.get("requested_range") or {}
    source_start = pd.Timestamp(requested.get("from_utc"))
    source_end = pd.Timestamp(requested.get("to_utc"))
    if source_start.tzinfo is None:
        source_start = source_start.tz_localize("UTC")
    else:
        source_start = source_start.tz_convert("UTC")
    if source_end.tzinfo is None:
        source_end = source_end.tz_localize("UTC")
    else:
        source_end = source_end.tz_convert("UTC")

    start = _utc(M024_HOLDOUT_START_UTC)
    end = _utc(M024_HOLDOUT_END_EXCLUSIVE_UTC)
    if source_start > start or source_end < end:
        raise ValueError("accepted source manifest does not cover M024 holdout")


def _require_exact_universe(dataset: LoadedHistoricalDataset) -> None:
    expected = tuple(sorted(M024_HOLDOUT_SYMBOLS))
    if tuple(sorted(dataset.m1_bars)) != expected:
        raise ValueError("M024 holdout Bid M1 symbol universe changed")
    if tuple(sorted(dataset.ask_m1_bars)) != expected:
        raise ValueError("M024 holdout Ask M1 symbol universe changed")
    if tuple(sorted(dataset.native_timeframe_bars)) != expected:
        raise ValueError("M024 holdout native symbol universe changed")
    for symbol in M024_HOLDOUT_SYMBOLS:
        if "M5" not in dataset.native_timeframe_bars[symbol]:
            raise ValueError(f"M024 holdout missing native M5 for {symbol}")


def _slice_holdout_metadata(
    dataset: LoadedHistoricalDataset,
) -> tuple[
    dict[str, pd.DataFrame],
    dict[str, pd.DataFrame],
    dict[str, Mapping[str | int, pd.DataFrame]],
    pd.DatetimeIndex,
    list[str],
]:
    start = _utc(M024_HOLDOUT_START_UTC)
    end = _utc(M024_HOLDOUT_END_EXCLUSIVE_UTC)

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

    for symbol in M024_HOLDOUT_SYMBOLS:
        if not m1[symbol].index.equals(ask[symbol].index):
            raise ValueError(f"M024 holdout Bid/Ask M1 mismatch for {symbol}")
        for frame in (m1[symbol], ask[symbol]):
            if frame.index.min() < start or frame.index.max() >= end:
                raise ValueError("M024 holdout slice escaped frozen time window")
        for frame in native[symbol].values():
            if frame.index.min() < start or frame.index.max() >= end:
                raise ValueError(
                    "M024 holdout native slice escaped frozen time window"
                )

    boundary_clock = _strict_common_boundary_clock(
        m1,
        ask,
        end_exclusive=end,
    )
    if boundary_clock.has_duplicates or not boundary_clock.is_monotonic_increasing:
        raise ValueError("M024 holdout replay clock is not deterministic")

    dates = list(
        dict.fromkeys(
            timestamp.date().isoformat()
            for timestamp in boundary_clock
            if timestamp < end
        )
    )
    if len(dates) != M024_HOLDOUT_TRADING_DATES:
        raise ValueError(
            "M024 holdout trading-date count changed: "
            f"{len(dates)} != {M024_HOLDOUT_TRADING_DATES}"
        )
    if dates != sorted(set(dates)):
        raise ValueError("M024 holdout dates are not unique chronological dates")

    return m1, ask, native, boundary_clock, dates


def _block_metadata(dates: Sequence[str]) -> list[dict[str, Any]]:
    if len(dates) != M024_HOLDOUT_TRADING_DATES:
        raise ValueError("M024 holdout block builder requires exactly 57 dates")

    blocks = []
    for index, label in enumerate(("H1", "H2", "H3")):
        chunk = list(
            dates[
                index * M024_HOLDOUT_BLOCK_SIZE :
                (index + 1) * M024_HOLDOUT_BLOCK_SIZE
            ]
        )
        if len(chunk) != M024_HOLDOUT_BLOCK_SIZE:
            raise ValueError(f"M024 holdout block {label} is not 19 dates")
        blocks.append(
            {
                "label": label,
                "first_date": chunk[0],
                "last_date": chunk[-1],
                "trading_dates": len(chunk),
                "date_list_sha256": _date_list_sha256(chunk),
            }
        )
    return blocks


def build_readiness(
    manifest_path: str | Path,
) -> dict[str, Any]:
    manifest_file = Path(manifest_path)
    source_sha = _sha256_path(manifest_file)
    if source_sha != M022_SOURCE_MANIFEST_SHA256:
        raise ValueError("accepted M022 source manifest SHA changed")

    full = load_mt5_dataset(manifest_file)
    _require_manifest_range(full.manifest)
    _require_exact_universe(full)

    m1, ask, native, boundary_clock, dates = _slice_holdout_metadata(full)
    blocks = _block_metadata(dates)
    date_sha = _date_list_sha256(dates)
    replay_sha = _datetime_index_sha256(boundary_clock)

    expected_partition = M022_PARTITIONS["historical_holdout"]
    if expected_partition != (
        M024_HOLDOUT_START_UTC,
        M024_HOLDOUT_END_EXCLUSIVE_UTC,
        M024_HOLDOUT_TRADING_DATES,
    ):
        raise ValueError("M022 historical-holdout partition contract changed")

    row_counts: dict[str, Any] = {}
    for symbol in M024_HOLDOUT_SYMBOLS:
        native_counts = {
            str(timeframe): int(len(frame))
            for timeframe, frame in sorted(
                native[symbol].items(),
                key=lambda item: str(item[0]),
            )
        }
        row_counts[symbol] = {
            "bid_m1": int(len(m1[symbol])),
            "ask_m1": int(len(ask[symbol])),
            "native": native_counts,
        }

    specification = {
        "source_manifest_sha256": source_sha,
        "start_utc": M024_HOLDOUT_START_UTC,
        "end_exclusive_utc": M024_HOLDOUT_END_EXCLUSIVE_UTC,
        "trading_dates": len(dates),
        "date_list_sha256": date_sha,
        "strict_common_boundary_clock": True,
        "full_symbol_m1_preserved": True,
        "replay_boundary_count": int(len(boundary_clock)),
        "replay_boundary_first_utc": _iso(boundary_clock[0]),
        "replay_boundary_last_utc": _iso(boundary_clock[-1]),
        "replay_boundary_sha256": replay_sha,
        "blocks": blocks,
        "symbols": list(M024_HOLDOUT_SYMBOLS),
    }

    return {
        "schema_version": 1,
        "milestone": "M024",
        "checkpoint": "historical-holdout-readiness",
        "readiness_only": True,
        "economics_computed": False,
        "ready": True,
        "partition": specification,
        "partition_spec_sha256": _canonical_json_sha256(specification),
        "row_counts": row_counts,
        "safety": {
            "broker_constructed": False,
            "strategy_constructed": False,
            "orders_constructed": False,
            "trades_computed": False,
            "pl_computed": False,
            "drawdown_computed": False,
            "win_rate_computed": False,
            "m021_post_cutoff_outcomes_used": False,
            "m025_outcomes_used": False,
            "real_order_api_called": False,
        },
    }


def write_readiness(report: Mapping[str, Any], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build metadata-only M024 holdout readiness evidence."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    report = build_readiness(args.manifest)
    path = write_readiness(report, args.output)
    payload = {
        "ok": True,
        "ready": report["ready"],
        "output": str(path),
        "artifact_sha256": _sha256_path(path),
        "partition": report["partition"],
        "partition_spec_sha256": report["partition_spec_sha256"],
        "safety": report["safety"],
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
