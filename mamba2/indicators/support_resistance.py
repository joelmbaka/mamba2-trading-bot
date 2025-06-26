import pandas as pd
from typing import Any, Union, Optional
from mamba2.crew.logger import logger

def draw_support_resistance(symbol: str, timeframe: Union[str, int] = None, method: str = 'classic', lookback_period: int = 0, rate_fetcher: Optional[Any] = None) -> Optional[pd.DataFrame]:
    if rate_fetcher is None:
        logger.error("No rate_fetcher provided to draw_support_resistance")
        return None
        
    rates = rate_fetcher.get_rates(symbol, str(timeframe))
    if rates is None or rates.empty:
        logger.error(f"No cached rates available for {symbol} {timeframe}")
        return None
        
    # If lookback_period is set, take the last N rows
    if lookback_period > 0:
        rates = rates.iloc[-lookback_period:]
        
    data = rates
    
    # Calculate pivot points
    if method == 'classic':
        pp = (data['high'] + data['low'] + data['close']) / 3
        r1 = 2 * pp - data['low']
        s1 = 2 * pp - data['high']
        r2 = pp + (data['high'] - data['low'])
        s2 = pp - (data['high'] - data['low'])
        r3 = pp + 2 * (data['high'] - data['low'])
        s3 = pp - 2 * (data['high'] - data['low'])
    elif method == 'fibonacci':
        pp = (data['high'] + data['low'] + data['close']) / 3
        r1 = pp + 0.382 * (data['high'] - data['low'])
        s1 = pp - 0.382 * (data['high'] - data['low'])
        r2 = pp + 0.618 * (data['high'] - data['low'])
        s2 = pp - 0.618 * (data['high'] - data['low'])
        r3 = pp + (data['high'] - data['low'])
        s3 = pp - (data['high'] - data['low'])
    elif method == 'camarilla':
        pp = (data['high'] + data['low'] + data['close']) / 3
        r1 = data['close'] + 1.1/12 * (data['high'] - data['low'])
        s1 = data['close'] - 1.1/12 * (data['high'] - data['low'])
        r2 = data['close'] + 1.6/12 * (data['high'] - data['low'])
        s2 = data['close'] - 1.6/12 * (data['high'] - data['low'])
        r3 = data['close'] + 2.2/12 * (data['high'] - data['low'])
        s3 = data['close'] - 2.2/12 * (data['high'] - data['low'])
        r4 = data['close'] + 3.7/12 * (data['high'] - data['low'])
        s4 = data['close'] - 3.7/12 * (data['high'] - data['low'])
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Create levels DataFrame
    levels = pd.DataFrame({
        'PP': pp,
        'R1': r1,
        'S1': s1,
        'R2': r2,
        'S2': s2,
        'R3': r3,
        'S3': s3
    })
    
    if method == 'camarilla':
        levels['R4'] = r4
        levels['S4'] = s4
        
    return levels