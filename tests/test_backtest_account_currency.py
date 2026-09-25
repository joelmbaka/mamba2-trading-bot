"""Account-currency conversion for deterministic historical P/L."""

import pandas as pd
import pytest

from mamba2.backtest import (
    AccountCurrencyConversionError,
    HistoricalBroker,
    ReplayFeed,
    SymbolExecutionMetadata,
)


def make_frame(
    symbol,
    *,
    opens,
    closes,
    point_size,
    spread=0,
):
    times = pd.date_range(
        "2025-01-02 10:00",
        periods=len(opens),
        freq="min",
        tz="UTC",
    )
    return pd.DataFrame(
        {
            "time": times,
            "open": opens,
            "high": [max(o, c) + point_size * 10 for o, c in zip(opens, closes)],
            "low": [min(o, c) - point_size * 10 for o, c in zip(opens, closes)],
            "close": closes,
            "tick_volume": [10] * len(opens),
            "spread": [spread] * len(opens),
            "real_volume": [0] * len(opens),
        }
    )


def metadata():
    return {
        "EURJPY": SymbolExecutionMetadata(
            point_size=0.001,
            digits=3,
            contract_size=100_000.0,
            quote_currency="JPY",
            base_currency="EUR",
        ),
        "USDJPY": SymbolExecutionMetadata(
            point_size=0.001,
            digits=3,
            contract_size=100_000.0,
            quote_currency="JPY",
            base_currency="USD",
        ),
        "EURUSD": SymbolExecutionMetadata(
            point_size=0.00001,
            digits=5,
            contract_size=100_000.0,
            quote_currency="USD",
            base_currency="EUR",
        ),
    }


def jpy_feed(*, eurjpy_close):
    eurjpy = make_frame(
        "EURJPY",
        opens=[160.0, 160.0, eurjpy_close],
        closes=[160.0, eurjpy_close, eurjpy_close],
        point_size=0.001,
    )
    usdjpy = make_frame(
        "USDJPY",
        opens=[150.0, 150.0, 150.0],
        closes=[150.0, 150.0, 150.0],
        point_size=0.001,
    )
    times = usdjpy["time"]
    usdjpy_ask = pd.DataFrame(
        {
            "time": times,
            "open": [151.0, 151.0, 151.0],
            "high": [151.1, 151.1, 151.1],
            "low": [150.9, 150.9, 150.9],
            "close": [151.0, 151.0, 151.0],
        }
    )
    return ReplayFeed(
        {"EURJPY": eurjpy, "USDJPY": usdjpy},
        ask_m1_bars={"USDJPY": usdjpy_ask},
    )


def open_eurjpy(feed, *, side=0):
    broker = HistoricalBroker(
        feed,
        symbol_metadata=metadata(),
        account_currency="USD",
    )
    broker.advance()
    broker.order_send(
        {
            "symbol": "EURJPY",
            "type": side,
            "volume": 1.0,
        }
    )
    broker.settle_pending_orders()
    return broker


def test_positive_jpy_profit_converts_to_usd_at_usdjpy_ask():
    broker = open_eurjpy(jpy_feed(eurjpy_close=161.0))

    broker.advance()
    position = broker.position_get_ticket(1)

    assert position["price_open"] == pytest.approx(160.0)
    assert position["price_current"] == pytest.approx(161.0)
    assert position["profit"] == pytest.approx(100_000.0 / 151.0)
    assert broker.account_info()["currency"] == "USD"


def test_negative_jpy_loss_converts_to_usd_at_usdjpy_bid():
    broker = open_eurjpy(jpy_feed(eurjpy_close=159.0))

    broker.advance()
    position = broker.position_get_ticket(1)

    assert position["profit"] == pytest.approx(-100_000.0 / 150.0)


def test_realized_jpy_profit_uses_same_boundary_conversion_close():
    broker = open_eurjpy(jpy_feed(eurjpy_close=161.0))

    broker.advance()
    assert broker.position_close(1)

    expected = 100_000.0 / 151.0
    assert broker.closed_trades[0].realized_pl == pytest.approx(expected)
    assert broker.account_info()["realized_profit"] == pytest.approx(expected)
    assert broker.account_info()["balance"] == pytest.approx(10_000.0 + expected)


def test_usd_quoted_pl_requires_no_conversion_pair():
    eurusd = make_frame(
        "EURUSD",
        opens=[1.10, 1.10, 1.11],
        closes=[1.10, 1.11, 1.11],
        point_size=0.00001,
    )
    feed = ReplayFeed({"EURUSD": eurusd})
    broker = HistoricalBroker(
        feed,
        symbol_metadata={"EURUSD": metadata()["EURUSD"]},
        account_currency="USD",
    )

    broker.advance()
    broker.order_send({"symbol": "EURUSD", "type": 0, "volume": 1.0})
    broker.settle_pending_orders()
    broker.advance()

    assert broker.position_get_ticket(1)["profit"] == pytest.approx(1000.0)


def test_missing_conversion_pair_fails_instead_of_treating_jpy_as_usd():
    eurjpy = make_frame(
        "EURJPY",
        opens=[160.0, 160.0, 161.0],
        closes=[160.0, 161.0, 161.0],
        point_size=0.001,
    )
    feed = ReplayFeed({"EURJPY": eurjpy})
    broker = HistoricalBroker(
        feed,
        symbol_metadata={"EURJPY": metadata()["EURJPY"]},
        account_currency="USD",
    )

    broker.advance()
    broker.order_send({"symbol": "EURJPY", "type": 0, "volume": 1.0})
    broker.settle_pending_orders()

    with pytest.raises(
        AccountCurrencyConversionError,
        match="no historical conversion pair",
    ):
        broker.advance()


def test_conversion_does_not_use_future_usdjpy_bar():
    eurjpy = make_frame(
        "EURJPY",
        opens=[160.0, 160.0, 161.0],
        closes=[160.0, 161.0, 161.0],
        point_size=0.001,
    )
    usdjpy = make_frame(
        "USDJPY",
        opens=[150.0, 150.0],
        closes=[150.0, 150.0],
        point_size=0.001,
    )
    # Remove the conversion bar that would need to complete at replay 10:02.
    usdjpy = usdjpy.iloc[[0]].copy()

    feed = ReplayFeed({"EURJPY": eurjpy, "USDJPY": usdjpy})
    broker = HistoricalBroker(
        feed,
        symbol_metadata=metadata(),
        account_currency="USD",
    )
    broker.advance()
    broker.order_send({"symbol": "EURJPY", "type": 0, "volume": 1.0})
    broker.settle_pending_orders()

    with pytest.raises(
        AccountCurrencyConversionError,
        match="no completed conversion bar",
    ):
        broker.advance()


def test_inverse_conversion_pair_uses_bid_for_profit_and_ask_for_loss():
    eurjpy_up = make_frame(
        "EURJPY",
        opens=[160.0, 160.0, 161.0],
        closes=[160.0, 161.0, 161.0],
        point_size=0.001,
    )
    jpyusd = make_frame(
        "JPYUSD",
        opens=[0.0066, 0.0066, 0.0066],
        closes=[0.0066, 0.0066, 0.0066],
        point_size=0.000001,
    )
    times = jpyusd["time"]
    jpyusd_ask = pd.DataFrame(
        {
            "time": times,
            "open": [0.0067] * 3,
            "high": [0.0068] * 3,
            "low": [0.0066] * 3,
            "close": [0.0067] * 3,
        }
    )
    md = {
        "EURJPY": metadata()["EURJPY"],
        "JPYUSD": SymbolExecutionMetadata(
            point_size=0.000001,
            digits=6,
            contract_size=100_000.0,
            quote_currency="USD",
            base_currency="JPY",
        ),
    }

    profit_feed = ReplayFeed(
        {"EURJPY": eurjpy_up, "JPYUSD": jpyusd},
        ask_m1_bars={"JPYUSD": jpyusd_ask},
    )
    profit = HistoricalBroker(
        profit_feed,
        symbol_metadata=md,
        account_currency="USD",
    )
    profit.advance()
    profit.order_send({"symbol": "EURJPY", "type": 0, "volume": 1.0})
    profit.settle_pending_orders()
    profit.advance()
    assert profit.position_get_ticket(1)["profit"] == pytest.approx(660.0)

    eurjpy_down = make_frame(
        "EURJPY",
        opens=[160.0, 160.0, 159.0],
        closes=[160.0, 159.0, 159.0],
        point_size=0.001,
    )
    loss_feed = ReplayFeed(
        {"EURJPY": eurjpy_down, "JPYUSD": jpyusd},
        ask_m1_bars={"JPYUSD": jpyusd_ask},
    )
    loss = HistoricalBroker(
        loss_feed,
        symbol_metadata=md,
        account_currency="USD",
    )
    loss.advance()
    loss.order_send({"symbol": "EURJPY", "type": 0, "volume": 1.0})
    loss.settle_pending_orders()
    loss.advance()
    assert loss.position_get_ticket(1)["profit"] == pytest.approx(-670.0)



def test_usdjpy_self_conversion_uses_same_boundary_bid_ask():
    usdjpy = make_frame(
        "USDJPY",
        opens=[150.0, 150.0, 151.0],
        closes=[150.0, 151.0, 151.0],
        point_size=0.001,
    )
    times = usdjpy["time"]
    ask = pd.DataFrame(
        {
            "time": times,
            "open": [150.1, 150.1, 151.1],
            "high": [150.2, 151.2, 151.2],
            "low": [150.0, 150.0, 151.0],
            "close": [150.1, 151.1, 151.1],
        }
    )
    feed = ReplayFeed(
        {"USDJPY": usdjpy},
        ask_m1_bars={"USDJPY": ask},
    )
    broker = HistoricalBroker(
        feed,
        symbol_metadata={"USDJPY": metadata()["USDJPY"]},
        account_currency="USD",
    )

    broker.advance()
    broker.order_send({"symbol": "USDJPY", "type": 0, "volume": 1.0})
    broker.settle_pending_orders()
    broker.advance()

    # Entry Ask is 150.1 and completed Bid close is 151.0, so raw P/L is
    # +90,000 JPY. Positive JPY converts to USD at the same-boundary Ask.
    expected = 90_000.0 / 151.1
    assert broker.position_get_ticket(1)["profit"] == pytest.approx(expected)


def test_six_letter_fx_symbol_infers_quote_currency_when_metadata_omits_it():
    eurjpy = make_frame(
        "EURJPY",
        opens=[160.0, 160.0, 161.0],
        closes=[160.0, 161.0, 161.0],
        point_size=0.001,
    )
    usdjpy = make_frame(
        "USDJPY",
        opens=[150.0, 150.0, 150.0],
        closes=[150.0, 150.0, 150.0],
        point_size=0.001,
    )
    feed = ReplayFeed({"EURJPY": eurjpy, "USDJPY": usdjpy})
    broker = HistoricalBroker(
        feed,
        symbol_metadata={
            "EURJPY": SymbolExecutionMetadata(
                point_size=0.001,
                digits=3,
                contract_size=100_000.0,
            ),
            "USDJPY": SymbolExecutionMetadata(
                point_size=0.001,
                digits=3,
                contract_size=100_000.0,
            ),
        },
        account_currency="USD",
    )

    broker.advance()
    broker.order_send({"symbol": "EURJPY", "type": 0, "volume": 1.0})
    broker.settle_pending_orders()
    broker.advance()

    assert broker.position_get_ticket(1)["profit"] == pytest.approx(
        100_000.0 / 150.0
    )
