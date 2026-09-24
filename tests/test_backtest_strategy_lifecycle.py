"""Deterministic replay of the production ATR/position lifecycle."""

from types import SimpleNamespace

import pandas as pd
import pytest

from mamba2.backtest import BacktestRunner, HistoricalBroker, ReplayFeed
from mamba2.crew.atr_manager import ATRManager
from mamba2.crew.position_manager import PositionManager


def lifecycle_bars(count=14):
    times = pd.date_range(
        "2025-01-02 10:00",
        periods=count,
        freq="min",
        tz="UTC",
    )
    opens = [1.1000 + index * 0.0001 for index in range(count)]
    return pd.DataFrame(
        {
            "time": times,
            "open": opens,
            "high": [value + 0.0004 for value in opens],
            "low": [value - 0.0004 for value in opens],
            "close": [value + 0.0001 for value in opens],
            "tick_volume": [10] * count,
            "spread": [10] * count,
            "real_volume": [0] * count,
        }
    )


class OneShotStrategy:
    symbol = "EURUSD"

    def __init__(self):
        self.calls = 0
        self.submitted = False

    async def evaluate(self, market):
        self.calls += 1
        if self.submitted:
            return
        if market["rate_fetcher"].current_time < pd.Timestamp(
            "2025-01-02 10:10",
            tz="UTC",
        ):
            return

        market["broker"].order_send(
            {
                "symbol": self.symbol,
                "type": 0,
                "volume": 0.1,
                "sl": 0.0,
                "tp": 0.0,
            }
        )
        self.submitted = True


class RepeatingStrategy:
    symbol = "EURUSD"

    def __init__(self):
        self.calls = 0

    async def evaluate(self, market):
        self.calls += 1
        market["broker"].order_send(
            {
                "symbol": self.symbol,
                "type": 0,
                "volume": 0.1,
                "sl": 0.0,
                "tp": 0.0,
            }
        )


def configure_lifecycle(monkeypatch):
    import mamba2.crew.atr_manager as atr_module
    import mamba2.crew.position_manager as position_module

    atr_config = SimpleNamespace(
        symbols=["EURUSD"],
        atr_timeframe="M5",
        atr_period=1,
        atr_update_interval=30,
    )
    position_config = SimpleNamespace(
        atr_timeframe="M5",
        atr_sl_multiplier=1.0,
        atr_tp_multiplier=2.0,
    )
    monkeypatch.setattr(atr_module, "config", atr_config)
    monkeypatch.setattr(position_module, "config", position_config)


def build_lifecycle(monkeypatch, strategy):
    configure_lifecycle(monkeypatch)
    feed = ReplayFeed(lifecycle_bars())
    broker = HistoricalBroker(feed)
    atr_manager = ATRManager(feed)
    position_manager = PositionManager(
        broker,
        atr_manager=atr_manager,
        rates_fetcher=feed,
    )
    runner = BacktestRunner(
        feed,
        broker,
        strategy,
        position_manager=position_manager,
        atr_manager=atr_manager,
    )
    return feed, broker, atr_manager, position_manager, runner


def test_runner_sets_initial_atr_stop_and_target_on_same_fill_boundary(monkeypatch):
    strategy = OneShotStrategy()
    feed, broker, atr_manager, _position_manager, runner = build_lifecycle(
        monkeypatch,
        strategy,
    )

    runner.run(max_steps=10)

    assert feed.current_time == pd.Timestamp("2025-01-02 10:10", tz="UTC")
    assert atr_manager.is_ready() is True
    atr = atr_manager.get_atr("EURUSD", "M5")
    assert atr is not None and atr > 0

    position = broker.position_get_ticket(1)
    assert position is not None
    assert position["price_open"] == pytest.approx(1.1010)
    assert position["sl"] == pytest.approx(position["price_open"] - atr)
    assert position["tp"] == pytest.approx(position["price_open"] + 2 * atr)


def test_runner_mirrors_live_one_open_position_per_symbol_guard(monkeypatch):
    strategy = RepeatingStrategy()
    _feed, broker, _atr_manager, _position_manager, runner = build_lifecycle(
        monkeypatch,
        strategy,
    )

    result = runner.run(max_steps=13)

    assert len(result.accepted_orders) == 1
    assert broker.positions_total() == 1
    assert strategy.calls == 1


def test_atr_refresh_uses_only_completed_m5_history(monkeypatch):
    strategy = OneShotStrategy()
    feed, _broker, atr_manager, _position_manager, runner = build_lifecycle(
        monkeypatch,
        strategy,
    )

    runner.run(max_steps=9)
    assert feed.current_time == pd.Timestamp("2025-01-02 10:09", tz="UTC")
    assert atr_manager.is_ready() is True
    before = atr_manager.get_atr("EURUSD", "M5")

    runner.run(max_steps=1)
    assert feed.current_time == pd.Timestamp("2025-01-02 10:10", tz="UTC")
    after = atr_manager.get_atr("EURUSD", "M5")

    assert before == pytest.approx(0.0008)
    assert after == pytest.approx(0.0008)
