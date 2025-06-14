"""Double Moving Average Crossover Strategy implementation."""

from mamba2.strategy.base import Strategy
from loguru import logger
import numpy as np


class DoubleCrossoverStrategy(Strategy):
    """
    A double moving average crossover strategy.
    
    This strategy generates signals based on the crossover of two moving averages:
    - Fast MA (shorter period)
    - Slow MA (longer period)
    
    Buy signal: When Fast MA crosses above Slow MA
    Sell signal: When Fast MA crosses below Slow MA
    """

    def __init__(self, fast_period=10, slow_period=30):
        """
        Initialize the double crossover strategy.
        
        Args:
            fast_period: Period for the fast moving average
            slow_period: Period for the slow moving average (must be > fast_period)
        """
        super().__init__()
        self.symbol = "EURUSD"  # Default trading symbol
        self.timeframe = 15     # 15-minute timeframe
        self.fast_period = fast_period
        self.slow_period = slow_period
        
        if slow_period <= fast_period:
            raise ValueError("slow_period must be greater than fast_period")

    def _calculate_sma(self, prices, period):
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period

    def _get_moving_averages(self, closes):
        """Calculate both fast and slow moving averages."""
        fast_ma = []
        slow_ma = []
        
        # Calculate MAs for each point where we have enough data
        for i in range(1, len(closes) + 1):
            if i >= self.fast_period:
                fast_ma.append(self._calculate_sma(closes[:i], self.fast_period))
            if i >= self.slow_period:
                slow_ma.append(self._calculate_sma(closes[:i], self.slow_period))
        
        return fast_ma, slow_ma

    async def evaluate(self, market):
        """
        Evaluate market conditions using double MA crossover strategy.
        
        Args:
            market: Market interface providing access to market data and order execution
        """
        logger.info("DoubleCrossoverStrategy: Evaluating market conditions...")
        
        try:
            # Get enough data points for the slow MA plus some buffer
            required_bars = self.slow_period + 2  # +2 to detect crossovers
            
            # Get rates through the rate fetcher
            if 'rate_fetcher' not in market:
                logger.error("No rate fetcher available in market interface")
                return
                
            rates = market['rate_fetcher'].get_rates(self.symbol, f'M{self.timeframe}')
            
            if rates is None or (hasattr(rates, 'empty') and rates.empty) or len(rates) < required_bars:
                logger.warning(f"Not enough data points for analysis. Need {required_bars}, got {len(rates) if rates else 0}")
                return
            
            # Extract closing prices
            closes = rates['close'].tolist()
            
            # Calculate moving averages
            fast_ma, slow_ma = self._get_moving_averages(closes)
            
            if len(fast_ma) < 2 or len(slow_ma) < 2:
                logger.warning("Not enough data points for crossover analysis")
                return
            
            # Current and previous values
            fast_prev, fast_curr = fast_ma[-2], fast_ma[-1]
            slow_prev, slow_curr = slow_ma[-2], slow_ma[-1]
            
            logger.info(f"{self.symbol} - Fast MA: {fast_curr:.5f}, Slow MA: {slow_curr:.5f}")
            
            # Check for crossover signals
            # Bullish crossover: Fast MA crosses above Slow MA
            if bool(fast_prev <= slow_prev) and bool(fast_curr > slow_curr):
                order = {
                    "symbol": self.symbol,
                    "type": "BUY",
                    "volume": 0.1,
                    "sl": closes[-1] * 0.995,  # 0.5% stop loss
                    "tp": closes[-1] * 1.01     # 1% take profit
                }
                logger.info(f"Bullish crossover detected. Placing BUY order: {order}")
                resp = market['broker'].order_send(order)
                if resp and resp.retcode == 0:
                    # Cache the position in position manager
                    market['position_manager'].positions[self.symbol] = resp.order
                logger.info(f"Order response: {resp}")
            
            # Bearish crossover: Fast MA crosses below Slow MA
            elif bool(fast_prev >= slow_prev) and bool(fast_curr < slow_curr):
                order = {
                    "symbol": self.symbol,
                    "type": "SELL",
                    "volume": 0.1,
                    "sl": closes[-1] * 1.005,  # 0.5% stop loss
                    "tp": closes[-1] * 0.99      # 1% take profit
                }
                logger.info(f"Bearish crossover detected. Placing SELL order: {order}")
                resp = market['broker'].order_send(order)
                if resp and resp.retcode == 0:
                    # Cache the position in position manager
                    market['position_manager'].positions[self.symbol] = resp.order
                logger.info(f"Order response: {resp}")
                
        except Exception as e:
            logger.error(f"Error in DoubleCrossoverStrategy: {str(e)}")
            raise
