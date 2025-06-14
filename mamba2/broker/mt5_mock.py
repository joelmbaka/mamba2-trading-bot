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
        
        # Volatility parameters for each symbol (mean, stddev)
        self._symbol_volatility = {
            'EURUSD': (0.00005, 0.001),  # Lower volatility
            'EURJPY': (0.0001, 0.002),   # Higher volatility
            'GBPUSD': (0.00008, 0.0015)  # Medium volatility
        }

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
        """Generate realistic price series for the given symbol with trend reversals.
        
        Args:
            symbol: Symbol to generate prices for
            count: Number of bars to generate
            
        Returns:
            Tuple of (open_prices, high_prices, low_prices, close_prices)
        """
        price_range = self._symbol_ranges.get(symbol, (1.0, 1.2))
        mean_return, stddev = self._symbol_volatility.get(symbol, (0.0005, 0.01))  # Increased volatility
        
        # Get the last close price if available, otherwise generate a random starting price
        last_close = None
        if symbol in self._price_history and len(self._price_history[symbol][3]) > 0:
            last_close = self._price_history[symbol][3][-1]
        
        if last_close is None:
            # First time generating prices for this symbol
            np.random.seed(self._price_seed + hash(symbol) % 10000)  # Use symbol-specific seed
            last_close = np.random.uniform(price_range[0], price_range[1])
        
        # Initialize arrays
        opens = []
        highs = []
        lows = []
        closes = []
        
        current_price = last_close
        
        # Generate each bar one at a time to ensure continuity
        for _ in range(count):
            # Generate random price movement with volatility
            price_change = np.random.normal(mean_return, stddev) * current_price
            
            # Add some trend component
            trend_strength = np.random.uniform(0.5, 2.0)
            if len(closes) > 1:
                # Continue the trend from previous bars
                prev_trend = closes[-1] - opens[-1] if len(closes) > 0 else 0
                price_change += trend_strength * prev_trend * 0.1  # Continue trend weakly
            
            # Calculate OHLC for this bar
            open_price = current_price
            close_price = open_price + price_change
            
            # Ensure price stays within reasonable bounds
            close_price = max(price_range[0] * 0.99, min(price_range[1] * 1.01, close_price))
            
            # Calculate high and low with some randomness
            price_range_this_bar = abs(price_change) * np.random.uniform(1.0, 3.0)
            high = max(open_price, close_price) + price_range_this_bar * 0.5
            low = min(open_price, close_price) - price_range_this_bar * 0.5
            
            # Ensure high > low and prices are within overall range
            high = max(open_price, close_price, high)
            low = min(open_price, close_price, low)
            high = min(high, price_range[1] * 1.01)
            low = max(low, price_range[0] * 0.99)
            
            # Add to our lists
            opens.append(open_price)
            highs.append(high)
            lows.append(low)
            closes.append(close_price)
            
            # Next bar's open is this bar's close
            current_price = close_price
        
        return opens.tolist(), highs.tolist(), lows.tolist(), closes.tolist()
        
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
    def positions_get(self, symbol: str = "") -> List[PositionInfo]:
        """Get open positions, optionally filtered by symbol."""
        # Combine mock broker positions with PositionManager cache
        all_positions = self.positions.copy()
        if hasattr(self, '_position_manager'):
            for symbol, position in getattr(self._position_manager, 'positions', {}).items():
                if position not in all_positions:
                    all_positions.append(position)
        
        if not symbol:
            return all_positions
        return [p for p in all_positions if p["symbol"] == symbol]

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
                # Calculate P/L (simplified)
                current_price = pos['price_current']
                price_diff = current_price - pos['price_open'] if pos['type'] == 0 else pos['price_open'] - current_price
                profit = price_diff * pos['volume'] * 100000  # 1 lot = 100,000 units
                
                # Update account balance
                self._account_balance += profit
                self._account_equity = self._account_balance
                
                # Remove position
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

# global singleton (to imitate `import MetaTrader5 as mt5` usage)
mt5 = MT5Mock()
