import time
import threading
import pandas as pd
from typing import Dict, Optional, Union
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta, timezone

# Import from the same package
from .logger import logger as loguru_logger
import config

# Create a logger instance for this module
logger = loguru_logger.bind(module='rate_fetcher')

@dataclass
class RateData:
    """Container for rate data with metadata."""
    symbol: str
    timeframe: str
    rates: pd.DataFrame
    last_updated: float

class RatesFetcher(threading.Thread):
    """Thread that fetches and caches rate data for multiple symbols and timeframes."""
    
    def __init__(self, broker):
        """
        Initialize the rate fetcher thread.
        
        Args:
            broker: Broker connection instance
        """
        super().__init__(daemon=True, name="RateFetcherThread")
        self.broker = broker
        self.update_interval = config.rates_fetcher['update_interval']
        self.rates_count = config.rates_fetcher['rates_count']
        self._stop_event = threading.Event()
        self.rates_cache: Dict[str, RateData] = {}
        self._initial_fetch_complete = False
        self._initial_fetch_lock = threading.Lock()
        self._loop = None  # Store event loop reference
        
    def stop(self):
        """Signal the thread to stop and wait for cleanup."""
        if not self._stop_event.is_set():
            logger.info("Stopping rate fetcher thread...")
            self._stop_event.set()
            
            # Wait for thread to complete
            if self.is_alive():
                self.join(timeout=5)
                if self.is_alive():
                    logger.warning("Rate fetcher thread did not stop cleanly")
                else:
                    logger.info("Rate fetcher thread stopped")
        
        # Cleanup resources
        if hasattr(self, 'rates_cache'):
            self.rates_cache.clear()
        
    def _run_thread_wrapper(self):
        """Wrapper to run the async loop in a thread with proper cleanup."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._run_loop())
        except Exception as e:
            logger.error(f"Fatal error in rate fetcher thread: {e}")
        finally:
            if self._loop and not self._loop.is_closed():
                self._loop.close()
            self._loop = None
    
    def is_ready(self) -> bool:
        """Check if rate data has been loaded for all symbols and timeframes."""
        if not hasattr(self, 'rates_cache') or not self._initial_fetch_complete:
            return False
            
        # Check if we have data for all combinations
        expected_combinations = len(config.symbols) * len(config.timeframes)
        if len(self.rates_cache) != expected_combinations:
            logger.debug(f"Rate fetcher not ready. Have {len(self.rates_cache)}/{expected_combinations} rate combinations")
            return False
            
        # Verify all cached rates have sufficient data
        for symbol in config.symbols:
            for timeframe in config.timeframes.keys():
                cache_key = f"{symbol}_{timeframe}"
                if cache_key not in self.rates_cache:
                    logger.debug(f"Missing rate data for {symbol} {timeframe}")
                    return False
                rate_data = self.rates_cache[cache_key]
                if rate_data.rates.empty or len(rate_data.rates) < 200:  # Minimum 200 candles required
                    logger.debug(f"Insufficient data for {symbol} {timeframe} (got {len(rate_data.rates)} candles)")
                    return False
                    
        return True
    
    def get_rates(self, symbol: str, timeframe: Union[str, int]) -> Optional[pd.DataFrame]:
        """
        Get rates from cache.
        
        Args:
            symbol: Symbol to get rates for (e.g., 'EURUSD')
            timeframe: Timeframe to get rates for (e.g., 'M1' or 1)
        """
        # Normalize timeframe to string format (e.g., 1 -> 'M1')
        normalized_tf = f"M{timeframe}" if isinstance(timeframe, int) else timeframe
        cache_key = f"{symbol}_{normalized_tf}"
        if cache_key in self.rates_cache:
            return self.rates_cache[cache_key].rates
        return None
    
    def _fetch_rates(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Fetch rates from MT5."""
        try:
            
            # Validate timeframe exists in config
            if timeframe not in config.timeframes:
                valid_timeframes = ', '.join(config.timeframes.keys())
                logger.error(f"Invalid timeframe '{timeframe}'. Valid options: {valid_timeframes}")
                return None
                
            timeframe_minutes = config.timeframes[timeframe]
            
            # Fetch rates from broker
            rates = self.broker.copy_rates_from_pos(
                symbol=symbol,
                timeframe=timeframe_minutes,
                start_pos=1,
                count=self.rates_count
            )
            """
            if rates is not None and len(rates) > 0:
                last_candle = rates.iloc[-1] if hasattr(rates, 'iloc') else rates[-1]
                last_candle_time = datetime.fromtimestamp(last_candle['time'])
                logger.info(
                    f"Fetched rates - Symbol: {symbol}, Timeframe: {timeframe}, "
                    f"Last Candle - Time: {last_candle_time}, "
                    f"Open: {last_candle['open']}, High: {last_candle['high']}, "
                    f"Low: {last_candle['low']}, Close: {last_candle['close']}, "
                    f"Volume: {last_candle['tick_volume'] if 'tick_volume' in last_candle else last_candle.get('real_volume', 'N/A')}"
                )
            """
            if rates is None or len(rates) == 0:
                logger.error(f"No rates returned for {symbol} {timeframe}")
                return None
                            
            # Convert numpy array to DataFrame with proper column names
            # The mock broker returns: [time, open, high, low, close, tick_volume, spread, real_volume]
            column_names = ['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
            
            # Handle both numpy array and pandas DataFrame inputs
            if hasattr(rates, 'columns'):
                # Already a DataFrame with columns
                df = rates.copy()
            else:
                # Convert numpy array to DataFrame with proper column names
                df = pd.DataFrame(rates, columns=column_names)
            
            # Ensure we have the required columns
            required_columns = ['time', 'open', 'high', 'low', 'close']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"Missing required price columns in rates for {symbol} {timeframe}. "
                             f"Got columns: {df.columns.tolist()}")
                return None
            
            # Convert timestamp and set as index
            try:
                df['time'] = pd.to_datetime(df['time'], unit='s', errors='coerce')
                df = df.dropna(subset=['time'])
                df.set_index('time', inplace=True)
                
                # Ensure numeric columns are float
                for col in ['open', 'high', 'low', 'close']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Drop any rows with NaN values in price columns
                df = df.dropna(subset=['open', 'high', 'low', 'close'])
                
            except Exception as e:
                logger.error(f"Error processing rates for {symbol} {timeframe}: {str(e)}")
                return None
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {symbol} {timeframe}: {str(e)}")
            return None
    
    async def _run_loop(self):
        """Main thread loop."""
        logger.info("📈 Starting rate fetcher thread")
        
        try:
            # Align to the next whole minute
            if not hasattr(self, '_initial_delay_done'):
                import time
                now = time.time()
                next_run = (now // 60 + 1) * 60
                time.sleep(next_run - now)
                self._initial_delay_done = True

            # Initial fetch
            await self._update_all_rates()
            
            with self._initial_fetch_lock:
                self._initial_fetch_complete = True
            
            # Main update loop
            while not self._stop_event.is_set():
                try:
                    await self._update_all_rates()
                    await asyncio.sleep(self.update_interval)
                except Exception as e:
                    logger.error(f"Error in rate fetcher: {str(e)}")
                    await asyncio.sleep(5)  # Prevent tight loop on errors
            
        except Exception as e:
            logger.error(f"Fatal error in rate fetcher thread: {str(e)}")
            raise
    
    async def _update_all_rates(self):
        """Update all rates for all symbols and timeframes."""
        for symbol in config.symbols:
            for timeframe in config.timeframes.keys():
                await self._update_rates(symbol, timeframe)
    
    async def _update_rates(self, symbol: str, timeframe: str):
        """Update rates for a specific symbol and timeframe."""
        try:
            # Normalize timeframe to ensure consistent cache keys
            normalized_tf = f"M{timeframe}" if isinstance(timeframe, int) else timeframe
            cache_key = f"{symbol}_{normalized_tf}"
            
            # Always update the rates when this method is called
            rates = await asyncio.to_thread(self._fetch_rates, symbol, timeframe)
            if rates is not None:
                self.rates_cache[cache_key] = RateData(
                    symbol=symbol,
                    timeframe=normalized_tf,
                    rates=rates,
                    last_updated=time.time()
                )
            else:
                logger.warning(f"Failed to fetch rates for {cache_key}")
                    
        except Exception as e:
            logger.error(f"Error updating rates for {symbol}_{timeframe}: {str(e)}")
    
    def run(self):
        self._run_thread_wrapper()