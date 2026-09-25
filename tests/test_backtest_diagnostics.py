"""Non-interference and evidence tests for baseline diagnostics."""

import asyncio
import json

import pandas as pd

from mamba2.backtest.broker import HistoricalBroker, SymbolExecutionMetadata
from mamba2.backtest.diagnostics import (
    DiagnosticHistoricalBroker,
    _drawdown_episodes,
    _loss_streaks,
    write_diagnostic_report,
)
from mamba2.backtest.feed import ReplayFeed


class _Atr:
    def get_atr(self, symbol, timeframe):
        assert symbol == "EURUSD"
        assert timeframe == "M5"
        return 0.00125


def _frames():
    times = pd.date_range(
        "2026-09-01T10:00:00Z",
        periods=4,
        freq="min",
    )
    bid = pd.DataFrame(
        {
            "time": times,
            "open": [1.1000, 1.1010, 1.1020, 1.1030],
            "high": [1.1005, 1.1015, 1.1025, 1.1035],
            "low": [1.0995, 1.1005, 1.1015, 1.1025],
            "close": [1.1002, 1.1012, 1.1022, 1.1032],
            "tick_volume": [10, 10, 10, 10],
            "spread": [20, 20, 20, 20],
            "real_volume": [0, 0, 0, 0],
        }
    )
    ask = pd.DataFrame(
        {
            "time": times,
            "open": [1.1002, 1.1012, 1.1022, 1.1032],
            "high": [1.1007, 1.1017, 1.1027, 1.1037],
            "low": [1.0997, 1.1007, 1.1017, 1.1027],
            "close": [1.1004, 1.1014, 1.1024, 1.1034],
        }
    )
    return bid, ask


def _make_broker(cls):
    bid, ask = _frames()
    feed = ReplayFeed(
        {"EURUSD": bid},
        ask_m1_bars={"EURUSD": ask},
    )
    broker = cls(
        feed,
        symbol_metadata={
            "EURUSD": SymbolExecutionMetadata(
                point_size=0.00001,
                digits=5,
                contract_size=100_000.0,
                base_currency="EUR",
                quote_currency="USD",
            )
        },
        account_currency="USD",
    )
    return broker


def _exercise(broker):
    broker.advance()
    broker.order_send(
        {
            "symbol": "EURUSD",
            "type": 0,
            "volume": 0.1,
        }
    )
    broker.settle_pending_orders()
    position = broker.position_get_ticket(1)
    assert position is not None

    asyncio.run(
        broker.order_modify(
            1,
            sl=position["price_current"] - 0.0010,
            tp=position["price_current"] + 0.0020,
        )
    )
    position = broker.position_get_ticket(1)
    asyncio.run(
        broker.order_modify(
            1,
            sl=position["sl"] + 0.0002,
            tp=position["tp"] + 0.0002,
        )
    )

    broker.advance()
    assert broker.position_close(1, reason="manual")
    return broker


def test_diagnostic_broker_preserves_base_broker_account_and_trade_semantics():
    base = _exercise(_make_broker(HistoricalBroker))

    diagnostic = _make_broker(DiagnosticHistoricalBroker)
    diagnostic.attach_atr_manager(_Atr())
    diagnostic = _exercise(diagnostic)

    assert diagnostic.account_info() == base.account_info()
    assert diagnostic.closed_trades == base.closed_trades

    rows = diagnostic.trade_diagnostics()
    assert len(rows) == 1
    row = rows[0]
    assert row["position_ticket"] == 1
    assert row["order_id"] == 1
    assert row["side"] == "BUY"
    assert row["entry_spread"]["ask_source"] == "tick-derived"
    assert row["entry_spread"]["spread_points"] == 20
    assert row["initial_protection"]["atr"] == 0.00125
    assert row["trailing_modification_count"] == 1
    assert row["exit_conversion"]["route_type"] == "none"
    assert row["exit_conversion"]["route_label"] == "USD->USD:none"


def test_two_leg_conversion_trace_uses_same_boundary_observed_prices():
    times = pd.date_range(
        "2026-09-14T00:00:00Z",
        periods=2,
        freq="min",
    )

    def bars(open_price, point):
        return pd.DataFrame(
            {
                "time": times,
                "open": [open_price, open_price],
                "high": [open_price + point, open_price + point],
                "low": [open_price - point, open_price - point],
                "close": [open_price, open_price],
                "tick_volume": [10, 10],
                "spread": [10, 10],
                "real_volume": [0, 0],
            }
        )

    eurjpy = bars(160.0, 0.001)
    eurusd = bars(1.2, 0.00001)
    usdjpy = bars(150.0, 0.001).iloc[[0]].copy()
    feed = ReplayFeed(
        {
            "EURJPY": eurjpy,
            "EURUSD": eurusd,
            "USDJPY": usdjpy,
        }
    )
    broker = DiagnosticHistoricalBroker(
        feed,
        symbol_metadata={
            "EURJPY": SymbolExecutionMetadata(
                point_size=0.001,
                digits=3,
                base_currency="EUR",
                quote_currency="JPY",
            ),
            "EURUSD": SymbolExecutionMetadata(
                point_size=0.00001,
                digits=5,
                base_currency="EUR",
                quote_currency="USD",
            ),
            "USDJPY": SymbolExecutionMetadata(
                point_size=0.001,
                digits=3,
                base_currency="USD",
                quote_currency="JPY",
            ),
        },
        account_currency="USD",
    )
    broker.advance()

    trace = broker._trace_conversion(
        -1000.0,
        quote_currency="JPY",
        phase="execution",
        field="open",
    )

    assert trace["route_type"] == "two_leg"
    assert [leg["symbol"] for leg in trace["legs"]] == [
        "EURJPY",
        "EURUSD",
    ]
    assert trace["legs"][0]["from_currency"] == "JPY"
    assert trace["legs"][1]["to_currency"] == "USD"


def test_loss_streaks_and_drawdown_episodes_are_deterministic():
    trades = [
        {
            "exit_time_utc": "2026-09-01T10:00:00Z",
            "position_ticket": 1,
            "outcome": "loss",
            "net_realized_pl": -10.0,
        },
        {
            "exit_time_utc": "2026-09-01T10:01:00Z",
            "position_ticket": 2,
            "outcome": "loss",
            "net_realized_pl": -20.0,
        },
        {
            "exit_time_utc": "2026-09-01T10:02:00Z",
            "position_ticket": 3,
            "outcome": "win",
            "net_realized_pl": 5.0,
        },
        {
            "exit_time_utc": "2026-09-01T10:03:00Z",
            "position_ticket": 4,
            "outcome": "loss",
            "net_realized_pl": -3.0,
        },
    ]
    streaks = _loss_streaks(trades)
    assert streaks["maximum_consecutive_losses"] == 2
    assert streaks["maximum_loss_streak"]["net_realized_pl"] == -30.0
    assert streaks["streak_length_distribution"] == {"1": 1, "2": 1}

    curve = [
        {"timestamp": "2026-09-01T10:00:00Z", "equity": 100.0},
        {"timestamp": "2026-09-01T10:01:00Z", "equity": 90.0},
        {"timestamp": "2026-09-01T10:02:00Z", "equity": 80.0},
        {"timestamp": "2026-09-01T10:03:00Z", "equity": 105.0},
        {"timestamp": "2026-09-01T10:04:00Z", "equity": 100.0},
    ]
    episodes = _drawdown_episodes(curve, starting_equity=100.0)
    assert episodes[0]["maximum_drawdown"] == 20.0
    assert episodes[0]["maximum_drawdown_pct"] == 20.0
    assert episodes[0]["recovered"] is True
    assert episodes[1]["maximum_drawdown"] == 5.0
    assert episodes[1]["recovered"] is False


def test_diagnostic_json_writer_is_byte_deterministic(tmp_path):
    report = {
        "diagnostic_schema_version": 1,
        "analysis": {"b": 2, "a": 1},
        "trades": [{"position_ticket": 1, "net_realized_pl": -1.25}],
    }
    first = write_diagnostic_report(report, tmp_path / "a.json")
    second = write_diagnostic_report(report, tmp_path / "b.json")

    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text()) == report
