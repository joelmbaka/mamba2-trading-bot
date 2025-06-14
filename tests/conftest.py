"""Pytest configuration and fixtures."""
import sys
from pathlib import Path
import pytest

# Add project root to Python path
PROJECT_ROOT = str(Path(__file__).parent.resolve())
sys.path.insert(0, PROJECT_ROOT)

# Mock config before importing any modules that depend on it
import sys
from unittest.mock import MagicMock

# Create a mock config module
mock_config = MagicMock()
mock_config.symbols = ['EURUSD', 'EURJPY', 'GBPUSD']
mock_config.timeframes = {'M1': 1, 'M5': 5, 'M15': 15}
mock_config.atr_period = 14
mock_config.rates_count = 200
mock_config.cache_ttl = 300

# Replace the real config with our mock
sys.modules['config'] = mock_config

# Now import the MT5 mock
from mamba2.broker.mt5_mock import mt5 as mt5_mock

@pytest.fixture(scope="session")
def broker():
    """Fixture providing a mock MT5 broker instance."""
    yield mt5_mock
    mt5_mock.shutdown()

@pytest.fixture(autouse=True)
def setup_imports():
    """Setup test environment before each test."""
    # This ensures our mock config is used in all tests
    pass
