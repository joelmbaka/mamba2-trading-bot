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
    assert feed.get_rates("EURUSD", "M1").empty
    feed.advance()  # replay time 10:01; source bar 10:00 is complete
    assert len(feed.get_rates("EURUSD", "M1")) == 1
    assert feed.get_rates("EURUSD", "M1").index[-1] == pd.Timestamp("2025-01-02 10:00", tz="UTC")
    assert pd.Timestamp("2025-01-02 10:01", tz="UTC") not in feed.get_rates("EURUSD", "M1").index
    assert feed.get_rates("EURUSD", "M1").index[-1].minute == 0
    assert feed.get_rates("EURUSD", "M5").empty
    assert feed.get_rates("EURUSD", "M15").empty

    for _ in range(6):
        feed.advance()  # replay time 10:02 through 10:07
    assert len(feed.get_rates("EURUSD", "M1")) == 7
    assert len(feed.get_rates("EURUSD", "M5")) == 1
    assert feed.get_rates("EURUSD", "M5").index[-1] == pd.Timestamp("2025-01-02 10:00", tz="UTC")
    assert pd.Timestamp("2025-01-02 10:05", tz="UTC") not in feed.get_rates("EURUSD", "M5").index
    assert feed.get_rates("EURUSD", "M15").empty

    feed.advance()  # replay time 10:08
    feed.advance()  # replay time 10:09; 10:05 M5 is still incomplete
    assert len(feed.get_rates("EURUSD", "M5")) == 1
    feed.advance()  # replay time 10:10; 10:05 M5 is complete
    assert len(feed.get_rates("EURUSD", "M5")) == 2


def test_boundary_crossing_releases_completed_m15_bar():
    feed = ReplayFeed(fixture_bars())
    for _ in range(14):
        feed.advance()  # replay time 10:14
    assert feed.get_rates("EURUSD", "M15").empty
    feed.advance()  # replay time 10:15
    m15 = feed.get_rates("EURUSD", "M15")
    assert len(m15) == 1
    assert m15.index[0] == pd.Timestamp("2025-01-02 10:00", tz="UTC")
    assert m15.iloc[0]["open"] == 100
    assert m15.iloc[0]["close"] == 115


def test_order_fills_on_next_m1_open_not_signal_candle():
    feed = ReplayFeed(fixture_bars())
    broker = HistoricalBroker(feed)
    broker.initialize()
    broker.advance()  # replay time 10:01; source 10:00 is visible
    submitted = broker.order_send({"symbol": "EURUSD", "type": 0, "volume": 1.0})
    assert submitted["deal"] == 0
    assert broker.positions_total() == 0

    broker.settle_pending_orders()  # fill at 10:01 open before its OHLC is visible
    position = broker.position_get_ticket(1)
    assert position is not None
    assert position["time"] == int(pd.Timestamp("2025-01-02 10:01", tz="UTC").timestamp())
    assert position["price_open"] == 101


def test_copy_rates_from_pos_returns_visible_bars_and_respects_slices():
    feed = ReplayFeed(fixture_bars())
    broker = HistoricalBroker(feed)
    for _ in range(8):
        broker.advance()  # visible through 10:07

    bars = broker.copy_rates_from_pos("EURUSD", 1, 0, 3)
    assert len(bars) == 3
    assert all(
        set(bar) == {"time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"}
        for bar in bars
    )
    assert [bar["open"] for bar in bars] == [105, 106, 107]
    assert [bar["close"] for bar in bars] == [106, 107, 108]
    assert all(bar["time"] <= int(feed.current_time.timestamp()) for bar in bars)

    prior_bars = broker.copy_rates_from_pos("EURUSD", 1, 1, 2)
    assert len(prior_bars) == 2
    assert [bar["open"] for bar in prior_bars] == [105, 106]


def test_copy_rates_from_pos_cannot_read_future_bars():
    feed = ReplayFeed(fixture_bars())
    broker = HistoricalBroker(feed)
    broker.advance()  # only 10:00 is visible

    bars = broker.copy_rates_from_pos("EURUSD", 1, 0, 100)
    assert len(bars) == 1
    assert bars[0]["open"] == 100


def test_pending_order_waits_for_a_real_symbol_candle():
    sparse_symbol = fixture_bars(4).iloc[[0, 3]].copy()
    other_symbol = fixture_bars(4).copy()
    feed = ReplayFeed({"EURUSD": sparse_symbol, "GBPUSD": other_symbol})
    broker = HistoricalBroker(feed)

    broker.advance()  # replay time 10:01; both symbols have completed 10:00
    broker.order_send({"symbol": "EURUSD", "type": 0, "volume": 1.0})

    broker.advance()  # replay time 10:02; EURUSD has no 10:02 execution bar
    assert broker.positions_total() == 0

    broker.advance()  # replay time 10:03; EURUSD's 10:03 bar is available
    position = broker.position_get_ticket(1)
    assert position is not None
    assert position["time"] == int(pd.Timestamp("2025-01-02 10:03", tz="UTC").timestamp())
    assert position["price_open"] == 103


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
