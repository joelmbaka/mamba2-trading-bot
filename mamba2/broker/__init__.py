"""Broker subpackage.

The live MT5 adapter is intentionally loaded lazily so importing the broker
package remains safe on native Linux backtest/research environments where the
Windows-only MetaTrader5 package is not installed.
"""

from typing import TYPE_CHECKING

from .base import Broker
from .mt5_mock import MT5Mock, mt5  # re-export for convenience

if TYPE_CHECKING:
    from .mt5_broker import MT5Broker as MT5Broker

__all__ = ["Broker", "MT5Mock", "MT5Broker", "mt5"]


def __getattr__(name: str):
    if name != "MT5Broker":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    try:
        from .mt5_broker import MT5Broker
    except ModuleNotFoundError as exc:
        if exc.name == "MetaTrader5":
            raise ImportError(
                "MT5Broker requires the Windows-only MetaTrader5 package. "
                "Native Linux backtests should use mamba2.backtest instead."
            ) from exc
        raise

    return MT5Broker
