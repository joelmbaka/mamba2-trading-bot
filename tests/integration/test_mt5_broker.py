"""Integration tests for the MT5Broker class.

These tests require a running MetaTrader 5 terminal with a demo account.
They are skipped if MT5 is not available.
"""
import os
import pytest
import time
import MetaTrader5 as mt5
from mamba2.broker import MT5Broker
import time
import datetime

# Skip all tests in this module if MT5 is not available
pytestmark = pytest.mark.skipif(
    not mt5.initialize(),
    reason="MT5 terminal is not available"
)

@pytest.fixture(scope="module")
def mt5_broker():
    """Fixture that provides an initialized MT5Broker instance with demo account."""
    broker = MT5Broker(
        login=93117167,
        password="B*8hZaYl",
        server="MetaQuotes-Demo"
    )
    if not broker.initialize():
        pytest.skip("Could not connect to MT5 terminal with provided credentials")
    
    yield broker
    
    # Cleanup
    broker.shutdown()

def is_forex_market_open():
    """Check if forex markets are likely open based on UTC time."""
    utc_now = datetime.datetime.utcnow()
    weekday = utc_now.weekday()  # Monday=0, Sunday=6
    hour = utc_now.hour
    
    # Forex market closed all day Saturday and Sunday before 5pm ET (21:00 UTC)
    if weekday == 5:  # Saturday
        return False
    if weekday == 6 and hour < 21:  # Sunday before 5pm ET
        return False
        
    # Some brokers have limited Friday closing (5pm ET = 21:00 UTC)
    if weekday == 4 and hour >= 21:  # Friday after 5pm ET
        return False
        
    return True

def test_initialization(mt5_broker):
    """Test that the broker initializes correctly."""
    assert mt5_broker.connected is True
    assert mt5_broker.initialize() is True  # Should be idempotent

def test_account_info(mt5_broker):
    """Test retrieving account information."""
    account = mt5_broker.account_info()
    
    # Check that we got some account info
    assert isinstance(account, dict)
    assert 'balance' in account
    assert 'equity' in account
    assert 'currency' in account
    assert 'server' in account

def test_symbol_selection(mt5_broker):
    """Test selecting market symbols."""
    # Test with a common forex pair
    assert mt5_broker.symbol_select("EURUSD") is True
    
    # Test with a non-existent symbol
    assert mt5_broker.symbol_select("NONEXISTENT") is False

def test_market_data(mt5_broker):
    """Test retrieving market data."""
    if not is_forex_market_open():
        pytest.skip("Forex market is closed (weekend or outside trading hours)")
        
    # First select the symbol
    if not mt5_broker.symbol_select("EURUSD"):
        pytest.skip("EURUSD symbol not available")
    
    # Get some historical data
    bars = mt5_broker.copy_rates_from_pos("EURUSD", 1, 0, 10)  # M1 timeframe, last 10 bars
    
    assert len(bars) == 10
    bar = bars[0]
    assert 'open' in bar
    assert 'high' in bar
    assert 'low' in bar
    assert 'close' in bar
    assert 'time' in bar
    assert 'volume' in bar or 'tick_volume' in bar

def test_position_management(mt5_broker):
    """Test position management functionality."""
    if not is_forex_market_open():
        pytest.skip("Forex market is closed (weekend or outside trading hours)")
        
    # Get initial positions
    initial_positions = mt5_broker.positions_total()
    
    # Get current market price
    symbol = "EURUSD"
    symbol_info = mt5.symbol_info_tick(symbol)
    if symbol_info is None:
        pytest.skip(f"Could not get tick data for {symbol}")
    
    # Place a market order
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": 0.01,  # Minimum lot size
        "type": mt5.ORDER_TYPE_BUY,
        "price": symbol_info.ask,
        "deviation": 10,
        "magic": 123456,
        "comment": "python test order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    
    try:
        # Check the order first
        check = mt5_broker.order_check(request)
        assert check['retcode'] == 0, f"Order check failed: {check}"
        
        # Send the order
        result = mt5_broker.order_send(request)
        assert result['retcode'] == mt5.TRADE_RETCODE_DONE, f"Order send failed: {result}"
        
        # Verify position was opened
        positions = mt5_broker.positions_get(symbol=symbol)
        assert len(positions) > initial_positions, "No new position was opened"
        
        # Get the most recent position
        position = positions[-1]
        
        # Close the position
        close_result = mt5_broker.position_close(position['ticket'])
        assert close_result is True, f"Failed to close position: {position['ticket']}"
        
        # Verify position was closed
        closed_position = mt5_broker.position_get_ticket(position['ticket'])
        assert closed_position is None, "Position was not properly closed"
        
    except Exception as e:
        # Attempt to close any open positions if something goes wrong
        for pos in mt5_broker.positions_get(symbol=symbol):
            if pos['ticket'] != position.get('ticket'):
                mt5_broker.position_close(pos['ticket'])
        raise e

def test_copy_rates_from_range(mt5_broker):
    """Test getting historical data between timestamps."""
    if not is_forex_market_open():
        pytest.skip("Forex market is closed (weekend or outside trading hours)")
        
    # First select the symbol
    if not mt5_broker.symbol_select("EURUSD"):
        pytest.skip("EURUSD symbol not available")
    
    # Use current time when market is open
    now = int(time.time())
    
    # Test getting data for last hour
    bars = mt5_broker.copy_rates_from_range(
        symbol="EURUSD",
        timeframe=1,  # M1
        date_from=now - 3600,
        date_to=now
    )
    
    # Should get some bars (exact count depends on market)
    if len(bars) == 0:
        pytest.skip("No data returned - market may be closed or symbol unavailable")
    
    # Verify bar structure
    bar = bars[0]
    assert "open" in bar
    assert "high" in bar
    assert "low" in bar
    assert "close" in bar
    assert "time" in bar
    assert "tick_volume" in bar
    
    # Verify time sequence is ascending
    for i in range(1, len(bars)):
        assert bars[i]["time"] > bars[i-1]["time"]