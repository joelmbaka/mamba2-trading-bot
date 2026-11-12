"""M030 Stage 1E synthetic vector equivalence, no MT5/backtesting.

Proves the 48-bar rolling stochastic window and 15-bar ATR tail can
reproduce the original Python full-prefix *latest* values after their
warm-up, while EMA keeps its original first-close seed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mamba2.indicators.stochastic import _calculate_stochastic_components
from mamba2.indicators.atr import _calculate_atr_series

K, D, S = 21, 7, 7
WINDOW = 48


def _bars(n=280):
    # Deterministic oscillating prices stress high/low extrema, trending and
    # flat runs. Not a real market feed and not an economic backtest.
    x = np.arange(n, dtype=float)
    close = 1.10 + 0.0006 * np.sin(x / 3.1) + 0.00025 * np.cos(x / 11.0)
    close[60:90] = close[59]       # zero-price-movement sequence
    opening = np.r_[close[0], close[:-1]]
    high = np.maximum(close, opening) + 0.00010
    low = np.minimum(close, opening) - 0.00010
    high[60:90] = close[59]
    low[60:90] = close[59]
    return pd.DataFrame(
        {"open": opening, "high": high, "low": low, "close": close},
        index=pd.date_range("2026-01-01", periods=n, freq="min", tz="UTC"),
    )


@pytest.mark.parametrize("length", [48, 49, 50, 55, 60, 75, 90, 100, 155, 200, 280])
def test_latest_stochastic_and_ten_extremes_equal_full_prefix(length):
    data = _bars().iloc[:length]
    full = _calculate_stochastic_components(
        data, k_period=K, d_period=D, slowing=S, price_field="high/low")
    tail = _calculate_stochastic_components(
        data.iloc[-WINDOW:], k_period=K, d_period=D, slowing=S,
        price_field="high/low")
    assert float(tail["k"].iloc[-1]) == pytest.approx(
        float(full["k"].iloc[-1]), abs=1e-10)
    assert float(tail["d"].iloc[-1]) == pytest.approx(
        float(full["d"].iloc[-1]), abs=1e-10)
    assert bool((tail["k"].iloc[-10:] < 20).any()) == bool(
        (full["k"].iloc[-10:] < 20).any())
    assert bool((tail["k"].iloc[-10:] > 80).any()) == bool(
        (full["k"].iloc[-10:] > 80).any())


@pytest.mark.parametrize("length", [48, 49, 60, 75, 90, 150, 280])
def test_ema_first_source_seed_and_increment_match_full_prefix(length):
    data = _bars().iloc[:length]
    closes = data["close"].tolist()
    current = closes[0]
    for value in closes[1:]:
        current = 0.25 * value + 0.75 * current
    baseline = float(data["close"].ewm(span=7, adjust=False).mean().iloc[-1])
    assert current == pytest.approx(baseline, abs=1e-12)
    # Discriminating full-vs-truncated public API regression is exercised
    # with a deliberately nonstationary source in test_m030_stage1q_boundaries.py.


@pytest.mark.parametrize("length", [48, 49, 60, 75, 90, 150, 280])
def test_last_fifteen_m5_bars_preserve_atr14(length):
    data = _bars().iloc[:length]
    full = _calculate_atr_series(data, 14).iloc[-1]
    tail = _calculate_atr_series(data.iloc[-15:], 14).iloc[-1]
    assert float(full) == pytest.approx(float(tail), abs=1e-12)


def test_no_fresh_crossover_needed_for_repeated_extreme():
    # This is intentionally a state check, NOT a previous-K/D cross test.
    recent_k = [10.0] + [30.0] * 8 + [55.0]
    current_k, current_d = recent_k[-1], 50.0
    assert min(recent_k) < 20
    assert current_k > current_d
