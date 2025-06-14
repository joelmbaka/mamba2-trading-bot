import numpy as np
import pandas as pd

def get_stochastic(rates, k_period=14, d_period=3, slowing=3, price_field='high/low', levels=(30, 70)):
    """
    Calculate Stochastic Oscillator using MT5's exact method.
    
    Args:
        rates (pandas.DataFrame): DataFrame containing OHLC price data with at least 200 candles
        k_period (int): %K period (default: 14)
        d_period (int): %D period (default: 3)
        slowing (int): Slowing period (default: 3)
        price_field (str): Price field to use, either 'high/low' or 'close/close' (default: 'high/low')
        levels (tuple): Overbought/oversold levels (default: (30, 70))
        
    Returns:
        dict: Dictionary containing %K, %D, and levels
            {
                'k': pandas.Series of %K values,
                'd': pandas.Series of %D values,
                'upper_level': float,
                'lower_level': float
            }
    """
    # Verify we have enough data (200 candles minimum as per note)
    if len(rates) < 200:
        raise ValueError("At least 200 candles of data are required for accurate Stochastic calculation")
    
    # Make copies of the required price data
    high = rates['high'].values
    low = rates['low'].values
    close = rates['close'].values
    
    # Initialize arrays for calculations
    length = len(rates)
    highest_high = np.zeros(length)
    lowest_low = np.zeros(length)
    main_k = np.zeros(length)
    signal_d = np.zeros(length)
    
    # Calculate highest_high and lowest_low (exactly as in MT5)
    for i in range(k_period-1, length):
        if price_field == 'high/low':
            highest_high[i] = max(high[i-k_period+1:i+1])
            lowest_low[i] = min(low[i-k_period+1:i+1])
        else:  # 'close/close'
            highest_high[i] = max(close[i-k_period+1:i+1])
            lowest_low[i] = min(close[i-k_period+1:i+1])
    
    # Calculate %K using MT5's approach (sum numerator and denominator separately)
    for i in range(k_period-1+slowing-1, length):
        sum_low = 0.0
        sum_high = 0.0
        
        # Sum over the slowing period
        for j in range(i-slowing+1, i+1):
            sum_low += (close[j] - lowest_low[j])
            sum_high += (highest_high[j] - lowest_low[j])
        
        # Divide to get %K, handle division by zero as MT5 does
        if sum_high == 0.0:
            main_k[i] = 100.0
        else:
            main_k[i] = (sum_low / sum_high) * 100.0
    
    # Calculate %D using simple moving average of %K
    for i in range(k_period-1+slowing-1+d_period-1, length):
        sum_k = 0.0
        for j in range(i-d_period+1, i+1):
            sum_k += main_k[j]
        signal_d[i] = sum_k / d_period
    
    # Convert back to pandas Series with the original index
    k_series = pd.Series(main_k, index=rates.index)
    d_series = pd.Series(signal_d, index=rates.index)
    
    return {
        'k': k_series,
        'd': d_series,
        'upper_level': levels[1],
        'lower_level': levels[0]
    }
