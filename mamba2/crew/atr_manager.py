"""
ATR Manager with improved thread-safe shutdown
"""
import asyncio
import logging
import threading
import time
from typing import Dict, Optional

import pandas as pd

from mamba2.crew.cache_manager import CacheManager
from mamba2.crew.logger import logger
import config

class ATRManager:
    def __init__(self, rate_fetcher):
        self.rate_fetcher = rate_fetcher
        self.atr_cache: Dict[str, Dict[str, float]] = {}
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()  # Thread safety
        self._shutdown_complete = threading.Event()
        self.cache = CacheManager("atr_cache.json")  # Initialize cache manager

    async def start(self):
        """Start the ATR manager in a dedicated thread."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                logger.warning("ATR manager is already running")
                return
                
            self._stop_event.clear()
            self._shutdown_complete.clear()
            self._thread = threading.Thread(
                target=self._run_thread_wrapper,
                daemon=True
            )
            self._thread.start()
            logger.info("ATR manager started")

    def _run_thread_wrapper(self):
        """Wrapper to run the async loop in a thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._run_loop())
        finally:
            loop.close()
            self._shutdown_complete.set()

    async def _run_loop(self):
        """Main ATR calculation loop with improved shutdown handling."""
        logger.info("Starting ATR calculation loop")
        
        # Wait for rate fetcher to initialize
        while not self.rate_fetcher.is_ready() and not self._stop_event.is_set():
            logger.debug("Waiting for rate fetcher to initialize...")
            await asyncio.sleep(1)
            
        logger.info(f"Rate fetcher ready: {self.rate_fetcher.is_ready()}")
        
        try:
            while not self._stop_event.is_set():
                for symbol in config.symbols:
                    for timeframe_str, _ in config.timeframes.items():
                        if self._stop_event.is_set():
                            break
                            
                        try:
                            rates = self.rate_fetcher.get_rates(symbol, timeframe_str)
                            if rates is None or rates.empty:
                                logger.warning(f"No rates available for {symbol} {timeframe_str}")
                                continue
                                
                            # Calculate ATR (simplified example)
                            atr = 0.001  # Mock ATR calculation
                            
                            # Store result
                            with self._lock:
                                if symbol not in self.atr_cache:
                                    self.atr_cache[symbol] = {}
                                self.atr_cache[symbol][timeframe_str] = atr
                                
                            # Determine decimal places based on currency pair
                            decimals = 3 if symbol.endswith('JPY') else 5
                            
                            logger.info(f"Calculated ATR for {symbol} {timeframe_str}: {atr:.{decimals}f}")
                            
                        except Exception as e:
                            logger.error(f"Error calculating ATR for {symbol} {timeframe_str}: {e}")
                            
                # Wait for next update interval
                if not self._stop_event.is_set():
                    await asyncio.sleep(config.atr_update_interval)
                    
        except Exception as e:
            logger.error(f"Error in ATR calculation loop: {e}")
            
        finally:
            logger.info("ATR calculation loop stopped")

    async def stop(self):
        """Stop the ATR manager and wait for completion."""
        with self._lock:
            if self._stop_event.is_set():
                return
                
            logger.info("Stopping ATR manager...")
            self._stop_event.set()
            
            if self._thread and self._thread.is_alive():
                # Wait for thread to complete
                try:
                    # Run blocking thread join in executor
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self._thread.join, 10)
                    
                    if self._thread.is_alive():
                        logger.warning("ATR manager thread did not stop cleanly")
                    else:
                        logger.info("ATR manager thread stopped")
                except Exception as e:
                    logger.error(f"Error stopping ATR manager thread: {e}")
            
            # Cleanup resources
            if hasattr(self, 'atr_cache'):
                self.atr_cache.clear()
            
            self._shutdown_complete.set()
            logger.info("ATR manager shutdown complete")

    def get_atr(self, symbol: str, timeframe: str) -> Optional[float]:
        """Get cached ATR value with thread safety."""
        with self._lock:
            return self.atr_cache.get(symbol, {}).get(timeframe)
