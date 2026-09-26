import numpy as np
import pandas as pd
from mamba2.crew.logger import logger
from typing import Union, Optional


def _calculate_stochastic_components(
    rates: pd.DataFrame,
    *,
    k_period: int,
    d_period: int,
    slowing: int,
    price_field: str,
):
    """Calculate stochastic arrays using the production arithmetic exactly."""

    high = rates["high"].values
    low = rates["low"].values
    close = rates["close"].values
    length = len(rates)

    highest_high = np.zeros(length)
    lowest_low = np.zeros(length)
    main_k = np.zeros(length)
    signal_d = np.zeros(length)

    for i in range(k_period - 1, length):
        if price_field == "high/low":
            highest_high[i] = max(high[i - k_period + 1:i + 1])
            lowest_low[i] = min(low[i - k_period + 1:i + 1])
        else:
            highest_high[i] = max(close[i - k_period + 1:i + 1])
            lowest_low[i] = min(close[i - k_period + 1:i + 1])

    for i in range(k_period - 1 + slowing - 1, length):
        sum_low = 0.0
        sum_high = 0.0

        for j in range(i - slowing + 1, i + 1):
            sum_low += close[j] - lowest_low[j]
            sum_high += highest_high[j] - lowest_low[j]

        if sum_high == 0.0:
            main_k[i] = 100.0
        else:
            main_k[i] = (sum_low / sum_high) * 100

    for i in range(d_period - 1, length):
        if i >= k_period - 1 + slowing - 1:
            signal_d[i] = np.mean(main_k[i - d_period + 1:i + 1])

    return {
        "highest_high": highest_high,
        "lowest_low": lowest_low,
        "k": pd.Series(main_k, index=rates.index),
        "d": pd.Series(signal_d, index=rates.index),
        "closes": rates["close"],
    }


def _replay_cached_components(
    rate_fetcher,
    *,
    symbol: str,
    timeframe: Union[str, int],
    visible_rates: pd.DataFrame,
    k_period: int,
    d_period: int,
    slowing: int,
    price_field: str,
):
    """Return causal cached components for ReplayFeed when safely available."""

    static_getter = getattr(
        rate_fetcher,
        "get_static_rates_for_indicator",
        None,
    )
    if not callable(static_getter):
        return None

    source = static_getter(symbol, str(timeframe))
    if source is None or len(source) < len(visible_rates):
        return None

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
            return None
    elif not source.index[:visible_length].equals(visible_rates.index):
        return None

    cache = getattr(rate_fetcher, "_replay_indicator_cache", None)
    if cache is None:
        cache = {}
        try:
            setattr(rate_fetcher, "_replay_indicator_cache", cache)
        except (AttributeError, TypeError):
            return None

    key = (
        "stochastic",
        symbol,
        str(timeframe),
        int(k_period),
        int(d_period),
        int(slowing),
        str(price_field),
    )
    signature = (
        id(source),
        len(source),
        source.index[0] if len(source) else None,
        source.index[-1] if len(source) else None,
    )
    cached = cache.get(key)
    if cached is None or cached["signature"] != signature:
        components = _calculate_stochastic_components(
            source,
            k_period=k_period,
            d_period=d_period,
            slowing=slowing,
            price_field=price_field,
        )
        unequal = (
            components["highest_high"] != components["lowest_low"]
        ).astype(np.uint8)
        range_seen = np.maximum.accumulate(unequal).astype(bool)
        cached = {
            "signature": signature,
            "components": components,
            "range_seen": range_seen,
        }
        cache[key] = cached

    components = cached["components"]
    all_prices_equal = (
        True
        if visible_length == 0
        else not bool(cached["range_seen"][visible_length - 1])
    )
    return {
        "highest_high": components["highest_high"][:visible_length],
        "lowest_low": components["lowest_low"][:visible_length],
        "k": components["k"].iloc[:visible_length],
        "d": components["d"].iloc[:visible_length],
        "closes": components["closes"].iloc[:visible_length],
        "all_prices_equal": all_prices_equal,
    }


def get_stochastic(
    symbol: str = "EURUSD",
    timeframe: Union[str, int] = None,
    k_period: int = 21,
    d_period: int = 7,
    slowing: int = 7,
    price_field: str = "high/low",
    rate_fetcher=None,
    lookback_period: int = 0,
) -> Optional[dict]:
    if rate_fetcher is None:
        logger.error("No rate_fetcher provided to get_stochastic")
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

        if len(rates) < k_period + d_period + slowing:
            logger.warning(
                f"Insufficient rates for {symbol} "
                f"(got {len(rates)}, need {k_period + d_period + slowing})"
            )
            return None

        components = _replay_cached_components(
            rate_fetcher,
            symbol=symbol,
            timeframe=timeframe,
            visible_rates=rates,
            k_period=k_period,
            d_period=d_period,
            slowing=slowing,
            price_field=price_field,
        )
        if components is None:
            components = _calculate_stochastic_components(
                rates,
                k_period=k_period,
                d_period=d_period,
                slowing=slowing,
                price_field=price_field,
            )

        highest_high = components["highest_high"]
        lowest_low = components["lowest_low"]
        all_prices_equal = components.get("all_prices_equal")
        if all_prices_equal is None:
            all_prices_equal = bool(np.all(highest_high == lowest_low))
        if all_prices_equal:
            logger.warning(
                f"All prices equal for {symbol} {timeframe} "
                "- cannot calculate stochastic"
            )
            return None

        k_series = components["k"]
        d_series = components["d"]
        closes_series = components["closes"]

        if lookback_period > 0:
            k_series = k_series.iloc[-lookback_period:]
            d_series = d_series.iloc[-lookback_period:]
            closes_series = closes_series.iloc[-lookback_period:]

        return {
            "k": k_series,
            "d": d_series,
            "closes": closes_series,
        }

    except Exception as e:
        logger.error(
            f"Error calculating stochastic for {symbol} {timeframe}: {str(e)}",
            exc_info=True,
        )
        return None
