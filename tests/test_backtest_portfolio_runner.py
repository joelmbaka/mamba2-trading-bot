"""Shared-account deterministic portfolio replay orchestration."""

from types import SimpleNamespace

import pandas as pd
import pytest

from mamba2.backtest import (
    ExecutionCostModel,
    HistoricalBroker,
    PortfolioBacktestRunner,
    ReplayFeed,
    SymbolExecutionMetadata,
)


def bars(
    *,
    base,
    count=4,
    point=0.00001,
    times=None,
    spread=0,
):
    if times is None:
        times = pd.date_range(
            "2025-01-02 10:00",
            periods=count,
            freq="min",
            tz="UTC",
        )
    opens = [base + index * point * 10 for index in range(len(times))]
    return pd.DataFrame(
        {
            "time": times,
            "open": opens,
            "high": [value + point * 4 for value in opens],
            "low": [value - point * 4 for value in opens],
            "close": [value + point * 2 for value in opens],
            "tick_volume": [10] * len(times),
            "spread": [spread] * len(times),
            "real_volume": [0] * len(times),
        }
    )


class RecordingStrategy:
    def __init__(self, symbol, calls, *, submit=True):
        self.symbol = symbol
        self.calls = calls
        self.submit = submit

    async def evaluate(self, market):
        self.calls.append((self.symbol, market["rate_fetcher"].current_time))
        if self.submit:
            market["broker"].order_send(
                {
                    "symbol": self.symbol,
                    "type": 0,
                    "volume": 0.1,
                    "sl": 0.0,
                    "tp": 0.0,
                }
            )


class SubmitAt:
    def __init__(self, symbol, calls, timestamp):
        self.symbol = symbol
        self.calls = calls
        self.timestamp = pd.Timestamp(timestamp)

    async def evaluate(self, market):
        self.calls.append((self.symbol, market["rate_fetcher"].current_time))
        if market["rate_fetcher"].current_time == self.timestamp:
            market["broker"].order_send(
                {
                    "symbol": self.symbol,
                    "type": 0,
                    "volume": 0.1,
                    "sl": 0.0,
                    "tp": 0.0,
                }
            )


class FakeATR:
    def __init__(self):
        self.calls = 0

    def refresh_once(self):
        self.calls += 1


class FakePositionManager:
    def __init__(self):
        self.calls = 0
        self.atr_manager = None

    async def update_once(self):
        self.calls += 1


class RejectingBroker(HistoricalBroker):
    def order_send(self, request):
        if request.get("symbol") == "GBPUSD":
            return {
                "retcode": 1,
                "deal": 0,
                "order": 0,
                "price": 0.0,
                "comment": "rejected for test",
            }
        return super().order_send(request)


def metadata():
    return {
        "EURUSD": SymbolExecutionMetadata(
            point_size=0.00001,
            digits=5,
            contract_size=100_000.0,
            base_currency="EUR",
            quote_currency="USD",
        ),
        "GBPUSD": SymbolExecutionMetadata(
            point_size=0.00001,
            digits=5,
            contract_size=100_000.0,
            base_currency="GBP",
            quote_currency="USD",
        ),
        "EURJPY": SymbolExecutionMetadata(
            point_size=0.001,
            digits=3,
            contract_size=100_000.0,
            base_currency="EUR",
            quote_currency="JPY",
        ),
        "USDJPY": SymbolExecutionMetadata(
            point_size=0.001,
            digits=3,
            contract_size=100_000.0,
            base_currency="USD",
            quote_currency="JPY",
        ),
    }


def test_two_symbol_strategies_share_broker_and_fill_same_boundary():
    feed = ReplayFeed(
        {
            "EURUSD": bars(base=1.1000),
            "GBPUSD": bars(base=1.2500),
        }
    )
    broker = HistoricalBroker(feed, symbol_metadata=metadata())
    calls = []
    runner = PortfolioBacktestRunner(
        feed,
        broker,
        [
            RecordingStrategy("EURUSD", calls),
            RecordingStrategy("GBPUSD", calls),
        ],
    )

    result = runner.run(max_steps=1)

    assert calls == [
        ("EURUSD", pd.Timestamp("2025-01-02 10:01", tz="UTC")),
        ("GBPUSD", pd.Timestamp("2025-01-02 10:01", tz="UTC")),
    ]
    assert broker.positions_total() == 2
    assert result.accepted_order_count == 2
    assert result.accepted_order_count_by_symbol == {
        "EURUSD": 1,
        "GBPUSD": 1,
    }
    assert len(result.open_positions_by_symbol["EURUSD"]) == 1
    assert len(result.open_positions_by_symbol["GBPUSD"]) == 1
    assert result.final_account == broker.account_info()


def test_rejected_order_response_is_not_counted_as_accepted():
    feed = ReplayFeed(
        {
            "EURUSD": bars(base=1.1000),
            "GBPUSD": bars(base=1.2500),
        }
    )
    broker = RejectingBroker(feed, symbol_metadata=metadata())
    calls = []
    runner = PortfolioBacktestRunner(
        feed,
        broker,
        [
            RecordingStrategy("EURUSD", calls),
            RecordingStrategy("GBPUSD", calls),
        ],
    )

    result = runner.run(max_steps=1)

    assert result.accepted_order_count == 1
    assert result.accepted_order_count_by_symbol == {
        "EURUSD": 1,
        "GBPUSD": 0,
    }
    assert broker.positions_total() == 1
    assert result.pending_orders_by_symbol == {
        "EURUSD": [],
        "GBPUSD": [],
    }


def test_open_position_blocks_only_its_own_symbol():
    feed = ReplayFeed(
        {
            "EURUSD": bars(base=1.1000),
            "GBPUSD": bars(base=1.2500),
        }
    )
    broker = HistoricalBroker(feed, symbol_metadata=metadata())
    calls = []
    runner = PortfolioBacktestRunner(
        feed,
        broker,
        [
            SubmitAt("EURUSD", calls, "2025-01-02 10:01Z"),
            SubmitAt("GBPUSD", calls, "2025-01-02 10:02Z"),
        ],
    )

    result = runner.run(max_steps=2)

    eur_calls = [call for call in calls if call[0] == "EURUSD"]
    gbp_calls = [call for call in calls if call[0] == "GBPUSD"]
    assert len(eur_calls) == 1
    assert len(gbp_calls) == 2
    assert result.accepted_order_count_by_symbol == {
        "EURUSD": 1,
        "GBPUSD": 1,
    }
    assert broker.positions_total() == 2


def test_pending_symbol_does_not_block_other_symbol():
    eur_times = pd.to_datetime(
        [
            "2025-01-02T10:00:00Z",
            "2025-01-02T10:03:00Z",
        ],
        utc=True,
    )
    gbp_times = pd.date_range(
        "2025-01-02 10:00",
        periods=4,
        freq="min",
        tz="UTC",
    )
    feed = ReplayFeed(
        {
            "EURUSD": bars(base=1.1000, times=eur_times),
            "GBPUSD": bars(base=1.2500, times=gbp_times),
        }
    )
    broker = HistoricalBroker(feed, symbol_metadata=metadata())
    calls = []
    runner = PortfolioBacktestRunner(
        feed,
        broker,
        [
            RecordingStrategy("EURUSD", calls),
            RecordingStrategy("GBPUSD", calls),
        ],
    )

    result = runner.run(max_steps=1)

    assert len(result.pending_orders_by_symbol["EURUSD"]) == 1
    assert len(result.open_positions_by_symbol["EURUSD"]) == 0
    assert len(result.open_positions_by_symbol["GBPUSD"]) == 1
    assert result.accepted_order_count_by_symbol == {
        "EURUSD": 1,
        "GBPUSD": 1,
    }


def test_strategy_order_atr_and_position_manager_run_once_per_boundary():
    feed = ReplayFeed(
        {
            "EURUSD": bars(base=1.1000),
            "GBPUSD": bars(base=1.2500),
        }
    )
    broker = HistoricalBroker(feed, symbol_metadata=metadata())
    calls = []
    atr = FakeATR()
    position_manager = FakePositionManager()
    runner = PortfolioBacktestRunner(
        feed,
        broker,
        [
            RecordingStrategy("GBPUSD", calls, submit=False),
            RecordingStrategy("EURUSD", calls, submit=False),
        ],
        position_manager=position_manager,
        atr_manager=atr,
    )

    result = runner.run(max_steps=3)

    assert [symbol for symbol, _timestamp in calls] == [
        "GBPUSD",
        "EURUSD",
        "GBPUSD",
        "EURUSD",
        "GBPUSD",
        "EURUSD",
    ]
    assert result.per_symbol_evaluations == {
        "GBPUSD": 3,
        "EURUSD": 3,
    }
    assert atr.calls == 3
    assert position_manager.calls == 3


def test_shared_account_applies_symbol_specific_commission():
    feed = ReplayFeed(
        {
            "EURUSD": bars(base=1.1000),
            "GBPUSD": bars(base=1.2500),
        }
    )
    broker = HistoricalBroker(
        feed,
        symbol_metadata=metadata(),
        execution_costs={
            "EURUSD": ExecutionCostModel(
                commission_per_lot_per_side=4.0,
            ),
            "GBPUSD": ExecutionCostModel(),
        },
    )
    calls = []
    runner = PortfolioBacktestRunner(
        feed,
        broker,
        [
            RecordingStrategy("EURUSD", calls),
            RecordingStrategy("GBPUSD", calls),
        ],
    )

    result = runner.run(max_steps=1)

    assert result.final_account["balance"] == pytest.approx(9999.6)
    assert result.final_account["commission_paid"] == pytest.approx(0.4)
    assert broker.positions_total() == 2


def test_jpy_position_uses_shared_usdjpy_conversion_history():
    eurjpy = bars(
        base=160.000,
        point=0.001,
        count=4,
    )
    usdjpy = bars(
        base=150.000,
        point=0.001,
        count=4,
    )
    feed = ReplayFeed(
        {
            "EURJPY": eurjpy,
            "USDJPY": usdjpy,
        }
    )
    broker = HistoricalBroker(
        feed,
        symbol_metadata=metadata(),
        account_currency="USD",
    )
    calls = []
    runner = PortfolioBacktestRunner(
        feed,
        broker,
        [
            SubmitAt("EURJPY", calls, "2025-01-02 10:01Z"),
            RecordingStrategy("USDJPY", calls, submit=False),
        ],
    )

    runner.run(max_steps=2)

    position = broker.position_get_ticket(1)
    assert position is not None
    raw_jpy = (
        (position["price_current"] - position["price_open"])
        * position["volume"]
        * metadata()["EURJPY"].contract_size
    )
    conversion_bid = feed.completed_bar("USDJPY")["close"]
    assert raw_jpy != 0
    expected = raw_jpy / conversion_bid
    assert position["profit"] == pytest.approx(expected)


def test_portfolio_result_reports_pending_open_closed_and_account_state():
    feed = ReplayFeed(
        {
            "EURUSD": bars(base=1.1000),
            "GBPUSD": bars(base=1.2500),
        }
    )
    broker = HistoricalBroker(feed, symbol_metadata=metadata())
    calls = []
    runner = PortfolioBacktestRunner(
        feed,
        broker,
        [
            RecordingStrategy("EURUSD", calls),
            RecordingStrategy("GBPUSD", calls, submit=False),
        ],
    )

    result = runner.run(max_steps=1)

    assert result.evaluations == 1
    assert result.timestamps == [
        pd.Timestamp("2025-01-02 10:01", tz="UTC")
    ]
    assert result.per_symbol_evaluations == {
        "EURUSD": 1,
        "GBPUSD": 1,
    }
    assert result.closed_trade_count_by_symbol == {
        "EURUSD": 0,
        "GBPUSD": 0,
    }
    assert result.pending_orders_by_symbol == {
        "EURUSD": [],
        "GBPUSD": [],
    }
    assert result.final_account["currency"] == "USD"


def test_portfolio_runner_rejects_missing_or_duplicate_strategy_symbols():
    feed = ReplayFeed({"EURUSD": bars(base=1.1000)})
    broker = HistoricalBroker(feed, symbol_metadata=metadata())

    with pytest.raises(ValueError, match="at least one strategy"):
        PortfolioBacktestRunner(feed, broker, [])

    with pytest.raises(ValueError, match="must expose a symbol"):
        PortfolioBacktestRunner(
            feed,
            broker,
            [SimpleNamespace()],
        )

    calls = []
    with pytest.raises(ValueError, match="symbols must be unique"):
        PortfolioBacktestRunner(
            feed,
            broker,
            [
                RecordingStrategy("EURUSD", calls, submit=False),
                RecordingStrategy("EURUSD", calls, submit=False),
            ],
        )
