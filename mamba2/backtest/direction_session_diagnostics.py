"""M023 read-only direction/session diagnostics over accepted M022 artifacts.

This module never runs strategy replay. It reads exact, pre-existing M022
trade-level diagnostic JSON artifacts, verifies their accepted hashes, and
produces descriptive attribution tables only.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
from pathlib import Path
from statistics import mean, median
import sys
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import TZPATH, ZoneInfo


SOURCE_SPECS: dict[str, dict[str, dict[str, Any]]] = {
    "P2-R": {
        "development": {
            "path": (
                "backtest_data/m022-phase1-development/reference-v3/"
                "M022-P1-REFERENCE-a-diagnostic.json"
            ),
            "diagnostic_sha256": (
                "ae124fea75ead8f6d1e5e50cf090fb6db401ad5cdef6316f6851641f034205c7"
            ),
            "baseline_sha256": (
                "55630b2ff48b8594f04ed2d7ebb2012ef7c39db5f7b3b50f2fb1212049418530"
            ),
            "closed_trades": 12006,
        },
        "validation": {
            "path": (
                "backtest_data/m022-phase2-validation-v1/P2-R/"
                "M022-P2-R-a-diagnostic.json"
            ),
            "diagnostic_sha256": (
                "7a470bfebfa4434793f2f25bfcb416f4342187b5b08ca6f319237d9ea4856979"
            ),
            "baseline_sha256": (
                "b0103541cc843109a41c7f6df34c01fa912ae74351324cb6233de3df2090c1c6"
            ),
            "closed_trades": 3908,
        },
    },
    "P2-03": {
        "development": {
            "path": (
                "backtest_data/m022-phase2-development-v1/P2-03/"
                "M022-P2-03-a-diagnostic.json"
            ),
            "diagnostic_sha256": (
                "28cce843b8969a3058fdb2dd1e7677cc69292dadca8ff7683dbf0df5332ec76e"
            ),
            "baseline_sha256": (
                "5d8a8e7470ba10e7398aee03e7df20668971f69985b3b6fea48a8c3b670ef794"
            ),
            "closed_trades": 8439,
        },
        "validation": {
            "path": (
                "backtest_data/m022-phase2-validation-v1/P2-03/"
                "M022-P2-03-a-diagnostic.json"
            ),
            "diagnostic_sha256": (
                "30b7718a0075278853a9224cd5939446ea4624bb73f2b566f333e1081ef8c0b8"
            ),
            "baseline_sha256": (
                "44e8e0b0b66823a681ab100d52c71ee0b75de55bbd2f3fa1c336ba8404308fae"
            ),
            "closed_trades": 2860,
        },
    },
    "P2-08": {
        "development": {
            "path": (
                "backtest_data/m022-phase2-development-v1/P2-08/"
                "M022-P2-08-a-diagnostic.json"
            ),
            "diagnostic_sha256": (
                "bc5ce5fae1717b42075f74860aee80b3c0f8155b860bae2096eefa6b9f7a800c"
            ),
            "baseline_sha256": (
                "c4a893ff0896eda2a6726ac9c14415a0128817fdee58f17b670976eed5eed55f"
            ),
            "closed_trades": 8620,
        },
        "validation": {
            "path": (
                "backtest_data/m022-phase2-validation-v1/P2-08/"
                "M022-P2-08-a-diagnostic.json"
            ),
            "diagnostic_sha256": (
                "a8e81708d5f1128f8ad17497ee35f08cae8d9bc70e4b018aca1be5acd765f2ce"
            ),
            "baseline_sha256": (
                "f333b76323459395d4d3f007a03fb842f210f86783bc114bd3eed57af21f3aae"
            ),
            "closed_trades": 2884,
        },
    },
}

DIRECTIONS = ("BOTH", "SELL", "BUY")
EAT_WINDOWS = (
    "EAT-MORNING",
    "EAT-MIDDAY",
    "EAT-AFTERNOON",
    "EAT-EVENING",
    "EAT-ACTIVE",
    "EAT-OFF-HOURS",
)
MARKET_WINDOWS = ("LONDON-OPEN-TRANSITION", "LONDON-NY-OVERLAP")
WINDOWS = ("ALL-HOURS", *EAT_WINDOWS, *MARKET_WINDOWS)
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")

UTC = timezone.utc
EAT = ZoneInfo("Africa/Nairobi")
LONDON = ZoneInfo("Europe/London")
NEW_YORK = ZoneInfo("America/New_York")


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_lines(lines: Sequence[str]) -> str:
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("diagnostic trade timestamp must be timezone-aware")
    return parsed.astimezone(UTC)


def _entry_spread_points(trade: Mapping[str, Any]) -> float | None:
    spread = trade.get("entry_spread") or {}
    value = spread.get("spread_points")
    return None if value is None else float(value)


def _window_labels(entry_utc: datetime) -> set[str]:
    eat = entry_utc.astimezone(EAT)
    london = entry_utc.astimezone(LONDON)
    new_york = entry_utc.astimezone(NEW_YORK)
    eat_hour = eat.hour

    labels = {"ALL-HOURS"}
    if 8 <= eat_hour <= 11:
        labels.add("EAT-MORNING")
    if 12 <= eat_hour <= 14:
        labels.add("EAT-MIDDAY")
    if 15 <= eat_hour <= 17:
        labels.add("EAT-AFTERNOON")
    if 18 <= eat_hour <= 20:
        labels.add("EAT-EVENING")
    if 8 <= eat_hour <= 20:
        labels.add("EAT-ACTIVE")
    else:
        labels.add("EAT-OFF-HOURS")

    if 7 <= london.hour <= 8:
        labels.add("LONDON-OPEN-TRANSITION")
    if 13 <= london.hour <= 16 and 8 <= new_york.hour <= 11:
        labels.add("LONDON-NY-OVERLAP")
    return labels


def decorate_trade(trade: Mapping[str, Any]) -> dict[str, Any]:
    entry = _parse_utc(str(trade["entry_time_utc"]))
    eat = entry.astimezone(EAT)
    london = entry.astimezone(LONDON)
    new_york = entry.astimezone(NEW_YORK)
    return {
        **dict(trade),
        "_entry_date_utc": entry.date().isoformat(),
        "_weekday": entry.strftime("%A"),
        "_eat_hour": eat.hour,
        "_london_hour": london.hour,
        "_new_york_hour": new_york.hour,
        "_eat_offset": eat.strftime("%z"),
        "_london_offset": london.strftime("%z"),
        "_new_york_offset": new_york.strftime("%z"),
        "_windows": sorted(_window_labels(entry)),
    }


def _direction_filter(
    trades: Sequence[Mapping[str, Any]], direction: str
) -> list[Mapping[str, Any]]:
    if direction == "BOTH":
        return list(trades)
    return [row for row in trades if row.get("side") == direction]


def _window_filter(
    trades: Sequence[Mapping[str, Any]], window: str
) -> list[Mapping[str, Any]]:
    if window == "ALL-HOURS":
        return list(trades)
    return [row for row in trades if window in row.get("_windows", ())]


def summarize(trades: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(trades)
    wins = sum(row.get("outcome") == "win" for row in rows)
    losses = sum(row.get("outcome") == "loss" for row in rows)
    flats = sum(row.get("outcome") == "flat" for row in rows)
    nonflat = wins + losses
    pls = [float(row.get("net_realized_pl", 0.0)) for row in rows]
    spreads = [
        value
        for value in (_entry_spread_points(row) for row in rows)
        if value is not None
    ]
    exit_reasons = {
        "take_profit": sum(row.get("exit_reason") == "take_profit" for row in rows),
        "stop_loss": sum(row.get("exit_reason") == "stop_loss" for row in rows),
    }
    exit_reasons["other"] = len(rows) - sum(exit_reasons.values())

    symbols: dict[str, dict[str, Any]] = {}
    for symbol in sorted({str(row.get("symbol")) for row in rows}):
        subset = [row for row in rows if str(row.get("symbol")) == symbol]
        symbol_pl = sum(float(row.get("net_realized_pl", 0.0)) for row in subset)
        symbols[symbol] = {
            "closed_trades": len(subset),
            "net_realized_pl": symbol_pl,
        }

    return {
        "closed_trades": len(rows),
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "win_rate_nonflat_pct": (
            (wins / nonflat) * 100.0 if nonflat else None
        ),
        "net_realized_pl": sum(pls),
        "mean_trade_pl": mean(pls) if pls else None,
        "median_trade_pl": median(pls) if pls else None,
        "entry_spread_points": {
            "count": len(spreads),
            "mean": mean(spreads) if spreads else None,
            "median": median(spreads) if spreads else None,
        },
        "exit_counts": exit_reasons,
        "per_symbol": symbols,
    }


def _partition_tables(
    trades: Sequence[Mapping[str, Any]], *, include_hourly: bool
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for direction in DIRECTIONS:
        direction_rows = _direction_filter(trades, direction)
        window_tables = {
            window: summarize(_window_filter(direction_rows, window))
            for window in WINDOWS
        }
        weekday_tables = {
            weekday: summarize(
                [row for row in direction_rows if row.get("_weekday") == weekday]
            )
            for weekday in WEEKDAYS
        }
        row: dict[str, Any] = {
            "overall": summarize(direction_rows),
            "windows": window_tables,
            "weekdays": weekday_tables,
        }
        if include_hourly:
            row["hourly"] = {
                "Africa/Nairobi": {
                    f"{hour:02d}:00": summarize(
                        [r for r in direction_rows if r.get("_eat_hour") == hour]
                    )
                    for hour in range(24)
                },
                "Europe/London": {
                    f"{hour:02d}:00": summarize(
                        [r for r in direction_rows if r.get("_london_hour") == hour]
                    )
                    for hour in range(24)
                },
                "America/New_York": {
                    f"{hour:02d}:00": summarize(
                        [r for r in direction_rows if r.get("_new_york_hour") == hour]
                    )
                    for hour in range(24)
                },
            }
        output[direction] = row
    return output


def build_folds(reference_combined: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    dates = sorted({str(row["_entry_date_utc"]) for row in reference_combined})
    if len(dates) != 225:
        raise ValueError(
            f"expected 225 accepted development+validation dates, observed {len(dates)}"
        )
    folds = []
    for index in range(5):
        chunk = dates[index * 45 : (index + 1) * 45]
        folds.append(
            {
                "label": f"F{index + 1}",
                "trading_dates": len(chunk),
                "first_date": chunk[0],
                "last_date": chunk[-1],
                "date_list_sha256": _sha256_lines(chunk),
                "dates": chunk,
            }
        )
    return folds


def _positive_symbol_count(summary: Mapping[str, Any]) -> int:
    return sum(
        float(row.get("net_realized_pl", 0.0)) > 0
        for row in (summary.get("per_symbol") or {}).values()
    )


def _fold_stability(
    trades: Sequence[Mapping[str, Any]],
    folds: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for direction in DIRECTIONS:
        direction_rows = _direction_filter(trades, direction)
        output[direction] = {}
        for window in WINDOWS:
            rows = _window_filter(direction_rows, window)
            fold_rows = []
            for fold in folds:
                allowed = set(fold["dates"])
                group = [
                    row for row in rows if row.get("_entry_date_utc") in allowed
                ]
                reference = [
                    row
                    for row in trades
                    if row.get("_entry_date_utc") in allowed
                ]
                group_summary = summarize(group)
                reference_summary = summarize(reference)
                group_pl = float(group_summary["net_realized_pl"])
                reference_pl = float(reference_summary["net_realized_pl"])
                group_mean = group_summary["mean_trade_pl"]
                reference_mean = reference_summary["mean_trade_pl"]
                fold_rows.append(
                    {
                        "fold": fold["label"],
                        "closed_trades": group_summary["closed_trades"],
                        "net_realized_pl": group_pl,
                        "mean_trade_pl": group_mean,
                        "positive_symbol_count": _positive_symbol_count(group_summary),
                        "net_pl_delta_vs_both_all_hours": group_pl - reference_pl,
                        "mean_trade_pl_delta_vs_both_all_hours": (
                            None
                            if group_mean is None or reference_mean is None
                            else float(group_mean) - float(reference_mean)
                        ),
                    }
                )

            positive_net = [
                row for row in fold_rows if row["net_realized_pl"] > 0
            ]
            positive_delta = [
                row
                for row in fold_rows
                if row["net_pl_delta_vs_both_all_hours"] > 0
            ]
            positive_delta_sum = sum(
                row["net_pl_delta_vs_both_all_hours"] for row in positive_delta
            )
            positive_net_sum = sum(row["net_realized_pl"] for row in positive_net)
            output[direction][window] = {
                "folds": fold_rows,
                "folds_positive_net_pl": len(positive_net),
                "folds_net_pl_above_both_all_hours": len(positive_delta),
                "folds_mean_trade_pl_above_both_all_hours": sum(
                    row["mean_trade_pl_delta_vs_both_all_hours"] is not None
                    and row["mean_trade_pl_delta_vs_both_all_hours"] > 0
                    for row in fold_rows
                ),
                "largest_fold_share_of_positive_net_pl": (
                    max(row["net_realized_pl"] for row in positive_net)
                    / positive_net_sum
                    if positive_net_sum > 0
                    else None
                ),
                "largest_fold_share_of_positive_delta_vs_both_all_hours": (
                    max(
                        row["net_pl_delta_vs_both_all_hours"]
                        for row in positive_delta
                    )
                    / positive_delta_sum
                    if positive_delta_sum > 0
                    else None
                ),
            }
    return output


def _tzdata_version() -> str | None:
    try:
        return metadata.version("tzdata")
    except metadata.PackageNotFoundError:
        return None


def _load_source(
    repo_root: Path,
    *,
    arm: str,
    partition: str,
    spec: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = repo_root / str(spec["path"])
    if not path.is_file():
        raise FileNotFoundError(f"missing accepted diagnostic: {spec['path']}")
    observed_sha = _sha256_path(path)
    expected_sha = str(spec["diagnostic_sha256"])
    if observed_sha != expected_sha:
        raise ValueError(
            f"{arm}/{partition} diagnostic SHA mismatch: "
            f"{observed_sha} != {expected_sha}"
        )
    document = json.loads(path.read_text(encoding="utf-8"))
    source_baseline = document.get("source_baseline_sha256")
    if source_baseline != spec["baseline_sha256"]:
        raise ValueError(
            f"{arm}/{partition} source baseline SHA mismatch: "
            f"{source_baseline} != {spec['baseline_sha256']}"
        )
    reconciliation = document.get("reconciliation") or {}
    trades = document.get("trades") or []
    if int(reconciliation.get("closed_trades", -1)) != int(spec["closed_trades"]):
        raise ValueError(f"{arm}/{partition} closed-trade count mismatch")
    if len(trades) != int(spec["closed_trades"]):
        raise ValueError(f"{arm}/{partition} diagnostic trade-row count mismatch")
    source = {
        "arm": arm,
        "partition": partition,
        "path": str(spec["path"]),
        "diagnostic_sha256": observed_sha,
        "source_baseline_sha256": source_baseline,
        "closed_trades": len(trades),
    }
    return document, source


def build_report(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    documents: dict[str, dict[str, dict[str, Any]]] = {}
    sources = []
    decorated: dict[str, dict[str, list[dict[str, Any]]]] = {}

    for arm, partitions in SOURCE_SPECS.items():
        documents[arm] = {}
        decorated[arm] = {}
        for partition, spec in partitions.items():
            document, source = _load_source(
                root, arm=arm, partition=partition, spec=spec
            )
            documents[arm][partition] = document
            sources.append(source)
            decorated[arm][partition] = [
                decorate_trade(row) for row in document["trades"]
            ]

    combined_reference = (
        decorated["P2-R"]["development"]
        + decorated["P2-R"]["validation"]
    )
    folds = build_folds(combined_reference)

    arms: dict[str, Any] = {}
    for arm in SOURCE_SPECS:
        development = decorated[arm]["development"]
        validation = decorated[arm]["validation"]
        combined = development + validation
        arms[arm] = {
            "development": _partition_tables(
                development, include_hourly=False
            ),
            "validation": _partition_tables(
                validation, include_hourly=False
            ),
            "combined": _partition_tables(
                combined, include_hourly=True
            ),
            "fold_stability": _fold_stability(combined, folds),
        }

    return {
        "schema_version": 1,
        "milestone": "M023",
        "analysis_kind": "read-only attribution/slicing diagnostic",
        "filtered_strategy_replay": False,
        "causal_warning": (
            "Removing trades from an existing all-hours artifact is not "
            "equivalent to replaying a strategy with entry suppression."
        ),
        "source_partitions": {
            "development": {
                "start_utc": "2025-08-25T00:00:00Z",
                "end_exclusive_utc": "2026-04-21T00:00:00Z",
                "trading_dates": 169,
            },
            "validation": {
                "start_utc": "2026-04-21T00:00:00Z",
                "end_exclusive_utc": "2026-07-08T00:00:00Z",
                "trading_dates": 56,
            },
            "historical_holdout_accessed": False,
        },
        "sources": sources,
        "timezone_runtime": {
            "python": sys.version.split()[0],
            "implementation": sys.implementation.name,
            "zoneinfo_module": "stdlib zoneinfo",
            "tzpath": [str(path) for path in TZPATH],
            "tzdata_package_version": _tzdata_version(),
            "zones": [
                "UTC",
                "Africa/Nairobi",
                "Europe/London",
                "America/New_York",
            ],
        },
        "fixed_windows": {
            "EAT-MORNING": "08:00-11:59 Africa/Nairobi",
            "EAT-MIDDAY": "12:00-14:59 Africa/Nairobi",
            "EAT-AFTERNOON": "15:00-17:59 Africa/Nairobi",
            "EAT-EVENING": "18:00-20:59 Africa/Nairobi",
            "EAT-ACTIVE": "08:00-20:59 Africa/Nairobi",
            "EAT-OFF-HOURS": "21:00-07:59 Africa/Nairobi",
            "LONDON-OPEN-TRANSITION": "07:00-08:59 Europe/London",
            "LONDON-NY-OVERLAP": (
                "13:00-16:59 Europe/London AND "
                "08:00-11:59 America/New_York"
            ),
        },
        "folds": folds,
        "arms": arms,
        "safety": {
            "economic_replay_run": False,
            "existing_diagnostic_json_only": True,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
        },
    }


def write_report(report: Mapping[str, Any], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _headline(report: Mapping[str, Any]) -> dict[str, Any]:
    arms = report["arms"]
    return {
        arm: {
            "development": {
                direction: arms[arm]["development"][direction]["overall"]
                for direction in DIRECTIONS
            },
            "validation": {
                direction: arms[arm]["validation"][direction]["overall"]
                for direction in DIRECTIONS
            },
            "combined": {
                direction: {
                    "overall": arms[arm]["combined"][direction]["overall"],
                    "windows": arms[arm]["combined"][direction]["windows"],
                    "weekdays": arms[arm]["combined"][direction]["weekdays"],
                }
                for direction in DIRECTIONS
            },
            "fold_stability": arms[arm]["fold_stability"],
        }
        for arm in SOURCE_SPECS
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build deterministic M023 read-only direction/session diagnostics."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    report = build_report(args.repo_root)
    output = write_report(report, args.output)
    payload = {
        "ok": True,
        "output": str(output),
        "sha256": _sha256_path(output),
        "sources": report["sources"],
        "timezone_runtime": report["timezone_runtime"],
        "folds": report["folds"],
        "headline": _headline(report),
        "safety": report["safety"],
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
