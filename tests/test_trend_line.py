"""Tests for the trend_line indicator."""
import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock

from mamba2.indicators.trend_line import get_trend_line, plot_trend_line

class DummyRateFetcher:
    """Minimal fetcher that satisfies get_rates contract."""
    def __init__(self, df):
        self._df = df
    def get_rates(self, symbol, timeframe):
        return self._df

@pytest.fixture
def sample_rates():
    # Create deterministic upward-trending close prices with noise.
    idx = pd.date_range(end=pd.Timestamp.now(), periods=120, freq="5min")
    closes = 1.10 + np.linspace(0, 0.010, 120) + np.random.normal(0, 0.0005, 120)
    df = pd.DataFrame({
        "open": closes - 0.0003,
        "high": closes + 0.0005,
        "low": closes - 0.0005,
        "close": closes,
    }, index=idx)
    return df


def test_get_trend_line(sample_rates):
    fetcher = DummyRateFetcher(sample_rates)
    result = get_trend_line(fetcher, symbol="EURUSD", timeframe="M5", lookback=100)
    assert result is not None, "Expected numeric trend line result"
    # Slope should be positive (overall upward trend)
    assert result["slope"] > 0
    # y array must align with x length
    assert len(result["y"]) == len(result["x"]) == 100


def test_plot_trend_line(tmp_path, sample_rates):
    fetcher = DummyRateFetcher(sample_rates)
    file_path = tmp_path / "trend.png"
    fig = plot_trend_line(fetcher, symbol="EURUSD", timeframe="M5", lookback=60, save_path=str(file_path))
    # Figure should be returned and file saved
    assert fig is not None
    assert file_path.exists(), "Plot image should have been created"
