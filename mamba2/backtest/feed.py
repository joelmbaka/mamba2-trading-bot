"""A completed-candle-only historical replay feed.

Historical source indexes are BAR OPEN timestamps. The replay clock is an
information-availability timestamp, so a source candle is strategy-visible
only when ``bar_open + timeframe <= replay_time``.
"""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from .data import REQUIRED_BAR_COLUMNS, canonicalize_bars


TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15}


class ReplayFeed:
    """Advance through M1 bars and expose only completed historical views.

    ``advance`` moves the information clock to the next M1 completion
    boundary. A derived M5/M15 candle becomes visible only after all of its
    constituent M1 candles are visible. The feed's clock is therefore the
    only source of historical time; callers cannot request bars beyond
    ``current_time``.
    """

    def __init__(self, bars: pd.DataFrame | Mapping[str, pd.DataFrame], *, symbol: str = "EURUSD"):
        if isinstance(bars, Mapping):
            self._bars = {name: canonicalize_bars(frame) for name, frame in bars.items()}
        else:
            self._bars = {symbol: canonicalize_bars(bars)}
        if not self._bars or any(frame.empty for frame in self._bars.values()):
            raise ValueError("at least one non-empty symbol history is required")
        self._timeline = pd.DatetimeIndex(
            sorted(
                set().union(
                    *(frame.index + pd.Timedelta(minutes=1) for frame in self._bars.values())
                )
            )
        )
        self._position = -1

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(self._bars)

    @property
    def current_time(self) -> pd.Timestamp | None:
        return None if self._position < 0 else self._timeline[self._position]

    @property
    def finished(self) -> bool:
        return self._position >= len(self._timeline) - 1

    def advance(self) -> pd.Timestamp:
        """Expose exactly one more timestamp and return the replay time."""
        if self.finished:
            raise StopIteration("replay has no more M1 candles")
        self._position += 1
        return self.current_time  # type: ignore[return-value]

    def current_bar(self, symbol: str) -> pd.Series | None:
        """Return the latest completed source bar visible to strategy code."""
        visible = self.get_rates(symbol, "M1")
        return None if visible.empty else visible.iloc[-1]

    def completed_bar(self, symbol: str) -> pd.Series | None:
        """Return the M1 bar whose range became known at current_time."""
        if self.current_time is None or symbol not in self._bars:
            return None
        opening = self.current_time - pd.Timedelta(minutes=1)
        source = self._bars[symbol]
        return source.loc[opening] if opening in source.index else None

    def execution_bar(self, symbol: str) -> pd.Series | None:
        """Return only the current bar open used for broker execution."""
        if self.current_time is None or symbol not in self._bars:
            return None
        source = self._bars[symbol]
        return source.loc[self.current_time] if self.current_time in source.index else None

    def get_rates(self, symbol: str, timeframe: str | int) -> pd.DataFrame:
        """Return completed bars visible at the current replay instant."""
        if symbol not in self._bars or self.current_time is None:
            return pd.DataFrame(columns=REQUIRED_BAR_COLUMNS, index=pd.DatetimeIndex([], name="time"))
        timeframe_name = f"M{timeframe}" if isinstance(timeframe, int) else timeframe
        if timeframe_name not in TIMEFRAME_MINUTES:
            raise ValueError(f"unsupported replay timeframe: {timeframe_name}")

        source = self._bars[symbol]
        visible = source.loc[
            source.index + pd.Timedelta(minutes=1) <= self.current_time
        ]
        if timeframe_name == "M1":
            return visible.copy()

        minutes = TIMEFRAME_MINUTES[timeframe_name]
        groups = visible.groupby(visible.index.floor(f"{minutes}min"), sort=True)
        rows: list[dict] = []
        for start, group in groups:
            expected = pd.date_range(start, periods=minutes, freq="min", tz="UTC")
            if len(group) != minutes or not group.index.equals(expected):
                continue
            rows.append(
                {
                    "time": start,
                    "open": group["open"].iloc[0],
                    "high": group["high"].max(),
                    "low": group["low"].min(),
                    "close": group["close"].iloc[-1],
                    "tick_volume": group["tick_volume"].sum(),
                    "spread": group["spread"].iloc[-1],
                    "real_volume": group["real_volume"].sum(),
                }
            )
        return canonicalize_bars(rows) if rows else pd.DataFrame(
            columns=REQUIRED_BAR_COLUMNS,
            index=pd.DatetimeIndex([], name="time"),
        )
