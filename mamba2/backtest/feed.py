"""A completed-candle-only historical replay feed.

Historical source indexes are BAR OPEN timestamps. The replay clock is an
information-availability timestamp, so a source candle is strategy-visible
only when ``bar_open + timeframe <= replay_time``.

M1 history drives the replay clock. Optional broker-native M5/M15 histories
may be supplied for strategy parity with live MT5 data. When a native
higher-timeframe series is present it is preferred over M1 resampling; when
it is absent, ReplayFeed deterministically derives the timeframe from M1.
"""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from .data import (
    REQUIRED_BAR_COLUMNS,
    canonicalize_bars,
    canonicalize_price_bars,
)


TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15}


def _empty_rates() -> pd.DataFrame:
    return pd.DataFrame(
        columns=REQUIRED_BAR_COLUMNS,
        index=pd.DatetimeIndex([], name="time"),
    )


def _timeframe_name(timeframe: str | int) -> str:
    name = f"M{timeframe}" if isinstance(timeframe, int) else timeframe
    if name not in TIMEFRAME_MINUTES:
        raise ValueError(f"unsupported replay timeframe: {name}")
    return name


class ReplayFeed:
    """Advance through M1 bars and expose only completed historical views.

    ``advance`` moves the information clock to the next M1 completion
    boundary. A candle is visible only after its full duration has elapsed.

    Higher-timeframe data may come from either:

    - broker-native M5/M15 OHLC supplied via ``native_timeframe_bars``; or
    - deterministic aggregation of the replay's M1 source history.

    Native bars are preferred when available so a later MT5 exporter can
    reproduce exactly the timeframe candles seen by the live strategy.
    """

    def __init__(
        self,
        bars: pd.DataFrame | Mapping[str, pd.DataFrame],
        *,
        symbol: str = "EURUSD",
        native_timeframe_bars: Mapping[
            str, Mapping[str | int, pd.DataFrame]
        ] | None = None,
        ask_m1_bars: Mapping[str, pd.DataFrame] | None = None,
    ):
        if isinstance(bars, Mapping):
            self._bars = {
                name: canonicalize_bars(frame)
                for name, frame in bars.items()
            }
        else:
            self._bars = {symbol: canonicalize_bars(bars)}

        if not self._bars or any(frame.empty for frame in self._bars.values()):
            raise ValueError("at least one non-empty symbol history is required")

        self._ask_m1_bars: dict[str, pd.DataFrame] = {}
        for ask_symbol, frame in (ask_m1_bars or {}).items():
            if ask_symbol not in self._bars:
                raise ValueError(
                    f"Ask M1 history has no Bid M1 source for symbol: {ask_symbol}"
                )
            ask = canonicalize_price_bars(frame)
            if not ask.index.isin(self._bars[ask_symbol].index).all():
                raise ValueError(
                    f"Ask M1 history contains timestamps absent from Bid M1: "
                    f"{ask_symbol}"
                )
            self._ask_m1_bars[ask_symbol] = ask

        self._native_timeframe_bars: dict[
            str, dict[str, pd.DataFrame]
        ] = {}
        for native_symbol, timeframe_map in (native_timeframe_bars or {}).items():
            if native_symbol not in self._bars:
                raise ValueError(
                    f"native timeframe history has no M1 source for symbol: "
                    f"{native_symbol}"
                )

            normalized: dict[str, pd.DataFrame] = {}
            for timeframe, frame in timeframe_map.items():
                name = _timeframe_name(timeframe)
                if name == "M1":
                    raise ValueError(
                        "M1 must be supplied through the primary bars source"
                    )

                native = canonicalize_bars(frame)
                minutes = TIMEFRAME_MINUTES[name]
                aligned = native.index == native.index.floor(f"{minutes}min")
                if not aligned.all():
                    raise ValueError(
                        f"{native_symbol} {name} bars must use aligned "
                        "bar-open timestamps"
                    )
                normalized[name] = native

            if normalized:
                self._native_timeframe_bars[native_symbol] = normalized

        self._timeline = pd.DatetimeIndex(
            sorted(
                set().union(
                    *(
                        frame.index + pd.Timedelta(minutes=1)
                        for frame in self._bars.values()
                    )
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
        """Expose exactly one more M1 completion boundary."""
        if self.finished:
            raise StopIteration("replay has no more M1 candles")
        self._position += 1
        return self.current_time  # type: ignore[return-value]

    def current_bar(self, symbol: str) -> pd.Series | None:
        """Return the latest completed M1 source bar without copying history."""
        if symbol not in self._bars or self.current_time is None:
            return None
        source = self._bars[symbol]
        cutoff = self.current_time - pd.Timedelta(minutes=1)
        stop = int(source.index.searchsorted(cutoff, side="right"))
        return None if stop == 0 else source.iloc[stop - 1]

    def current_ask_bar(self, symbol: str) -> pd.Series | None:
        """Return Ask OHLC matching the latest completed visible M1 bar."""
        bid = self.current_bar(symbol)
        if bid is None:
            return None
        source = self._ask_m1_bars.get(symbol)
        if source is None or bid.name not in source.index:
            return None
        return source.loc[bid.name]

    def completed_ask_bar(self, symbol: str) -> pd.Series | None:
        """Return Ask OHLC for the M1 bar completing at current_time."""
        if self.current_time is None:
            return None
        source = self._ask_m1_bars.get(symbol)
        if source is None:
            return None
        opening = self.current_time - pd.Timedelta(minutes=1)
        return source.loc[opening] if opening in source.index else None

    def execution_ask_bar(self, symbol: str) -> pd.Series | None:
        """Return Ask OHLC for the M1 execution bar at current_time."""
        if self.current_time is None:
            return None
        source = self._ask_m1_bars.get(symbol)
        if source is None:
            return None
        return (
            source.loc[self.current_time]
            if self.current_time in source.index
            else None
        )

    def completed_bar(self, symbol: str) -> pd.Series | None:
        """Return the M1 bar whose range became known at current_time."""
        if self.current_time is None or symbol not in self._bars:
            return None
        opening = self.current_time - pd.Timedelta(minutes=1)
        source = self._bars[symbol]
        return source.loc[opening] if opening in source.index else None

    def execution_bar(self, symbol: str) -> pd.Series | None:
        """Return only the M1 bar whose open is usable for execution now."""
        if self.current_time is None or symbol not in self._bars:
            return None
        source = self._bars[symbol]
        return (
            source.loc[self.current_time]
            if self.current_time in source.index
            else None
        )

    def get_visible_rates_for_indicator(
        self,
        symbol: str,
        timeframe: str | int,
    ) -> pd.DataFrame:
        """Return a causal replay-only read view without deep-copying history.

        This hook is intentionally separate from get_rates. Production
        callers retain the existing copy-returning API. Replay indicators and
        strategy reads may use this hook only as immutable input.
        """
        if symbol not in self._bars or self.current_time is None:
            return _empty_rates()

        timeframe_name = _timeframe_name(timeframe)
        if timeframe_name == "M1":
            source = self._bars[symbol]
            cutoff = self.current_time - pd.Timedelta(minutes=1)
            stop = int(source.index.searchsorted(cutoff, side="right"))
            return source.iloc[:stop]

        minutes = TIMEFRAME_MINUTES[timeframe_name]
        native = self._native_timeframe_bars.get(symbol, {}).get(
            timeframe_name
        )
        if native is not None:
            cutoff = self.current_time - pd.Timedelta(minutes=minutes)
            stop = int(native.index.searchsorted(cutoff, side="right"))
            return native.iloc[:stop]

        # Preserve the accepted derived-timeframe aggregation path when no
        # broker-native timeframe exists.
        return self.get_rates(symbol, timeframe_name)


    def get_static_rates_for_indicator(
        self,
        symbol: str,
        timeframe: str | int,
    ) -> pd.DataFrame | None:
        """Return immutable full source history for causal indicator caching.

        This replay-only hook intentionally exposes the source series, including
        future rows, only to indicator implementations that precompute causal
        values and then slice them back to the currently visible prefix.
        Production rate fetchers do not implement this hook.

        Native higher-timeframe history is returned only when it exists.  The
        derived-M5/M15 fallback remains on the ordinary visible-data path so
        precomputation cannot alter aggregation semantics.
        """
        if symbol not in self._bars:
            return None

        timeframe_name = _timeframe_name(timeframe)
        if timeframe_name == "M1":
            return self._bars[symbol]
        return self._native_timeframe_bars.get(symbol, {}).get(timeframe_name)

    def get_rates(
        self,
        symbol: str,
        timeframe: str | int,
    ) -> pd.DataFrame:
        """Return completed bars visible at the current replay instant."""
        if symbol not in self._bars or self.current_time is None:
            return _empty_rates()

        timeframe_name = _timeframe_name(timeframe)
        source = self._bars[symbol]
        m1_cutoff = self.current_time - pd.Timedelta(minutes=1)
        m1_stop = int(source.index.searchsorted(m1_cutoff, side="right"))
        visible_m1 = source.iloc[:m1_stop]
        if timeframe_name == "M1":
            return visible_m1.copy()

        minutes = TIMEFRAME_MINUTES[timeframe_name]
        native = self._native_timeframe_bars.get(symbol, {}).get(timeframe_name)
        if native is not None:
            native_cutoff = self.current_time - pd.Timedelta(minutes=minutes)
            native_stop = int(
                native.index.searchsorted(native_cutoff, side="right")
            )
            return native.iloc[:native_stop].copy()

        groups = visible_m1.groupby(
            visible_m1.index.floor(f"{minutes}min"),
            sort=True,
        )
        rows: list[dict] = []
        for start, group in groups:
            expected = pd.date_range(
                start,
                periods=minutes,
                freq="min",
                tz="UTC",
            )
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

        return canonicalize_bars(rows) if rows else _empty_rates()
