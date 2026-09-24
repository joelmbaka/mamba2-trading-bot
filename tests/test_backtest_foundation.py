"""Offline replay-clock, aggregation, and fill-timing tests."""

import pandas as pd
import pytest

from mamba2.backtest import HistoricalBroker, HistoricalDataError, ReplayFeed, canonicalize_bars


def fixture_bars(count=16):
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


def test_bar_validation_and_timezone_normalization():
    frame = fixture_bars(1)
    frame["time"] = pd.DatetimeIndex([pd.Timestamp("2025-01-02 10:00", tz="Africa/Nairobi")])
    assert canonicalize_bars(frame).index[0] == pd.Timestamp("2025-01-02 07:00", tz="UTC")

    duplicate = pd.concat([fixture_bars(1), fixture_bars(1)], ignore_index=True)
    with pytest.raises(HistoricalDataError, match="duplicate"):
        canonicalize_bars(duplicate)

    invalid = fixture_bars(1)
    invalid.loc[0, "high"] = 0
    with pytest.raises(HistoricalDataError, match="OHLC"):
        canonicalize_bars(invalid)


def test_future_m1_and_incomplete_higher_timeframes_are_hidden():
    feed = ReplayFeed(fixture_bars())
    feed.advance()  # 10:00
    assert len(feed.get_rates("EURUSD", "M1")) == 1
    assert feed.get_rates("EURUSD", "M1").index[-1].minute == 0
    assert feed.get_rates("EURUSD", "M5").empty
    assert feed.get_rates("EURUSD", "M15").empty

    for _ in range(7):
        feed.advance()  # 10:01 through 10:07
    assert len(feed.get_rates("EURUSD", "M1")) == 8
    assert len(feed.get_rates("EURUSD", "M5")) == 1
    assert feed.get_rates("EURUSD", "M5").index[-1] == pd.Timestamp("2025-01-02 10:00", tz="UTC")
    assert pd.Timestamp("2025-01-02 10:05", tz="UTC") not in feed.get_rates("EURUSD", "M5").index
    assert feed.get_rates("EURUSD", "M15").empty

    feed.advance()  # 10:08
    feed.advance()  # 10:09: the 10:05 M5 bar is now complete
    assert len(feed.get_rates("EURUSD", "M5")) == 2


def test_boundary_crossing_releases_completed_m15_bar():
    feed = ReplayFeed(fixture_bars())
    for _ in range(15):
        feed.advance()
    m15 = feed.get_rates("EURUSD", "M15")
    assert len(m15) == 1
    assert m15.index[0] == pd.Timestamp("2025-01-02 10:00", tz="UTC")
    assert m15.iloc[0]["open"] == 100
    assert m15.iloc[0]["close"] == 115


def test_order_fills_on_next_m1_open_not_signal_candle():
    feed = ReplayFeed(fixture_bars())
    broker = HistoricalBroker(feed)
    broker.initialize()
    broker.advance()  # signal candle 10:00
    submitted = broker.order_send({"symbol": "EURUSD", "type": 0, "volume": 1.0})
    assert submitted["deal"] == 0
    assert broker.positions_total() == 0

    broker.advance()  # execution candle 10:01
    position = broker.position_get_ticket(1)
    assert position is not None
    assert position["time"] == int(pd.Timestamp("2025-01-02 10:01", tz="UTC").timestamp())
    assert position["price_open"] == 101


def replay_snapshot():
    feed = ReplayFeed(fixture_bars())
    snapshot = []
    while not feed.finished:
        feed.advance()
        visible = feed.get_rates("EURUSD", "M5")
        snapshot.append((feed.current_time, tuple(visible["close"].tolist())))
    return snapshot


def test_replay_is_deterministic_across_repeated_runs():
    assert replay_snapshot() == replay_snapshot()
