"""Day trader implementation for executing trading strategies."""
import asyncio
from loguru import logger
from mamba2.strategy.double_crossover import DoubleCrossoverStrategy
from config import config
import pandas as pd
import inspect

class DayTrader:
    """Executes trading strategies at regular intervals."""
    
    def __init__(self, broker, position_manager=None, cache=None, rate_fetcher=None):
        """Initialize the day trader with required components.
        
        Args:
            broker: Broker instance
            position_manager: Optional position manager instance
            cache: Optional cache manager instance
            rate_fetcher: Optional rate fetcher instance
        """
        self.broker = broker
        self.position_manager = position_manager
        self.cache = cache
        self.rate_fetcher = rate_fetcher
        self.running = False
        self.strategy = DoubleCrossoverStrategy(fast_period=10, slow_period=30)
        self.symbols = config.symbols
        self.risk_per_trade = config.risk_per_trade
    
    async def run_strategy(self, symbol: str):
        """Run trading strategy for a specific symbol."""
        logger.info(f"Analyzing {symbol} for trading opportunities...")
        
        # Create market context with access to both broker and rate fetcher
        market_context = {
            'broker': self.broker,
            'rate_fetcher': self.rate_fetcher,  # Pass rate fetcher to strategies
            'position_manager': self.position_manager
        }
        
        try:
            # Get current position for symbol
            position = self.position_manager.get_position(symbol)
            account_info = self.broker.account_info()
            
            # Get current price for symbol
            current_price = self.broker.copy_rates_from_pos(symbol, 1, 0, 1)[0]['close']
            
            logger.info(f"Symbol: {symbol}, Position: {position.volume if position else 0} lots, "
                       f"Price: {current_price:.5f}, "
                       f"Leverage: 1:{account_info['leverage']}, "
                       f"Margin Required: ${position.margin if position else 100:.2f}")
            
            # Evaluate strategy
            if hasattr(self.strategy, 'evaluate') and callable(self.strategy.evaluate):
                if inspect.iscoroutinefunction(self.strategy.evaluate):
                    await self.strategy.evaluate(market_context)
                else:
                    self.strategy.evaluate(market_context)
            
        except Exception as e:
            logger.error(f"Error evaluating {symbol}: {str(e)}")
            return
        
    async def run(self):
        """Run the trader to execute strategies at regular intervals."""
        self.running = True
        logger.info("📈 Starting day trader...")
        
        try:
            while self.running:
                try:
                    # Execute the strategy
                    for symbol in self.symbols:
                        await self.run_strategy(symbol)
                    
                    # Wait for the next interval (default 60 seconds if not specified)
                    trading_interval = getattr(config, 'trading_interval_seconds', 60)
                    await asyncio.sleep(trading_interval)
                    
                except asyncio.CancelledError:
                    logger.info("📈 Trading loop cancelled")
                    break
                    
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    # Wait a bit before retrying
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"Fatal error in day trader: {e}")
            raise
        finally:
            self.running = False
            logger.info("📈 Day trader stopped")
    
    async def stop(self):
        """Stop the trader."""
        self.running = False
        return True