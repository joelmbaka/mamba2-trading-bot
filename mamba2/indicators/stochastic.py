import numpy as np
import pandas as pd
from mamba2.crew.logger import logger
from typing import Union, Optional

def get_stochastic(symbol: str = "EURUSD", timeframe: Union[str, int] = None, 
                   k_period: int = 14, d_period: int = 3, slowing: int = 3, 
                   price_field: str = 'high/low', levels: tuple = (30, 70),
                   rate_fetcher=None) -> Optional[dict]:
    """
    Calculate Stochastic Oscillator using MT5's exact method with cached rates.
    
    Args:
        symbol: Trading symbol (default: EURUSD)
        timeframe: Timeframe string (e.g. 'M5') or integer in minutes
        k_period: %K period (default: 14)
        d_period: %D period (default: 3)
        slowing: Slowing period (default: 3)
        price_field: Price field to use ('high/low' or 'close/close')
        levels: Overbought/oversold levels (default: (30, 70))
        rate_fetcher: RateFetcher instance for cached rates
    
    Returns:
        dict: Dictionary containing %K, %D, and levels
    """
    if rate_fetcher is None:
        logger.error("No rate_fetcher provided to get_stochastic")
        return None
        
    try:
        # Fetch rates using cache
        rates = rate_fetcher.get_rates(symbol, str(timeframe))
        if rates is None:
            logger.error(f"No cached rates available for {symbol} {timeframe}")
            return None
            
        # Verify sufficient data
        if len(rates) < 200:
            logger.warning(f"Insufficient rates for {symbol} (got {len(rates)}, need 200)")
            return None
            
        # Existing calculation logic remains unchanged below
        high = rates['high'].values
        low = rates['low'].values
        close = rates['close'].values

        length = len(rates)
        highest_high = np.zeros(length)
        lowest_low = np.zeros(length)
        main_k = np.zeros(length)
        signal_d = np.zeros(length)

        for i in range(k_period-1, length):
            if price_field == 'high/low':
                highest_high[i] = max(high[i-k_period+1:i+1])
                lowest_low[i] = min(low[i-k_period+1:i+1])
            else:  # 'close/close'
                highest_high[i] = max(close[i-k_period+1:i+1])
                lowest_low[i] = min(close[i-k_period+1:i+1])

        # Handle cases where all prices are equal
        if np.all(highest_high == lowest_low):
            logger.warning(f"All prices equal for {symbol} {timeframe} - cannot calculate stochastic")
            return None

        for i in range(k_period-1, length):
            sum_low = 0.0
            sum_high = 0.0
            
            for j in range(i-k_period+1, i+1):
                sum_low += (close[j] - lowest_low[j])
                sum_high += (highest_high[j] - lowest_low[j])
            
            if sum_high == 0:
                # Use previous valid value if available, otherwise skip
                if i > 0 and main_k[i-1] not in [0.0, 100.0]:
                    main_k[i] = main_k[i-1]
                else:
                    main_k[i] = 50.0  # Neutral value
                logger.debug(f"Stochastic calculation for {symbol} {timeframe} at index {i} had sum_high=0 - using fallback value")
            else:
                main_k[i] = (sum_low / sum_high) * 100.0

        for i in range(k_period-1+slowing-1, length):
            sum_k = 0.0
            for j in range(i-slowing+1, i+1):
                sum_k += main_k[j]
            signal_d[i] = sum_k / slowing

        for i in range(k_period-1+slowing-1+d_period-1, length):
            sum_k = 0.0
            for j in range(i-d_period+1, i+1):
                sum_k += signal_d[j]
            signal_d[i] = sum_k / d_period

        k_series = pd.Series(main_k, index=rates.index)
        d_series = pd.Series(signal_d, index=rates.index)

        return {
            'k': k_series,
            'd': d_series,
            'upper_level': levels[1],
            'lower_level': levels[0]
        }
        
    except Exception as e:
        logger.error(f"Error calculating stochastic for {symbol}: {str(e)}")
        return None
