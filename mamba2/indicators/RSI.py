from mamba2.crew.logger import logger
import pandas as pd
import numpy as np
from typing import Optional, Union

def get_rsi(symbol: str = "EURUSD", timeframe: Union[str, int] = None, rsi_period: int = 14, 
             price_field: str = 'close', rate_fetcher=None) -> Optional[float]:
    """
    Calculate the current RSI value for a symbol using cached rates.

    Args:
        symbol: Trading symbol (default: EURUSD)
        timeframe: Timeframe string (e.g. 'M5') or integer in minutes
        rsi_period: RSI period (default: 14)
        price_field: The price field to use (default: 'close'). Must be one of: 'close', 'open', 'high', 'low'.
        rate_fetcher: RateFetcher instance for cached rates

    Returns:
        Current RSI value or None if not available
    """
    if rate_fetcher is None:
        logger.error("No rate_fetcher provided to get_rsi")
        return None

    try:
        # Get cached rates and work on a copy to avoid mutating shared cache
        rates = rate_fetcher.get_rates(symbol, str(timeframe))
        if rates is None:
            logger.error(f"No cached rates available for {symbol} {timeframe}")
            return None

        # We need at least rsi_period+1 to calculate because we are taking the diff
        if len(rates) < rsi_period + 1:
            logger.warning(f"Insufficient rates for {symbol} (got {len(rates)}, need {rsi_period+1})")
            return None

        # Use the specified price field
        prices = rates[price_field].copy()

        # Calculate price changes
        delta = prices.diff()

        # Create gain (up) and loss (down) Series
        gain = delta.copy()
        loss = delta.copy()
        
        gain[gain < 0] = 0
        loss[loss > 0] = 0
        loss = abs(loss)
        
        # First average gain and loss calculations using SMA (simple moving average)
        # We skip the first value (which is NaN because of diff) and take the next `rsi_period` values
        first_avg_gain = gain.iloc[1:rsi_period+1].mean()
        first_avg_loss = loss.iloc[1:rsi_period+1].mean()
        
        # Initialize avg_gain and avg_loss Series with NaN values
        avg_gain = pd.Series(np.nan, index=prices.index)
        avg_loss = pd.Series(np.nan, index=prices.index)
        
        # Set the first value at position 'rsi_period'
        avg_gain.iloc[rsi_period] = first_avg_gain
        avg_loss.iloc[rsi_period] = first_avg_loss
        
        # Calculate subsequent values using Wilder's smoothing method
        for i in range(rsi_period + 1, len(prices)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (rsi_period - 1) + gain.iloc[i]) / rsi_period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (rsi_period - 1) + loss.iloc[i]) / rsi_period
        
        # Calculate RS (Relative Strength)
        rs = avg_gain / avg_loss
        
        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))
        
        # Return the most recent RSI value
        return rsi.iloc[-1]
        
    except Exception as e:
        logger.error(f"Error calculating RSI for {symbol}: {str(e)}")
        return None