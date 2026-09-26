"""M020-D causal decision-time spread treatment tests."""

from types import SimpleNamespace

import pandas as pd

from mamba2.backtest import m020_spread_treatment


def _broker_for_spread(spread_points):
    broker = m020_spread_treatment.DecisionSpreadFilterBroker.__new__(
        m020_spread_treatment.DecisionSpreadFilterBroker
    )
    broker.feed = SimpleNamespace(
        current_time=pd.Timestamp("2026-07-01T00:01:00Z")
    )
    broker.max_spread_points = 10.0
    broker.rejected_orders = []
    broker.accepted_decision_spreads = {}
    broker._next_order_id = 1
    broker._pending = []
    broker.symbol_info_tick = lambda symbol: {
        "bid": 1.1000,
        "ask": 1.1000 + spread_points * 0.0001,
    }
    broker.get_point_size = lambda symbol: 0.0001
    return broker


def test_m020d_allows_exactly_10_points():
    broker = _broker_for_spread(10.0)

    result = broker.order_send(
        {
            "symbol": "EURUSD",
            "type": 0,
            "volume": 0.1,
        }
    )

    assert result["order"] == 1
    assert len(broker._pending) == 1
    assert broker.rejected_orders == []
    assert broker.accepted_decision_spreads[1]["spread_points"] == 10.0


def test_m020d_rejects_above_10_points_without_pending_order():
    broker = _broker_for_spread(10.1)

    result = broker.order_send(
        {
            "symbol": "EURUSD",
            "type": 1,
            "volume": 0.1,
        }
    )

    assert result["retcode"] == 1
    assert result["order"] == 0
    assert broker._pending == []
    assert broker.accepted_decision_spreads == {}
    assert len(broker.rejected_orders) == 1
    assert broker.rejected_orders[0]["side"] == "SELL"
    assert broker.rejected_orders[0]["spread_points"] == 10.1


def test_m020d_accepted_spread_gate_detects_violation():
    trades = [
        {
            "order_id": 1,
            "position_ticket": 11,
            "symbol": "EURUSD",
            "side": "BUY",
            "entry_time_utc": "2026-07-01T00:02:00Z",
            "outcome": "loss",
            "net_realized_pl": -1.0,
        },
        {
            "order_id": 2,
            "position_ticket": 12,
            "symbol": "GBPJPY",
            "side": "SELL",
            "entry_time_utc": "2026-07-01T00:03:00Z",
            "outcome": "win",
            "net_realized_pl": 2.0,
        },
    ]
    accepted = {
        1: {
            "timestamp_utc": "2026-07-01T00:01:00Z",
            "spread_points": 10.0,
        },
        2: {
            "timestamp_utc": "2026-07-01T00:02:00Z",
            "spread_points": 11.0,
        },
    }

    result = m020_spread_treatment._accepted_spread_stats(
        trades,
        accepted,
    )

    assert result["closed_trade_rows_with_decision_spread"] == 2
    assert result["accepted_spread_violation_count"] == 1
    assert result["maximum_accepted_decision_spread_points"] == 11.0
    assert result["accepted_spread_violations"][0][
        "position_ticket"
    ] == 12
