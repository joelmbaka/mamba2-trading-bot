"""Tests for the current ATR manager API."""

import threading
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from mamba2.crew.atr_manager import ATRManager
from mamba2.crew.rates import RatesFetcher


@pytest.fixture
def rate_fetcher():
    fetcher = Mock(spec=RatesFetcher)
    fetcher.is_ready.return_value = True
    fetcher.get_rates.return_value = pd.DataFrame(
        {
            "open": [1.10, 1.11, 1.12],
            "high": [1.12, 1.13, 1.14],
            "low": [1.09, 1.10, 1.11],
            "close": [1.11, 1.12, 1.13],
        }
    )
    return fetcher


@pytest.fixture
def atr_manager(rate_fetcher):
    return ATRManager(rate_fetcher)


def test_initialization(atr_manager, rate_fetcher):
    assert atr_manager.rate_fetcher is rate_fetcher
    assert atr_manager.atr_cache == {}
    assert atr_manager._thread is None
    assert isinstance(atr_manager._stop_event, threading.Event)
    assert atr_manager.is_ready() is False
    assert atr_manager.get_atr("EURUSD", "M5") is None


def test_get_atr_and_readiness(atr_manager):
    atr_manager.atr_cache = {"EURUSD": {"M5": 0.01}}
    assert atr_manager.get_atr("EURUSD", "M5") == 0.01
    assert atr_manager.get_atr("EURUSD", "M15") is None

    atr_manager._initialized = True
    assert atr_manager.is_ready() is True


@pytest.mark.asyncio
async def test_run_loop_calculates_one_value(atr_manager):
    async def stop_after_sleep(_):
        atr_manager._stop_event.set()

    with patch("mamba2.crew.atr_manager.get_atr", return_value=0.01) as get_atr:
        with patch("mamba2.crew.atr_manager.asyncio.sleep", side_effect=stop_after_sleep):
            await atr_manager._run_loop()

    assert get_atr.call_count == 3
    assert atr_manager.get_atr("EURUSD", "M5") == 0.01
    assert atr_manager.get_atr("EURJPY", "M5") == 0.01
    assert atr_manager.get_atr("GBPUSD", "M5") == 0.01
    assert atr_manager.is_ready() is True


@pytest.mark.asyncio
async def test_start_stop_lifecycle(atr_manager):
    with patch.object(atr_manager, "_run_thread_wrapper", return_value=None):
        await atr_manager.start()
        assert atr_manager._thread is not None
        await atr_manager.stop()

    assert atr_manager._stop_event.is_set()
    assert not atr_manager._thread.is_alive()
    assert atr_manager.atr_cache == {}
