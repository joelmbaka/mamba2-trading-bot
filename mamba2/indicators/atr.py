from mamba2.crew.logger import logger
from typing import List

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
        # Get cached rates and work on a copy to avoid mutating shared cache
        rates = rate_fetcher.get_rates(symbol, str(timeframe))
        if rates is not None:
            rates = rates.copy()
        if rates is None:
            logger.error(f"No cached rates available for {symbol} {timeframe}")
            return None
            
        if len(rates) < atr_period+1:
            logger.warning(f"Insufficient rates for {symbol} (got {len(rates)}, need {atr_period+1})")
            return 0.0
                
        # Calculate True Range
        rates['prev_close'] = rates['close'].shift(1)
        rates['high-low'] = rates['high'] - rates['low']
        rates['high-prev_close'] = abs(rates['high'] - rates['prev_close'])
        rates['low-prev_close'] = abs(rates['low'] - rates['prev_close'])
        rates['tr'] = rates[['high-low', 'high-prev_close', 'low-prev_close']].max(axis=1)
        
        # Calculate ATR
        atr = rates['tr'].rolling(atr_period).mean().iloc[-1]
        return atr
        
    except Exception as e:
        logger.error(f"Error calculating ATR for {symbol}: {str(e)}")
        return None
