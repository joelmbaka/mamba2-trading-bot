"""Deterministic commission and slippage accounting for replay."""

import asyncio

import pandas as pd
import pytest

from mamba2.backtest import (
    ExecutionCostModel,
    HistoricalBroker,
    ReplayFeed,
    SymbolExecutionMetadata,
)


def frame(*, spread=0):
    times = pd.date_range(
        "2025-01-02 10:00",
        periods=4,
        freq="min",
        tz="UTC",
    )
    return pd.DataFrame(
        {
            "time": times,
            "open": [1.1000, 1.1000, 1.1010, 1.1020],
            "high": [1.1003, 1.1004, 1.1014, 1.1024],
            "low": [1.0997, 1.0996, 1.1006, 1.1016],
            "close": [1.1000, 1.1002, 1.1010, 1.1020],
            "tick_volume": [10] * 4,
            "spread": [spread] * 4,
            "real_volume": [0] * 4,
        }
    )


def make_broker(*, side=0, commission=0.0, slippage=0.0, spread=0):
    feed = ReplayFeed(frame(spread=spread))
    broker = HistoricalBroker(
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
        execution_costs={
            "EURUSD": ExecutionCostModel(
                commission_per_lot_per_side=commission,
                slippage_points=slippage,
            )
        },
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
    return broker


@pytest.mark.parametrize(
    ("side", "expected_open", "expected_current"),
    [
        (0, 1.10012, 1.10000),
        (1, 1.09998, 1.10010),
    ],
)
def test_entry_slippage_is_adverse_and_distinct_from_spread(
    side,
    expected_open,
    expected_current,
):
    broker = make_broker(
        side=side,
        slippage=2,
        spread=10,
    )
    position = broker.position_get_ticket(1)

    assert position["price_open"] == pytest.approx(expected_open)
    assert position["price_current"] == pytest.approx(expected_current)
    assert position["profit"] == pytest.approx(-12.0)


def test_entry_commission_debits_balance_but_not_position_market_profit():
    broker = make_broker(
        commission=3.5,
        slippage=2,
        spread=10,
    )
    info = broker.account_info()

    assert broker.position_get_ticket(1)["profit"] == pytest.approx(-12.0)
    assert info["balance"] == pytest.approx(9996.5)
    assert info["realized_profit"] == pytest.approx(-3.5)
    assert info["unrealized_profit"] == pytest.approx(-12.0)
    assert info["equity"] == pytest.approx(9984.5)
    assert info["commission_paid"] == pytest.approx(3.5)


def test_manual_market_close_applies_exit_slippage_and_two_side_commission():
    broker = make_broker(
        commission=3.5,
        slippage=2,
        spread=0,
    )
    broker.advance()  # completed 10:01 close = 1.1002

    assert broker.position_close(1)

    trade = broker.closed_trades[0]
    # Entry 1.10002, broker-derived BUY exit 1.10020 - 2 points = 1.10018.
    assert trade.open_price == pytest.approx(1.10002)
    assert trade.close_price == pytest.approx(1.10018)
    assert trade.gross_realized_pl == pytest.approx(16.0)
    assert trade.commission == pytest.approx(7.0)
    assert trade.realized_pl == pytest.approx(9.0)

    info = broker.account_info()
    assert info["balance"] == pytest.approx(10009.0)
    assert info["realized_profit"] == pytest.approx(9.0)
    assert info["commission_paid"] == pytest.approx(7.0)


def test_explicit_manual_close_price_is_preserved_but_commission_still_charged():
    broker = make_broker(
        commission=3.5,
        slippage=2,
        spread=0,
    )
    broker.advance()

    assert broker.position_close(1, price=1.10020)

    trade = broker.closed_trades[0]
    assert trade.close_price == pytest.approx(1.10020)
    assert trade.gross_realized_pl == pytest.approx(18.0)
    assert trade.commission == pytest.approx(7.0)
    assert trade.realized_pl == pytest.approx(11.0)


@pytest.mark.parametrize(
    ("side", "tp", "expected_close"),
    [
        (0, 1.10030, 1.10028),
        (1, 1.09980, 1.09982),
    ],
)
def test_take_profit_trigger_remains_market_based_but_fill_gets_adverse_slippage(
    side,
    tp,
    expected_close,
):
    broker = make_broker(
        side=side,
        slippage=2,
        spread=0,
    )
    asyncio.run(broker.order_modify(1, tp=tp))
    broker.advance()

    assert broker.positions_total() == 0
    trade = broker.closed_trades[0]
    assert trade.exit_reason == "take_profit"
    assert trade.close_price == pytest.approx(expected_close)


def test_zero_cost_model_preserves_existing_execution_prices():
    broker = make_broker(
        commission=0,
        slippage=0,
        spread=10,
    )
    position = broker.position_get_ticket(1)

    assert position["price_open"] == pytest.approx(1.10010)
    assert position["price_current"] == pytest.approx(1.10000)
    assert broker.account_info()["balance"] == pytest.approx(10_000.0)
    assert broker.account_info()["commission_paid"] == pytest.approx(0.0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"commission_per_lot_per_side": -0.01},
        {"slippage_points": -1},
        {"commission_per_lot_per_side": float("inf")},
        {"slippage_points": float("nan")},
    ],
)
def test_execution_cost_model_rejects_invalid_values(kwargs):
    with pytest.raises(ValueError):
        ExecutionCostModel(**kwargs)
