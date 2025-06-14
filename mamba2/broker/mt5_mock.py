"""Mock MetaTrader5 module for testing purposes."""

from typing import List, Dict, Any

class MT5Mock:
    def __init__(self):
        self.connected = True
        self.positions: List[Dict[str, Any]] = []
        self.orders: List[Dict[str, Any]] = []

    # --- connection helpers
    def initialize(self) -> bool:
        self.connected = True
        return self.connected

    def shutdown(self) -> None:
        self.connected = False

    # --- market data stubs
    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        return True

    def copy_rates_from_pos(self, symbol: str, timeframe: int, start_pos: int, count: int):
        # return list of dummy candle dictionaries
        return [{"open": 1.1, "close": 1.2, "high": 1.3, "low": 1.0, "time": 0}] * count

    # --- trading stubs
    def order_send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        self.orders.append(request)
        return {"retcode": 0, "order": len(self.orders)}

    def positions_get(self):
        return self.positions

# global singleton (to imitate `import MetaTrader5 as mt5` usage)
mt5 = MT5Mock()
