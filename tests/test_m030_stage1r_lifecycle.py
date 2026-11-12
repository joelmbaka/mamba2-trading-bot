"""M030 Stage 1R: deterministic in-memory lifecycle, no native MT5 or market history.

All prices and clocks are synthetic. These tests do not assess profitability
or establish equivalence to native MetaTrader ticks, bars, or broker fills.
"""
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest

from mamba2.backtest import BacktestRunner, HistoricalBroker, ReplayFeed
from mamba2.backtest.m030_parity import EventSink, event, utc_millis
from mamba2.crew.position_manager import PositionManager


DATE = "2025-01-02"


def bars(opens, *, lows=None, highs=None, times=None):
    if times is None:
        times = pd.date_range(f"{DATE} 10:00", periods=len(opens), freq="min", tz="UTC")
    lows = lows if lows is not None else [value - 0.0001 for value in opens]
    highs = highs if highs is not None else [value + 0.0003 for value in opens]
    return pd.DataFrame({
        "time": times,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": [value + 0.0001 for value in opens],
        "tick_volume": [10] * len(opens),
        "spread": [0] * len(opens),
        "real_volume": [0] * len(opens),
    })


def snapshot(feed, symbol):
    boundary = feed.current_time
    opening = boundary - pd.Timedelta(minutes=1)
    return event(
        engine="python", kind="SIGNAL", symbol=symbol,
        utc_time_ms=utc_millis(boundary.to_pydatetime()),
        m1_source_open_utc=opening.strftime("%Y-%m-%dT%H:%M:%SZ"),
        signal="BUY", reason_or_error_code="ENTRY_CONDITIONS",
    )


class OneShot:
    symbol = "EURUSD"

    def __init__(self):
        self.calls = 0

    async def evaluate(self, market):
        self.calls += 1
        if self.calls == 1:
            market["broker"].order_send({
                "symbol": self.symbol, "type": 0, "volume": 0.1,
                "sl": 0.0, "tp": 0.0,
            })


class FixedATR:
    def refresh_once(self):
        return None

    def get_atr(self, symbol, timeframe):
        assert symbol == "EURUSD"
        assert timeframe == "M5"
        return 0.0004


def test_m030_lifecycle_order_and_source_bar_clock(monkeypatch):
    """An exit from the completed bar precedes its boundary's M1_CLOSE."""
    from mamba2.backtest import runner as runner_module
    import mamba2.crew.position_manager as manager_module

    monkeypatch.setattr(runner_module, "observe_candidate", snapshot)
    monkeypatch.setattr(manager_module, "config", SimpleNamespace(
        atr_timeframe="M5", atr_sl_multiplier=1.0, atr_tp_multiplier=2.0,
    ))
    # 10:01 order fills at the execution bar open 1.1010. Its low pierces
    # the protected stop; that range is only known at boundary 10:02.
    feed = ReplayFeed(bars(
        [1.1000, 1.1010, 1.1015],
        lows=[1.0998, 1.1000, 1.1014],
        highs=[1.1004, 1.1013, 1.1018],
    ))
    sink = EventSink()
    broker = HistoricalBroker(feed, event_sink=sink)
    atr = FixedATR()
    manager = PositionManager(broker, atr_manager=atr, rates_fetcher=feed)
    strategy = OneShot()
    runner = BacktestRunner(
        feed, broker, strategy, position_manager=manager,
        atr_manager=atr, event_sink=sink,
    )

    first = runner.run(max_steps=1)
    kinds = [item["event_kind"] for item in sink.events]
    assert kinds == ["M1_CLOSE", "SIGNAL", "SUBMIT", "FILL", "SLTP_MODIFY"]
    assert len(first.accepted_orders) == 1
    assert broker.positions_total() == 1
    boundary_1 = pd.Timestamp(f"{DATE}T10:01:00Z")
    timestamp_1 = utc_millis(boundary_1.to_pydatetime())
    for item in sink.events:
        assert item["utc_time_ms"] == timestamp_1
        assert item["m1_source_open_utc"] == f"{DATE}T10:00:00Z"
    submit, fill, protection = sink.events[2:5]
    assert submit["reason_or_error_code"] == "10008_PENDING"
    assert submit["sl"] == submit["tp"] == 0.0
    assert fill["entry_or_exit_price"] == pytest.approx(1.1010)
    assert fill["bid"] == pytest.approx(1.1010)
    assert fill["sl"] == fill["tp"] == 0.0
    assert submit["request_id"] == fill["request_id"]
    assert fill["position_id"] == protection["position_id"]
    assert protection["sl_before"] == protection["tp_before"] == 0.0
    assert protection["sl"] == pytest.approx(1.1006)
    assert protection["tp"] == pytest.approx(1.1018)

    runner.run(max_steps=1)
    # After the stopped position is closed, the runner is again permitted to
    # observe an entry candidate and evaluate a (one-shot) strategy.
    assert [item["event_kind"] for item in sink.events] == [
        "M1_CLOSE", "SIGNAL", "SUBMIT", "FILL", "SLTP_MODIFY",
        "EXIT", "M1_CLOSE", "SIGNAL",
    ]
    boundary_2 = pd.Timestamp(f"{DATE}T10:02:00Z")
    timestamp_2 = utc_millis(boundary_2.to_pydatetime())
    for item in sink.events[5:]:
        assert item["utc_time_ms"] == timestamp_2
        assert item["m1_source_open_utc"] == f"{DATE}T10:01:00Z"
    assert sink.events[5]["exit_reason"] == "stop_loss"
    assert sink.events[5]["request_id"] == fill["request_id"]
    assert sink.events[5]["position_id"] == fill["position_id"]
    assert len(broker.closed_trades) == 1
    assert broker.positions_total() == 0


def configure_real_strategy(monkeypatch):
    from mamba2.strategy import triple_cross
    from mamba2.indicators import moving_average

    cfg = SimpleNamespace(
        stochastic_timeframes={"higher": "M15", "trading": "M5", "entry": "M1"},
        use_higher_tf=False,
        ENABLE_TREND_CONDITION=False,
        ENABLE_RSI_CONDITION=False,
        position_size=0.1,
        stochastic_k_period=21,
        stochastic_d_period=7,
        stochastic_slowing=7,
    )
    monkeypatch.setattr(triple_cross, "config", cfg)

    def fake_stochastic(symbol, timeframe, rate_fetcher, **kwargs):
        if timeframe == "M1":
            assert kwargs["lookback_period"] == 10
            k = [10.0] + [30.0] * 7 + [55.0, 60.0]
            d = [20.0] + [25.0] * 7 + [50.0, 50.0]
        elif timeframe == "M5":
            k, d = [55.0, 60.0], [50.0, 50.0]
        else:
            raise AssertionError("higher timeframe is disabled")
        return {"k": pd.Series(k), "d": pd.Series(d),
                "closes": pd.Series([1.0] * len(k))}

    monkeypatch.setattr(triple_cross, "get_stochastic", fake_stochastic)
    monkeypatch.setattr(
        moving_average, "get_moving_average",
        lambda *args, **kwargs: 1.0000,
    )
    strategy = triple_cross.StochasticTripleTFStrategy("EURUSD")
    # The real runner intentionally does not set reporting_enabled=False;
    # replace only the reporting side-effect boundary, never evaluate().
    reporting = Mock()
    monkeypatch.setattr(strategy, "_record_entry_artifacts", reporting)
    return strategy, reporting


def instrument_real_evaluations(monkeypatch, strategy, feed):
    actual_evaluate = strategy.evaluate
    evaluated_at = []

    async def recorded_evaluate(market):
        evaluated_at.append(feed.current_time)
        return await actual_evaluate(market)

    monkeypatch.setattr(strategy, "evaluate", recorded_evaluate)
    return evaluated_at


def test_real_production_strategy_open_position_blocks_second_entry(monkeypatch):
    from mamba2.backtest import runner as runner_module

    monkeypatch.setattr(runner_module, "observe_candidate", snapshot)
    # The first boundary has one visible M1 bar and cannot submit. At
    # 10:02, the second completed M1 bar permits a real BUY.
    feed = ReplayFeed(bars(
        [1.1000, 1.1003, 1.1006, 1.1009, 1.1012],
    ))
    broker = HistoricalBroker(feed)
    manager = PositionManager(broker, atr_manager=None, rates_fetcher=feed)
    strategy, reporting = configure_real_strategy(monkeypatch)
    evaluated_at = instrument_real_evaluations(monkeypatch, strategy, feed)
    runner = BacktestRunner(
        feed, broker, strategy, position_manager=manager,
    )

    first = runner.run(max_steps=2)
    assert len(first.accepted_orders) == 1
    assert first.accepted_orders[0]["retcode"] == 0
    assert broker.positions_total() == 1
    assert len(broker.pending_orders) == 0
    assert evaluated_at == [
        pd.Timestamp(f"{DATE}T10:01:00Z"),
        pd.Timestamp(f"{DATE}T10:02:00Z"),
    ]
    assert reporting.call_count == 1

    later = runner.run(max_steps=2)
    assert len(later.accepted_orders) == 1
    assert broker.positions_total() == 1
    assert evaluated_at == [
        pd.Timestamp(f"{DATE}T10:01:00Z"),
        pd.Timestamp(f"{DATE}T10:02:00Z"),
    ]
    assert reporting.call_count == 1


def test_real_production_strategy_pending_order_blocks_until_fill(monkeypatch):
    from mamba2.backtest import runner as runner_module

    monkeypatch.setattr(runner_module, "observe_candidate", snapshot)
    # A real strategy requires >=2 completed M1 rates. At 10:02 it has
    # 10:00 and 10:01 source bars, but NO 10:02 execution bar, hence
    # pending until the source 10:04 bar. GBPUSD advances global time.
    eur_times = pd.DatetimeIndex([
        f"{DATE}T10:00:00Z", f"{DATE}T10:01:00Z",
        f"{DATE}T10:04:00Z",
    ])
    gbp_times = pd.date_range(f"{DATE} 10:00", periods=5, freq="min", tz="UTC")
    feed = ReplayFeed({
        "EURUSD": bars([1.1000, 1.1003, 1.1009], times=eur_times),
        "GBPUSD": bars([1.2500, 1.2501, 1.2502, 1.2503, 1.2504],
                       times=gbp_times),
    })
    broker = HistoricalBroker(feed)
    manager = PositionManager(broker, atr_manager=None, rates_fetcher=feed)
    strategy, reporting = configure_real_strategy(monkeypatch)
    evaluated_at = instrument_real_evaluations(monkeypatch, strategy, feed)
    sink = EventSink()
    runner = BacktestRunner(feed, broker, strategy, position_manager=manager,
                            event_sink=sink)

    first = runner.run(max_steps=2)
    assert len(first.accepted_orders) == 1
    assert broker.positions_total() == 0
    assert len(broker.pending_orders) == 1
    assert evaluated_at == [
        pd.Timestamp(f"{DATE}T10:01:00Z"),
        pd.Timestamp(f"{DATE}T10:02:00Z"),
    ]
    assert [ev["event_kind"] for ev in sink.events].count("SUBMIT") == 1
    assert [ev["event_kind"] for ev in sink.events].count("SIGNAL") == 2
    assert reporting.call_count == 1

    runner.run(max_steps=1)  # 10:03, pending blocks both observer and strategy.
    assert broker.positions_total() == 0
    assert len(broker.pending_orders) == 1
    assert len(evaluated_at) == 2
    assert [ev["event_kind"] for ev in sink.events].count("SIGNAL") == 2

    runner.run(max_steps=1)  # 10:04, settle during broker.advance().
    assert broker.positions_total() == 1
    assert len(broker.pending_orders) == 0
    assert len(evaluated_at) == 2
    kinds = [ev["event_kind"] for ev in sink.events]
    assert kinds.count("SUBMIT") == 1
    assert kinds.count("FILL") == 1
    assert kinds.count("SIGNAL") == 2  # blocked candidates are not observed.
    assert kinds.index("FILL") < [i for i, kind in enumerate(kinds)
                                  if kind == "M1_CLOSE"][-1]
    assert reporting.call_count == 1
