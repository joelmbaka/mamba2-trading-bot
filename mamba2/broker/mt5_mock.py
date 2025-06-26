"""Mock MetaTrader5 module for testing purposes."""

from typing import List, Dict, Any, Optional, Tuple
import time
import random
import numpy as np
from .base import Broker, BarData, PositionInfo, OrderCheckResult, OrderSendResult
from ..crew.logger import logger

class MT5Mock(Broker):
    def __init__(self):
        self.connected = False
        self.positions: List[Dict[str, Any]] = []
        self.orders: List[Dict[str, Any]] = []
        self._account_balance = 10000.0
        self._account_equity = 10000.0
        self._leverage = 1000  # 1:1000 leverage
        self._last_ticket = 0
        self._last_order_ticket = 0
        self._price_history: Dict[str, Tuple[List[float], List[float], List[float], List[float]]] = {}
        self._last_update_time: Dict[str, float] = {}
        self._price_seed = int(time.time())  # Seed for reproducibility
        
        # Typical price ranges for each symbol
        self._symbol_ranges = {
            'EURUSD': (1.0, 1.2),  # Typical EURUSD range
            'EURJPY': (130.0, 160.0),  # Typical EURJPY range
            'GBPUSD': (1.2, 1.4)  # Typical GBPUSD range
        }
        
        # More realistic volatility parameters
        self._symbol_volatility = {
            'EURUSD': (0.0001, 0.0005),  # More realistic daily volatility
            'EURJPY': (0.0002, 0.0008),
            'GBPUSD': (0.00015, 0.0006)
        }
        
        # Minimum and maximum price movement constraints
        self._min_move = 0.0002  # 2 pips minimum movement
        self._max_move = 0.0020  # 20 pips maximum movement

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

    def _generate_price_series(self, symbol: str, count: int) -> Tuple[List[float], List[float], List[float], List[float]]:
        """Generate more realistic price series with constrained movements."""
        price_range = self._symbol_ranges.get(symbol, (1.0, 1.2))
        mean_return, stddev = self._symbol_volatility.get(symbol, (0.0001, 0.0005))
        
        # Get the last close price if available
        last_close = None
        if symbol in self._price_history and len(self._price_history[symbol][3]) > 0:
            last_close = self._price_history[symbol][3][-1]
        
        if last_close is None:
            np.random.seed(self._price_seed + hash(symbol) % 10000)
            last_close = np.random.uniform(price_range[0], price_range[1])
        
        current_price = last_close
        opens, highs, lows, closes = [], [], [], []
        
        for _ in range(count):
            # Generate constrained price movement
            while True:
                price_change = np.random.normal(mean_return, stddev) * current_price
                if abs(price_change) >= self._min_move and abs(price_change) <= self._max_move:
                    break
            
            # Calculate OHLC with realistic spreads
            open_price = current_price
            close_price = open_price + price_change
            
            # Constrain high/low to be within reasonable bounds of open/close
            spread = abs(price_change) * np.random.uniform(0.1, 0.3)
            high_price = max(open_price, close_price) + spread
            low_price = min(open_price, close_price) - spread
            
            # Ensure prices stay within symbol range
            min_bound, max_bound = price_range
            close_price = np.clip(close_price, min_bound, max_bound)
            high_price = np.clip(high_price, min_bound, max_bound)
            low_price = np.clip(low_price, min_bound, max_bound)
            
            opens.append(open_price)
            highs.append(high_price)
            lows.append(low_price)
            closes.append(close_price)
            
            current_price = close_price
        
        return opens, highs, lows, closes
        
    def copy_rates_from_pos(
        self,
        symbol: str,
        timeframe: int,
        start_pos: int,
        count: int
    ) -> List[BarData]:
        """Mock implementation of copy_rates_from_pos."""
        if symbol not in self._price_history:
            # Generate initial price series if none exists
            opens, highs, lows, closes = self._generate_price_series(symbol, 1000)
            self._price_history[symbol] = (opens, highs, lows, closes)
        else:
            # Generate a few new bars (1 to 5) to simulate new ticks
            new_bars_count = random.randint(1, 5)
            opens, highs, lows, closes = self._generate_price_series(symbol, new_bars_count)
            # Update stored history with new prices
            self._price_history[symbol][0].extend(opens)
            self._price_history[symbol][1].extend(highs)
            self._price_history[symbol][2].extend(lows)
            self._price_history[symbol][3].extend(closes)
        
        # Get the current history
        opens, highs, lows, closes = self._price_history[symbol]
        total_bars = len(closes)
        
        # Calculate the slice indices
        start_index = total_bars - start_pos - count
        end_index = total_bars - start_pos
        
        if start_index < 0:
            # Not enough bars, so adjust to return all bars we have
            start_index = 0
            end_index = total_bars
            count = total_bars
        else:
            end_index = min(end_index, total_bars)
        
        # Extract the slice
        opens_slice = opens[start_index:end_index]
        highs_slice = highs[start_index:end_index]
        lows_slice = lows[start_index:end_index]
        closes_slice = closes[start_index:end_index]
        
        # Create the bars in chronological order (oldest first)
        current_time = int(time.time())
        bars = []
        for i in range(count):
            # Time for this bar: current_time - (count - 1 - i) * (timeframe in seconds)
            bar_time = current_time - (count - 1 - i) * timeframe * 60
            bars.append({
                'time': bar_time,
                'open': opens_slice[i],
                'high': highs_slice[i],
                'low': lows_slice[i],
                'close': closes_slice[i],
                'tick_volume': 1000,
                'spread': 10,
                'real_volume': 1000000
            })
        
        return bars

    # --- account information
    def account_info(self) -> Dict[str, Any]:
        """Get account information."""
        # Calculate used margin from open positions
        used_margin = sum(
            (pos['volume'] * 100000 * pos['price_open']) / self._leverage 
            for pos in self.positions
        )
        
        return {
            "balance": self._account_balance,
            "equity": self._account_equity,
            "margin": used_margin,
            "free_margin": self._account_equity - used_margin,
            "leverage": self._leverage,
            "currency": "USD",
            "margin_level": (self._account_equity / used_margin * 100) if used_margin > 0 else 0,
            "margin_mode": 0,  # 0 = retail, 1 = retail no rebates, 2 = exchange
            "margin_so_mode": 0,  # 0 = percent, 1 = currency, 100 = points
            "margin_initial": 0.0,  # Not used in this mock
            "margin_maintenance": 0.0  # Not used in this mock
        }

    # --- position management
    async def positions_get(self, symbol: Optional[str] = None, ticket: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get open positions.
        
        Args:
            symbol: Optional symbol filter (e.g. "EURUSD")
            ticket: Optional position ticket filter
            
        Returns:
            List of position information dictionaries
        """
        if symbol and ticket:
            return [p for p in self.positions if p['symbol'] == symbol and p['ticket'] == ticket]
        elif symbol:
            return [p for p in self.positions if p['symbol'] == symbol]
        elif ticket:
            return [p for p in self.positions if p['ticket'] == ticket]
        return self.positions

    def positions_total(self) -> int:
        """Get the number of open positions."""
        return len(self.positions)

    
    def position_get_ticket(self, ticket: int) -> Optional[PositionInfo]:
        """Get position by ticket number."""
        for pos in self.positions:
            if pos["ticket"] == ticket:
                return pos
        return None
    
    async def position_by_ticket(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Get a position by its ticket number.

        Args:
            ticket: The position ticket number.

        Returns:
            A dictionary containing the position details, or None if not found.
        """
        for position in self.positions:
            if position.get('ticket') == ticket:
                return position.copy()
        return None
        
    def position_close(self, ticket: int) -> bool:
        """Close an open position by ticket."""
        position = self.position_get_ticket(ticket)
        if not position:
            return False
            
        # Create a close request
        symbol = position['symbol']
        volume = position['volume']
        position_type = position['type']
        
        # Calculate P/L (simplified)
        current_price = position['price_current']
        price_diff = current_price - position['price_open'] if position['type'] == 0 else position['price_open'] - current_price
        profit = price_diff * position['volume'] * 100000  # 1 lot = 100,000 units
                
        # Update account balance
        self._account_balance += profit
        self._account_equity = self._account_balance
                
        # Remove position
        for i, pos in enumerate(self.positions):
            if pos['ticket'] == ticket:
                del self.positions[i]
                return True
        return False

    # --- order management
    def order_check(self, request: Dict[str, Any]) -> OrderCheckResult:
        """Check order validity without sending it."""
        volume = request.get('volume', 1)
        symbol = request.get('symbol', 'EURUSD')
        
        # Get current price for margin calculation
        rates = self.copy_rates_from_pos(symbol, 1, 0, 1)
        if not rates:
            return {
                "retcode": 10019,  # TRADE_RETCODE_NO_PRICES
                "comment": f"No prices for {symbol}"
            }
            
        price = rates[0]['close']
        margin_required = (volume * 100000 * price) / self._leverage
        account_info = self.account_info()
        
        if margin_required > account_info['free_margin']:
            return {
                "retcode": 10014,  # TRADE_RETCODE_NOT_ENOUGH_MONEY
                "balance": self._account_balance,
                "equity": self._account_equity,
                "profit": 0.0,
                "margin": account_info['margin'],
                "free_margin": account_info['free_margin'],
                "comment": "Not enough money"
            }
            
        return {
            "retcode": 0,
            "balance": self._account_balance,
            "equity": self._account_equity,
            "profit": 0.0,
            "margin": margin_required,
            "free_margin": account_info['free_margin'] - margin_required,
            "comment": "ok"
        }

    def order_send(self, request: Dict[str, Any]) -> OrderSendResult:
        """Send an order to the broker."""
        self._last_order_ticket += 1
        self._last_ticket += 1
        
        # Get current price for the symbol
        symbol = request.get("symbol", "EURUSD")
        if symbol in self._price_history and self._price_history[symbol][3]:  # Check if we have close prices
            current_price = self._price_history[symbol][3][-1]  # Last close price
        else:
            current_price = 1.1  # Fallback price
        
        # In a real implementation, we'd validate the order and update positions/account
        order_result = {
            "retcode": 0,
            "deal": self._last_ticket,
            "order": self._last_order_ticket,
            "volume": request.get("volume", 0.1),
            "price": current_price,
            "bid": current_price - 0.0001,  # Add small spread
            "ask": current_price + 0.0001,
            "comment": ""
        }
        
        # If this is a market order, create a position
        if request.get("type") in [0, 1]:  # Buy or Sell
            position = {
                "ticket": self._last_ticket,
                "time": int(time.time()),
                "symbol": symbol,
                "type": request.get("type", 0),
                "volume": request.get("volume", 0.1),
                "price_open": current_price,
                "sl": request.get("sl", 0.0),
                "tp": request.get("tp", 0.0),
                "price_current": current_price,
                "profit": 0.0
            }
            self.positions.append(position)
            
        return order_result

    def order_modify(self, ticket: int, sl: float = 0.0, tp: float = 0.0) -> Dict[str, Any]:
        """Modify an existing order's stop loss and take profit levels.
        
        Args:
            ticket: Order ticket number
            sl: New stop loss price
            tp: New take profit price
            
        Returns:
            Dictionary with modification result
        """
        # Find the order
        order = next((o for o in self.orders if o['ticket'] == ticket), None)
        
        if not order:
            return {'retcode': 1, 'error': 'Order not found'}
            
        # Update the order
        order['sl'] = sl
        order['tp'] = tp
        
        return {
            'retcode': 0,
            'ticket': ticket,
            'sl': sl,
            'tp': tp,
            'bid': self._get_current_price(order['symbol'], 'bid'),
            'ask': self._get_current_price(order['symbol'], 'ask')
        }

    def symbol_info_tick(self, symbol: str) -> Dict[str, Any]:
        """Get current tick data for a symbol.
        
        Args:
            symbol: Symbol name (e.g. "EURUSD")
            
        Returns:
            Dictionary containing current bid/ask prices and other tick data
        """
        if symbol not in self._price_history or len(self._price_history[symbol][3]) == 0:
            self._generate_price_series(symbol, 1)
            
        return {
            'bid': self._price_history[symbol][3][-1] - 0.0001,  # bid slightly below last close
            'ask': self._price_history[symbol][3][-1] + 0.0001,  # ask slightly above last close
            'last': self._price_history[symbol][3][-1],
            'volume': random.randint(1000, 5000),
            'time': int(time.time())
        }

# global singleton (to imitate `import MetaTrader5 as mt5` usage)
mt5 = MT5Mock()
