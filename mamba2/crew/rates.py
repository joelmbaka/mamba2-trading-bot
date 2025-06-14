import time
import threading
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

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

class RateFetcher(threading.Thread):
    """Thread that fetches and caches rate data for multiple symbols and timeframes."""
    
    def __init__(self, broker, update_interval: int = 60):
        """
        Initialize the rate fetcher thread.
        
        Args:
            mt5: MT5 connection instance
            update_interval: How often to update rates (in seconds, default: 60)
        """
        super().__init__(daemon=True)
        self.broker = broker
        self.update_interval = update_interval
        self._stop_event = threading.Event()
        self.rates_cache: Dict[str, RateData] = {}
        self._initial_fetch_complete = False
        self._initial_fetch_lock = threading.Lock()
        
    def stop(self):
        """Signal the thread to stop."""
        self._stop_event.set()
    
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
                if rate_data.rates.empty or len(rate_data.rates) < 10:  # Minimum 10 candles required
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
            logger.debug(f"Checking cache for {symbol} {timeframe}")
            logger.debug(f"Fetching rates for {symbol} {timeframe}...")
            
            # Validate timeframe exists in config
            if timeframe not in config.timeframes:
                valid_timeframes = ', '.join(config.timeframes.keys())
                logger.error(f"Invalid timeframe '{timeframe}'. Valid options: {valid_timeframes}")
                return None
                
            timeframe_minutes = config.timeframes[timeframe]
            
            # Log rate fetching parameters
            logger.debug(f"Fetching {config.rates_count} rates for {symbol} {timeframe} ({timeframe_minutes} min)")
            
            # Fetch rates from broker
            rates = self.broker.copy_rates_from_pos(
                symbol=symbol,
                timeframe=timeframe_minutes,
                start_pos=1,
                count=config.rates_count
            )
            
            if rates is None or len(rates) == 0:
                logger.error(f"No rates returned for {symbol} {timeframe}")
                return None
                
            logger.debug(f"Received {len(rates)} rates for {symbol} {timeframe}")
            
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
            
            logger.debug(f"Processed rates DataFrame for {symbol} {timeframe} (shape: {df.shape})")
            logger.debug(f"Cached {len(df)} rates for {symbol} {timeframe}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {symbol} {timeframe}: {str(e)}")
            return None
    
    def _update_all_rates(self):
        """Update all rates for all symbols and timeframes."""
        for symbol in config.symbols:
            for timeframe in config.timeframes.keys():
                self._update_rates(symbol, timeframe)
    
    def _update_rates(self, symbol: str, timeframe: str):
        """Update rates for a specific symbol and timeframe."""
        try:
            # Normalize timeframe to ensure consistent cache keys
            normalized_tf = f"M{timeframe}" if isinstance(timeframe, int) else timeframe
            cache_key = f"{symbol}_{normalized_tf}"
            
            # Check if we need to update (cache expired or first time)
            now = time.time()
            needs_update = True
            
            if cache_key in self.rates_cache:
                last_updated = self.rates_cache[cache_key].last_updated
                needs_update = (now - last_updated) > config.cache_ttl
            
            if needs_update:
                logger.debug(f"Updating {symbol} {normalized_tf}...")
                rates = self._fetch_rates(symbol, timeframe)
                if rates is not None:
                    self.rates_cache[cache_key] = RateData(
                        symbol=symbol,
                        timeframe=normalized_tf,
                        rates=rates,
                        last_updated=now
                    )
                    logger.debug(f"Successfully cached {len(rates)} rates for {cache_key}")
                else:
                    logger.warning(f"Failed to fetch rates for {cache_key}")
                    
        except Exception as e:
            logger.error(f"Error updating rates for {symbol}_{timeframe}: {str(e)}")
    
    def run(self):
        """Main thread loop."""
        logger.info("📈 Starting rate fetcher thread")
        
        try:
            # Initial fetch
            logger.info("Performing initial rate fetch...")
            self._update_all_rates()
            
            with self._initial_fetch_lock:
                self._initial_fetch_complete = True
                logger.info("Initial rate fetch completed")
            
            # Main update loop
            while not self._stop_event.is_set():
                try:
                    self._update_all_rates()
                    time.sleep(self.update_interval)
                except Exception as e:
                    logger.error(f"Error in rate fetcher: {str(e)}")
                    time.sleep(5)  # Prevent tight loop on errors
            
            logger.info("Rate fetcher thread stopped")
        except Exception as e:
            logger.error(f"Fatal error in rate fetcher thread: {str(e)}")
            raise