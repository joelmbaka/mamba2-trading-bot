"""Read-only diagnostics for M020 controlled-experiment confounds."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd


PERCENTILES = (0, 25, 50, 75, 90, 95, 99, 100)

SPREAD_BANDS = (
    ("00 <=2", None, 2.0),
    ("01 >2-5", 2.0, 5.0),
    ("02 >5-10", 5.0, 10.0),
    ("03 >10-20", 10.0, 20.0),
    ("04 >20-50", 20.0, 50.0),
    ("05 >50-100", 50.0, 100.0),
    ("06 >100", 100.0, None),
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _spread_points(trade: Mapping[str, Any]) -> float | None:
    spread = trade.get("entry_spread") or {}
    value = spread.get("spread_points")
    return None if value is None else float(value)


def _spread_band(value: float) -> str:
    for label, lower, upper in SPREAD_BANDS:
        if lower is not None and value <= lower:
            continue
        if upper is not None and value > upper:
            continue
        return label
    raise ValueError(f"spread value did not match a band: {value}")


def _trade_stats(
    trades: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    spreads = [
        spread
        for trade in trades
        if (spread := _spread_points(trade)) is not None
    ]
    return {
        "closed_trades": len(trades),
        "wins": sum(trade["outcome"] == "win" for trade in trades),
        "losses": sum(trade["outcome"] == "loss" for trade in trades),
        "flats": sum(trade["outcome"] == "flat" for trade in trades),
        "net_realized_pl": sum(
            float(trade["net_realized_pl"]) for trade in trades
        ),
        "entry_spread_points": {
            "count": len(spreads),
            "mean": (
                sum(spreads) / len(spreads) if spreads else None
            ),
            "minimum": min(spreads) if spreads else None,
            "maximum": max(spreads) if spreads else None,
        },
    }


def _group_by_spread_band(
    trades: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for trade in trades:
        spread = _spread_points(trade)
        if spread is None:
            continue
        grouped[_spread_band(spread)].append(trade)

    return {
        label: _trade_stats(grouped.get(label, []))
        for label, _lower, _upper in SPREAD_BANDS
    }


def _blocked_session(trade: Mapping[str, Any]) -> bool:
    hour = int(trade["entry_utc_hour"])
    return 0 <= hour < 4


def _entry_month(trade: Mapping[str, Any]) -> str:
    return pd.Timestamp(trade["entry_time_utc"]).strftime("%Y-%m")


def _nested_band_breakdown(
    trades: Sequence[Mapping[str, Any]],
    key,
) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for trade in trades:
        grouped[str(key(trade))].append(trade)
    return {
        name: _group_by_spread_band(rows)
        for name, rows in sorted(grouped.items())
    }


def _spread_percentiles(
    trades: Sequence[Mapping[str, Any]],
) -> dict[str, float | None]:
    values = [
        spread
        for trade in trades
        if (spread := _spread_points(trade)) is not None
    ]
    if not values:
        return {f"p{percentile:02d}": None for percentile in PERCENTILES}

    series = pd.Series(values, dtype="float64")
    return {
        f"p{percentile:02d}": float(
            series.quantile(percentile / 100.0, interpolation="linear")
        )
        for percentile in PERCENTILES
    }


def build_m020b_spread_diagnostic(
    control_diagnostic: Mapping[str, Any],
) -> dict[str, Any]:
    """Diagnose time-vs-spread confounding without changing strategy behavior."""

    trades = list(control_diagnostic.get("trades", []))
    blocked = [trade for trade in trades if _blocked_session(trade)]
    outside = [trade for trade in trades if not _blocked_session(trade)]

    blocked_bands = _group_by_spread_band(blocked)
    outside_bands = _group_by_spread_band(outside)

    return {
        "diagnostic_id": "M020-B",
        "purpose": (
            "Describe whether 00:00-03:59 UTC losses persist across ordinary "
            "spread levels or are concentrated in wide-spread tails."
        ),
        "strategy_behavior_changed": False,
        "blocked_utc_start": "00:00:00",
        "blocked_utc_end_exclusive": "04:00:00",
        "spread_band_definition": [
            {
                "label": label,
                "lower_exclusive": lower,
                "upper_inclusive": upper,
            }
            for label, lower, upper in SPREAD_BANDS
        ],
        "blocked_session": {
            "summary": _trade_stats(blocked),
            "spread_percentiles": _spread_percentiles(blocked),
            "by_spread_band": blocked_bands,
            "by_symbol_and_spread_band": _nested_band_breakdown(
                blocked,
                lambda trade: trade["symbol"],
            ),
            "by_side_and_spread_band": _nested_band_breakdown(
                blocked,
                lambda trade: trade["side"],
            ),
            "by_entry_month_and_spread_band": _nested_band_breakdown(
                blocked,
                _entry_month,
            ),
        },
        "outside_blocked_session": {
            "summary": _trade_stats(outside),
            "spread_percentiles": _spread_percentiles(outside),
            "by_spread_band": outside_bands,
        },
        "matched_spread_band_comparison": {
            label: {
                "blocked_session": blocked_bands[label],
                "outside_blocked_session": outside_bands[label],
            }
            for label, _lower, _upper in SPREAD_BANDS
        },
    }


def run_m020b_diagnostic(
    control_diagnostic_path: str | Path,
    *,
    output: str | Path,
    expected_control_diagnostic_sha256: str,
) -> dict[str, Any]:
    source = Path(control_diagnostic_path)
    source_bytes = source.read_bytes()
    source_sha = _sha256_bytes(source_bytes)
    if source_sha != expected_control_diagnostic_sha256:
        return {
            "ok": False,
            "reason": "control diagnostic hash mismatch",
            "source_control_diagnostic_sha256": source_sha,
            "expected_control_diagnostic_sha256": (
                expected_control_diagnostic_sha256
            ),
        }

    control_diagnostic = json.loads(source_bytes)
    report = build_m020b_spread_diagnostic(control_diagnostic)
    report["source_control_diagnostic_sha256"] = source_sha

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "diagnostic_id": "M020-B",
        "strategy_behavior_changed": False,
        "source_control_diagnostic_sha256": source_sha,
        "output": str(output_path),
        "output_sha256": _sha256_bytes(output_path.read_bytes()),
        "summary": {
            "blocked_session": report["blocked_session"]["summary"],
            "blocked_session_spread_percentiles": report[
                "blocked_session"
            ]["spread_percentiles"],
            "outside_blocked_session": report[
                "outside_blocked_session"
            ]["summary"],
            "matched_spread_band_comparison": report[
                "matched_spread_band_comparison"
            ],
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the read-only M020-B spread confound diagnostic."
    )
    parser.add_argument("--control-diagnostic", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--expected-control-diagnostic-sha256",
        required=True,
    )
    args = parser.parse_args(argv)

    result = run_m020b_diagnostic(
        args.control_diagnostic,
        output=args.output,
        expected_control_diagnostic_sha256=(
            args.expected_control_diagnostic_sha256
        ),
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
