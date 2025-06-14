"""Mock MetaTrader5 module for testing purposes."""

from typing import List, Dict, Any, Optional
import time
from .base import Broker, BarData, PositionInfo, OrderCheckResult, OrderSendResult

class MT5Mock(Broker):
    def __init__(self):
        self.connected = False
        self.positions: List[Dict[str, Any]] = []
        self.orders: List[Dict[str, Any]] = []
        self._account_balance = 10000.0
        self._account_equity = 10000.0
        self._last_ticket = 0
        self._last_order_ticket = 0

    # --- connection helpers
    def initialize(self) -> bool:
        """Initialize the mock broker connection."""
        self.connected = True
        return self.connected

    def shutdown(self) -> None:
        """Shutdown the mock broker connection."""
        self.connected = False

    # --- market data stubs
    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        """Select a symbol in the MarketWatch."""
        return True

    def copy_rates_from_pos(self, symbol: str, timeframe: int, start_pos: int, count: int) -> List[BarData]:
        """Get historical data from the broker."""
        current_time = int(time.time())
        return [{
            "open": 1.1, 
            "close": 1.2, 
            "high": 1.3, 
            "low": 1.0, 
            "time": current_time - (i * 60),  # 1 minute intervals
            "tick_volume": 100,
            "spread": 10,
            "real_volume": 1000
        } for i in range(count)]

    def copy_rates_from_range(
        self,
        symbol: str,
        timeframe: int,
        date_from: int,
        date_to: int
    ) -> List[BarData]:
        """Mock implementation of getting historical data between timestamps.
        
        Args:
            symbol: Symbol name (e.g. "EURUSD")
            timeframe: MT5 timeframe constant (mock ignores this)
            date_from: Start timestamp (Unix time)
            date_to: End timestamp (Unix time)
            
        Returns:
            List of mock BarData dictionaries
        """
        # Calculate number of minutes between dates (mock always uses 1 minute bars)
        duration_minutes = max(1, (date_to - date_from) // 60)
        
        return [{
            "open": 1.1 + (i * 0.01), 
            "close": 1.2 + (i * 0.01), 
            "high": 1.3 + (i * 0.01), 
            "low": 1.0 + (i * 0.01), 
            "time": date_from + (i * 60),  # 1 minute intervals
            "tick_volume": 100,
            "spread": 10,
            "real_volume": 1000
        } for i in range(duration_minutes)]

    # --- account information
    def account_info(self) -> Dict[str, Any]:
        """Get account information."""
        return {
            "balance": self._account_balance,
            "equity": self._account_equity,
            "margin": 0.0,
            "free_margin": self._account_equity,
            "leverage": 100,
            "currency": "USD"
        }

    # --- position management
    def positions_get(self, symbol: str = "") -> List[PositionInfo]:
        """Get open positions, optionally filtered by symbol."""
        if not symbol:
            return self.positions
        return [p for p in self.positions if p["symbol"] == symbol]

    def positions_total(self) -> int:
        """Get the number of open positions."""
        return len(self.positions)

    
    def position_get_ticket(self, ticket: int) -> Optional[PositionInfo]:
        """Get position by ticket number."""
        for pos in self.positions:
            if pos["ticket"] == ticket:
                return pos
        return None
    
    def position_close(self, ticket: int) -> bool:
        """Close an open position."""
        for i, pos in enumerate(self.positions):
            if pos["ticket"] == ticket:
                # In a real implementation, we'd update account balance here
                del self.positions[i]
                return True
        return False

    # --- order management
    def order_check(self, request: Dict[str, Any]) -> OrderCheckResult:
        """Check order validity without sending it."""
        return {
            "retcode": 0,
            "balance": self._account_balance,
            "equity": self._account_equity,
            "profit": 0.0,
            "margin": 0.0,
            "free_margin": self._account_equity,
            "comment": "ok"
        }

    def order_send(self, request: Dict[str, Any]) -> OrderSendResult:
        """Send an order to the broker."""
        self._last_order_ticket += 1
        self._last_ticket += 1
        
        # In a real implementation, we'd validate the order and update positions/account
        order_result = {
            "retcode": 0,
            "deal": self._last_ticket,
            "order": self._last_order_ticket,
            "volume": request.get("volume", 0.1),
            "price": 1.1,  # Would be current price in a real implementation
            "bid": 1.1,
            "ask": 1.1,
            "comment": ""
        }
        
        # If this is a market order, create a position
        if request.get("type") in [0, 1]:  # Buy or Sell
            position = {
                "ticket": self._last_ticket,
                "time": int(time.time()),
                "symbol": request.get("symbol", "EURUSD"),
                "type": request.get("type", 0),
                "volume": request.get("volume", 0.1),
                "price_open": 1.1,
                "sl": request.get("sl", 0.0),
                "tp": request.get("tp", 0.0),
                "price_current": 1.1,
                "profit": 0.0
            }
            self.positions.append(position)
            
        return order_result

# global singleton (to imitate `import MetaTrader5 as mt5` usage)
mt5 = MT5Mock()
