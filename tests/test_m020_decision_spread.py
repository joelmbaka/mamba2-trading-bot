"""M020-C causal decision-time spread diagnostic tests."""

from types import SimpleNamespace

import pandas as pd

from mamba2.backtest import m020_decision_spread


def _trade(
    *,
    order_id,
    ticket,
    symbol,
    side,
    fill_time,
    fill_spread,
    outcome,
    pl,
):
    return {
        "order_id": order_id,
        "position_ticket": ticket,
        "symbol": symbol,
        "side": side,
        "entry_time_utc": fill_time,
        "entry_spread": {"spread_points": fill_spread},
        "outcome": outcome,
        "net_realized_pl": pl,
    }


def test_decision_broker_records_submission_spread_without_changing_order():
    broker = m020_decision_spread.DecisionSpreadDiagnosticBroker.__new__(
        m020_decision_spread.DecisionSpreadDiagnosticBroker
    )
    broker.feed = SimpleNamespace(
        current_time=pd.Timestamp("2026-07-01T00:01:00Z")
    )
    broker._next_order_id = 7
    broker._pending = []
    broker.decision_spreads = {}
    broker.symbol_info_tick = lambda symbol: {
        "bid": 1.1000,
        "ask": 1.1004,
    }
    broker.get_point_size = lambda symbol: 0.0001

    result = broker.order_send(
        {
            "symbol": "EURUSD",
            "type": 0,
            "volume": 0.1,
        }
    )

    assert result["order"] == 7
    assert len(broker._pending) == 1
    assert broker._pending[0]["submitted_at"] == pd.Timestamp(
        "2026-07-01T00:01:00Z"
    )
    assert broker.decision_spreads[7] == {
        "timestamp_utc": "2026-07-01T00:01:00Z",
        "bid": 1.1,
        "ask": 1.1004,
        "spread_price": 0.00039999999999995595,
        "spread_points": 4.0,
    }


def test_decision_report_reconciles_and_groups_causal_spreads():
    diagnostic = {
        "trades": [
            _trade(
                order_id=1,
                ticket=11,
                symbol="EURUSD",
                side="BUY",
                fill_time="2026-06-23T00:02:00Z",
                fill_spread=80.0,
                outcome="loss",
                pl=-10.0,
            ),
            _trade(
                order_id=2,
                ticket=12,
                symbol="GBPJPY",
                side="SELL",
                fill_time="2026-07-01T04:01:00Z",
                fill_spread=4.0,
                outcome="win",
                pl=5.0,
            ),
        ]
    }
    decisions = {
        1: {
            "timestamp_utc": "2026-06-23T00:01:00Z",
            "bid": 1.0,
            "ask": 1.0002,
            "spread_price": 0.0002,
            "spread_points": 2.0,
        },
        2: {
            "timestamp_utc": "2026-07-01T04:00:00Z",
            "bid": 2.0,
            "ask": 2.0012,
            "spread_price": 0.0012,
            "spread_points": 12.0,
        },
    }

    report = m020_decision_spread.build_decision_spread_report(
        diagnostic,
        decisions,
    )

    assert report["strategy_behavior_changed"] is False
    assert report["reconciliation"] == {
        "diagnostic_trade_rows": 2,
        "decision_spread_rows": 2,
        "missing_decision_spread_rows": 0,
    }
    assert report["by_decision_spread_band"]["00 <=2"][
        "net_realized_pl"
    ] == -10.0
    assert report["by_decision_spread_band"]["03 >10-20"][
        "net_realized_pl"
    ] == 5.0
    assert report["decision_to_fill_band_transitions"]["00 <=2"][
        "05 >50-100"
    ] == 1
    assert report["decision_to_fill_band_transitions"]["03 >10-20"][
        "01 >2-5"
    ] == 1
    assert report["by_symbol_and_decision_spread_band"]["EURUSD"][
        "00 <=2"
    ]["closed_trades"] == 1
    assert report["by_side_and_decision_spread_band"]["SELL"][
        "03 >10-20"
    ]["wins"] == 1
    assert report["by_entry_month_and_decision_spread_band"]["2026-06"][
        "00 <=2"
    ]["losses"] == 1


def test_decision_report_exposes_missing_submission_evidence():
    diagnostic = {
        "trades": [
            _trade(
                order_id=1,
                ticket=11,
                symbol="EURUSD",
                side="BUY",
                fill_time="2026-06-23T00:02:00Z",
                fill_spread=2.0,
                outcome="loss",
                pl=-1.0,
            ),
            _trade(
                order_id=2,
                ticket=12,
                symbol="EURUSD",
                side="BUY",
                fill_time="2026-06-23T00:03:00Z",
                fill_spread=2.0,
                outcome="win",
                pl=2.0,
            ),
        ]
    }
    decisions = {
        1: {
            "timestamp_utc": "2026-06-23T00:01:00Z",
            "bid": 1.0,
            "ask": 1.0001,
            "spread_price": 0.0001,
            "spread_points": 1.0,
        }
    }

    report = m020_decision_spread.build_decision_spread_report(
        diagnostic,
        decisions,
    )

    assert report["reconciliation"]["diagnostic_trade_rows"] == 2
    assert report["reconciliation"]["decision_spread_rows"] == 1
    assert report["reconciliation"]["missing_decision_spread_rows"] == 1
