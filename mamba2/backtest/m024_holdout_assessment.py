"""Mechanical M024 H-UJ holdout assessment.

Reads only an already-completed deterministic H-UJ summary and applies the
prospectively frozen representation/economic support rules.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .m024_holdout_research import (
    M024_ACCEPTED_BLOCK_SHA256,
    M024_ACCEPTED_DATE_LIST_SHA256,
    M024_ACCEPTED_PARTITION_SPEC_SHA256,
    M024_ACCEPTED_READINESS_SHA256,
    M024_ACCEPTED_REPLAY_SHA256,
    M024_HOLDOUT_CANDIDATE,
)
from .parameter_research import _sha256_path


def assess_summary(summary: Mapping[str, Any]) -> dict[str, Any]:
    if summary.get("candidate") != M024_HOLDOUT_CANDIDATE:
        raise ValueError("only H-UJ may be assessed")

    readiness = summary.get("readiness") or {}
    partition = summary.get("partition") or {}
    direction = summary.get("direction_invariants") or {}
    symbols = summary.get("symbol_invariants") or {}
    tp = summary.get("tp_safety") or {}
    safety = summary.get("safety") or {}

    invariant_checks = {
        "readiness_artifact": readiness.get("artifact_sha256")
        == M024_ACCEPTED_READINESS_SHA256,
        "partition_spec": readiness.get("partition_spec_sha256")
        == M024_ACCEPTED_PARTITION_SPEC_SHA256,
        "date_sha": readiness.get("date_list_sha256")
        == M024_ACCEPTED_DATE_LIST_SHA256
        and partition.get("date_list_sha256") == M024_ACCEPTED_DATE_LIST_SHA256,
        "replay_sha": readiness.get("replay_boundary_sha256")
        == M024_ACCEPTED_REPLAY_SHA256
        and partition.get("replay_boundary_sha256")
        == M024_ACCEPTED_REPLAY_SHA256,
        "block_hashes": readiness.get("block_sha256")
        == M024_ACCEPTED_BLOCK_SHA256,
        "strategy_symbols": summary.get("strategy_symbols") == ["USDJPY"],
        "market_symbols": summary.get("market_data_symbols")
        == ["EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"],
        "buy_only": summary.get("direction") == "BUY",
        "sell_entries_zero": int(direction.get("sell_accepted_entries", -1)) == 0,
        "excluded_symbol_rows_zero": int(
            symbols.get("excluded_symbol_closed_trade_rows", -1)
        ) == 0,
        "m15_disabled": summary.get("m15_signal_enabled") is False,
        "session_all_hours": summary.get("session") == "all-hours",
        "position_size": float(summary.get("position_size", 0.0)) == 0.1,
        "wrong_side_tp_zero": int(tp.get("wrong_side_initial_tp", -1)) == 0,
        "negative_pl_tp_zero": int(
            tp.get("negative_pl_take_profit_exits", -1)
        ) == 0,
        "m021_unused": safety.get("m021_post_cutoff_data_used") is False,
        "m025_unused": safety.get("m025_outcomes_used") is False,
        "real_order_unused": safety.get("real_order_api_called") is False,
        "session_filter_absent": safety.get("session_filter_applied") is False,
        "weekday_filter_absent": safety.get("weekday_filter_applied") is False,
        "market_data_not_reduced": (
            safety.get("market_data_universe_reduced") is False
        ),
    }
    if not all(invariant_checks.values()):
        return {
            "classification": "INELIGIBLE — INVARIANT FAILURE",
            "invariant_checks": invariant_checks,
            "supported": False,
        }

    aggregate = summary.get("aggregate") or {}
    closed = int(aggregate.get("closed_trades", 0))
    net_pl = float(aggregate.get("net_realized_pl", 0.0))
    mean_pl = net_pl / closed if closed else None

    blocks = summary.get("blocks") or {}
    block_rows = {
        label: {
            "closed_trades": int((blocks.get(label) or {}).get("closed_trades", 0)),
            "net_realized_pl": float(
                (blocks.get(label) or {}).get("net_realized_pl", 0.0)
            ),
            "mean_trade_pl": (blocks.get(label) or {}).get("mean_trade_pl"),
        }
        for label in ("H1", "H2", "H3")
    }

    date_counts = summary.get("trading_date_counts") or {}
    represented_dates = sum(int(count) > 0 for count in date_counts.values())
    weeks = summary.get("iso_weeks") or {}
    eligible_weeks = [
        row for row in weeks.values()
        if int(row.get("closed_trades", 0)) >= 5
    ]
    positive_mean_weeks = [
        row for row in eligible_weeks
        if row.get("mean_trade_pl") is not None
        and float(row["mean_trade_pl"]) > 0
    ]
    positive_week_ratio = (
        len(positive_mean_weeks) / len(eligible_weeks)
        if eligible_weeks else 0.0
    )

    representation = {
        "total_closed_trades_ge_200": closed >= 200,
        "each_block_closed_trades_ge_50": all(
            row["closed_trades"] >= 50 for row in block_rows.values()
        ),
        "represented_dates_ge_80pct": represented_dates / 57 >= 0.80,
        "eligible_iso_weeks_ge_8": len(eligible_weeks) >= 8,
        "closed_trades": closed,
        "represented_trading_dates": represented_dates,
        "represented_date_fraction": represented_dates / 57,
        "eligible_iso_weeks": len(eligible_weeks),
    }
    representation["ok"] = all(
        representation[key]
        for key in (
            "total_closed_trades_ge_200",
            "each_block_closed_trades_ge_50",
            "represented_dates_ge_80pct",
            "eligible_iso_weeks_ge_8",
        )
    )
    if not representation["ok"]:
        return {
            "classification": "HOLDOUT NOT SUPPORTED",
            "invariant_checks": invariant_checks,
            "representation": representation,
            "supported": False,
        }

    positive_blocks = [
        row for row in block_rows.values()
        if row["net_realized_pl"] > 0
    ]
    positive_block_sum = sum(row["net_realized_pl"] for row in positive_blocks)
    max_positive_block_share = (
        max(row["net_realized_pl"] for row in positive_blocks)
        / positive_block_sum
        if positive_block_sum > 0
        else None
    )

    support = {
        "aggregate_net_pl_positive": net_pl > 0,
        "aggregate_mean_trade_pl_positive": mean_pl is not None and mean_pl > 0,
        "positive_net_pl_blocks_ge_2": sum(
            row["net_realized_pl"] > 0 for row in block_rows.values()
        ) >= 2,
        "positive_mean_blocks_ge_2": sum(
            row["mean_trade_pl"] is not None
            and float(row["mean_trade_pl"]) > 0
            for row in block_rows.values()
        ) >= 2,
        "positive_block_concentration_le_70pct": (
            max_positive_block_share is not None
            and max_positive_block_share <= 0.70
        ),
        "positive_mean_iso_weeks_ge_50pct": positive_week_ratio >= 0.50,
    }
    supported = all(support.values())
    return {
        "classification": (
            "HOLDOUT SUPPORTED — RESEARCH VALIDATION ONLY"
            if supported
            else "HOLDOUT NOT SUPPORTED"
        ),
        "supported": supported,
        "invariant_checks": invariant_checks,
        "representation": representation,
        "support_checks": support,
        "economics": {
            "closed_trades": closed,
            "net_realized_pl": net_pl,
            "mean_trade_pl": mean_pl,
            "maximum_equity_drawdown": aggregate.get("maximum_equity_drawdown"),
            "maximum_equity_drawdown_pct": aggregate.get(
                "maximum_equity_drawdown_pct"
            ),
            "win_rate_nonflat_pct": aggregate.get("win_rate_nonflat_pct"),
        },
        "blocks": block_rows,
        "weekly": {
            "eligible_iso_weeks": len(eligible_weeks),
            "positive_mean_iso_weeks": len(positive_mean_weeks),
            "positive_mean_iso_week_ratio": positive_week_ratio,
        },
        "max_positive_block_pl_share": max_positive_block_share,
    }


def assess_file(summary_path: str | Path) -> dict[str, Any]:
    path = Path(summary_path)
    summary = json.loads(path.read_text(encoding="utf-8"))
    result = assess_summary(summary)
    result["summary_path"] = str(path)
    result["summary_sha256"] = _sha256_path(path)
    result["historical_holdout_execution_authorized"] = False
    result["production_live_promotion_authorized"] = False
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mechanically assess the one-shot M024 H-UJ holdout."
    )
    parser.add_argument("--summary", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    result = assess_file(args.summary)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
