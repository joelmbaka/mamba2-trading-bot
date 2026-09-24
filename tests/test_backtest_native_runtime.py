"""Native-runtime and broker-timeframe parity tests."""

import pandas as pd
import pytest

from mamba2.backtest import ReplayFeed


def m1_fixture(count: int = 16) -> pd.DataFrame:
    times = pd.date_range(
        "2025-01-02 10:00",
        periods=count,
        freq="min",
        tz="UTC",
    )
    return pd.DataFrame(
        {
            "time": times,
            "open": [100 + i for i in range(count)],
            "high": [102 + i for i in range(count)],
            "low": [99 + i for i in range(count)],
            "close": [101 + i for i in range(count)],
            "tick_volume": [10] * count,
            "spread": [1] * count,
            "real_volume": [100] * count,
        }
    )


def higher_bar(
    open_time: str,
    *,
    open_price: float,
    high: float,
    low: float,
    close: float,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": [pd.Timestamp(open_time, tz="UTC")],
            "open": [open_price],
            "high": [high],
            "low": [low],
            "close": [close],
            "tick_volume": [500],
            "spread": [2],
            "real_volume": [5000],
        }
    )


def test_native_m5_and_m15_are_preferred_at_their_close_boundaries():
    native_m5 = higher_bar(
        "2025-01-02 10:00",
        open_price=200,
        high=220,
        low=190,
        close=210,
    )
    native_m15 = higher_bar(
        "2025-01-02 10:00",
        open_price=300,
        high=340,
        low=280,
        close=330,
    )
    feed = ReplayFeed(
        m1_fixture(),
        native_timeframe_bars={
            "EURUSD": {
                "M5": native_m5,
                "M15": native_m15,
            }
        },
    )

    for _ in range(4):
        feed.advance()  # replay time through 10:04

    assert feed.current_time == pd.Timestamp("2025-01-02 10:04", tz="UTC")
    assert feed.get_rates("EURUSD", "M5").empty
    assert feed.get_rates("EURUSD", "M15").empty

    feed.advance()  # replay time 10:05
    m5 = feed.get_rates("EURUSD", "M5")
    assert len(m5) == 1
    assert m5.index[0] == pd.Timestamp("2025-01-02 10:00", tz="UTC")
    assert m5.iloc[0]["close"] == 210

    for _ in range(10):
        feed.advance()  # replay time 10:15

    m15 = feed.get_rates("EURUSD", "M15")
    assert len(m15) == 1
    assert m15.index[0] == pd.Timestamp("2025-01-02 10:00", tz="UTC")
    assert m15.iloc[0]["close"] == 330


def test_m1_aggregation_remains_the_fallback_without_native_history():
    feed = ReplayFeed(m1_fixture())
    for _ in range(5):
        feed.advance()  # replay time 10:05

    m5 = feed.get_rates("EURUSD", "M5")
    assert len(m5) == 1
    assert m5.index[0] == pd.Timestamp("2025-01-02 10:00", tz="UTC")
    assert m5.iloc[0]["open"] == 100
    assert m5.iloc[0]["close"] == 105


def test_native_timeframes_require_matching_m1_symbol_and_alignment():
    with pytest.raises(ValueError, match="no M1 source"):
        ReplayFeed(
            m1_fixture(),
            native_timeframe_bars={
                "GBPUSD": {
                    "M5": higher_bar(
                        "2025-01-02 10:00",
                        open_price=200,
                        high=220,
                        low=190,
                        close=210,
                    )
                }
            },
        )

    misaligned = higher_bar(
        "2025-01-02 10:01",
        open_price=200,
        high=220,
        low=190,
        close=210,
    )
    with pytest.raises(ValueError, match="aligned"):
        ReplayFeed(
            m1_fixture(),
            native_timeframe_bars={"EURUSD": {"M5": misaligned}},
        )
