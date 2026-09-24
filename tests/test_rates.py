"""Tests for the rates module."""
import time
import threading
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from mamba2.crew.rates import RatesFetcher, RateData
from mamba2.broker.mt5_mock import MT5Mock
import config

class TestRatesFetcher:
    """Test suite for RatesFetcher class."""
    
    @pytest.fixture
    def mock_broker(self):
        """Create a mock broker instance."""
        broker = MT5Mock()
        broker.initialize()
        return broker
    
    @pytest.fixture
    def rate_fetcher(self, mock_broker):
        """Create a RatesFetcher instance for testing."""
        fetcher = RatesFetcher(broker=mock_broker)
        fetcher.update_interval = 0.1
        return fetcher
    
    def test_initialization(self, rate_fetcher):
        """Test RatesFetcher initialization."""
        assert rate_fetcher is not None
        assert not rate_fetcher._stop_event.is_set()
        assert rate_fetcher.update_interval == 0.1
        assert len(rate_fetcher.rates_cache) == 0
    
    def test_stop(self, rate_fetcher):
        """Test stopping the rates fetcher."""
        rate_fetcher.stop()
        assert rate_fetcher._stop_event.is_set()
    
    def test_get_rates_empty_cache(self, rate_fetcher):
        """Test getting rates when cache is empty."""
        rates = rate_fetcher.get_rates('EURUSD', 'M1')
        assert rates is None
    
    def test_fetch_rates_success(self, rate_fetcher, mock_broker):
        """Test successful rate fetching."""
        # Mock the broker's copy_rates_from_pos to return test data
        test_data = np.array([
            (int(time.time()), 1.1, 1.2, 1.09, 1.15, 100, 10, 1000),
            (int(time.time())-60, 1.09, 1.11, 1.08, 1.1, 90, 10, 900),
        ], dtype=[
            ('time', 'i8'), ('open', 'f8'), ('high', 'f8'), 
            ('low', 'f8'), ('close', 'f8'), ('tick_volume', 'i8'),
            ('spread', 'i8'), ('real_volume', 'i8')
        ])
        
        mock_broker.copy_rates_from_pos = MagicMock(return_value=test_data)
        
        # Test fetching rates
        rates = rate_fetcher._fetch_rates('EURUSD', 'M1')
        
        # Verify results
        assert rates is not None
        assert isinstance(rates, pd.DataFrame)
        assert len(rates) == 2
        assert 'open' in rates.columns
        assert 'high' in rates.columns
        assert 'low' in rates.columns
        assert 'close' in rates.columns
        assert isinstance(rates.index, pd.DatetimeIndex)
    
    @pytest.mark.asyncio
    async def test_update_rates(self, rate_fetcher, mock_broker):
        """Test updating rates for a symbol and timeframe."""
        # Mock the _fetch_rates method to return test data
        test_data = pd.DataFrame({
            'open': [1.1, 1.11],
            'high': [1.12, 1.115],
            'low': [1.09, 1.105],
            'close': [1.105, 1.11]
        }, index=pd.to_datetime([int(time.time())*1e9, (int(time.time())-60)*1e9]))
        
        rate_fetcher._fetch_rates = MagicMock(return_value=test_data)
        
        # Update rates
        await rate_fetcher._update_rates('EURUSD', 'M1')
        
        # Verify cache was updated
        cache_key = 'EURUSD_M1'
        assert cache_key in rate_fetcher.rates_cache
        cached_data = rate_fetcher.rates_cache[cache_key]
        assert isinstance(cached_data, RateData)
        assert cached_data.symbol == 'EURUSD'
        assert cached_data.timeframe == 'M1'
        assert len(cached_data.rates) == 2
    
    def test_is_ready(self, rate_fetcher, mock_broker):
        """Test the is_ready method."""
        # Initially should not be ready
        assert not rate_fetcher.is_ready()
        
        symbols = list(config.symbols)
        timeframes = dict(config.timeframes)
        expected_combinations = len(symbols) * len(timeframes)
        
        # Create test data with all required columns
        num_bars = 200  # Current RatesFetcher readiness threshold
        timestamps = [int(time.time() - i*60) for i in range(num_bars)]
        
        # Create test data in the expected format
        test_data = {
            'time': timestamps,
            'open': [1.1 + i*0.001 for i in range(num_bars)],
            'high': [1.12 + i*0.001 for i in range(num_bars)],
            'low': [1.09 + i*0.001 for i in range(num_bars)],
            'close': [1.105 + i*0.001 for i in range(num_bars)],
            'tick_volume': [100] * num_bars,
            'spread': [10] * num_bars,
            'real_volume': [1000] * num_bars
        }
        
        # Create DataFrame and set index
        df = pd.DataFrame(test_data)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        # Clear any existing cache
        rate_fetcher.rates_cache = {}
        
        # Add test data for all required symbols and timeframes
        for symbol in symbols:
            for tf in timeframes.keys():
                cache_key = f"{symbol}_{tf}"
                rate_fetcher.rates_cache[cache_key] = RateData(
                    symbol=symbol,
                    timeframe=tf,
                    rates=df.copy(),  # Make a copy for each symbol/timeframe
                    last_updated=time.time()
                )
        
        # Mark initial fetch as complete
        rate_fetcher._initial_fetch_complete = True
        
        assert rate_fetcher.is_ready()
    
    def test_run_stop_behavior(self, rate_fetcher, mock_broker):
        """Test the run method and stop behavior."""
        first_update = threading.Event()

        async def update_once():
            first_update.set()

        with patch("mamba2.crew.rates.time.sleep"):
            with patch.object(rate_fetcher, "_update_all_rates", side_effect=update_once):
                rate_fetcher.start()
                assert first_update.wait(timeout=2)
                rate_fetcher.stop()

        assert not rate_fetcher.is_alive()
        assert rate_fetcher.rates_cache == {}
