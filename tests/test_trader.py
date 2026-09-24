from unittest.mock import MagicMock

from mamba2.trader.client import TraderClient


def test_load_and_run_strategy(broker):
    broker.copy_rates_from_pos = MagicMock(
        return_value=[{"open": 1.0, "close": 1.1}]
    )
    broker.order_send = MagicMock(return_value={"retcode": 0})

    client = TraderClient(broker)
    client.load_strategy("examples.simple_strategy")
    client.run()

    broker.order_send.assert_called_once_with({"symbol": "EURUSD", "type": "BUY"})
