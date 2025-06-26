"""
Detects the market trend (uptrend, downtrend, or range) for the given symbol and timeframe.
"""

import pandas as pd
import numpy as np
from scipy.stats import linregress

def detect_trend(ohlc_data: pd.DataFrame, 
                 timeframe: str, 
                 symbol: str, 
                 lookback_period: int = 24) -> str:
    if len(ohlc_data) < 2:
        return "range"

    closes = ohlc_data['close'].values[-lookback_period:]
    x = np.arange(len(closes))
    slope, _, _, _, _ = linregress(x, closes)
    
    if slope > 0:
        return "uptrend"
    elif slope < 0:
        return "downtrend"
    else:
        return "range"

def calculate_5min_trendline(ohlc_data: pd.DataFrame, lookback_period: int = 30) -> str:
    return detect_trend(ohlc_data, '5m', '', lookback_period)