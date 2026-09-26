"""Exact-parity tests for replay-only causal indicator caching."""

import numpy as np
import pandas as pd

from mamba2.backtest.feed import ReplayFeed
from mamba2.indicators.atr import get_atr
from mamba2.indicators.moving_average import get_moving_average
from mamba2.indicators.stochastic import get_stochastic


class _VisibleOnlyFetcher:
    """Expose only ReplayFeed's public visible-rate API (legacy path)."""

    def __init__(self, feed):
        self.feed = feed

    def get_rates(self, symbol, timeframe):
        return self.feed.get_rates(symbol, timeframe)


def _bars(count=240):
    index = pd.date_range(
        "2026-09-01T00:00:00Z",
        periods=count,
        freq="min",
    )
    phase = np.linspace(0.0, 12.0 * np.pi, count)
    close = 1.1000 + np.linspace(0.0, 0.0120, count) + 0.0015 * np.sin(phase)
    open_ = close - 0.0002 * np.cos(phase * 0.7)
    high = np.maximum(open_, close) + 0.00035
    low = np.minimum(open_, close) - 0.00030
    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "tick_volume": np.arange(count) + 100,
            "spread": np.full(count, 12),
            "real_volume": np.zeros(count),
        },
        index=index,
    )


def _native_m5(m1):
    return m1.resample("5min").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "tick_volume": "sum",
            "spread": "last",
            "real_volume": "sum",
        }
    )


def _assert_stochastic_equal(cached, legacy):
    if cached is None or legacy is None:
        assert cached is legacy
        return
    pd.testing.assert_series_equal(cached["k"], legacy["k"], check_exact=True)
    pd.testing.assert_series_equal(cached["d"], legacy["d"], check_exact=True)
    pd.testing.assert_series_equal(
        cached["closes"],
        legacy["closes"],
        check_exact=True,
    )


def test_replay_cached_indicators_match_visible_only_legacy_path_exactly():
    m1 = _bars()
    m5 = _native_m5(m1)
    feed = ReplayFeed(
        {"EURUSD": m1},
        native_timeframe_bars={"EURUSD": {"M5": m5}},
    )
    legacy = _VisibleOnlyFetcher(feed)

    checkpoints = {34, 35, 74, 75, 174, 175, 199, 239}
    first_cached_k_id = None

    for step in range(len(m1)):
        now = feed.advance()
        if step not in checkpoints:
            continue

        visible_m1 = feed.get_rates("EURUSD", "M1")
        expected_m1 = m1.loc[
            m1.index + pd.Timedelta(minutes=1) <= now
        ].rename_axis("time")
        pd.testing.assert_frame_equal(visible_m1, expected_m1)

        visible_m5 = feed.get_rates("EURUSD", "M5")
        expected_m5 = m5.loc[
            m5.index + pd.Timedelta(minutes=5) <= now
        ].rename_axis("time")
        pd.testing.assert_frame_equal(visible_m5, expected_m5)

        cached_m1 = get_stochastic(
            symbol="EURUSD",
            timeframe="M1",
            k_period=21,
            d_period=7,
            slowing=7,
            lookback_period=10,
            rate_fetcher=feed,
        )
        legacy_m1 = get_stochastic(
            symbol="EURUSD",
            timeframe="M1",
            k_period=21,
            d_period=7,
            slowing=7,
            lookback_period=10,
            rate_fetcher=legacy,
        )
        _assert_stochastic_equal(cached_m1, legacy_m1)

        cached_m5 = get_stochastic(
            symbol="EURUSD",
            timeframe="M5",
            k_period=21,
            d_period=7,
            slowing=7,
            rate_fetcher=feed,
        )
        legacy_m5 = get_stochastic(
            symbol="EURUSD",
            timeframe="M5",
            k_period=21,
            d_period=7,
            slowing=7,
            rate_fetcher=legacy,
        )
        _assert_stochastic_equal(cached_m5, legacy_m5)

        cached_ema = get_moving_average(
            symbol="EURUSD",
            timeframe="M1",
            ma_period=7,
            ma_method="ema",
            rate_fetcher=feed,
        )
        legacy_ema = get_moving_average(
            symbol="EURUSD",
            timeframe="M1",
            ma_period=7,
            ma_method="ema",
            rate_fetcher=legacy,
        )
        assert cached_ema == legacy_ema

        cached_atr = get_atr(
            symbol="EURUSD",
            timeframe="M5",
            atr_period=14,
            rate_fetcher=feed,
        )
        legacy_atr = get_atr(
            symbol="EURUSD",
            timeframe="M5",
            atr_period=14,
            rate_fetcher=legacy,
        )
        if pd.isna(cached_atr) or pd.isna(legacy_atr):
            assert pd.isna(cached_atr) and pd.isna(legacy_atr)
        else:
            assert cached_atr == legacy_atr

        if cached_m1 is not None:
            cache = feed._replay_indicator_cache
            key = ("stochastic", "EURUSD", "M1", 21, 7, 7, "high/low")
            cached_k_id = id(cache[key]["components"]["k"])
            if first_cached_k_id is None:
                first_cached_k_id = cached_k_id
            else:
                assert cached_k_id == first_cached_k_id

    assert first_cached_k_id is not None
    ema_key = ("moving_average", "EURUSD", "M1", 7, "ema")
    assert ema_key in feed._replay_indicator_cache


def test_static_indicator_hook_does_not_precompute_derived_timeframes():
    m1 = _bars(60)
    feed = ReplayFeed({"EURUSD": m1})

    assert feed.get_static_rates_for_indicator("EURUSD", "M1") is not None
    assert feed.get_static_rates_for_indicator("EURUSD", "M5") is None
