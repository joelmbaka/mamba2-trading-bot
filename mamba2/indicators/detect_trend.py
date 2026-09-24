"""Classify price direction from the ordinary-least-squares close-price slope.

This module intentionally depends only on NumPy/Pandas. The strategy uses only
the sign of the regression slope; computing that slope directly avoids loading
SciPy in the Wine/Windows trading runtime while preserving the same OLS model
used previously via scipy.stats.linregress.
"""

import numpy as np
import pandas as pd


def _ols_slope(values: np.ndarray) -> float:
    """Return the simple-regression slope for equally spaced observations."""
    y = np.asarray(values, dtype=float)
    if y.size < 2:
        return 0.0

    x = np.arange(y.size, dtype=float)
    x_centered = x - x.mean()
    y_centered = y - y.mean()
    denominator = float(np.dot(x_centered, x_centered))
    if denominator == 0.0:
        return 0.0
    return float(np.dot(x_centered, y_centered) / denominator)


def detect_trend(
    ohlc_data: pd.DataFrame,
    timeframe: str,
    symbol: str,
    lookback_period: int = 24,
) -> str:
    if len(ohlc_data) < 2:
        return "range"

    closes = ohlc_data["close"].to_numpy(dtype=float)[-lookback_period:]
    slope = _ols_slope(closes)

    if slope > 0:
        return "uptrend"
    if slope < 0:
        return "downtrend"
    return "range"


def calculate_5min_trendline(
    ohlc_data: pd.DataFrame,
    lookback_period: int = 30,
) -> str:
    return detect_trend(ohlc_data, "5m", "", lookback_period)
