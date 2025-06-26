"""MetaTrader 5 broker implementation."""

import time
from typing import Dict, List, Any, Optional, Union
import MetaTrader5 as mt5
from .base import Broker, BarData, PositionInfo, OrderCheckResult, OrderSendResult
from datetime import datetime
from mamba2.crew.logger import logger

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
    
    def symbol_info_tick(self, symbol: str) -> Dict[str, float]:
        """Get the current tick data for a symbol."""
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            error = mt5.last_error()
            raise RuntimeError(f"Failed to get tick for {symbol}: {error}")
        return {
            'bid': float(tick.bid),
            'ask': float(tick.ask),
            'last': float(tick.last),
            'volume': int(tick.volume),
            'time': int(tick.time)
        }
    
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
    
    async def positions_get(self, symbol: str = "", ticket: int = 0) -> List[PositionInfo]:
        """Get open positions, optionally filtered by symbol or ticket."""
        if ticket:
            positions = mt5.positions_get(ticket=ticket)
        elif symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
            
        if positions is None:
            error = mt5.last_error()
            raise RuntimeError(f"Failed to get positions: {error}")
        
        return [self._parse_position(p) for p in positions]
    
    def positions_total(self) -> int:
        """Get the number of open positions."""
        return mt5.positions_total()
    
    async def position_by_ticket(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Get a position by its ticket number.

        Args:
            ticket: The position ticket number.

        Returns:
            A dictionary containing the position details, or None if not found.
        """
        try:
            # Fetch the position by ticket
            positions = mt5.positions_get(ticket=ticket)
            if positions is None:
                error = mt5.last_error()
                # Check if this is actually an error or just "no positions found"
                if error[0] != mt5.TRADE_RETCODE_DONE:
                    logger.error(f"Error getting position by ticket {ticket}: {error}")
                return None
            # If positions is an empty list, no position was found
            if not positions:
                return None
                
            # We expect exactly one position
            if len(positions) == 0:
                return None
                
            # Get the first (and should be only) position
            pos = positions[0]
            return {
                'ticket': pos.ticket,
                'time': pos.time,
                'time_msc': getattr(pos, 'time_msc', 0),
                'time_update': getattr(pos, 'time_update', 0),
                'time_update_msc': getattr(pos, 'time_update_msc', 0),
                'symbol': pos.symbol,
                'type': pos.type,
                'magic': getattr(pos, 'magic', 0),
                'identifier': getattr(pos, 'identifier', 0),
                'reason': getattr(pos, 'reason', -1),
                'volume': float(pos.volume),
                'price_open': float(pos.price_open),
                'sl': float(pos.sl),
                'tp': float(pos.tp),
                'price_current': float(pos.price_current),
                'swap': float(getattr(pos, 'swap', 0)),
                'profit': float(pos.profit),
                'comment': getattr(pos, 'comment', ''),
                'external_id': getattr(pos, 'external_id', '')
            }
            
        except Exception as e:
            logger.error(f"Error in position_by_ticket for ticket {ticket}: {str(e)}")
            return None
    
   
    async def order_modify(self, ticket: int, sl: float = 0.0, tp: float = 0.0) -> Dict[str, Any]:
        """Modify an existing position's stop loss and take profit levels.
        
        Args:
            ticket: Position ticket number
            sl: New stop loss price
            tp: New take profit price
            
        Returns:
            Dictionary with modification result
        """
        # Get the current position
        position = await self.position_by_ticket(ticket)
        if not position:
            return {'retcode': 1, 'error': 'Position not found'}
            
        # Get symbol info for validation
        symbol_info = mt5.symbol_info(position['symbol'])
        if not symbol_info:
            return {'retcode': 1, 'error': 'Failed to get symbol info'}
            
        # Validate stop levels
        digits = symbol_info.digits
        min_stop_distance = symbol_info.trade_stops_level * symbol_info.point
        current_price = position['price_current']
        
        # Normalize prices
        sl = round(sl, digits) if sl else 0.0
        tp = round(tp, digits) if tp else 0.0
        
        # Check stop levels are valid
        if sl and ((position['type'] == 0 and sl >= current_price - min_stop_distance) or 
                  (position['type'] == 1 and sl <= current_price + min_stop_distance)):
            return {'retcode': 10016, 'error': 'Invalid stops', 
                   'comment': f'SL must be {min_stop_distance} points away from price'}
                   
        if tp and ((position['type'] == 0 and tp <= current_price + min_stop_distance) or 
                  (position['type'] == 1 and tp >= current_price - min_stop_distance)):
            return {'retcode': 10016, 'error': 'Invalid stops', 
                   'comment': f'TP must be {min_stop_distance} points away from price'}
        
        # Create modification request
        request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'position': ticket,
            'symbol': position['symbol'],
            'sl': sl,
            'tp': tp
        }
        
        # Send the modification request
        result = mt5.order_send(request)
        if result is None:
            error = mt5.last_error()
            return {'retcode': 1, 'error': f"MT5 error: {error}"}
            
        return {
            'retcode': result.retcode,
            'ticket': ticket,
            'sl': sl,
            'tp': tp,
            'comment': result.comment
        }
    
    # --- Closed Positions ---
    
    
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
    
    def get_point_size(self, symbol: str) -> float:
        """Get the point size for a symbol."""
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return 0.0
        return symbol_info.point
        
    def _parse_position(self, position):
        """Parse MT5 position object or dictionary into a standardized dictionary."""
        # If it's an MT5 position object
        if hasattr(position, 'ticket'):
            return {
                'ticket': position.ticket,
                'time_open': position.time,
                'time': position.time,
                'time_msc': position.time_msc,
                'symbol': position.symbol,
                'type': position.type,
                'volume': position.volume,
                'price_open': position.price_open,
                'price_current': position.price_current,
                'sl': position.sl,
                'tp': position.tp,
                'profit': position.profit,
                'swap': position.swap,
                'comment': position.comment
            }
        # If it's already a dictionary
        else:
            return position
