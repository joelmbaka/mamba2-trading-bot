"""
Main bot file with improved shutdown sequence
"""
import asyncio
import os
import signal
import time
import threading

# Import cache manager
from mamba2.crew.cache_manager import CacheManager
from mamba2.crew.logger import logger

# Import brokers
from mamba2.broker.mt5_mock import MT5Mock
from mamba2.broker.mt5_broker import MT5Broker

# Import components
from mamba2.crew.rates import RatesFetcher
from mamba2.crew.position_manager import PositionManager
from mamba2.crew.day_trader import DayTrader
from mamba2.crew.atr_manager import ATRManager

import config

class Bot:
    def __init__(self):
        self.broker = None
        self.cache = CacheManager("bot_cache.json")
        self.running = False
        self.active_tasks = []  # Track all active tasks
        self._shutdown_lock = asyncio.Lock()  # Prevent multiple shutdowns

    def _create_broker(self):
        """Create and initialize the appropriate broker instance."""
        if config.use_mock:
            print("Using mock MT5 broker")
            broker = MT5Mock()
        else:
            print(f"Connecting to real MT5 account: {config.mt5.login}")
            broker = MT5Broker(
                path=config.mt5.path,
                login=config.mt5.login,
                password=config.mt5.password,
                server=config.mt5.server,
                timeout=config.mt5.timeout,
                portable=config.mt5.portable
            )
        return broker
    
    async def initialize(self):
        """Initialize the bot with the configured broker."""
        self.broker = self._create_broker()
        
        if not self.broker.initialize():
            broker_type = "mock" if config.use_mock else "real"
            raise RuntimeError(f"Failed to initialize {broker_type} MT5 connection")
        
        # Log account info on startup
        account_info = self.broker.account_info()
        print(f"Bot started with account info: {account_info}")
        
        # Store account info in cache
        self.cache.set("last_account_info", account_info)
        self.cache.set("last_broker_type", "mock" if config.use_mock else "real", save=True)
        
        self.running = True
        print(f"Using {'mock' if config.use_mock else 'real'} MT5 broker")

    async def run(self):
        """Main bot event loop with improved shutdown handling."""
        # Initialize crew members
        self.rate_fetcher = RatesFetcher(self.broker)
        self.atr_manager = ATRManager(self.rate_fetcher)
        self.position_manager = PositionManager(self.broker, self.atr_manager)
        self.day_trader = DayTrader(
            self.broker, 
            self.position_manager, 
            self.cache,
            self.rate_fetcher
        )
        
        # Start components and store tasks
        try:
            # Start rate fetcher thread directly (non-blocking)
            self.rate_fetcher.start()
            
            if not await self._wait_for_initial_rates():
                logger.error("Failed to get initial rate data. Cannot start ATR manager.")
                self.running = False
                return
                
            atr_task = asyncio.create_task(self.atr_manager.start())
            position_task = asyncio.create_task(self.position_manager.run())
            trader_task = asyncio.create_task(self.day_trader.run())
            
            self.active_tasks.extend([atr_task, position_task, trader_task])
            
            # Main event loop
            while self.running:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Shutdown signal received")
            await self.shutdown()
            
        except Exception as e:
            logger.error(f"Bot error: {e}")
            await self.shutdown()
            
        finally:
            # Final cleanup if we exited abnormally
            if self.running:
                await self.shutdown()

    async def _wait_for_initial_rates(self, timeout: int = 60):
        """Wait for initial rate data to be loaded."""
        start_time = time.time()
        logger.info("Waiting for initial rate data...")
        
        while time.time() - start_time < timeout:
            if self.rate_fetcher.is_ready():
                logger.info("Rate data is now available")
                return True
            logger.debug("Rate data not ready yet, waiting...")
            await asyncio.sleep(1)
            
        logger.error("Timed out waiting for initial rate data")
        return False
    
    async def shutdown(self):
        """Gracefully shutdown all components."""
        async with self._shutdown_lock:  # Prevent multiple concurrent shutdowns
            if not self.running:
                return
                
            self.running = False
            logger.info("Starting graceful shutdown...")
            
            # Stop components in reverse order of initialization
            try:
                if hasattr(self, 'day_trader'):
                    await self.day_trader.stop()
                if hasattr(self, 'position_manager'):
                    await self.position_manager.stop()
                if hasattr(self, 'atr_manager'):
                    logger.info("Stopping ATR manager and waiting for calculations to complete...")
                    await self.atr_manager.stop()
                if hasattr(self, 'rate_fetcher'):
                    logger.info("Stopping rate fetcher...")
                    # Run blocking stop in a thread
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self.rate_fetcher.stop)
                    
                if hasattr(self, 'broker') and self.broker:
                    self.broker.shutdown()
                    
                # Wait for all active tasks to complete
                if self.active_tasks:
                    logger.info("Waiting for all tasks to complete...")
                    await asyncio.gather(*self.active_tasks, return_exceptions=True)
                    
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
                
            finally:
                self.cache.save_cache()
                logger.info("Shutdown completed")
                self.active_tasks.clear()

def setup_signal_handlers(bot):
    """Setup signal handlers for graceful shutdown."""
    def shutdown(signal, frame=None):
        logger.info(f"Received shutdown signal {signal}")
        
        # First try graceful shutdown
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule the async shutdown
                asyncio.create_task(bot.shutdown())
                loop.stop()
        except Exception as e:
            logger.error(f"Error in graceful shutdown: {e}")
            
        # Force exit if still running after 2 seconds
        def force_exit():
            logger.warning("Forcefully exiting after timeout")
            os._exit(1)
            
        threading.Timer(2.0, force_exit).start()
    
    # Set up signal handlers
    if os.name == 'nt':  # Windows
        try:
            import win32api
            win32api.SetConsoleCtrlHandler(lambda sig: shutdown(sig), True)
        except ImportError:
            print("Warning: pywin32 not installed, using basic keyboard interrupt handling")
            signal.signal(signal.SIGINT, shutdown)
    else:  # Unix
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, shutdown)

async def main():
    """Main entry point for the bot."""
    print("Starting Mamba2 Trading Bot with Mock MT5...")
    bot = Bot()
    setup_signal_handlers(bot)
    
    try:
        print("Initializing bot...")
        await bot.initialize()
        print("Bot initialized. Starting main loop...")
        await bot.run()
    except Exception as e:
        print(f"Bot error: {e}")
    finally:
        print("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
