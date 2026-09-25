"""Bid/Ask spread semantics for deterministic historical execution."""

import asyncio

import pandas as pd
import pytest

from mamba2.backtest import HistoricalBroker, ReplayFeed, SymbolExecutionMetadata


POINT = 0.00001


def make_spread_broker(
    *,
    opens,
    highs,
    lows,
    closes,
    spreads,
):
    times = pd.date_range(
        "2025-01-02 10:00",
        periods=len(opens),
        freq="min",
        tz="UTC",
    )
    frame = pd.DataFrame(
        {
            "time": times,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "tick_volume": [10] * len(opens),
            "spread": spreads,
            "real_volume": [0] * len(opens),
        }
    )
    feed = ReplayFeed(frame)
    broker = HistoricalBroker(
        feed,
        symbol_metadata={
            "EURUSD": SymbolExecutionMetadata(
                point_size=POINT,
                digits=5,
                contract_size=100_000.0,
                quote_currency="USD",
            )
        },
    )
    return feed, broker


def test_symbol_tick_synthesizes_ask_from_completed_bid_close_and_spread():
    _feed, broker = make_spread_broker(
        opens=[1.1000, 1.1005],
        highs=[1.1004, 1.1009],
        lows=[1.0998, 1.1003],
        closes=[1.1002, 1.1007],
        spreads=[12, 12],
    )

    broker.advance()
    tick = broker.symbol_info_tick("EURUSD")

    assert tick["bid"] == pytest.approx(1.1002)
    assert tick["ask"] == pytest.approx(1.10032)
    assert tick["last"] == pytest.approx(tick["bid"])


@pytest.mark.parametrize(
    ("side", "expected_open", "expected_current", "expected_profit"),
    [
        (0, 1.10120, 1.10100, -20.0),
        (1, 1.10100, 1.10120, -20.0),
    ],
)
def test_market_entry_uses_ask_for_buy_bid_for_sell_and_marks_immediate_spread(
    side,
    expected_open,
    expected_current,
    expected_profit,
):
    _feed, broker = make_spread_broker(
        opens=[1.1000, 1.1010],
        highs=[1.1004, 1.1015],
        lows=[1.0998, 1.1007],
        closes=[1.1002, 1.1013],
        spreads=[20, 20],
    )

    broker.advance()
    broker.order_send(
        {
            "symbol": "EURUSD",
            "type": side,
            "volume": 1.0,
        }
    )
    broker.settle_pending_orders()

    position = broker.position_get_ticket(1)
    assert position["price_open"] == pytest.approx(expected_open)
    assert position["price_current"] == pytest.approx(expected_current)
    assert position["profit"] == pytest.approx(expected_profit)


def test_marks_use_bid_for_buy_and_ask_for_sell():
    rows = dict(
        opens=[1.1000, 1.1010, 1.1020],
        highs=[1.1004, 1.1018, 1.1024],
        lows=[1.0998, 1.1007, 1.1017],
        closes=[1.1002, 1.1015, 1.1022],
        spreads=[20, 20, 20],
    )

    _feed, buy = make_spread_broker(**rows)
    buy.advance()
    buy.order_send({"symbol": "EURUSD", "type": 0, "volume": 1.0})
    buy.settle_pending_orders()
    buy.advance()
    buy_position = buy.position_get_ticket(1)
    assert buy_position["price_open"] == pytest.approx(1.1012)
    assert buy_position["price_current"] == pytest.approx(1.1015)
    assert buy_position["profit"] == pytest.approx(30.0)

    _feed, sell = make_spread_broker(**rows)
    sell.advance()
    sell.order_send({"symbol": "EURUSD", "type": 1, "volume": 1.0})
    sell.settle_pending_orders()
    sell.advance()
    sell_position = sell.position_get_ticket(1)
    assert sell_position["price_open"] == pytest.approx(1.1010)
    assert sell_position["price_current"] == pytest.approx(1.1017)
    assert sell_position["profit"] == pytest.approx(-70.0)


def test_sell_stop_uses_ask_range_while_buy_target_uses_bid_range():
    rows = dict(
        opens=[1.1000, 1.1000],
        highs=[1.1004, 1.1007],
        lows=[1.0998, 1.0996],
        closes=[1.1002, 1.1001],
        spreads=[20, 20],
    )

    _feed, sell = make_spread_broker(**rows)
    sell.advance()
    sell.order_send(
        {
            "symbol": "EURUSD",
            "type": 1,
            "volume": 1.0,
            "sl": 1.1008,
        }
    )
    sell.settle_pending_orders()
    sell.advance()

    assert sell.positions_total() == 0
    assert sell.closed_trades[0].exit_reason == "stop_loss"
    assert sell.closed_trades[0].close_price == pytest.approx(1.1008)

    _feed, buy = make_spread_broker(**rows)
    buy.advance()
    buy.order_send(
        {
            "symbol": "EURUSD",
            "type": 0,
            "volume": 1.0,
            "tp": 1.1008,
        }
    )
    buy.settle_pending_orders()
    buy.advance()

    # Ask high reached 1.1009, but BUY exits are triggered by Bid high 1.1007.
    assert buy.positions_total() == 1
    assert buy.closed_trades == ()


def test_sell_target_requires_ask_low_and_sell_stop_gap_uses_ask_open():
    no_target_rows = dict(
        opens=[1.1000, 1.1000],
        highs=[1.1004, 1.1006],
        lows=[1.0998, 1.0991],
        closes=[1.1002, 1.0995],
        spreads=[20, 20],
    )
    _feed, sell = make_spread_broker(**no_target_rows)
    sell.advance()
    sell.order_send(
        {
            "symbol": "EURUSD",
            "type": 1,
            "volume": 1.0,
            "tp": 1.0992,
        }
    )
    sell.settle_pending_orders()
    sell.advance()

    # Bid low crossed 1.0992, but synthetic Ask low was 1.0993.
    assert sell.positions_total() == 1
    assert sell.closed_trades == ()

    gap_rows = dict(
        opens=[1.1000, 1.1000, 1.1007],
        highs=[1.1004, 1.1004, 1.1010],
        lows=[1.0998, 1.0998, 1.1006],
        closes=[1.1002, 1.1001, 1.1008],
        spreads=[20, 20, 20],
    )
    _feed, gap_sell = make_spread_broker(**gap_rows)
    gap_sell.advance()
    gap_sell.order_send({"symbol": "EURUSD", "type": 1, "volume": 1.0})
    gap_sell.settle_pending_orders()
    asyncio.run(gap_sell.order_modify(1, sl=1.1008))
    gap_sell.advance()
    gap_sell.advance()

    assert gap_sell.positions_total() == 0
    assert gap_sell.closed_trades[0].exit_reason == "stop_loss"
    assert gap_sell.closed_trades[0].close_price == pytest.approx(1.1009)
