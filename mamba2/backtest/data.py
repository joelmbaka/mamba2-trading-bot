"""Canonical historical bar validation for offline replay."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import numpy as np
import pandas as pd


REQUIRED_BAR_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
)


class HistoricalDataError(ValueError):
    """Raised when historical bars cannot be used deterministically."""


def canonicalize_bars(
    bars: pd.DataFrame | Iterable[Mapping],
    *,
    timestamp_column: str = "time",
) -> pd.DataFrame:
    """Return validated bars indexed by UTC timestamps.

    Naive timestamps are interpreted as UTC. A timezone-aware input is
    converted to UTC. This explicit rule keeps replay independent of the host
    machine timezone. Input rows must already be strictly chronological;
    duplicate or out-of-order timestamps are rejected rather than silently
    reordered.
    """

    frame = bars.copy() if isinstance(bars, pd.DataFrame) else pd.DataFrame(list(bars))
    if timestamp_column in frame.columns:
        timestamps = pd.to_datetime(frame.pop(timestamp_column), utc=True, errors="coerce")
    elif isinstance(frame.index, pd.DatetimeIndex):
        timestamps = pd.to_datetime(frame.index, utc=True, errors="coerce")
    else:
        raise HistoricalDataError(f"missing timestamp column: {timestamp_column}")

    missing = [column for column in REQUIRED_BAR_COLUMNS if column not in frame.columns]
    if missing:
        raise HistoricalDataError(f"missing required bar columns: {missing}")
    if timestamps.isna().any():
        raise HistoricalDataError("timestamps must be valid")
    if timestamps.duplicated().any():
        raise HistoricalDataError("duplicate timestamps are not allowed")
    if not timestamps.is_monotonic_increasing:
        raise HistoricalDataError("timestamps must be strictly chronological")

    result = frame.loc[:, REQUIRED_BAR_COLUMNS].copy()
    for column in REQUIRED_BAR_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    if result.loc[:, REQUIRED_BAR_COLUMNS].isna().any().any():
        raise HistoricalDataError("bar values must be numeric and non-null")

    prices = result[["open", "high", "low", "close"]].to_numpy(dtype=float)
    if not np.isfinite(prices).all():
        raise HistoricalDataError("OHLC values must be finite")
    if ((result["high"] < result[["open", "close"]].max(axis=1)).any() or
            (result["low"] > result[["open", "close"]].min(axis=1)).any()):
        raise HistoricalDataError("OHLC values violate high/low bounds")
    if (result[["tick_volume", "spread", "real_volume"]] < 0).any().any():
        raise HistoricalDataError("volume and spread values cannot be negative")

    result.index = pd.DatetimeIndex(timestamps, name="time")
    return result
