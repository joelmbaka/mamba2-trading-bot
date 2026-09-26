from mamba2.crew.logger import logger
import pandas as pd
from typing import Optional, Union

def _replay_cached_moving_average(
    rate_fetcher,
    *,
    symbol: str,
    timeframe: Union[str, int],
    visible_rates: pd.DataFrame,
    ma_period: int,
    ma_method: str,
):
    """Return an exact causal replay cache for supported moving averages."""

    if ma_method not in {"ema", "sma"}:
        return None, False

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
    if not source.index[:visible_length].equals(visible_rates.index):
        return None, False

    cache = getattr(rate_fetcher, "_replay_indicator_cache", None)
    if cache is None:
        cache = {}
        try:
            setattr(rate_fetcher, "_replay_indicator_cache", cache)
        except (AttributeError, TypeError):
            return None, False

    key = (
        "moving_average",
        symbol,
        str(timeframe),
        int(ma_period),
        str(ma_method),
    )
    signature = (
        id(source),
        len(source),
        source.index[0] if len(source) else None,
        source.index[-1] if len(source) else None,
    )
    cached = cache.get(key)
    if cached is None or cached["signature"] != signature:
        closes = source["close"]
        if ma_method == "ema":
            series = closes.ewm(span=ma_period, adjust=False).mean()
        else:
            series = closes.rolling(ma_period).mean()
        cached = {
            "signature": signature,
            "series": series,
        }
        cache[key] = cached

    return cached["series"].iloc[visible_length - 1], True


def get_moving_average(symbol: str = "EURUSD", timeframe: Union[str, int] = None, ma_period: int = 13, 
                       ma_method: str = "ema", rate_fetcher=None) -> Optional[float]:
    """
    Calculate Moving Average for a symbol using cached rates.

    Args:
        symbol: Trading symbol (default: EURUSD)
        timeframe: Timeframe string (e.g. 'M5') or integer in minutes
        ma_period: MA calculation period (default: 13)
        ma_method: Moving average method. Supported: 'sma', 'ema', 'smma', 'lwma'. Default: 'ema'
        rate_fetcher: RateFetcher instance for cached rates

    Returns:
        Current MA value or None if not available
    """
    if rate_fetcher is None:
        logger.error("No rate_fetcher provided to get_moving_average")
        return None

    try:
        # ReplayFeed exposes a causal read-only view so historical
        # evaluation does not deep-copy the whole visible prefix. Production
        # fetchers keep using their ordinary get_rates contract.
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

        if len(rates) < ma_period:
            logger.warning(f"Insufficient rates for {symbol} (got {len(rates)}, need {ma_period})")
            return 0.0

        # We'll use the 'close' price for calculation
        closes = rates['close']

        cached_ma, used_cache = _replay_cached_moving_average(
            rate_fetcher,
            symbol=symbol,
            timeframe=timeframe,
            visible_rates=rates,
            ma_period=ma_period,
            ma_method=ma_method,
        )
        if used_cache:
            return cached_ma

        # Calculate the moving average based on the method
        if ma_method == 'sma':
            # Simple Moving Average
            ma = closes.rolling(ma_period).mean().iloc[-1]
        elif ma_method == 'ema':
            # Exponential Moving Average
            ma = closes.ewm(span=ma_period, adjust=False).mean().iloc[-1]
        elif ma_method == 'smma':
            # Smoothed Moving Average (SMMA)
            # Initialize with the first value as the SMA of the first `ma_period` values
            if len(closes) < ma_period:
                return 0.0
            smma = closes.iloc[:ma_period].mean()
            # Calculate the remaining values
            for i in range(ma_period, len(closes)):
                smma = (smma * (ma_period-1) + closes.iloc[i]) / ma_period
            ma = smma
        elif ma_method == 'lwma':
            # Linear Weighted Moving Average
            # Weights: from 1 to ma_period (most recent has the highest weight)
            weights = pd.Series(range(1, ma_period+1))
            # Extract the last `ma_period` closes
            last_closes = closes.iloc[-ma_period:]
            ma = (last_closes * weights).sum() / weights.sum()
        else:
            logger.error(f"Unsupported moving average method: {ma_method}")
            return None

        return ma

    except Exception as e:
        logger.error(f"Error calculating moving average for {symbol}: {str(e)}")
        return None