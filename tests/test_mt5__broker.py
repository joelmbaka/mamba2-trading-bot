"""Tests for the broker interface and implementations."""
import pytest
import time
from mamba2.broker import Broker, MT5Mock, mt5

def test_broker_interface():
    """Test that MT5Mock implements the Broker interface."""
    # This will raise TypeError if any abstract methods are not implemented
    broker = MT5Mock()
    assert isinstance(broker, Broker)

def test_connection():
    """Test broker connection lifecycle."""
    broker = MT5Mock()
    assert not broker.connected
    
    # Test initialization
    assert broker.initialize() is True
    assert broker.connected is True
    
    # Test shutdown
    broker.shutdown()
    assert broker.connected is False

def test_market_data():
    """Test market data retrieval."""
    broker = MT5Mock()
    broker.initialize()
    
    # Test symbol selection
    assert broker.symbol_select("EURUSD") is True
    
    # Test getting historical data
    bars = broker.copy_rates_from_pos("EURUSD", 1, 0, 10)
    assert len(bars) == 10
    assert "open" in bars[0]
    assert "high" in bars[0]
    assert "low" in bars[0]
    assert "close" in bars[0]
    assert "time" in bars[0]

def test_account_info():
    """Test account information retrieval."""
    broker = MT5Mock()
    account = broker.account_info()
    
    assert "balance" in account
    assert "equity" in account
    assert "margin" in account
    assert "free_margin" in account
    assert "leverage" in account
    assert "currency" in account

def test_order_management():
    """Test order placement and position management."""
    broker = MT5Mock()
    broker.initialize()
    
    # Check initial state
    assert broker.positions_total() == 0
    
    # Place a buy order
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
    
    # Check order validity
    check_result = broker.order_check(order)
    assert check_result["retcode"] == 0
    
    # Send the order
    result = broker.order_send(order)
    assert result["retcode"] == 0
    assert result["order"] > 0
    
    # Verify position was created
    assert broker.positions_total() == 1
    
    # Get position by ticket
    position = broker.position_get_ticket(1)
    assert position is not None
    assert position["symbol"] == "EURUSD"
    assert position["volume"] == 0.1
    
    # Close position
    assert broker.position_close(1) is True
    assert broker.positions_total() == 0

def test_copy_rates_from_range():
    """Test getting historical data between timestamps."""
    broker = MT5Mock()
    broker.initialize()
    
    # Get current timestamp
    now = int(time.time())
    
    # Test getting data for last hour
    bars = broker.copy_rates_from_range(
        symbol="EURUSD",
        timeframe=1,  # M1
        date_from=now - 3600,
        date_to=now
    )
    
    # Should get approximately 60 bars (1 per minute)
    assert 50 <= len(bars) <= 70
    
    # Verify bar structure
    bar = bars[0]
    assert "open" in bar
    assert "high" in bar
    assert "low" in bar
    assert "close" in bar
    assert "time" in bar
    assert "tick_volume" in bar
    
    # Verify time sequence
    for i in range(1, len(bars)):
        assert bars[i]["time"] == bars[i-1]["time"] + 60

def test_global_instance():
    """Test the global MT5 mock instance."""
    assert mt5.initialize() is True
    assert mt5.connected is True
    
    # Test a simple operation
    assert mt5.symbol_select("EURUSD") is True
    
    mt5.shutdown()
    assert mt5.connected is False
