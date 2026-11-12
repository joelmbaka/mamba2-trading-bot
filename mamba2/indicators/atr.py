from mamba2.crew.logger import logger
from typing import List


def _calculate_atr_series(rates, atr_period):
    """Calculate the production ATR series with the existing arithmetic."""

    work = rates.copy()
    work["prev_close"] = work["close"].shift(1)
    work["high-low"] = work["high"] - work["low"]
    work["high-prev_close"] = abs(work["high"] - work["prev_close"])
    work["low-prev_close"] = abs(work["low"] - work["prev_close"])
    work["tr"] = work[
        ["high-low", "high-prev_close", "low-prev_close"]
    ].max(axis=1)
    return work["tr"].rolling(atr_period).mean()


def _replay_cached_atr(
    rate_fetcher,
    *,
    symbol,
    timeframe,
    visible_rates,
    atr_period,
):
    """Return the causal cached ATR value for ReplayFeed when available."""

    static_getter = getattr(
        rate_fetcher,
        "get_static_rates_for_indicator",
        None,
    )
    if not callable(static_getter):
        return None, False

    source = static_getter(symbol, str(timeframe))
    if source is None or len(source) < len(visible_rates):
        return None, False

    visible_length = len(visible_rates)
    prefix_getter = getattr(
        rate_fetcher,
        "get_visible_prefix_length_for_indicator",
        None,
    )
    expected_length = (
        prefix_getter(symbol, str(timeframe))
        if callable(prefix_getter)
        else None
    )
    if expected_length is not None:
        if int(expected_length) != visible_length:
            return None, False
    elif not source.index[:visible_length].equals(visible_rates.index):
        return None, False

    cache = getattr(rate_fetcher, "_replay_indicator_cache", None)
    if cache is None:
        cache = {}
        try:
            setattr(rate_fetcher, "_replay_indicator_cache", cache)
        except (AttributeError, TypeError):
            return None, False

    key = (
        "atr",
        symbol,
        str(timeframe),
        int(atr_period),
    )
    signature = (
        id(source),
        len(source),
        source.index[0] if len(source) else None,
        source.index[-1] if len(source) else None,
    )
    cached = cache.get(key)
    if cached is None or cached["signature"] != signature:
        cached = {
            "signature": signature,
            "series": _calculate_atr_series(source, atr_period),
        }
        cache[key] = cached

    return cached["series"].iloc[visible_length - 1], True


def get_atr(symbol="EURUSD", timeframe=None, atr_period=14, rate_fetcher=None):
    """
    Calculate Average True Range (ATR) for a symbol using cached rates

    Args:
        symbol: Trading symbol (default: EURUSD)
        timeframe: Timeframe string (e.g. 'M5')
        atr_period: ATR calculation period (default: 14)
        rate_fetcher: RateFetcher instance for cached rates

    Returns:
        Current ATR value or None if not available
    """
    if rate_fetcher is None:
        logger.error("No rate_fetcher provided to get_atr")
        return None

    try:
        replay_getter = getattr(
            rate_fetcher,
            "get_visible_rates_for_indicator",
            None,
        )
        rates = (
            replay_getter(symbol, str(timeframe))
            if callable(replay_getter)
            else rate_fetcher.get_rates(symbol, str(timeframe))
        )
        if rates is None:
            logger.error(f"No cached rates available for {symbol} {timeframe}")
            return None

        if len(rates) < atr_period + 1:
            logger.warning(
                f"Insufficient rates for {symbol} "
                f"(got {len(rates)}, need {atr_period + 1})"
            )
            return 0.0

        cached_atr, used_cache = _replay_cached_atr(
            rate_fetcher,
            symbol=symbol,
            timeframe=timeframe,
            visible_rates=rates,
            atr_period=atr_period,
        )
        if used_cache:
            return cached_atr

        return _calculate_atr_series(rates, atr_period).iloc[-1]

    except Exception as e:
        logger.error(f"Error calculating ATR for {symbol}: {str(e)}")
        return None
