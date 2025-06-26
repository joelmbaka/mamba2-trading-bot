from mamba2.crew.logger import logger
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Union, Dict

def get_macd(symbol: str = "EURUSD", timeframe: Union[str, int] = None, 
              fast_period: int = 5, slow_period: int = 35, signal_period: int = 5,
              price_field: str = 'close', rate_fetcher=None, lookback_period: int = 0) -> Optional[Dict[str, pd.Series]]:
    """
    Calculate MACD values for a symbol using cached rates.

    Args:
        symbol: Trading symbol (default: EURUSD)
        timeframe: Timeframe string (e.g. 'M5') or integer in minutes
        fast_period: Fast EMA period (default: 5)
        slow_period: Slow EMA period (default: 35)
        signal_period: Signal line SMA period (default: 5)
        price_field: The price field to use (default: 'close')
        rate_fetcher: RateFetcher instance for cached rates
        lookback_period: Number of periods to return (0 returns all)

    Returns:
        dict: Dictionary with keys 'macd', 'signal', 'histogram' containing pandas Series, or None if not available
    """
    if rate_fetcher is None:
        logger.error("No rate_fetcher provided to get_macd")
        return None

    try:
        # Get cached rates and work on a copy to avoid mutating shared cache
        rates = rate_fetcher.get_rates(symbol, str(timeframe))
        if rates is None:
            logger.error(f"No cached rates available for {symbol} {timeframe}")
            return None

        # We need at least slow_period + signal_period - 1 candles
        min_rates = slow_period + signal_period - 1
        if len(rates) < min_rates:
            logger.warning(f"Insufficient rates for {symbol} (got {len(rates)}, need {min_rates})")
            return None

        # Use the specified price field
        prices = rates[price_field].copy()

        # Calculate Fast EMA
        fast_ema = prices.ewm(span=fast_period, adjust=False).mean()
        
        # Calculate Slow EMA
        slow_ema = prices.ewm(span=slow_period, adjust=False).mean()
        
        # Calculate MACD line (Fast EMA - Slow EMA)
        macd_line = fast_ema - slow_ema
        
        # Calculate Signal line (SMA of MACD line)
        signal_line = macd_line.rolling(window=signal_period).mean()
        
        # Calculate MACD histogram (MACD line - Signal line)
        macd_histogram = macd_line - signal_line
        
        # Convert to pandas Series with the same index as rates
        macd_series = pd.Series(macd_line.values, index=rates.index)
        signal_series = pd.Series(signal_line.values, index=rates.index)
        hist_series = pd.Series(macd_histogram.values, index=rates.index)
        
        # Apply lookback period if specified
        if lookback_period > 0:
            macd_series = macd_series.iloc[-lookback_period:]
            signal_series = signal_series.iloc[-lookback_period:]
            hist_series = hist_series.iloc[-lookback_period:]
        
        return {
            'macd': macd_series,
            'signal': signal_series,
            'histogram': hist_series
        }
        
    except Exception as e:
        logger.error(f"Error calculating MACD for {symbol}: {str(e)}")
        return None