from mamba2.trader.client import TraderClient
from mamba2.broker.mt5_mock import mt5


def test_load_and_run_strategy(broker):
    client = TraderClient(broker)
    client.load_strategy("examples.simple_strategy")
    client.run()

    assert len(broker.orders) == 1
