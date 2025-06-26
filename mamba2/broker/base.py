"""Broker abstract base class defining the interface for all broker implementations."""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Literal, TypedDict
from datetime import datetime

class BarData(TypedDict):
    """Market data bar/candle structure."""
    time: int  # Timestamp in seconds since epoch
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int
    real_volume: int


class PositionInfo(TypedDict):
    """Position information structure."""
    ticket: int
    time: int
    symbol: str
    type: int  # 0 for buy, 1 for sell
    volume: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    profit: float


class OrderCheckResult(TypedDict):
    """Order check/pre-check result structure."""
    retcode: int
    balance: float
    equity: float
    profit: float
    margin: float
    free_margin: float
    comment: str


class OrderSendResult(TypedDict):
    """Order send result structure."""
    retcode: int
    deal: int
    order: int
    volume: float
    price: float
    bid: float
    ask: float
    comment: str


class Broker(ABC):
    """Abstract base class for all broker implementations.
    
    This defines the interface that all broker implementations must follow,
    whether they're real brokers, mocks, or test implementations.
    """
    
    # --- Connection Management ---
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize connection to the broker.
        
        Returns:
            bool: True if connection was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown connection to the broker."""
        pass
    
    # --- Market Data ---
    
    @abstractmethod
    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        """Select a symbol in the MarketWatch.
        
        Args:
            symbol: Symbol name (e.g., "EURUSD").
            enable: If True, the symbol will be selected, otherwise unselected.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def copy_rates_from_pos(
        self,
        symbol: str,
        timeframe: int,
        start_pos: int,
        count: int
    ) -> List[BarData]:
        """Get historical data from the broker.
        
        Args:
            symbol: Symbol name.
            timeframe: Timeframe (e.g., mt5.TIMEFRAME_M1, mt5.TIMEFRAME_H1).
            start_pos: Initial position in the data array (0 - current bar).
            count: Number of bars to return.
            
        Returns:
            List of bar data dictionaries.
        """
        pass
    
    # --- Account Information ---
    
    @abstractmethod
    def account_info(self) -> Dict[str, Any]:
        """Get account information.
        
        Returns:
            Dictionary containing account information.
        """
        pass
    
    @abstractmethod
    def positions_get(self, symbol: str = "") -> List[PositionInfo]:
        """Get open positions.
        
        Args:
            symbol: Optional symbol filter.
            
        Returns:
            List of open positions.
        """
        pass
    
    # --- Order Management ---
    
    @abstractmethod
    def order_check(self, request: Dict[str, Any]) -> OrderCheckResult:
        """Check order validity without sending it.
        
        Args:
            request: Order request dictionary.
            
        Returns:
            Order check result.
        """
        pass
    
    @abstractmethod
    def order_send(self, request: Dict[str, Any]) -> OrderSendResult:
        """Send an order to the broker.
        
        Args:
            request: Order request dictionary.
            
        Returns:
            Order send result.
        """
        pass
    
    @abstractmethod
    def positions_total(self) -> int:
        """Get the number of open positions.
        
        Returns:
            Number of open positions.
        """
        pass
  
        
    @abstractmethod
    async def order_modify(self, ticket: int, sl: float = 0.0, tp: float = 0.0) -> Dict[str, Any]:
        """Modify an existing position's stop loss and take profit levels.
        
        Args:
            ticket: Position ticket number
            sl: New stop loss price
            tp: New take profit price
            
        Returns:
            Dictionary with modification result including 'retcode' (0 for success)
        """
        pass
    
    @abstractmethod
    async def position_by_ticket(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Get a position by its ticket number.

        Args:
            ticket: The position ticket number.

        Returns:
            A dictionary containing the position details, or None if not found.
        """
        pass
