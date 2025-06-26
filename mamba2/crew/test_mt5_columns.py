"""
Script to fetch and display the latest 5-minute EURUSD candle data from MT5.
This helps understand the structure and columns returned by MT5's copy_rates_from_pos function.
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def get_mt5_columns():
    """
    Fetch the latest 5-minute EURUSD candle and display its columns and values.
    """
    # Initialize MT5 connection
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return
    
    try:
        # Set the symbol and timeframe
        symbol = "EURUSD"
        timeframe = mt5.TIMEFRAME_M5  # 5-minute timeframe
        
        # Get the latest 1 candle (most recent completed candle)
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
        
        if rates is None or len(rates) == 0:
            print(f"No data returned for {symbol} {timeframe}")
            return
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(rates)
        
        # Convert timestamp to datetime
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Display column information
        print("\n=== MT5 Candle Data Structure ===")
        print(f"Symbol: {symbol}")
        print(f"Timeframe: 5 minutes")
        print(f"Number of candles: {len(df)}")
        
        print("\n=== Column Names and Types ===")
        print(df.dtypes)
        
        print("\n=== Latest Candle Values ===")
        # Print each column and its value
        for column in df.columns:
            print(f"{column}: {df[column].values[0]}")
            
        # Print a sample of the data
        print("\n=== Raw Data Sample ===")
        print(df)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Shutdown MT5 connection
        mt5.shutdown()

if __name__ == "__main__":
    print("Fetching latest 5-minute EURUSD candle from MT5...")
    get_mt5_columns()
