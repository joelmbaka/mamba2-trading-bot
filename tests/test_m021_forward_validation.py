"""Synthetic tests for the frozen M021 prospective-validation protocol."""

import json

import pandas as pd
import pytest

from mamba2.backtest import m021_forward_validation as m021


def _baseline(*, closed, pl, dd, dd_pct, equity=10000.0):
    return {
        "aggregate": {
            "accepted_orders": closed,
            "closed_trades": closed,
            "net_realized_pl": pl,
            "ending_equity": equity,
            "maximum_equity_drawdown": dd,
            "maximum_equity_drawdown_pct": dd_pct,
        },
        "per_symbol": {
            symbol: {"closed_trades": 200, "net_realized_pl": 1.0}
            for symbol in m021.M021_SYMBOLS
        },
    }


def test_readiness_refuses_before_primary_cutoff():
    result = m021.readiness(
        now_utc="2026-09-26T00:00:00Z",
        cutoff_utc="2026-10-23T00:00:00Z",
    )

    assert result["ready"] is False
    assert result["economic_results_computed"] is False
    assert result["prospective_start_utc"] == "2026-09-25T00:00:00Z"
    assert result["cutoff_utc"] == "2026-10-23T00:00:00Z"


def test_run_window_returns_before_manifest_or_replay_pre_cutoff(tmp_path):
    output = tmp_path / "output"
    result = m021.run_m021_window(
        tmp_path / "does-not-exist.json",
        output_dir=output,
        cutoff_utc="2026-10-23T00:00:00Z",
        now_utc="2026-09-26T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["reason"] == "frozen M021 cutoff is not complete"
    assert result["economic_results_computed"] is False
    assert not output.exists()


def test_only_frozen_cutoffs_are_accepted():
    with pytest.raises(ValueError, match="not one of the frozen"):
        m021.readiness(
            now_utc="2026-12-01T00:00:00Z",
            cutoff_utc="2026-10-24T00:00:00Z",
        )


def test_fixed_period_boundaries_are_stable():
    assert m021._period_index(
        "2026-09-25T00:00:00Z",
        cutoff_utc="2026-10-23T00:00:00Z",
    ) == 0
    assert m021._period_index(
        "2026-10-01T23:59:59Z",
        cutoff_utc="2026-10-23T00:00:00Z",
    ) == 0
    assert m021._period_index(
        "2026-10-02T00:00:00Z",
        cutoff_utc="2026-10-23T00:00:00Z",
    ) == 1
    with pytest.raises(ValueError, match="outside frozen M021 window"):
        m021._period_index(
            "2026-10-23T00:00:00Z",
            cutoff_utc="2026-10-23T00:00:00Z",
        )


def test_manifest_requires_exact_frozen_range_and_tick_ask(tmp_path):
    manifest = {
        "requested_range": {
            "from_utc": "2026-09-25T00:00:00Z",
            "to_utc": "2026-10-23T00:00:00Z",
        },
        "symbols": {
            symbol: {
                "files": {
                    "M1": {"sha256": "m1"},
                    "M5": {"sha256": "m5"},
                    "M15": {"sha256": "m15"},
                },
                "ask_m1": {
                    "source": "copy_ticks_range",
                    "sha256": "ask",
                },
            }
            for symbol in m021.M021_SYMBOLS
        },
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    loaded = m021._manifest_payload(
        path,
        cutoff_utc="2026-10-23T00:00:00Z",
    )
    assert loaded["requested_range"] == manifest["requested_range"]

    manifest["requested_range"]["from_utc"] = "2026-09-24T00:00:00Z"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="range mismatch"):
        m021._manifest_payload(
            path,
            cutoff_utc="2026-10-23T00:00:00Z",
        )


def test_rejection_gate_treats_10_as_allowed_and_above_10_as_rejected():
    stats = m021._rejection_stats(
        [
            {
                "symbol": "EURUSD",
                "side": "BUY",
                "timestamp_utc": "2026-09-25T01:00:00Z",
                "spread_points": 10.1,
            },
            {
                "symbol": "GBPJPY",
                "side": "SELL",
                "timestamp_utc": "2026-10-02T01:00:00Z",
                "spread_points": 11.0,
            },
        ],
        cutoff_utc="2026-10-23T00:00:00Z",
    )
    assert stats["minimum_rejected_decision_spread_points"] == 10.1
    assert stats["treatment_rejections_at_or_below_10_points"] == 0

    invalid = m021._rejection_stats(
        [
            {
                "symbol": "EURUSD",
                "side": "BUY",
                "timestamp_utc": "2026-09-25T01:00:00Z",
                "spread_points": 10.0,
            }
        ],
        cutoff_utc="2026-10-23T00:00:00Z",
    )
    assert invalid["treatment_rejections_at_or_below_10_points"] == 1


def test_minimum_evidence_requires_control_candidate_symbols_and_both_sides():
    control = _baseline(closed=1000, pl=-5, dd=100, dd_pct=1)
    candidate = _baseline(closed=900, pl=5, dd=90, dd_pct=0.9)
    sides = {
        "BUY": {"closed_trades": 300},
        "SELL": {"closed_trades": 300},
    }

    result = m021._minimum_evidence(control, candidate, sides)
    assert result["satisfied"] is True

    sides["SELL"]["closed_trades"] = 299
    result = m021._minimum_evidence(control, candidate, sides)
    assert result["satisfied"] is False
    assert result["checks"]["both_sides"] is False


def _delta(values):
    return {
        name: {"net_realized_pl_delta": value}
        for name, value in values.items()
    }


def test_predeclared_classification_forward_supported():
    control = _baseline(closed=1000, pl=-10, dd=100, dd_pct=1.0)
    candidate = _baseline(closed=900, pl=20, dd=90, dd_pct=0.9)
    count_gate = {"satisfied": True}

    classification = m021._classification(
        cutoff_utc="2026-10-23T00:00:00Z",
        count_gate=count_gate,
        deterministic=True,
        boundary_ok=True,
        safety_ok=True,
        control_baseline=control,
        candidate_baseline=candidate,
        symbol_delta=_delta({
            "EURUSD": 1,
            "EURJPY": 1,
            "GBPUSD": 1,
            "GBPJPY": 1,
            "USDJPY": -1,
        }),
        side_delta=_delta({"BUY": 1, "SELL": 1}),
        period_delta=_delta({"P01": 1, "P02": 1, "P03": 1, "P04": 0}),
    )

    assert classification == "FORWARD-SUPPORTED"


def test_predeclared_classification_mixed_when_improved_but_loss_making():
    control = _baseline(closed=1000, pl=-100, dd=100, dd_pct=1.0)
    candidate = _baseline(closed=900, pl=-20, dd=90, dd_pct=0.9)

    classification = m021._classification(
        cutoff_utc="2026-10-23T00:00:00Z",
        count_gate={"satisfied": True},
        deterministic=True,
        boundary_ok=True,
        safety_ok=True,
        control_baseline=control,
        candidate_baseline=candidate,
        symbol_delta=_delta({symbol: 1 for symbol in m021.M021_SYMBOLS}),
        side_delta=_delta({"BUY": 1, "SELL": 1}),
        period_delta=_delta({"P01": 1, "P02": 1, "P03": 1, "P04": 1}),
    )

    assert classification == "MIXED"


def test_insufficient_counts_extend_then_stop_at_eight_weeks():
    control = _baseline(closed=500, pl=0, dd=10, dd_pct=0.1)
    candidate = _baseline(closed=400, pl=0, dd=10, dd_pct=0.1)
    deltas = _delta({symbol: 0 for symbol in m021.M021_SYMBOLS})

    early = m021._classification(
        cutoff_utc="2026-10-23T00:00:00Z",
        count_gate={"satisfied": False},
        deterministic=True,
        boundary_ok=True,
        safety_ok=True,
        control_baseline=control,
        candidate_baseline=candidate,
        symbol_delta=deltas,
        side_delta=_delta({"BUY": 0, "SELL": 0}),
        period_delta=_delta({"P01": 0, "P02": 0, "P03": 0, "P04": 0}),
    )
    assert early == "EXTEND WITHOUT ECONOMIC INTERPRETATION"

    final = m021._classification(
        cutoff_utc="2026-11-20T00:00:00Z",
        count_gate={"satisfied": False},
        deterministic=True,
        boundary_ok=True,
        safety_ok=True,
        control_baseline=control,
        candidate_baseline=candidate,
        symbol_delta=deltas,
        side_delta=_delta({"BUY": 0, "SELL": 0}),
        period_delta=_delta({f"P{i:02d}": 0 for i in range(1, 9)}),
    )
    assert final == "INSUFFICIENT FOR CLASSIFICATION"


def test_cost_label_is_frozen_with_swap_unmodeled():
    assert m021.M021_COST_LABEL == (
        "SPREAD-INCLUDED / EXPLICIT-COMMISSION-AND-SLIPPAGE-ZERO / "
        "SWAP-UNMODELED"
    )
