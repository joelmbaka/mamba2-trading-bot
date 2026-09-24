"""Regression tests for strategy trend-direction classification."""

import pandas as pd

from mamba2.indicators.detect_trend import calculate_5min_trendline, detect_trend


def closes(values):
    return pd.DataFrame({"close": values})


def test_detect_trend_classifies_positive_negative_and_flat_ols_slopes():
    assert detect_trend(closes([1.0, 2.0, 3.0, 4.0]), "M5", "EURUSD") == "uptrend"
    assert detect_trend(closes([4.0, 3.0, 2.0, 1.0]), "M5", "EURUSD") == "downtrend"
    assert detect_trend(closes([2.0, 2.0, 2.0, 2.0]), "M5", "EURUSD") == "range"


def test_detect_trend_preserves_lookback_and_short_history_behavior():
    data = closes([10.0, 9.0, 8.0, 7.0, 8.0, 9.0, 10.0])
    assert detect_trend(data, "M5", "EURUSD", lookback_period=3) == "uptrend"
    assert detect_trend(closes([1.0]), "M5", "EURUSD") == "range"


def test_calculate_5min_trendline_uses_same_direction_classifier():
    assert calculate_5min_trendline(closes([1.0, 1.5, 2.0])) == "uptrend"
