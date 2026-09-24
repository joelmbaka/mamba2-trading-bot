"""Deterministic execution and position-lifecycle tests."""

import asyncio

import pandas as pd
import pytest

from mamba2.backtest import HistoricalBroker, ReplayFeed, SymbolExecutionMetadata


def make_broker(opens, highs, lows, closes):
    times = pd.date_range("2025-01-02 10:00", periods=len(opens), freq="min", tz="UTC")
    frame = pd.DataFrame(
        {
            "time": times,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "tick_volume": [10] * len(opens),
            "spread": [1] * len(opens),
            "real_volume": [100] * len(opens),
        }
    )
    metadata = {"EURUSD": SymbolExecutionMetadata(contract_size=100_000.0, point_size=0.00001, digits=5)}
    feed = ReplayFeed(frame)
    return HistoricalBroker(feed, symbol_metadata=metadata)


def open_position(broker, *, side=0, volume=1.0, **request):
    broker.advance()
    response = broker.order_send({"symbol": "EURUSD", "type": side, "volume": volume, **request})
    broker.settle_pending_orders()
    broker.advance()
    return response, broker.position_get_ticket(1)


def test_buy_unrealized_and_realized_pl_use_contract_size():
    broker = make_broker([100, 101, 102], [101, 104, 103], [99, 100, 101], [100, 103, 102])
    response, position = open_position(broker, volume=0.5)

    assert response["order"] == 1
    assert position["ticket"] == 1
    assert position["order_id"] == 1
    assert position["price_open"] == 101
    assert position["profit"] == 100_000.0
    info = broker.account_info()
    assert info["balance"] == 10_000.0
    assert info["realized_profit"] == 0.0
    assert info["unrealized_profit"] == 100_000.0
    assert info["equity"] == 110_000.0

    assert broker.position_close(1)
    info = broker.account_info()
    assert info["balance"] == 110_000.0
    assert info["realized_profit"] == 100_000.0
    assert info["unrealized_profit"] == 0.0
    assert broker.positions_total() == 0
    trade = broker.closed_trades[0]
    assert trade.order_id == 1
    assert trade.position_ticket == 1
    assert trade.close_price == 103
    assert trade.realized_pl == 100_000.0
    assert trade.exit_reason == "manual"


def test_sell_unrealized_and_realized_pl_use_short_direction():
    broker = make_broker([100, 99, 98], [101, 100, 99], [99, 96, 97], [100, 97, 98])
    _response, position = open_position(broker, side=1, volume=0.5)

    assert position["price_open"] == 99
    assert position["profit"] == 100_000.0
    assert broker.position_close(1)
    assert broker.account_info()["balance"] == 110_000.0
    assert broker.closed_trades[0].realized_pl == 100_000.0
    assert broker.closed_trades[0].side == 1


@pytest.mark.parametrize(
    ("side", "sl", "tp", "expected_price", "expected_reason"),
    [
        (0, 98, 104, 98, "stop_loss"),
        (1, 102, 96, 102, "stop_loss"),
    ],
)
def test_same_candle_sl_tp_uses_conservative_stop_first(side, sl, tp, expected_price, expected_reason):
    if side == 0:
        broker = make_broker([100, 100], [101, 105], [99, 95], [100, 102])
    else:
        broker = make_broker([100, 100], [101, 105], [99, 95], [100, 98])
    _response, position = open_position(broker, side=side, sl=sl, tp=tp)

    assert position is None
    trade = broker.closed_trades[0]
    assert trade.close_price == expected_price
    assert trade.exit_reason == expected_reason


def test_buy_and_sell_take_profit_exits():
    buy = make_broker([100, 100], [101, 105], [99, 99], [100, 104])
    _response, position = open_position(buy, side=0, sl=95, tp=103)
    assert position is None
    assert buy.closed_trades[0].close_price == 103
    assert buy.closed_trades[0].exit_reason == "take_profit"

    sell = make_broker([100, 100], [101, 101], [99, 95], [100, 96])
    _response, position = open_position(sell, side=1, sl=105, tp=97)
    assert position is None
    assert sell.closed_trades[0].close_price == 97
    assert sell.closed_trades[0].exit_reason == "take_profit"


def test_sl_tp_is_not_evaluated_until_execution_candle_completes():
    broker = make_broker([100, 100, 102], [101, 105, 103], [99, 95, 101], [100, 102, 102])
    broker.advance()  # replay time 10:01; source 10:00 is visible
    broker.order_send({"symbol": "EURUSD", "type": 0, "volume": 1.0, "sl": 98, "tp": 104})
    broker.settle_pending_orders()  # fill at 10:01 open

    assert broker.positions_total() == 1
    assert broker.closed_trades == ()

    broker.advance()  # replay time 10:02; source 10:01 range is now known
    assert broker.positions_total() == 0
    assert broker.closed_trades[0].exit_reason == "stop_loss"


def test_adverse_stop_gaps_fill_at_next_bar_open_for_buy_and_sell():
    buy = make_broker([100, 100, 95], [101, 101, 96], [99, 99, 94], [100, 100, 95])
    _response, position = open_position(buy)
    assert position is not None
    asyncio.run(buy.order_modify(position["ticket"], sl=98))
    buy.advance()
    assert buy.closed_trades[0].close_price == 95

    sell = make_broker([100, 100, 105], [101, 101, 106], [99, 99, 104], [100, 100, 105])
    _response, position = open_position(sell, side=1)
    assert position is not None
    asyncio.run(sell.order_modify(position["ticket"], sl=102))
    sell.advance()
    assert sell.closed_trades[0].close_price == 105


def test_target_gaps_use_target_level_conservatively():
    buy = make_broker([100, 100, 105], [101, 101, 106], [99, 99, 104], [100, 100, 105])
    _response, position = open_position(buy)
    asyncio.run(buy.order_modify(position["ticket"], tp=102))
    buy.advance()
    assert buy.closed_trades[0].close_price == 102

    sell = make_broker([100, 100, 95], [101, 101, 96], [99, 99, 94], [100, 100, 95])
    _response, position = open_position(sell, side=1)
    asyncio.run(sell.order_modify(position["ticket"], tp=98))
    sell.advance()
    assert sell.closed_trades[0].close_price == 98


def test_position_manager_compatibility_surface_and_identity():
    broker = make_broker([100, 100], [101, 101], [99, 99], [100, 100])
    _response, position = open_position(broker)
    positions = asyncio.run(broker.positions_get())

    assert len(positions) == 1
    assert positions[0]["ticket"] == position["ticket"]
    assert broker.get_point_size("EURUSD") == 0.00001
    assert asyncio.run(broker.position_by_ticket(position["ticket"]))["order_id"] == 1
    assert asyncio.run(broker.order_modify(position["ticket"], sl=99.0, tp=102.0))["retcode"] == 0
    assert broker.position_get_ticket(position["ticket"])["sl"] == 99.0

    assert broker.position_close(position["ticket"])
    with pytest.raises(AttributeError):
        broker.closed_trades[0].realized_pl = 0
