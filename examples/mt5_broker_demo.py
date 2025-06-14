"""
MT5Broker Demo

This script demonstrates how to use the MT5Broker class to interact with a MetaTrader 5 terminal.

Prerequisites:
- MetaTrader 5 installed
- Python package: MetaTrader5 (pip install MetaTrader5)
- A demo account configured in MT5
"""
import time
from mamba2.broker import MT5Broker

def main():
    # Initialize the broker with your credentials
    print("Initializing MT5 broker...")
    broker = MT5Broker(
        login=93117167,
        password="B*8hZaYl",
        server="MetaQuotes-Demo"
    )
    
    try:
        # Connect to MT5
        if not broker.initialize():
            print("Failed to initialize MT5 connection")
            return
        
        print("\n=== Account Information ===")
        account = broker.account_info()
        print(f"Account: {account.get('login')}")
        print(f"Balance: {account.get('balance')} {account.get('currency')}")
        print(f"Equity: {account.get('equity')} {account.get('currency')}")
        print(f"Server: {account.get('server')}")
        
        # Select a symbol
        symbol = "EURUSD"
        print(f"\n=== Market Data for {symbol} ===")
        if not broker.symbol_select(symbol):
            print(f"Failed to select {symbol}")
            return
        
        # Get historical data
        print("\nFetching historical data...")
        bars = broker.copy_rates_from_pos(symbol, 1, 0, 5)  # M1 timeframe, last 5 bars
        
        print("\nLast 5 M1 bars:")
        for i, bar in enumerate(bars):
            print(f"Bar {i+1}: Time={bar['time']}, O={bar['open']}, H={bar['high']}, L={bar['low']}, C={bar['close']}")
        
        # Show open positions
        print("\n=== Open Positions ===")
        positions = broker.positions_get()
        print(f"Open positions: {len(positions)}")
        for pos in positions:
            print(f"  {pos['symbol']} {pos['type']} {pos['volume']} lots @ {pos['price_open']}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Always shutdown the connection when done
        print("\nShutting down MT5 connection...")
        broker.shutdown()

if __name__ == "__main__":
    main()
