import pytest

from mamba2.broker.mt5_mock import mt5 as mt5_mock

@pytest.fixture(scope="session")
def broker():
    yield mt5_mock
    mt5_mock.shutdown()
