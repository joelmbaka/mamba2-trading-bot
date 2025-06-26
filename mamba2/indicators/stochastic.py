import numpy as np
import pandas as pd
from mamba2.crew.logger import logger
from typing import Union, Optional

def get_stochastic(symbol: str = "EURUSD", timeframe: Union[str, int] = None, 
                   k_period: int = 21, d_period: int = 7, slowing: int = 7, 
                   price_field: str = 'high/low',
                   rate_fetcher=None, lookback_period: int = 0) -> Optional[dict]:
    if rate_fetcher is None:
        logger.error("No rate_fetcher provided to get_stochastic")
        return None
        
    try:
        rates = rate_fetcher.get_rates(symbol, str(timeframe))
        if rates is None:
            logger.error(f"No cached rates available for {symbol} {timeframe}")
            return None
            
        if len(rates) < k_period + d_period + slowing:
            logger.warning(f"Insufficient rates for {symbol} (got {len(rates)}, need {k_period + d_period + slowing})")
            return None
            
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
            else:
                highest_high[i] = max(close[i-k_period+1:i+1])
                lowest_low[i] = min(close[i-k_period+1:i+1])

        if np.all(highest_high == lowest_low):
            logger.warning(f"All prices equal for {symbol} {timeframe} - cannot calculate stochastic")
            return None

        for i in range(k_period-1+slowing-1, length):
            sum_low = 0.0
            sum_high = 0.0
            
            for j in range(i-slowing+1, i+1):
                sum_low += (close[j] - lowest_low[j])
                sum_high += (highest_high[j] - lowest_low[j])
            
            if sum_high == 0.0:
                main_k[i] = 100.0
            else:
                main_k[i] = (sum_low / sum_high) * 100
        
        # Calculate signal line (D)
        for i in range(d_period-1, length):
            if i >= k_period-1+slowing-1:
                signal_d[i] = np.mean(main_k[i-d_period+1:i+1])
        
        # Convert to pandas Series
        k_series = pd.Series(main_k, index=rates.index)
        d_series = pd.Series(signal_d, index=rates.index)
        closes_series = rates['close']
        
        # Apply lookback period if specified
        if lookback_period > 0:
            k_series = k_series.iloc[-lookback_period:]
            d_series = d_series.iloc[-lookback_period:]
            closes_series = closes_series.iloc[-lookback_period:]
        
        return {
            'k': k_series,
            'd': d_series,
            'closes': closes_series
        }
        
    except Exception as e:
        logger.error(f"Error calculating stochastic for {symbol} {timeframe}: {str(e)}", exc_info=True)
        return None
