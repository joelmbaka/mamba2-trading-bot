"""Trend line indicator utility.

Provides two functions:
- `get_trend_line`: calculate a simple linear‐regression trend line for the last
  *lookback* bars.
- `plot_trend_line`: fetch recent prices, compute the trend line and plot the
  close-price series together with the trend line, returning the figure (and
  optionally saving it).

NOTE:  This is a pragmatic implementation suited for automated tests.  It does
NOT attempt to find swing-high / swing-low anchor points; instead it uses a
least-squares line of best fit.  This keeps the code compact, dependency-free
and deterministic while still demonstrating how a trend line can be drawn.
"""
from __future__ import annotations

from typing import Dict, Union, Optional

import numpy as np
import pandas as pd

from mamba2.crew.logger import logger

# Matplotlib is only imported inside the plotting helper so that users that
# merely need the numeric output do not pay the import cost.

def get_trend_line(
    rate_fetcher,
    symbol: str = "EURUSD",
    timeframe: Union[str, int] = "M5",
    lookback: int = 100,
) -> Optional[Dict[str, Union[np.ndarray, float]]]:
    """Calculate a linear trend line for *symbol* / *timeframe*.

    Args:
        rate_fetcher: RatesFetcher-like object that exposes ``get_rates``.
        symbol: Trading symbol, e.g. ``"EURUSD"``.
        timeframe: Time-frame string or minutes, e.g. ``"M5"`` or ``5``.
        lookback: Number of most-recent bars used to build the line.  Must be
            **≥ 3** to ensure the line is meaningful.

    Returns:
        ``dict`` with keys ``slope``, ``intercept``, ``x`` (array of indices)
        and ``y`` (array of fitted values) **or** ``None`` if data is
        unavailable / insufficient.
    """
    if lookback < 3:
        logger.warning("Trend line requires at least 3 points; got %d", lookback)
        return None

    if rate_fetcher is None or not hasattr(rate_fetcher, "get_rates"):
        logger.error("A valid rate_fetcher must be supplied to get_trend_line")
        return None

    # Fetch OHLCV data from cache
    rates: Optional[pd.DataFrame] = rate_fetcher.get_rates(symbol, str(timeframe))
    if rates is None or rates.empty:
        logger.error("No cached rates available for %s %s", symbol, timeframe)
        return None

    # Work only on a *copy* of the last *lookback* rows so we never mutate the
    # shared cache.
    data = rates.iloc[-lookback:].copy()

    if len(data) < 3:
        logger.warning("Insufficient bars (need ≥ 3, got %d) for trend line", len(data))
        return None

    # Use close prices for the regression.
    closes = data["close"].values.astype(float)
    x = np.arange(len(closes))

    # Ordinary least squares: y = m·x + c
    slope, intercept = np.polyfit(x, closes, 1)
    y = slope * x + intercept

    return {
        "slope": slope,
        "intercept": intercept,
        "x": x,
        "y": y,
        "closes": closes,
        "index": data.index,
    }


def plot_trend_line(
    rate_fetcher,
    symbol: str = "EURUSD",
    timeframe: Union[str, int] = "M5",
    lookback: int = 100,
    save_path: str | None = None,
):
    """Plot close prices with the computed trend line.

    On success returns the ``matplotlib.figure.Figure`` instance; otherwise
    returns ``None``.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # Always use non-interactive backend
        import matplotlib.pyplot as plt
    except Exception as e:  # pragma: no cover – Import errors handled gracefully
        logger.error("Matplotlib unavailable: %s", e)
        return None

    result = get_trend_line(rate_fetcher, symbol, timeframe, lookback)
    if result is None:
        return None

    x = result["x"]
    closes = result["closes"]
    y = result["y"]
    idx = result["index"]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(idx, closes, label="Close", linewidth=1.0)
    ax.plot(idx, y, label="Trend line", color="orange", linewidth=1.5)
    ax.set_title(f"{symbol} {timeframe} – Trend Line ({lookback} bars)")
    ax.set_xlabel("Time")
    ax.set_ylabel("Price")
    ax.legend()
    fig.autofmt_xdate()

    if save_path:
        try:
            fig.savefig(save_path, dpi=110, bbox_inches="tight")
        except Exception as e:
            logger.error("Failed to save trend line plot: %s", e)

    # Close the figure if the caller does not need it.
    plt.close(fig)
    return fig
