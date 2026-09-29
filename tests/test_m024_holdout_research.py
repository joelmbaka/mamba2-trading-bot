from __future__ import annotations

from copy import deepcopy

import pytest

from mamba2.backtest.m024_holdout_assessment import assess_summary
from mamba2.backtest.m024_holdout_research import (
    M024_ACCEPTED_BLOCK_SHA256,
    M024_ACCEPTED_DATE_LIST_SHA256,
    M024_ACCEPTED_PARTITION_SPEC_SHA256,
    M024_ACCEPTED_READINESS_SHA256,
    M024_ACCEPTED_REPLAY_SHA256,
    M024_HOLDOUT_CANDIDATE,
    load_accepted_readiness,
)


def _summary():
    weeks = {
        f"2026-W{index:02d}": {
            "closed_trades": 20,
            "mean_trade_pl": 1.0 if index <= 4 else -0.5,
        }
        for index in range(1, 9)
    }
    dates = {f"2026-07-{index:02d}": 4 for index in range(1, 58)}
    return {
        "candidate": M024_HOLDOUT_CANDIDATE,
        "strategy_symbols": ["USDJPY"],
        "market_data_symbols": [
            "EURUSD", "EURJPY", "GBPUSD", "GBPJPY", "USDJPY"
        ],
        "direction": "BUY",
        "session": "all-hours",
        "m15_signal_enabled": False,
        "position_size": 0.1,
        "readiness": {
            "artifact_sha256": M024_ACCEPTED_READINESS_SHA256,
            "partition_spec_sha256": M024_ACCEPTED_PARTITION_SPEC_SHA256,
            "date_list_sha256": M024_ACCEPTED_DATE_LIST_SHA256,
            "replay_boundary_sha256": M024_ACCEPTED_REPLAY_SHA256,
            "block_sha256": dict(M024_ACCEPTED_BLOCK_SHA256),
        },
        "partition": {
            "date_list_sha256": M024_ACCEPTED_DATE_LIST_SHA256,
            "replay_boundary_sha256": M024_ACCEPTED_REPLAY_SHA256,
        },
        "aggregate": {
            "closed_trades": 240,
            "net_realized_pl": 120.0,
            "maximum_equity_drawdown": 50.0,
            "maximum_equity_drawdown_pct": 0.5,
            "win_rate_nonflat_pct": 45.0,
        },
        "blocks": {
            "H1": {"closed_trades": 80, "net_realized_pl": 30.0, "mean_trade_pl": 0.375},
            "H2": {"closed_trades": 80, "net_realized_pl": 40.0, "mean_trade_pl": 0.5},
            "H3": {"closed_trades": 80, "net_realized_pl": 50.0, "mean_trade_pl": 0.625},
        },
        "iso_weeks": weeks,
        "trading_date_counts": dates,
        "direction_invariants": {"sell_accepted_entries": 0},
        "symbol_invariants": {"excluded_symbol_closed_trade_rows": 0},
        "tp_safety": {
            "wrong_side_initial_tp": 0,
            "negative_pl_take_profit_exits": 0,
        },
        "safety": {
            "m021_post_cutoff_data_used": False,
            "m025_outcomes_used": False,
            "real_order_api_called": False,
            "session_filter_applied": False,
            "weekday_filter_applied": False,
            "market_data_universe_reduced": False,
        },
    }


def test_only_h_uj_candidate_is_assessable():
    summary = _summary()
    summary["candidate"] = "H-JPY"
    with pytest.raises(ValueError, match="only H-UJ"):
        assess_summary(summary)


def test_supported_requires_every_frozen_gate():
    result = assess_summary(_summary())
    assert result["classification"] == (
        "HOLDOUT SUPPORTED — RESEARCH VALIDATION ONLY"
    )
    assert result["supported"] is True
    assert result["representation"]["ok"] is True
    assert all(result["support_checks"].values())


def test_failed_economic_gate_is_not_supported():
    summary = _summary()
    summary["aggregate"]["net_realized_pl"] = -1.0
    result = assess_summary(summary)
    assert result["classification"] == "HOLDOUT NOT SUPPORTED"
    assert result["support_checks"]["aggregate_net_pl_positive"] is False


def test_failed_representation_stops_support():
    summary = _summary()
    summary["aggregate"]["closed_trades"] = 199
    result = assess_summary(summary)
    assert result["classification"] == "HOLDOUT NOT SUPPORTED"
    assert result["representation"]["total_closed_trades_ge_200"] is False


def test_readiness_hash_drift_is_invariant_failure():
    summary = _summary()
    summary["readiness"]["date_list_sha256"] = "drift"
    result = assess_summary(summary)
    assert result["classification"] == "INELIGIBLE — INVARIANT FAILURE"
    assert result["invariant_checks"]["date_sha"] is False


def test_readiness_is_required_before_source_manifest_access():
    with pytest.raises(FileNotFoundError, match="readiness artifact required"):
        load_accepted_readiness("/definitely/not/readiness.json")
