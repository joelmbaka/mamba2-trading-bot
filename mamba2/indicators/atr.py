import pandas as pd
import MetaTrader5 as mt5
import logging

def get_atr(symbol="EURUSD", timeframe=mt5.TIMEFRAME_M5, atr_period=14):
    """
    Calculate Average True Range (ATR) for a symbol
    
    Args:
        symbol: Trading symbol (default: EURUSD)
        timeframe: MT5 timeframe (default: M5)
        atr_period: ATR calculation period (default: 14)
        
    Returns:
        Current ATR value or None if error occurs
    """
    try:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, atr_period+1)
        if rates is None:
            logging.error(f"Failed to get rates for {symbol}: {mt5.last_error()}")
            return None
            
        if len(rates) < atr_period+1:
            logging.error(f"Insufficient rates for {symbol} (got {len(rates)}, need {atr_period+1})")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Calculate True Range
        df['prev_close'] = df['close'].shift(1)
        df['high-low'] = df['high'] - df['low']
        df['high-prev_close'] = abs(df['high'] - df['prev_close'])
        df['low-prev_close'] = abs(df['low'] - df['prev_close'])
        df['tr'] = df[['high-low', 'high-prev_close', 'low-prev_close']].max(axis=1)
        
        # Calculate ATR
        atr = df['tr'].rolling(atr_period).mean().iloc[-1]
        return atr
        
    except Exception as e:
        logging.error(f"Error calculating ATR for {symbol}: {str(e)}")
        return None
