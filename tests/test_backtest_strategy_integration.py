"""Offline integration tests for the unchanged triple-cross strategy path."""

from types import SimpleNamespace
from unittest.mock import Mock
import sys
import types

import pandas as pd

from mamba2.backtest import BacktestRunner, HistoricalBroker, ReplayFeed


def fixture_bars(count=30):
    times = pd.date_range("2025-01-02 10:00", periods=count, freq="min", tz="UTC")
    return pd.DataFrame(
        {
            "time": times,
            "open": range(100, 100 + count),
            "high": [value + 2 for value in range(100, 100 + count)],
            "low": [value - 1 for value in range(100, 100 + count)],
            "close": [value + 1 for value in range(100, 100 + count)],
            "tick_volume": [10] * count,
            "spread": [1] * count,
            "real_volume": [100] * count,
        }
    )


def strategy_config(*, trend_enabled=False):
    return SimpleNamespace(
        stochastic_timeframes={"higher": "M15", "trading": "M5", "entry": "M1"},
        use_higher_tf=False,
        ENABLE_TREND_CONDITION=trend_enabled,
        ENABLE_RSI_CONDITION=False,
        position_size=0.1,
    )


def load_strategy(monkeypatch):
    """Avoid importing Wine-incompatible SciPy during this test-only path."""
    trend_module = types.ModuleType("mamba2.indicators.detect_trend")
    trend_module.calculate_5min_trendline = lambda rates: "range"
    monkeypatch.setitem(sys.modules, "mamba2.indicators.detect_trend", trend_module)
    from mamba2.strategy import triple_cross
    return triple_cross


class RecordingRateFetcher:
    def __init__(self, feed):
        self.feed = feed
        self.calls = []

    def get_rates(self, symbol, timeframe):
        rates = self.feed.get_rates(symbol, timeframe)
        self.calls.append((self.feed.current_time, timeframe, rates.index.max() if not rates.empty else None))
        return rates


def test_current_config_replays_warmup_without_orders(monkeypatch):
    triple_cross = load_strategy(monkeypatch)
    monkeypatch.setattr(triple_cross, "config", strategy_config(trend_enabled=False))
    strategy = triple_cross.StochasticTripleTFStrategy("EURUSD")
    feed = ReplayFeed(fixture_bars())
    broker = HistoricalBroker(feed)

    result = BacktestRunner(feed, broker, strategy).run()

    assert result.evaluations == 30
    assert result.accepted_orders == []
    assert broker.positions_total() == 0


def test_forced_buy_is_accepted_but_fills_on_next_bar(monkeypatch):
    from mamba2.indicators import moving_average
    from mamba2.crew import market_analyst, plotter
    triple_cross = load_strategy(monkeypatch)

    monkeypatch.setattr(triple_cross, "config", strategy_config(trend_enabled=True))
    monkeypatch.setattr(triple_cross, "calculate_5min_trendline", lambda rates: "uptrend")
    monkeypatch.setattr(triple_cross, "count_candle_pattern", lambda *args: 0)
    monkeypatch.setattr(moving_average, "get_moving_average", lambda *args, **kwargs: 0.0)
    monkeypatch.setattr(plotter, "plot_rates", Mock(return_value="not-written"))
    monkeypatch.setattr(market_analyst, "get_metrics", Mock(return_value=None))

    def forced_stochastic(symbol, timeframe, rate_fetcher, **kwargs):
        if timeframe == "M1":
            values = ([10.0, 30.0], [20.0, 20.0])
        else:
            values = ([50.0, 60.0], [40.0, 50.0])
        index = pd.RangeIndex(len(values[0]))
        return {"k": pd.Series(values[0], index=index), "d": pd.Series(values[1], index=index), "closes": pd.Series([1.0, 1.0], index=index)}

    monkeypatch.setattr(triple_cross, "get_stochastic", forced_stochastic)

    feed = ReplayFeed(fixture_bars(3))
    recorder = RecordingRateFetcher(feed)
    broker = HistoricalBroker(feed)
    strategy = triple_cross.StochasticTripleTFStrategy("EURUSD")
    runner = BacktestRunner(feed, broker, strategy, rate_fetcher=recorder)

    result = runner.run(max_steps=2)

    assert len(result.accepted_orders) == 1
    assert result.accepted_orders[0]["retcode"] == 0
    assert result.accepted_orders[0]["price"] == 0.0
    assert broker.positions_total() == 0
    assert all(
        visible_time is None or visible_time <= evaluation_time
        for evaluation_time, _timeframe, visible_time in recorder.calls
    )

    broker.advance()
    position = broker.position_get_ticket(1)
    assert position is not None
    assert position["price_open"] == 102
    assert position["time"] == int(pd.Timestamp("2025-01-02 10:02", tz="UTC").timestamp())
