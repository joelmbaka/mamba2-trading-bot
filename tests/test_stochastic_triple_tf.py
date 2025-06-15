"""Unit tests for StochasticTripleTFStrategy signal detection."""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, AsyncMock
from mamba2.strategy.stochastic_triple_tf import StochasticTripleTFStrategy

class TestStochasticSignalDetection:
    """Test suite for StochasticTripleTFStrategy signal generation."""

    @pytest.fixture
    def strategy(self):
        """Create a strategy instance with mock config."""
        with patch('mamba2.strategy.stochastic_triple_tf.config') as mock_config:
            # Create a simple namespace object for config
            mock_config.green_candle_tolerance_pips = 0.5
            mock_config.stochastic_timeframes = {
                'higher': 'M15',
                'trading': 'M5',
                'entry': 'M1'
            }
            mock_config.stochastic_k_period = 14
            mock_config.ema_period_entry = 7
            
            # Force config module to be reloaded in strategy
            import importlib
            import mamba2.strategy.stochastic_triple_tf
            importlib.reload(mamba2.strategy.stochastic_triple_tf)
            
            strat = mamba2.strategy.stochastic_triple_tf.StochasticTripleTFStrategy(symbol="EURUSD")
        return strat

    @pytest.fixture
    def mock_market(self):
        """Create a minimal mock market object."""
        market = {
            'rate_fetcher': MagicMock(),
            'broker': MagicMock(),
            'position_manager': MagicMock()
        }
        market['broker'].order_send.return_value = {'retcode': 0, 'order': 12345}
        return market

    @pytest.mark.asyncio
    async def test_buy_signal_generation(self, strategy, mock_market):
        """Test proper generation of buy signals."""
        with patch('mamba2.strategy.stochastic_triple_tf.get_stochastic') as mock_stoch, \
             patch('mamba2.strategy.stochastic_triple_tf.get_moving_average') as mock_ma, \
             patch('mamba2.strategy.stochastic_triple_tf.config.green_candle_tolerance_pips', 0.5), \
             patch('mamba2.strategy.stochastic_triple_tf.config.stochastic_timeframes', {'higher': 'M15', 'trading': 'M5', 'entry': 'M1'}), \
             patch('mamba2.strategy.stochastic_triple_tf.config.ema_period_entry', 7):

            # Setup mock data for buy signal
            mock_stoch.return_value = {
                'k': pd.Series([25, 28, 22, 26, 27]),  # K > D in last periods
                'd': pd.Series([30, 29, 28, 25, 20])
            }
            mock_ma.return_value = 1.0990  # EMA value

            # Setup rates with bullish pattern
            rates = pd.DataFrame({
                'open': [1.0990, 1.0995, 1.1000],
                'high': [1.1000, 1.1005, 1.1010],
                'low': [1.0985, 1.0990, 1.0995],
                'close': [1.0995, 1.1000, 1.1005],  # Green candle above EMA
                'volume': [1000] * 3
            })
            mock_market['rate_fetcher'].get_rates.return_value = rates

            await strategy.evaluate(mock_market)
            
            # Verify buy order was sent
            mock_market['broker'].order_send.assert_called_once()
            order = mock_market['broker'].order_send.call_args[0][0]
            assert order['type'] == 0  # BUY order
            assert order['symbol'] == 'EURUSD'

    @pytest.mark.asyncio
    async def test_sell_signal_generation(self, strategy, mock_market):
        """Test proper generation of sell signals."""
        with patch('mamba2.strategy.stochastic_triple_tf.get_stochastic') as mock_stoch, \
             patch('mamba2.strategy.stochastic_triple_tf.get_moving_average') as mock_ma:
            
            # Setup mock data for sell signal
            mock_stoch.return_value = {
                'k': pd.Series([75, 72, 78, 74, 73]),  # K < D in last periods
                'd': pd.Series([60, 65, 70, 72, 75])
            }
            mock_ma.return_value = 1.1010  # EMA value
            
            # Setup rates with bearish pattern
            rates = pd.DataFrame({
                'open': [1.1010, 1.1005, 1.1000],
                'high': [1.1015, 1.1010, 1.1005],
                'low': [1.1005, 1.1000, 1.0995],
                'close': [1.1005, 1.1000, 1.0995],  # Red candle below EMA
                'volume': [1000] * 3
            })
            mock_market['rate_fetcher'].get_rates.return_value = rates

            await strategy.evaluate(mock_market)
            
            # Verify sell order was sent
            mock_market['broker'].order_send.assert_called_once()
            order = mock_market['broker'].order_send.call_args[0][0]
            assert order['type'] == 1  # SELL order
            assert order['symbol'] == 'EURUSD'

    @pytest.mark.asyncio
    async def test_no_signal_when_no_clear_trend(self, strategy, mock_market):
        """Test that no signal is generated when trend is unclear."""
        with patch('mamba2.strategy.stochastic_triple_tf.get_stochastic') as mock_stoch, \
             patch('mamba2.strategy.stochastic_triple_tf.get_moving_average') as mock_ma:
            
            # Setup mock data for no clear trend
            mock_stoch.return_value = {
                'k': pd.Series([50, 55, 45, 60, 40]),
                'd': pd.Series([55, 50, 55, 50, 55])
            }
            mock_ma.return_value = 1.1000
            
            # Setup rates with no clear pattern
            rates = pd.DataFrame({
                'open': [1.1000, 1.1005, 1.1000],
                'high': [1.1005, 1.1010, 1.1005],
                'low': [1.0995, 1.1000, 1.0995],
                'close': [1.1005, 1.1000, 1.1005],
                'volume': [1000] * 3
            })
            mock_market['rate_fetcher'].get_rates.return_value = rates

            await strategy.evaluate(mock_market)
            
            # Verify no order was sent
            mock_market['broker'].order_send.assert_not_called()