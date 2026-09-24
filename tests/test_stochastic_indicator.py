"""Tests for the stochastic indicator calculation."""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from mamba2.indicators.stochastic import get_stochastic
from mamba2.crew.rates import RatesFetcher

class TestStochasticIndicator:
    """Test suite for stochastic indicator calculations."""

    @pytest.fixture
    def mock_rate_fetcher(self):
        """Create a mock rate fetcher with controlled test data."""
        # Create sample rate data with enough points for calculations
        np.random.seed(42)  # For reproducible results
        n_points = 200
        base = 170.0
        
        # Create trending data with known pattern to get expected stochastic values
        time_index = pd.date_range(end=pd.Timestamp.now(), periods=n_points, freq='15min')
        
        # Create a sine wave pattern with adjusted amplitude and frequency for 15min timeframe
        x = np.linspace(0, 15*np.pi, n_points)  # Adjusted frequency for 15min
        close = base + 7 * np.sin(x) + np.random.normal(0, 0.3, n_points)  # Adjusted amplitude and noise
        
        # Ensure high/low have proper spread around close
        high = close + 0.1 + np.random.random(n_points) * 0.5
        low = close - 0.1 - np.random.random(n_points) * 0.5
        
        # Create DataFrame with required columns
        rates = pd.DataFrame({
            'time': time_index,
            'open': close - 0.1 + np.random.random(n_points) * 0.2,
            'high': high,
            'low': low,
            'close': close,
            'tick_volume': np.random.randint(100, 1000, n_points),
            'spread': np.zeros(n_points),
            'real_volume': np.random.randint(100, 1000, n_points)
        }).set_index('time')
        
        # Create mock rate fetcher
        mock_fetcher = MagicMock(spec=RatesFetcher)
        mock_fetcher.get_rates.return_value = rates
        return mock_fetcher

    def test_stochastic_calculation(self, mock_rate_fetcher):
        """Test stochastic calculation with controlled data."""
        # Call the function with test data
        result = get_stochastic(
            symbol="EURJPY",
            timeframe="M15",
            k_period=14,
            d_period=3,
            slowing=3,
            rate_fetcher=mock_rate_fetcher
        )
        
        # Verify results
        assert result is not None, "Stochastic calculation returned None"
        assert 'k' in result, "Result missing 'k' (stochastic %K)"
        assert 'd' in result, "Result missing 'd' (stochastic %D)"
        
        assert set(result) >= {'k', 'd', 'closes'}
        assert len(result['k']) == len(result['d']) == len(result['closes'])
        assert np.isfinite(result['k'].iloc[-1])
        assert np.isfinite(result['d'].iloc[-1])
        assert 0 <= result['k'].iloc[-1] <= 100
        assert 0 <= result['d'].iloc[-1] <= 100

    def test_insufficient_data(self, mock_rate_fetcher):
        """Test behavior with insufficient data."""
        # Configure mock to return too little data
        mock_rate_fetcher.get_rates.return_value = mock_rate_fetcher.get_rates.return_value.iloc[:10]
        
        result = get_stochastic(
            symbol="EURJPY",
            timeframe="M5",
            rate_fetcher=mock_rate_fetcher
        )
        
        assert result is None, "Should return None for insufficient data"

    def test_all_prices_equal(self, mock_rate_fetcher):
        """Test behavior when all prices are equal."""
        # Get the rates and modify them to have all equal prices
        rates = mock_rate_fetcher.get_rates.return_value
        rates['high'] = 170.0
        rates['low'] = 170.0
        rates['close'] = 170.0
        
        result = get_stochastic(
            symbol="EURJPY",
            timeframe="M5",
            rate_fetcher=mock_rate_fetcher
        )
        
        assert result is None, "Should return None when all prices are equal"

    def test_custom_parameters(self, mock_rate_fetcher):
        """Test with custom parameters."""
        result = get_stochastic(
            symbol="EURJPY",
            timeframe="M5",
            k_period=5,
            d_period=5,
            slowing=5,
            lookback_period=7,
            rate_fetcher=mock_rate_fetcher
        )
        
        assert result is not None
        assert set(result) >= {'k', 'd', 'closes'}
        assert len(result['k']) == len(result['d']) == len(result['closes'])
        assert len(result['k']) == 7
        assert np.isfinite(result['k'].iloc[-1])
        assert np.isfinite(result['d'].iloc[-1])
