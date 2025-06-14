"""MetaTrader 5 broker implementation."""

import time
from typing import Dict, List, Any, Optional, Union
import MetaTrader5 as mt5
from .base import Broker, BarData, PositionInfo, OrderCheckResult, OrderSendResult

class MT5Broker(Broker):
    """Broker implementation for MetaTrader 5.
    
    This class provides a concrete implementation of the Broker interface
    that connects to a live MetaTrader 5 terminal.
    """
    
    def __init__(self, 
                 path: str = "", 
                 login: int = None, 
                 password: str = "", 
                 server: str = "",
                 timeout: int = 60000,
                 portable: bool = False):
        """Initialize the MT5 broker.
        
        Args:
            path: Path to the MetaTrader 5 terminal executable.
            login: Account login (if not provided, will use the last logged in account).
            password: Account password.
            server: Trading server name.
            timeout: Connection timeout in milliseconds.
            portable: If True, run in portable mode.
        """
        self.path = path
        self.login = login
        self.password = password
        self.server = server
        self.timeout = timeout
        self.portable = portable
        self.connected = False
    
    # --- Connection Management ---
    
    def initialize(self) -> bool:
        """Initialize connection to the MetaTrader 5 terminal."""
        if not mt5.initialize(path=self.path, 
                            login=self.login, 
                            password=self.password,
                            server=self.server,
                            timeout=self.timeout,
                            portable=self.portable):
            error = mt5.last_error()
            raise ConnectionError(f"Failed to initialize MT5: {error}")
        
        self.connected = True
        return True
    
    def shutdown(self) -> None:
        """Shutdown connection to the MetaTrader 5 terminal."""
        mt5.shutdown()
        self.connected = False
    
    # --- Market Data ---
    
    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        """Select a symbol in the MarketWatch."""
        return mt5.symbol_select(symbol, enable)
    
    def copy_rates_from_pos(
        self,
        symbol: str,
        timeframe: int,
        start_pos: int,
        count: int
    ) -> List[BarData]:
        """Get historical data from MT5."""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
        if rates is None:
            error = mt5.last_error()
            raise RuntimeError(f"Failed to get rates: {error}")
        
        # Convert from numpy.recarray to list of dicts
        return [{
            'time': int(rate['time']),
            'open': float(rate['open']),
            'high': float(rate['high']),
            'low': float(rate['low']),
            'close': float(rate['close']),
            'tick_volume': int(rate['tick_volume']),
            'spread': int(rate['spread']),
            'real_volume': int(rate['real_volume'])
        } for rate in rates]
    
    def copy_rates_from_range(
        self,
        symbol: str,
        timeframe: int,
        date_from: int,
        date_to: int
    ) -> List[BarData]:
        """Get historical data between two timestamps.
        
        Args:
            symbol: Symbol name (e.g. "EURUSD")
            timeframe: MT5 timeframe constant (e.g. mt5.TIMEFRAME_M1)
            date_from: Start timestamp (Unix time)
            date_to: End timestamp (Unix time)
            
        Returns:
            List of BarData dictionaries
        """
        rates = mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
        if rates is None:
            error = mt5.last_error()
            raise RuntimeError(f"Failed to get rates: {error}")
        
        return [{
            'time': int(rate['time']),
            'open': float(rate['open']),
            'high': float(rate['high']),
            'low': float(rate['low']),
            'close': float(rate['close']),
            'tick_volume': int(rate['tick_volume']),
            'spread': int(rate['spread']),
            'real_volume': int(rate['real_volume'])
        } for rate in rates]
    
    # --- Account Information ---
    
    def account_info(self) -> Dict[str, Any]:
        """Get account information."""
        info = mt5.account_info()
        if info is None:
            error = mt5.last_error()
            raise RuntimeError(f"Failed to get account info: {error}")
        
        # Convert to dict and filter out MT5-specific fields
        return {
            'login': info.login,
            'trade_mode': info.trade_mode,
            'leverage': info.leverage,
            'margin_mode': info.margin_mode,
            'currency_digits': info.currency_digits,
            'balance': float(info.balance),
            'credit': float(info.credit),
            'profit': float(info.profit),
            'equity': float(info.equity),
            'margin': float(info.margin),
            'margin_free': float(info.margin_free),
            'margin_level': float(info.margin_level) if info.margin_level is not None else 0.0,
            'margin_so_mode': info.margin_so_mode,
            'margin_initial': float(info.margin_initial) if info.margin_initial is not None else 0.0,
            'margin_maintenance': float(info.margin_maintenance) if info.margin_maintenance is not None else 0.0,
            'assets': float(info.assets) if hasattr(info, 'assets') else 0.0,
            'liabilities': float(info.liabilities) if hasattr(info, 'liabilities') else 0.0,
            'commission_blocked': float(info.commission_blocked) if hasattr(info, 'commission_blocked') else 0.0,
            'name': info.name,
            'server': info.server,
            'currency': info.currency,
            'company': info.company
        }
    
    # --- Position Management ---
    
    def positions_get(self, symbol: str = "") -> List[PositionInfo]:
        """Get open positions, optionally filtered by symbol."""
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
        
        if positions is None:
            error = mt5.last_error()
            if error[0] == 1:  # TRADE_RETCODE_ERROR
                return []  # No positions
            raise RuntimeError(f"Failed to get positions: {error}")
        
        return [self._parse_position(pos) for pos in positions]
    
    def positions_total(self) -> int:
        """Get the number of open positions."""
        return mt5.positions_total()
    
    def position_get_ticket(self, ticket: int) -> Optional[PositionInfo]:
        """Get position by ticket number."""
        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            return None
        return self._parse_position(position[0])
    
    def position_close(self, ticket: int) -> bool:
        """Close an open position by ticket."""
        position = self.position_get_ticket(ticket)
        if not position:
            return False
            
        # Create a close request
        symbol = position['symbol']
        volume = position['volume']
        position_type = position['type']
        
        # Determine the close price and order type
        symbol_info = mt5.symbol_info_tick(symbol)
        if symbol_info is None:
            error = mt5.last_error()
            raise RuntimeError(f"Failed to get tick for {symbol}: {error}")
            
        price = symbol_info.bid if position_type == 0 else symbol_info.ask
        
        # Create and send the close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": 1 if position_type == 0 else 0,  # Reverse the position type
            "position": ticket,
            "price": price,
            "deviation": 10,
            "magic": 0,
            "comment": "python script close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        
        result = mt5.order_send(request)
        if result is None:
            error = mt5.last_error()
            raise RuntimeError(f"Failed to close position {ticket}: {error}")
            
        return result.retcode == mt5.TRADE_RETCODE_DONE
    
    # --- Order Management ---
    
    def order_check(self, request: Dict[str, Any]) -> OrderCheckResult:
        """Check order validity without sending it."""
        result = mt5.order_check(request)
        if result is None:
            error = mt5.last_error()
            raise RuntimeError(f"Order check failed: {error}")
        
        return {
            'retcode': result.retcode,
            'balance': float(result.balance),
            'equity': float(result.equity),
            'profit': float(result.profit),
            'margin': float(result.margin),
            'free_margin': float(result.margin_free),
            'comment': result.comment
        }
    
    def order_send(self, request: Dict[str, Any]) -> OrderSendResult:
        """Send an order to the broker."""
        result = mt5.order_send(request)
        if result is None:
            error = mt5.last_error()
            raise RuntimeError(f"Order send failed: {error}")
        
        return {
            'retcode': result.retcode,
            'deal': result.deal,
            'order': result.order,
            'volume': float(result.volume),
            'price': float(result.price),
            'bid': float(result.bid),
            'ask': float(result.ask),
            'comment': result.comment
        }
    
    # --- Helper Methods ---
    
    def _parse_position(self, position) -> PositionInfo:
        """Convert MT5 position object to PositionInfo dict."""
        return {
            'ticket': position.ticket,
            'time': position.time,
            'time_msc': position.time_msc,
            'time_update': position.time_update,
            'time_update_msc': position.time_update_msc,
            'type': position.type,
            'magic': position.magic,
            'identifier': position.identifier,
            'reason': position.reason,
            'volume': float(position.volume),
            'price_open': float(position.price_open),
            'sl': float(position.sl),
            'tp': float(position.tp),
            'price_current': float(position.price_current),
            'swap': float(position.swap),
            'profit': float(position.profit),
            'symbol': position.symbol,
            'comment': position.comment,
            'external_id': position.external_id
        }
