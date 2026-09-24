"""
ATR Manager with improved thread-safe shutdown
"""
import asyncio
import threading
from typing import Dict, Optional

from mamba2.crew.cache_manager import CacheManager
from mamba2.crew.logger import logger
import config
from mamba2.indicators.atr import get_atr

class ATRManager:
    def __init__(self, rate_fetcher):
        self.rate_fetcher = rate_fetcher
        self.atr_cache: Dict[str, Dict[str, float]] = {}
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()  # Thread safety
        self._shutdown_complete = threading.Event()
        self.cache = CacheManager("atr_cache.json")  # Initialize cache manager
        self._initialized = False  # Track initialization status

    def is_ready(self):
        """Check if ATR manager has initialized and has data."""
        with self._lock:
            return self._initialized and bool(self.atr_cache)

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

    def refresh_once(self) -> int:
        """Refresh the ATR cache once from the currently visible rate data.

        The live thread calls this method on its normal cadence. Deterministic
        backtests can call the same production calculation once per replay
        boundary without introducing wall-clock sleeps or background threads.
        """

        updated = 0
        for symbol in config.symbols:
            timeframe_str = config.atr_timeframe
            try:
                rates = self.rate_fetcher.get_rates(symbol, timeframe_str)
                if rates is None or rates.empty:
                    continue

                atr = get_atr(
                    symbol=symbol,
                    timeframe=timeframe_str,
                    atr_period=config.atr_period,
                    rate_fetcher=self.rate_fetcher,
                )
                if atr is None:
                    continue

                with self._lock:
                    if symbol not in self.atr_cache:
                        self.atr_cache[symbol] = {}
                    self.atr_cache[symbol][timeframe_str] = atr
                    self._initialized = True
                updated += 1
            except Exception as e:
                logger.error(
                    f"Error calculating ATR for {symbol} {timeframe_str}: {e}"
                )
        return updated

    async def _run_loop(self):
        """Main ATR calculation loop with improved shutdown handling."""

        while not self.rate_fetcher.is_ready() and not self._stop_event.is_set():
            await asyncio.sleep(1)

        try:
            while not self._stop_event.is_set():
                self.refresh_once()

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
