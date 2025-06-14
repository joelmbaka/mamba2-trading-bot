"""Tests for the ATR Manager module."""
import pytest
from unittest.mock import MagicMock, patch, Mock, AsyncMock
import pandas as pd
import numpy as np
import asyncio
import threading

from mamba2.crew.atr_manager import ATRManager
from mamba2.crew.rates import RateFetcher

class TestATRManager:
    """Test suite for ATRManager class."""
    
    @pytest.fixture
    def mock_rate_fetcher(self):
        """Create a mock rate fetcher."""
        fetcher = Mock(spec=RateFetcher)
        fetcher.get_rates.return_value = pd.DataFrame({
            'open': [1.1, 1.11, 1.12, 1.13, 1.14],
            'high': [1.12, 1.115, 1.125, 1.135, 1.145],
            'low': [1.09, 1.095, 1.105, 1.115, 1.125],
            'close': [1.105, 1.11, 1.115, 1.125, 1.135]
        })
        return fetcher
    
    @pytest.fixture
    def atr_manager(self, mock_rate_fetcher):
        """Create an ATRManager instance for testing."""
        manager = ATRManager()
        manager.rate_fetcher = mock_rate_fetcher
        return manager
    
    def test_initialization(self, atr_manager):
        """Test ATRManager initialization."""
        assert atr_manager is not None
        assert atr_manager.running is False
        assert atr_manager.thread is None
        assert isinstance(atr_manager._stop_event, threading.Event)
    
    @patch('mamba2.indicators.atr.get_atr')
    def test_get_atr(self, mock_get_atr, atr_manager):
        """Test getting ATR values through public interface."""
        # Setup mock
        mock_get_atr.return_value = 0.01
        
        # Test getting ATR - should return None initially
        symbol = "EURUSD"
        timeframe = "M15"
        
        # Initially should return None
        atr_value = atr_manager.get_atr(symbol, timeframe)
        assert atr_value is None
        
        # Populate cache manually
        atr_manager.atr_values = {"EURUSD": {"M15": 0.01}}
        
        # Now should return cached value
        atr_value = atr_manager.get_atr(symbol, timeframe)
        assert atr_value == 0.01
    
    def test_run_loop_behavior(self, atr_manager):
        """Test the main run loop behavior."""
        # Setup
        atr_manager.running = True
        atr_manager._stop_event.is_set = lambda: False
        
        # Mock the periodic operations
        with patch.object(atr_manager, 'get_atr') as mock_get_atr:
            # Run test
            atr_manager._run_loop()
            
            # Verify periodic operations were called
            mock_get_atr.assert_called()
    
    @patch('asyncio.sleep')
    @patch('mamba2.crew.atr_manager.ATRManager._update_atr_values')
    def test_run_loop(self, mock_update, mock_sleep, atr_manager):
        """Test the main run loop."""
        # Setup
        atr_manager.running = True
        atr_manager._stop_event.is_set = lambda: False
        
        # Run test
        atr_manager._run_loop()
        
        # Verify
        mock_update.assert_called()
        mock_sleep.assert_called()
    
    @patch('mamba2.crew.atr_manager.ATRManager._run_loop')
    def test_start_stop(self, mock_run_loop, atr_manager):
        """Test starting and stopping the manager."""
        # Test start
        asyncio.run(atr_manager.start())
        assert atr_manager.running is True
        assert atr_manager.thread is not None
        
        # Test stop
        asyncio.run(atr_manager.stop())
        assert atr_manager.running is False
        assert atr_manager._stop_event.is_set()
        
        # Verify thread was started
        mock_run_loop.assert_called_once()

@pytest.fixture
def mock_rate_fetcher():
    fetcher = Mock(spec=RateFetcher)
    fetcher.is_ready.return_value = True
    return fetcher

@pytest.fixture
def mock_cache():
    return Mock()

@pytest.fixture
def atr_manager(mock_rate_fetcher, mock_cache):
    manager = ATRManager(rate_fetcher=mock_rate_fetcher, cache=mock_cache)
    manager._stop_event = Mock()
    manager._stop_event.is_set.return_value = False
    manager.loop = asyncio.new_event_loop()
    return manager

@pytest.mark.asyncio
async def test_atr_manager_initialization(atr_manager):
    assert atr_manager is not None
    assert atr_manager.rate_fetcher is not None
    assert atr_manager.cache is not None

@pytest.mark.asyncio
async def test_run_loop_with_retries(atr_manager, mock_rate_fetcher):
    # Setup mock with initial failure then success
    mock_rate_fetcher.get_rates.side_effect = [
        None,  # First attempt fails
        None,  # Second attempt fails
        Mock(rates=Mock())  # Third attempt succeeds
    ]
    
    await atr_manager._run_loop()
    
    # Verify retry behavior
    assert mock_rate_fetcher.get_rates.call_count == 3
    
@pytest.mark.asyncio
async def test_run_loop_with_max_retries(atr_manager, mock_rate_fetcher):
    # Setup mock to always return None
    mock_rate_fetcher.get_rates.return_value = None
    
    await atr_manager._run_loop()
    
    # Verify max retries (5) was respected
    assert mock_rate_fetcher.get_rates.call_count == 5
    
@pytest.mark.asyncio
async def test_run_loop_with_stop_event(atr_manager, mock_rate_fetcher):
    # Setup stop event to trigger after first attempt
    atr_manager._stop_event.is_set.side_effect = [False, True]
    
    await atr_manager._run_loop()
    
    # Should exit early due to stop event
    assert mock_rate_fetcher.get_rates.call_count == 1

@pytest.mark.asyncio
async def test_run_loop_with_exception(atr_manager, mock_rate_fetcher):
    # Setup mock to raise exception first, then succeed
    mock_rate_fetcher.get_rates.side_effect = [
        Exception("Test error"),
        Mock(rates=Mock())
    ]
    
    await atr_manager._run_loop()
    
    # Should retry after exception
    assert mock_rate_fetcher.get_rates.call_count == 2

@pytest.mark.asyncio
async def test_get_atr_value(atr_manager):
    # Setup test data
    test_atr = 0.005
    atr_manager.atr_values = {"EURUSD": {"M1": test_atr}}
    
    # Verify value retrieval
    result = atr_manager.get_atr("EURUSD", "M1")
    assert result == test_atr
    
    # Verify None for missing values
    assert atr_manager.get_atr("EURUSD", "M5") is None
    assert atr_manager.get_atr("USDJPY", "M1") is None
