"""M024 read-only symbol-specialization diagnostics.

This module never replays the strategy. It reads only the exact accepted M023
Stage-A D-B / BUY-only deterministic summary pair, verifies that immutable
source evidence, and computes descriptive attribution for four prospectively
frozen symbol subsets.

A descriptive subset is not equivalent to a causal symbol-filtered replay.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


M024_SOURCE_A = (
    "backtest_data/m023-stage-a-direction-v1/D-B/"
    "M023-A-D-B-a-summary.json"
)
M024_SOURCE_B = (
    "backtest_data/m023-stage-a-direction-v1/D-B/"
    "M023-A-D-B-b-summary.json"
)
M024_ACCEPTED_SOURCE_SHA256 = (
    "7f16803e8174ffddc7afe6d7d273cc04a4b2859dd61753f6fae1f272ce28551c"
)
M024_DATE_LIST_SHA256 = (
    "50b56aabc47dd0f485d07ee531b9967922a7b81780b02aacf8affc80f744dfb0"
)
M024_START_UTC = "2025-08-25T00:00:00Z"
M024_END_EXCLUSIVE_UTC = "2026-07-08T00:00:00Z"
M024_EXPECTED_SYMBOLS = (
    "EURUSD",
    "EURJPY",
    "GBPUSD",
    "GBPJPY",
    "USDJPY",
)
M024_SUBSETS: Mapping[str, tuple[str, ...]] = {
    "SYM-R": M024_EXPECTED_SYMBOLS,
    "SYM-UJ": ("USDJPY",),
    "SYM-JPY": ("EURJPY", "GBPJPY", "USDJPY"),
    "SYM-NONJPY": ("EURUSD", "GBPUSD"),
}


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _expected_parameters() -> dict[str, Any]:
    return {
        "stochastic_k_period": 21,
        "stochastic_d_period": 7,
        "stochastic_slowing": 7,
        "oversold_level": 20.0,
        "overbought_level": 80.0,
        "ema_period": 7,
        "decision_spread_max_points": None,
        "atr_sl_multiplier": 1.5,
        "atr_tp_multiplier": 3.0,
        "block_00_04_utc": False,
    }


def validate_accepted_d_b_summary(summary: Mapping[str, Any]) -> dict[str, bool]:
    partition = summary.get("partition") or {}
    safety = summary.get("safety") or {}
    invariants = summary.get("direction_invariants") or {}
    tp = summary.get("tp_safety") or {}
    observed_symbols = tuple(sorted((summary.get("per_symbol") or {}).keys()))

    checks = {
        "milestone": summary.get("milestone") == "M023",
        "stage": summary.get("stage") == "A",
        "experiment_id": summary.get("experiment_id") == "M023-A-D-B",
        "arm_id": summary.get("arm_id") == "D-B",
        "direction": summary.get("direction") == "BUY",
        "parameters": summary.get("parameters") == _expected_parameters(),
        "cost_contract": summary.get("cost_contract")
        == (
            "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
            "SWAP-UNMODELED"
        ),
        "start_utc": partition.get("start_utc") == M024_START_UTC,
        "end_exclusive_utc": (
            partition.get("end_exclusive_utc") == M024_END_EXCLUSIVE_UTC
        ),
        "trading_dates": int(partition.get("trading_dates", 0)) == 225,
        "date_list_sha256": (
            partition.get("date_list_sha256") == M024_DATE_LIST_SHA256
        ),
        "strict_common_boundary_clock": (
            partition.get("strict_common_boundary_clock") is True
        ),
        "full_symbol_m1_preserved": (
            partition.get("full_symbol_m1_preserved") is True
        ),
        "five_folds": len(partition.get("folds") or []) == 5,
        "expected_symbols": observed_symbols == tuple(sorted(M024_EXPECTED_SYMBOLS)),
        "buy_only_invariant": int(invariants.get("sell_accepted_entries", -1)) == 0,
        "tp_negative_zero": int(
            tp.get("negative_pl_take_profit_exits", -1)
        ) == 0,
        "tp_wrong_side_zero": int(tp.get("wrong_side_initial_tp", -1)) == 0,
        "holdout_unused": (
            safety.get("historical_holdout_economic_data_used") is False
        ),
        "m021_unused": safety.get("m021_post_cutoff_data_used") is False,
        "real_order_unused": safety.get("real_order_api_called") is False,
        "session_filter_absent": safety.get("session_filter_applied") is False,
        "weekday_filter_absent": safety.get("weekday_filter_applied") is False,
    }
    return checks


def _require_accepted_d_b_summary(summary: Mapping[str, Any]) -> None:
    checks = validate_accepted_d_b_summary(summary)
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"accepted M023 D-B summary invariant drift: {failed}")


def load_accepted_d_b_summary(
    repo_root: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(repo_root).resolve()
    path_a = root / M024_SOURCE_A
    path_b = root / M024_SOURCE_B
    if not path_a.is_file() or not path_b.is_file():
        raise FileNotFoundError(
            "exact accepted M023 Stage-A D-B summary pair is required"
        )

    sha_a = _sha256_path(path_a)
    sha_b = _sha256_path(path_b)
    if sha_a != M024_ACCEPTED_SOURCE_SHA256:
        raise ValueError(
            f"M023 D-B summary A SHA mismatch: {sha_a} != "
            f"{M024_ACCEPTED_SOURCE_SHA256}"
        )
    if sha_b != M024_ACCEPTED_SOURCE_SHA256:
        raise ValueError(
            f"M023 D-B summary B SHA mismatch: {sha_b} != "
            f"{M024_ACCEPTED_SOURCE_SHA256}"
        )

    summary_a = json.loads(path_a.read_text(encoding="utf-8"))
    summary_b = json.loads(path_b.read_text(encoding="utf-8"))
    if summary_a != summary_b:
        raise ValueError("accepted M023 D-B summary A/B content differs")
    _require_accepted_d_b_summary(summary_a)

    source = {
        "a_path": M024_SOURCE_A,
        "b_path": M024_SOURCE_B,
        "a_sha256": sha_a,
        "b_sha256": sha_b,
        "deterministic_pair": True,
        "accepted_m023_stage_a_family_result":
            "04f8cb971ac56b06739aba594df1a2090745f396",
        "accepted_m023_stage_a_assessment":
            "ed01975c5ea7945d9890d807c58ff133e07a6aa1",
    }
    return summary_a, source


def _aggregate_symbol_rows(
    rows: Mapping[str, Mapping[str, Any]],
    symbols: Sequence[str],
) -> dict[str, Any]:
    missing = [symbol for symbol in symbols if symbol not in rows]
    if missing:
        raise ValueError(f"missing frozen M024 symbol evidence: {missing}")

    selected = [rows[symbol] for symbol in symbols]
    closed = sum(int(row.get("closed_trades", 0)) for row in selected)
    net_pl = sum(float(row.get("net_realized_pl", 0.0)) for row in selected)
    wins_available = all("wins" in row for row in selected)
    losses_available = all("losses" in row for row in selected)

    result: dict[str, Any] = {
        "closed_trades": closed,
        "net_realized_pl": net_pl,
        "mean_trade_pl": (net_pl / closed if closed else None),
    }
    if wins_available and losses_available:
        wins = sum(int(row.get("wins", 0)) for row in selected)
        losses = sum(int(row.get("losses", 0)) for row in selected)
        result.update(
            {
                "wins": wins,
                "losses": losses,
                "flats": closed - wins - losses,
                "win_rate_nonflat_pct": (
                    (wins / (wins + losses)) * 100.0
                    if wins + losses
                    else None
                ),
            }
        )
    else:
        result.update(
            {
                "wins": None,
                "losses": None,
                "flats": None,
                "win_rate_nonflat_pct": None,
            }
        )
    result["median_trade_pl"] = None
    return result


def _subset_breakdown(
    summary: Mapping[str, Any],
    symbols: Sequence[str],
) -> dict[str, Any]:
    overall = _aggregate_symbol_rows(summary["per_symbol"], symbols)

    folds: dict[str, Any] = {}
    for label, fold in sorted((summary.get("folds") or {}).items()):
        folds[label] = _aggregate_symbol_rows(
            fold.get("per_symbol") or {},
            symbols,
        )

    weeks: dict[str, Any] = {}
    for label, week in sorted((summary.get("iso_weeks") or {}).items()):
        weeks[label] = _aggregate_symbol_rows(
            week.get("per_symbol") or {},
            symbols,
        )

    total_closed = int((summary.get("aggregate") or {}).get("closed_trades", 0))
    activity_share = (
        overall["closed_trades"] / total_closed if total_closed else None
    )

    positive_folds = [
        label
        for label, row in folds.items()
        if float(row["net_realized_pl"]) > 0
    ]
    positive_mean_folds = [
        label
        for label, row in folds.items()
        if row["mean_trade_pl"] is not None and float(row["mean_trade_pl"]) > 0
    ]
    positive_fold_sum = sum(
        float(folds[label]["net_realized_pl"])
        for label in positive_folds
    )
    max_positive_fold_share = (
        max(
            float(folds[label]["net_realized_pl"])
            for label in positive_folds
        ) / positive_fold_sum
        if positive_fold_sum > 0
        else None
    )

    eligible_weeks = {
        label: row
        for label, row in weeks.items()
        if int(row["closed_trades"]) >= 5
    }
    positive_pl_weeks = [
        label
        for label, row in eligible_weeks.items()
        if float(row["net_realized_pl"]) > 0
    ]
    positive_mean_weeks = [
        label
        for label, row in eligible_weeks.items()
        if row["mean_trade_pl"] is not None and float(row["mean_trade_pl"]) > 0
    ]
    eligible_count = len(eligible_weeks)

    contributions = {
        symbol: {
            "closed_trades": int(summary["per_symbol"][symbol]["closed_trades"]),
            "net_realized_pl": float(
                summary["per_symbol"][symbol]["net_realized_pl"]
            ),
            "mean_trade_pl": float(
                summary["per_symbol"][symbol]["mean_trade_pl"]
            ),
        }
        for symbol in symbols
    }

    return {
        "symbols": list(symbols),
        "overall": overall,
        "activity_share_of_d_b": activity_share,
        "folds": folds,
        "fold_stability": {
            "positive_net_pl_folds": positive_folds,
            "positive_net_pl_fold_count": len(positive_folds),
            "positive_mean_trade_pl_folds": positive_mean_folds,
            "positive_mean_trade_pl_fold_count": len(positive_mean_folds),
            "max_positive_fold_pl_share": max_positive_fold_share,
        },
        "iso_weeks": weeks,
        "weekly_stability": {
            "eligible_week_min_trades": 5,
            "eligible_week_count": eligible_count,
            "positive_net_pl_week_count": len(positive_pl_weeks),
            "positive_net_pl_week_fraction": (
                len(positive_pl_weeks) / eligible_count
                if eligible_count
                else None
            ),
            "positive_mean_trade_pl_week_count": len(positive_mean_weeks),
            "positive_mean_trade_pl_week_fraction": (
                len(positive_mean_weeks) / eligible_count
                if eligible_count
                else None
            ),
        },
        "symbol_contributions": contributions,
    }


def _classification(
    subset_id: str,
    row: Mapping[str, Any],
) -> tuple[str, dict[str, bool]]:
    if subset_id == "SYM-R":
        return "REFERENCE", {}

    overall = row["overall"]
    folds = row["fold_stability"]
    weekly = row["weekly_stability"]
    concentration = folds["max_positive_fold_pl_share"]
    positive_week_fraction = weekly["positive_mean_trade_pl_week_fraction"]

    checks = {
        "aggregate_net_pl_positive": float(overall["net_realized_pl"]) > 0,
        "aggregate_mean_trade_pl_positive": (
            overall["mean_trade_pl"] is not None
            and float(overall["mean_trade_pl"]) > 0
        ),
        "positive_net_pl_folds_ge_3": (
            int(folds["positive_net_pl_fold_count"]) >= 3
        ),
        "positive_mean_trade_pl_folds_ge_3": (
            int(folds["positive_mean_trade_pl_fold_count"]) >= 3
        ),
        "positive_fold_concentration_le_60pct": (
            concentration is not None and float(concentration) <= 0.60
        ),
        "eligible_iso_weeks_ge_20": int(weekly["eligible_week_count"]) >= 20,
        "positive_mean_iso_weeks_ge_50pct": (
            positive_week_fraction is not None
            and float(positive_week_fraction) >= 0.50
        ),
    }
    return (
        "DESCRIPTIVELY PROMISING"
        if all(checks.values())
        else "DESCRIPTIVELY UNSUPPORTED",
        checks,
    )


def build_report_from_summary(
    summary: Mapping[str, Any],
    *,
    source: Mapping[str, Any],
) -> dict[str, Any]:
    _require_accepted_d_b_summary(summary)

    subsets: dict[str, Any] = {}
    promising: list[str] = []
    for subset_id, symbols in M024_SUBSETS.items():
        row = _subset_breakdown(summary, symbols)
        classification, checks = _classification(subset_id, row)
        row["classification"] = classification
        row["descriptive_screen_checks"] = checks
        subsets[subset_id] = row
        if classification == "DESCRIPTIVELY PROMISING":
            promising.append(subset_id)

    report = {
        "schema_version": 1,
        "milestone": "M024",
        "analysis_kind": "DESCRIPTIVE SUBSET ATTRIBUTION",
        "causal_symbol_filtered_replay": False,
        "causal_warning": (
            "Removing symbols from accepted all-five-symbol evidence is not "
            "equivalent to replaying the strategy with symbol eligibility "
            "suppressed."
        ),
        "source": dict(source),
        "partition": {
            "start_utc": M024_START_UTC,
            "end_exclusive_utc": M024_END_EXCLUSIVE_UTC,
            "trading_dates": 225,
            "date_list_sha256": M024_DATE_LIST_SHA256,
            "historical_holdout_accessed": False,
        },
        "frozen_subsets": {
            key: list(value) for key, value in M024_SUBSETS.items()
        },
        "subsets": subsets,
        "descriptively_promising_subsets": promising,
        "next_stage_authorized": bool(promising),
        "next_stage_rule": (
            "freeze a prospective causal symbol-filtered replay family before "
            "fresh economics"
            if promising
            else "stop M024; no causal symbol-filtered replay"
        ),
        "safety": {
            "economic_replay_run": False,
            "accepted_m023_d_b_summary_only": True,
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "m025_outcomes_used": False,
            "real_order_api_called": False,
            "session_filter_run": False,
            "weekday_filter_run": False,
        },
    }
    report["report_sha256"] = _canonical_json_sha256(report)
    return report


def build_report(repo_root: str | Path) -> dict[str, Any]:
    summary, source = load_accepted_d_b_summary(repo_root)
    return build_report_from_summary(summary, source=source)


def write_report(report: Mapping[str, Any], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _headline(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        subset_id: {
            "classification": row["classification"],
            "symbols": row["symbols"],
            "closed_trades": row["overall"]["closed_trades"],
            "net_realized_pl": row["overall"]["net_realized_pl"],
            "mean_trade_pl": row["overall"]["mean_trade_pl"],
            "positive_folds": row["fold_stability"][
                "positive_net_pl_fold_count"
            ],
            "eligible_weeks": row["weekly_stability"]["eligible_week_count"],
            "positive_mean_week_fraction": row["weekly_stability"][
                "positive_mean_trade_pl_week_fraction"
            ],
        }
        for subset_id, row in report["subsets"].items()
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build deterministic M024 descriptive symbol diagnostics."
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
        "report_sha256": report["report_sha256"],
        "headline": _headline(report),
        "descriptively_promising_subsets":
            report["descriptively_promising_subsets"],
        "safety": report["safety"],
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
