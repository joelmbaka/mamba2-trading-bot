from __future__ import annotations

from copy import deepcopy

import pytest

from mamba2.backtest.m024_symbol_specialization import (
    M024_DATE_LIST_SHA256,
    M024_EXPECTED_SYMBOLS,
    M024_SUBSETS,
    build_report_from_summary,
    validate_accepted_d_b_summary,
)


def _symbol(closed, pl, *, wins=None, losses=None):
    row = {
        "closed_trades": closed,
        "net_realized_pl": pl,
        "mean_trade_pl": pl / closed,
    }
    if wins is not None:
        row["wins"] = wins
    if losses is not None:
        row["losses"] = losses
    return row


def _synthetic_summary():
    symbols = {
        "EURUSD": _symbol(100, -100.0, wins=40, losses=60),
        "EURJPY": _symbol(100, -50.0, wins=45, losses=55),
        "GBPUSD": _symbol(100, -100.0, wins=40, losses=60),
        "GBPJPY": _symbol(100, -50.0, wins=45, losses=55),
        "USDJPY": _symbol(100, 100.0, wins=60, losses=40),
    }

    fold_usdjpy = [10.0, 20.0, 30.0, -5.0, 45.0]
    folds = {}
    for index, usdjpy_pl in enumerate(fold_usdjpy, start=1):
        folds[f"F{index}"] = {
            "per_symbol": {
                "EURUSD": _symbol(20, -20.0),
                "EURJPY": _symbol(20, -10.0),
                "GBPUSD": _symbol(20, -20.0),
                "GBPJPY": _symbol(20, -10.0),
                "USDJPY": _symbol(20, usdjpy_pl),
            }
        }

    weeks = {}
    for index in range(1, 25):
        usdjpy_pl = 3.0 if index <= 15 else -1.0
        weeks[f"2026-W{index:02d}"] = {
            "per_symbol": {
                "EURUSD": _symbol(5, -5.0),
                "EURJPY": _symbol(5, -5.0),
                "GBPUSD": _symbol(5, -5.0),
                "GBPJPY": _symbol(5, -5.0),
                "USDJPY": _symbol(5, usdjpy_pl),
            }
        }

    return {
        "milestone": "M023",
        "stage": "A",
        "experiment_id": "M023-A-D-B",
        "arm_id": "D-B",
        "direction": "BUY",
        "parameters": {
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
        },
        "cost_contract": (
            "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
            "SWAP-UNMODELED"
        ),
        "partition": {
            "start_utc": "2025-08-25T00:00:00Z",
            "end_exclusive_utc": "2026-07-08T00:00:00Z",
            "trading_dates": 225,
            "date_list_sha256": M024_DATE_LIST_SHA256,
            "strict_common_boundary_clock": True,
            "full_symbol_m1_preserved": True,
            "folds": [{}, {}, {}, {}, {}],
        },
        "aggregate": {"closed_trades": 500},
        "per_symbol": symbols,
        "folds": folds,
        "iso_weeks": weeks,
        "direction_invariants": {"sell_accepted_entries": 0},
        "tp_safety": {
            "negative_pl_take_profit_exits": 0,
            "wrong_side_initial_tp": 0,
        },
        "safety": {
            "historical_holdout_economic_data_used": False,
            "m021_post_cutoff_data_used": False,
            "real_order_api_called": False,
            "session_filter_applied": False,
            "weekday_filter_applied": False,
        },
    }


def test_frozen_subset_matrix_is_exact():
    assert M024_SUBSETS == {
        "SYM-R": M024_EXPECTED_SYMBOLS,
        "SYM-UJ": ("USDJPY",),
        "SYM-JPY": ("EURJPY", "GBPJPY", "USDJPY"),
        "SYM-NONJPY": ("EURUSD", "GBPUSD"),
    }


def test_source_invariants_require_exact_m023_d_b_contract():
    summary = _synthetic_summary()
    checks = validate_accepted_d_b_summary(summary)
    assert all(checks.values())

    drifted = deepcopy(summary)
    drifted["direction"] = "BOTH"
    checks = validate_accepted_d_b_summary(drifted)
    assert checks["direction"] is False


def test_report_is_descriptive_only_and_never_claims_replay():
    report = build_report_from_summary(
        _synthetic_summary(),
        source={"a_sha256": "x", "b_sha256": "x"},
    )
    assert report["analysis_kind"] == "DESCRIPTIVE SUBSET ATTRIBUTION"
    assert report["causal_symbol_filtered_replay"] is False
    assert report["safety"]["economic_replay_run"] is False
    assert report["partition"]["historical_holdout_accessed"] is False


def test_usdjpy_can_be_descriptively_promising_only_by_frozen_rules():
    report = build_report_from_summary(
        _synthetic_summary(),
        source={"a_sha256": "x", "b_sha256": "x"},
    )
    row = report["subsets"]["SYM-UJ"]

    assert row["overall"]["net_realized_pl"] == 100.0
    assert row["overall"]["mean_trade_pl"] == 1.0
    assert row["fold_stability"]["positive_net_pl_fold_count"] == 4
    assert row["fold_stability"]["positive_mean_trade_pl_fold_count"] == 4
    assert row["fold_stability"]["max_positive_fold_pl_share"] == pytest.approx(
        45.0 / 105.0
    )
    assert row["weekly_stability"]["eligible_week_count"] == 24
    assert row["weekly_stability"][
        "positive_mean_trade_pl_week_fraction"
    ] == pytest.approx(15.0 / 24.0)
    assert row["classification"] == "DESCRIPTIVELY PROMISING"


def test_multi_symbol_subset_is_weighted_by_trade_count_not_symbol_average():
    summary = _synthetic_summary()
    summary["per_symbol"]["EURJPY"] = _symbol(10, 100.0, wins=8, losses=2)
    summary["per_symbol"]["GBPJPY"] = _symbol(90, -90.0, wins=30, losses=60)
    summary["per_symbol"]["USDJPY"] = _symbol(100, 100.0, wins=60, losses=40)
    summary["aggregate"]["closed_trades"] = 400

    report = build_report_from_summary(
        summary,
        source={"a_sha256": "x", "b_sha256": "x"},
    )
    overall = report["subsets"]["SYM-JPY"]["overall"]

    assert overall["closed_trades"] == 200
    assert overall["net_realized_pl"] == 110.0
    assert overall["mean_trade_pl"] == pytest.approx(110.0 / 200.0)


def test_negative_or_unstable_subset_is_not_supported():
    summary = _synthetic_summary()
    for fold in summary["folds"].values():
        fold["per_symbol"]["USDJPY"]["net_realized_pl"] = -1.0
        fold["per_symbol"]["USDJPY"]["mean_trade_pl"] = -0.05

    report = build_report_from_summary(
        summary,
        source={"a_sha256": "x", "b_sha256": "x"},
    )
    row = report["subsets"]["SYM-UJ"]

    assert row["classification"] == "DESCRIPTIVELY UNSUPPORTED"
    assert row["descriptive_screen_checks"]["positive_net_pl_folds_ge_3"] is False


def test_report_hash_is_deterministic():
    summary = _synthetic_summary()
    source = {"a_sha256": "x", "b_sha256": "x"}
    first = build_report_from_summary(summary, source=source)
    second = build_report_from_summary(summary, source=source)
    assert first["report_sha256"] == second["report_sha256"]
