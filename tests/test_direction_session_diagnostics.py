from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mamba2.backtest.direction_session_diagnostics import (
    _window_labels,
    build_folds,
    decorate_trade,
    summarize,
)


def _trade(
    *,
    time="2026-01-15T08:00:00Z",
    side="SELL",
    outcome="win",
    pl=10.0,
    symbol="EURUSD",
    spread=5.0,
    reason="take_profit",
):
    return {
        "position_ticket": 1,
        "symbol": symbol,
        "side": side,
        "entry_time_utc": time,
        "exit_time_utc": time,
        "outcome": outcome,
        "net_realized_pl": pl,
        "gross_realized_pl": pl,
        "entry_spread": {"spread_points": spread},
        "exit_reason": reason,
    }


def test_timezone_conversion_is_dst_aware():
    winter = decorate_trade(_trade(time="2026-01-15T08:00:00Z"))
    summer = decorate_trade(_trade(time="2026-07-15T08:00:00Z"))

    assert winter["_eat_hour"] == 11
    assert summer["_eat_hour"] == 11

    assert winter["_london_hour"] == 8
    assert summer["_london_hour"] == 9

    assert winter["_new_york_hour"] == 3
    assert summer["_new_york_hour"] == 4


def test_fixed_eat_and_market_windows():
    morning = datetime(2026, 1, 15, 5, 0, tzinfo=timezone.utc)
    labels = _window_labels(morning)
    assert "EAT-MORNING" in labels
    assert "EAT-ACTIVE" in labels
    assert "EAT-OFF-HOURS" not in labels

    off_hours = datetime(2026, 1, 15, 3, 0, tzinfo=timezone.utc)
    labels = _window_labels(off_hours)
    assert "EAT-OFF-HOURS" in labels
    assert "EAT-ACTIVE" not in labels

    london_open = datetime(2026, 1, 15, 8, 0, tzinfo=timezone.utc)
    assert "LONDON-OPEN-TRANSITION" in _window_labels(london_open)

    overlap = datetime(2026, 7, 15, 13, 0, tzinfo=timezone.utc)
    assert "LONDON-NY-OVERLAP" in _window_labels(overlap)


def test_summarize_required_trade_metrics():
    rows = [
        _trade(outcome="win", pl=10.0, spread=4.0, reason="take_profit"),
        _trade(
            outcome="loss",
            pl=-5.0,
            spread=6.0,
            reason="stop_loss",
            symbol="GBPUSD",
        ),
        _trade(
            outcome="flat",
            pl=0.0,
            spread=5.0,
            reason="manual",
            symbol="GBPUSD",
        ),
    ]
    result = summarize(rows)

    assert result["closed_trades"] == 3
    assert result["wins"] == 1
    assert result["losses"] == 1
    assert result["flats"] == 1
    assert result["win_rate_nonflat_pct"] == 50.0
    assert result["net_realized_pl"] == 5.0
    assert result["mean_trade_pl"] == pytest.approx(5.0 / 3.0)
    assert result["median_trade_pl"] == 0.0
    assert result["entry_spread_points"]["mean"] == 5.0
    assert result["entry_spread_points"]["median"] == 5.0
    assert result["exit_counts"] == {
        "take_profit": 1,
        "stop_loss": 1,
        "other": 1,
    }
    assert result["per_symbol"]["EURUSD"]["closed_trades"] == 1
    assert result["per_symbol"]["GBPUSD"]["net_realized_pl"] == -5.0


def test_build_folds_requires_exact_225_dates_and_is_chronological():
    rows = []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    for index in range(225):
        current = start.fromordinal(start.toordinal() + index)
        rows.append({"_entry_date_utc": current.date().isoformat()})

    folds = build_folds(rows)
    assert len(folds) == 5
    assert [fold["trading_dates"] for fold in folds] == [45] * 5
    assert folds[0]["first_date"] == "2025-01-01"
    assert folds[4]["last_date"] == "2025-08-13"
    assert all(len(fold["date_list_sha256"]) == 64 for fold in folds)

    with pytest.raises(ValueError, match="expected 225"):
        build_folds(rows[:-1])


def test_decorate_trade_preserves_original_and_adds_diagnostic_labels():
    row = _trade(time="2026-07-15T13:30:00Z", side="BUY")
    decorated = decorate_trade(row)

    assert decorated["side"] == "BUY"
    assert decorated["entry_time_utc"] == row["entry_time_utc"]
    assert decorated["_weekday"] == "Wednesday"
    assert "LONDON-NY-OVERLAP" in decorated["_windows"]
