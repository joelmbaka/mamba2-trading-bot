"""TEMPORARY M018 local diagnostic extraction.

This test intentionally fails to surface selected rows from the ignored,
already-accepted M017 diagnostic artifact through the fixed local-control
pytest action. Remove this file after the evidence is captured.
"""

import json
from pathlib import Path

import pytest


DIAGNOSTIC = Path(
    "backtest_data/first-baseline-20260901-20260925/diagnostic-a.json"
)


def _report():
    if not DIAGNOSTIC.is_file():
        pytest.skip("accepted local M017 diagnostic artifact is unavailable")
    return json.loads(DIAGNOSTIC.read_text(encoding="utf-8"))


def _compact_trade(row):
    return {
        key: row.get(key)
        for key in (
            "order_id",
            "position_ticket",
            "symbol",
            "side",
            "entry_time_utc",
            "entry_price",
            "exit_time_utc",
            "exit_price",
            "exit_reason",
            "gross_realized_pl",
            "net_realized_pl",
            "entry_spread",
            "initial_protection",
            "trailing_modifications",
            "final_sl",
            "final_tp",
            "exit_spread_open",
            "exit_spread_close",
            "exit_conversion",
        )
    }


def test_surface_negative_take_profit_trades():
    rows = [
        _compact_trade(row)
        for row in _report()["trades"]
        if row["exit_reason"] == "take_profit"
        and float(row["net_realized_pl"]) < 0
    ]
    assert False, "NEGATIVE_TP_TRADES=" + json.dumps(
        rows,
        sort_keys=True,
        separators=(",", ":"),
    )


def test_surface_largest_entry_spread_trade_per_symbol():
    rows = _report()["trades"]
    selected = {}
    for symbol in sorted({row["symbol"] for row in rows}):
        candidates = [row for row in rows if row["symbol"] == symbol]
        selected[symbol] = _compact_trade(
            max(
                candidates,
                key=lambda row: float(
                    row["entry_spread"]["spread_points"]
                ),
            )
        )
    assert False, "MAX_SPREAD_TRADES=" + json.dumps(
        selected,
        sort_keys=True,
        separators=(",", ":"),
    )


def test_surface_buy_sell_payoff_components():
    rows = _report()["trades"]
    summary = {}
    for side in ("BUY", "SELL"):
        side_rows = [row for row in rows if row["side"] == side]
        wins = [
            float(row["net_realized_pl"])
            for row in side_rows
            if float(row["net_realized_pl"]) > 0
        ]
        losses = [
            float(row["net_realized_pl"])
            for row in side_rows
            if float(row["net_realized_pl"]) < 0
        ]
        summary[side] = {
            "trades": len(side_rows),
            "wins": len(wins),
            "losses": len(losses),
            "avg_win": sum(wins) / len(wins),
            "avg_loss": sum(losses) / len(losses),
            "total_win_pl": sum(wins),
            "total_loss_pl": sum(losses),
            "take_profit": {
                "count": sum(
                    row["exit_reason"] == "take_profit"
                    for row in side_rows
                ),
                "pl": sum(
                    float(row["net_realized_pl"])
                    for row in side_rows
                    if row["exit_reason"] == "take_profit"
                ),
            },
            "stop_loss": {
                "count": sum(
                    row["exit_reason"] == "stop_loss"
                    for row in side_rows
                ),
                "pl": sum(
                    float(row["net_realized_pl"])
                    for row in side_rows
                    if row["exit_reason"] == "stop_loss"
                ),
            },
        }
    assert False, "SIDE_PAYOFF=" + json.dumps(
        summary,
        sort_keys=True,
        separators=(",", ":"),
    )
