"""Configuration-flag semantics for the production triple-cross strategy."""

from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest


def strategy_config(*, trend=False, rsi=False, higher=False):
    return SimpleNamespace(
        stochastic_timeframes={
            "higher": "M15",
            "trading": "M5",
            "entry": "M1",
        },
        use_higher_tf=higher,
        ENABLE_TREND_CONDITION=trend,
        ENABLE_RSI_CONDITION=rsi,
        position_size=0.1,
    )


class RateFetcher:
    def __init__(self, *, bullish):
        if bullish:
            self.m1 = pd.DataFrame(
                {
                    "open": [1.1000, 1.1000],
                    "high": [1.1003, 1.1006],
                    "low": [1.0997, 1.0998],
                    "close": [1.1001, 1.1005],
                }
            )
        else:
            self.m1 = pd.DataFrame(
                {
                    "open": [1.1000, 1.1005],
                    "high": [1.1003, 1.1007],
                    "low": [1.0997, 1.0998],
                    "close": [1.0999, 1.1000],
                }
            )

    def get_rates(self, symbol, timeframe):
        if timeframe == "M1":
            return self.m1
        return self.m1.copy()


class Broker:
    def __init__(self):
        self.order_send = Mock(
            return_value={"retcode": 0, "order": 123, "price": 0.0}
        )

    def symbol_info_tick(self, symbol):
        return {"bid": 1.1000, "ask": 1.1001}


def stochastic_values(*, signal):
    if signal == "buy":
        return {
            "M15": ([50.0, 60.0], [40.0, 50.0]),
            "M5": ([40.0, 60.0], [50.0, 50.0]),
            "M1": ([10.0, 30.0], [20.0, 20.0]),
        }
    if signal == "sell":
        return {
            "M15": ([60.0, 50.0], [50.0, 55.0]),
            "M5": ([60.0, 40.0], [50.0, 50.0]),
            "M1": ([90.0, 70.0], [80.0, 80.0]),
        }
    return {
        "M15": ([50.0, 50.0], [50.0, 50.0]),
        "M5": ([50.0, 50.0], [50.0, 50.0]),
        "M1": ([50.0, 50.0], [50.0, 50.0]),
    }


async def evaluate_case(
    monkeypatch,
    *,
    signal,
    trend_enabled,
    rsi_enabled,
    trend_result,
    rsi_value=55.0,
):
    from mamba2.crew import market_analyst, plotter
    from mamba2.indicators import moving_average
    from mamba2.strategy import triple_cross

    cfg = strategy_config(trend=trend_enabled, rsi=rsi_enabled)
    monkeypatch.setattr(triple_cross, "config", cfg)

    values = stochastic_values(signal=signal)

    def fake_stochastic(symbol, timeframe, rate_fetcher, **kwargs):
        k, d = values[timeframe]
        index = pd.RangeIndex(len(k))
        return {
            "k": pd.Series(k, index=index),
            "d": pd.Series(d, index=index),
            "closes": pd.Series([1.0] * len(k), index=index),
        }

    trend_mock = Mock(return_value=trend_result)
    rsi_mock = Mock(return_value=pd.Series([rsi_value]))
    monkeypatch.setattr(triple_cross, "get_stochastic", fake_stochastic)
    monkeypatch.setattr(triple_cross, "calculate_5min_trendline", trend_mock)
    monkeypatch.setattr(triple_cross, "get_rsi", rsi_mock)
    monkeypatch.setattr(
        moving_average,
        "get_moving_average",
        lambda *args, **kwargs: 1.1002 if signal == "buy" else 1.1003,
    )
    monkeypatch.setattr(plotter, "plot_rates", Mock(return_value="not-written"))
    monkeypatch.setattr(market_analyst, "get_metrics", Mock(return_value=None))
    monkeypatch.setattr(triple_cross, "count_candle_pattern", lambda *args: 0)

    broker = Broker()
    fetcher = RateFetcher(bullish=signal == "buy")
    strategy = triple_cross.StochasticTripleTFStrategy("EURUSD")
    await strategy.evaluate(
        {
            "broker": broker,
            "rate_fetcher": fetcher,
            "position_manager": None,
        }
    )
    return broker, trend_mock, rsi_mock


@pytest.mark.asyncio
@pytest.mark.parametrize("trend_result", ["uptrend", "downtrend", "sideways", None])
async def test_trend_off_buy_does_not_depend_on_trend(
    monkeypatch,
    trend_result,
):
    broker, trend_mock, rsi_mock = await evaluate_case(
        monkeypatch,
        signal="buy",
        trend_enabled=False,
        rsi_enabled=False,
        trend_result=trend_result,
    )

    broker.order_send.assert_called_once()
    assert broker.order_send.call_args.args[0]["type"] == 0
    trend_mock.assert_not_called()
    rsi_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("trend_result", ["uptrend", "downtrend", "sideways", None])
async def test_trend_off_sell_does_not_depend_on_trend(
    monkeypatch,
    trend_result,
):
    broker, trend_mock, rsi_mock = await evaluate_case(
        monkeypatch,
        signal="sell",
        trend_enabled=False,
        rsi_enabled=False,
        trend_result=trend_result,
    )

    broker.order_send.assert_called_once()
    assert broker.order_send.call_args.args[0]["type"] == 1
    trend_mock.assert_not_called()
    rsi_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("signal", "trend_result", "expected_orders"),
    [
        ("buy", "uptrend", 1),
        ("buy", "downtrend", 0),
        ("sell", "downtrend", 1),
        ("sell", "uptrend", 0),
        ("buy", "sideways", 0),
        ("sell", "sideways", 0),
    ],
)
async def test_trend_on_filters_signal_direction(
    monkeypatch,
    signal,
    trend_result,
    expected_orders,
):
    broker, trend_mock, _rsi_mock = await evaluate_case(
        monkeypatch,
        signal=signal,
        trend_enabled=True,
        rsi_enabled=False,
        trend_result=trend_result,
    )

    assert broker.order_send.call_count == expected_orders
    trend_mock.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("signal", "rsi_value", "expected_orders"),
    [
        ("buy", 51.0, 1),
        ("buy", 50.0, 0),
        ("sell", 49.0, 1),
        ("sell", 50.0, 0),
    ],
)
async def test_rsi_on_preserves_existing_thresholds(
    monkeypatch,
    signal,
    rsi_value,
    expected_orders,
):
    broker, trend_mock, rsi_mock = await evaluate_case(
        monkeypatch,
        signal=signal,
        trend_enabled=False,
        rsi_enabled=True,
        trend_result="sideways",
        rsi_value=rsi_value,
    )

    assert broker.order_send.call_count == expected_orders
    trend_mock.assert_not_called()
    rsi_mock.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("signal", ["buy", "sell"])
async def test_stochastic_conditions_still_block_orders(monkeypatch, signal):
    from mamba2.crew import market_analyst, plotter
    from mamba2.indicators import moving_average
    from mamba2.strategy import triple_cross

    monkeypatch.setattr(
        triple_cross,
        "config",
        strategy_config(trend=False, rsi=False),
    )

    values = stochastic_values(signal="none")

    def fake_stochastic(symbol, timeframe, rate_fetcher, **kwargs):
        k, d = values[timeframe]
        return {
            "k": pd.Series(k),
            "d": pd.Series(d),
            "closes": pd.Series([1.0, 1.0]),
        }

    trend_mock = Mock(side_effect=AssertionError("trend must be disabled"))
    rsi_mock = Mock(side_effect=AssertionError("RSI must be disabled"))
    monkeypatch.setattr(triple_cross, "get_stochastic", fake_stochastic)
    monkeypatch.setattr(triple_cross, "calculate_5min_trendline", trend_mock)
    monkeypatch.setattr(triple_cross, "get_rsi", rsi_mock)
    monkeypatch.setattr(
        moving_average,
        "get_moving_average",
        lambda *args, **kwargs: 1.1002,
    )
    monkeypatch.setattr(plotter, "plot_rates", Mock(return_value="not-written"))
    monkeypatch.setattr(market_analyst, "get_metrics", Mock(return_value=None))

    broker = Broker()
    strategy = triple_cross.StochasticTripleTFStrategy("EURUSD")
    await strategy.evaluate(
        {
            "broker": broker,
            "rate_fetcher": RateFetcher(bullish=signal == "buy"),
            "position_manager": None,
        }
    )

    broker.order_send.assert_not_called()
    trend_mock.assert_not_called()
    rsi_mock.assert_not_called()



@pytest.mark.asyncio
@pytest.mark.parametrize("signal", ["buy", "sell"])
async def test_higher_tf_off_does_not_require_m15_data(monkeypatch, signal):
    from mamba2.crew import market_analyst, plotter
    from mamba2.indicators import moving_average
    from mamba2.strategy import triple_cross

    monkeypatch.setattr(
        triple_cross,
        "config",
        strategy_config(trend=False, rsi=False, higher=False),
    )
    values = stochastic_values(signal=signal)
    stochastic_calls = []

    def fake_stochastic(symbol, timeframe, rate_fetcher, **kwargs):
        stochastic_calls.append(timeframe)
        if timeframe == "M15":
            raise AssertionError("M15 stochastic must not run when disabled")
        k, d = values[timeframe]
        return {
            "k": pd.Series(k),
            "d": pd.Series(d),
            "closes": pd.Series([1.0, 1.0]),
        }

    class NoHigherRateFetcher(RateFetcher):
        def get_rates(self, symbol, timeframe):
            if timeframe == "M15":
                raise AssertionError("M15 rates must not be required")
            return super().get_rates(symbol, timeframe)

    monkeypatch.setattr(triple_cross, "get_stochastic", fake_stochastic)
    monkeypatch.setattr(triple_cross, "get_rsi", Mock())
    monkeypatch.setattr(
        moving_average,
        "get_moving_average",
        lambda *args, **kwargs: 1.1002 if signal == "buy" else 1.1003,
    )
    monkeypatch.setattr(plotter, "plot_rates", Mock(return_value="not-written"))
    metrics = Mock(return_value=None)
    monkeypatch.setattr(market_analyst, "get_metrics", metrics)
    monkeypatch.setattr(triple_cross, "count_candle_pattern", lambda *args: 0)

    broker = Broker()
    strategy = triple_cross.StochasticTripleTFStrategy("EURUSD")
    await strategy.evaluate(
        {
            "broker": broker,
            "rate_fetcher": NoHigherRateFetcher(bullish=signal == "buy"),
            "position_manager": None,
        }
    )

    broker.order_send.assert_called_once()
    assert "M15" not in stochastic_calls
    assert metrics.call_args.kwargs["include_higher_tf"] is False


@pytest.mark.asyncio
async def test_higher_tf_on_still_requires_m15_stochastic(monkeypatch):
    from mamba2.crew import market_analyst, plotter
    from mamba2.indicators import moving_average
    from mamba2.strategy import triple_cross

    monkeypatch.setattr(
        triple_cross,
        "config",
        strategy_config(trend=False, rsi=False, higher=True),
    )
    values = stochastic_values(signal="buy")
    calls = []

    def fake_stochastic(symbol, timeframe, rate_fetcher, **kwargs):
        calls.append(timeframe)
        k, d = values[timeframe]
        return {
            "k": pd.Series(k),
            "d": pd.Series(d),
            "closes": pd.Series([1.0, 1.0]),
        }

    monkeypatch.setattr(triple_cross, "get_stochastic", fake_stochastic)
    monkeypatch.setattr(
        moving_average,
        "get_moving_average",
        lambda *args, **kwargs: 1.1002,
    )
    monkeypatch.setattr(plotter, "plot_rates", Mock(return_value="not-written"))
    metrics = Mock(return_value=None)
    monkeypatch.setattr(market_analyst, "get_metrics", metrics)
    monkeypatch.setattr(triple_cross, "count_candle_pattern", lambda *args: 0)

    broker = Broker()
    strategy = triple_cross.StochasticTripleTFStrategy("EURUSD")
    await strategy.evaluate(
        {
            "broker": broker,
            "rate_fetcher": RateFetcher(bullish=True),
            "position_manager": None,
        }
    )

    assert "M15" in calls
    metrics.assert_called_once()
    assert metrics.call_args.kwargs["include_higher_tf"] is True



@pytest.mark.asyncio
@pytest.mark.parametrize("signal", ["buy", "sell"])
async def test_reporting_disabled_preserves_order_without_artifacts(
    monkeypatch,
    signal,
):
    from mamba2.crew import market_analyst, plotter
    from mamba2.indicators import moving_average
    from mamba2.strategy import triple_cross

    monkeypatch.setattr(
        triple_cross,
        "config",
        strategy_config(trend=False, rsi=False, higher=False),
    )
    values = stochastic_values(signal=signal)

    def fake_stochastic(symbol, timeframe, rate_fetcher, **kwargs):
        k, d = values[timeframe]
        return {
            "k": pd.Series(k),
            "d": pd.Series(d),
            "closes": pd.Series([1.0, 1.0]),
        }

    monkeypatch.setattr(triple_cross, "get_stochastic", fake_stochastic)
    monkeypatch.setattr(
        moving_average,
        "get_moving_average",
        lambda *args, **kwargs: 1.1002 if signal == "buy" else 1.1003,
    )
    monkeypatch.setattr(
        plotter,
        "plot_rates",
        Mock(side_effect=AssertionError("plotting must be disabled")),
    )
    monkeypatch.setattr(
        market_analyst,
        "get_metrics",
        Mock(side_effect=AssertionError("metrics must be disabled")),
    )
    monkeypatch.setattr(triple_cross, "count_candle_pattern", lambda *args: 0)

    broker = Broker()
    strategy = triple_cross.StochasticTripleTFStrategy("EURUSD")
    await strategy.evaluate(
        {
            "broker": broker,
            "rate_fetcher": RateFetcher(bullish=signal == "buy"),
            "position_manager": None,
            "reporting_enabled": False,
        }
    )

    broker.order_send.assert_called_once()



@pytest.mark.asyncio
async def test_strategy_passes_explicit_stochastic_parameters(monkeypatch):
    from mamba2.crew import market_analyst, plotter
    from mamba2.indicators import moving_average
    from mamba2.strategy import triple_cross

    cfg = strategy_config(trend=False, rsi=False, higher=False)
    cfg.stochastic_k_period = 21
    cfg.stochastic_d_period = 7
    cfg.stochastic_slowing = 7
    monkeypatch.setattr(triple_cross, "config", cfg)

    values = stochastic_values(signal="buy")
    calls = []

    def fake_stochastic(symbol, timeframe, rate_fetcher, **kwargs):
        calls.append((timeframe, kwargs.copy()))
        k, d = values[timeframe]
        return {
            "k": pd.Series(k),
            "d": pd.Series(d),
            "closes": pd.Series([1.0, 1.0]),
        }

    monkeypatch.setattr(triple_cross, "get_stochastic", fake_stochastic)
    monkeypatch.setattr(
        moving_average,
        "get_moving_average",
        lambda *args, **kwargs: 1.1002,
    )
    monkeypatch.setattr(plotter, "plot_rates", Mock(return_value="not-written"))
    monkeypatch.setattr(market_analyst, "get_metrics", Mock(return_value=None))
    monkeypatch.setattr(triple_cross, "count_candle_pattern", lambda *args: 0)

    broker = Broker()
    strategy = triple_cross.StochasticTripleTFStrategy("EURUSD")
    await strategy.evaluate(
        {
            "broker": broker,
            "rate_fetcher": RateFetcher(bullish=True),
            "position_manager": None,
            "reporting_enabled": False,
        }
    )

    broker.order_send.assert_called_once()
    assert {timeframe for timeframe, _kwargs in calls} == {"M5", "M1"}
    for _timeframe, kwargs in calls:
        assert kwargs["k_period"] == 21
        assert kwargs["d_period"] == 7
        assert kwargs["slowing"] == 7
