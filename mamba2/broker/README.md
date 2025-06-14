# Broker Module

This module provides a unified interface for interacting with different trading brokers. It defines a common `Broker` abstract base class that all broker implementations must follow.

## Available Brokers

### 1. `MT5Broker`
A concrete implementation for MetaTrader 5. This requires the `MetaTrader5` Python package and a running MT5 terminal.

**Example Usage:**
```python
from mamba2.broker import MT5Broker

# Initialize the broker
broker = MT5Broker()

# Connect to MT5
if broker.initialize():
    try:
        # Get account info
        account = broker.account_info()
        print(f"Account: {account['login']} Balance: {account['balance']}")
        
        # Get market data
        if broker.symbol_select("EURUSD"):
            bars = broker.copy_rates_from_pos("EURUSD", 1, 0, 10)  # Last 10 M1 bars
            print(f"Got {len(bars)} bars of EURUSD data")
            
        # Get open positions
        positions = broker.positions_get()
        print(f"Open positions: {len(positions)}")
        
    finally:
        # Always shutdown when done
        broker.shutdown()
```

### 2. `MT5Mock`
A mock implementation for testing purposes. This simulates a trading environment without requiring a live connection.

**Example Usage:**
```python
from mamba2.broker import MT5Mock

# Initialize the mock broker
broker = MT5Mock()
broker.initialize()

try:
    # Test your strategy with the mock broker
    if broker.symbol_select("EURUSD"):
        bars = broker.copy_rates_from_pos("EURUSD", 1, 0, 10)
        print(f"Got {len(bars)} mock bars")
        
    # Place a mock order
    order = {
        "action": 1,  # TRADE_ACTION_DEAL
        "symbol": "EURUSD",
        "volume": 0.1,
        "type": 0,  # ORDER_TYPE_BUY
        "price": 1.1,
        "sl": 1.09,
        "tp": 1.11,
        "deviation": 10,
        "magic": 123456,
        "comment": "test order",
        "type_time": 0,  # ORDER_TIME_GTC
        "type_filling": 2,  # ORDER_FILLING_RETURN
    }
    
    result = broker.order_send(order)
    print(f"Order result: {result}")
    
    # Check open positions
    positions = broker.positions_get()
    print(f"Open positions: {len(positions)}")
    
finally:
    broker.shutdown()
```

## Implementing a Custom Broker

To implement support for a new broker, create a class that inherits from `Broker` and implement all abstract methods. See `mt5_broker.py` and `mt5_mock.py` for reference implementations.

## Running Tests

Unit tests are in `tests/test_broker.py` and can be run with:
```bash
pytest tests/test_broker.py -v
```

Integration tests (requires MT5) are in `tests/integration/test_mt5_broker.py` and can be run with:
```bash
pytest tests/integration/test_mt5_broker.py -v
```

## Dependencies

- For `MT5Broker`: `MetaTrader5` package and a running MT5 terminal
- For testing: `pytest`
- For type checking: Python 3.7+ with `typing` module
