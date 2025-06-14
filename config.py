"""Configuration settings for the trading bot."""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class MT5Config:
    """MT5 connection configuration."""
    login: int = 93117167
    password: str = "B*8hZaYl"
    server: str = "MetaQuotes-Demo"
    path: str = ""  # Path to MT5 terminal executable
    timeout: int = 60000
    portable: bool = False

@dataclass
class Config:
    """Main configuration class."""
    # Broker settings
    use_mock: bool = False  # Set to False to use real MT5
    mt5: MT5Config = MT5Config()
    
    # Rate fetcher settings
    rates_count: int = 200  # Number of historical rates to fetch
    
    # Trading symbols configuration
    symbols: list = field(default_factory=lambda: ['EURUSD', 'EURJPY', 'GBPUSD'])
    
    # Trading settings
    timeframe: str = "M1"
    
    # Risk management
    risk_per_trade: float = 0.01  # 1% risk per trade
    
    # Position sizing
    position_size: float = 1.0  # 1 standard lot = 100,000 units
    leverage: int = 1000  # Account leverage
    
    # Position manager
    trailing_stop_pips: float = 20.0
    trailing_step_pips: float = 5.0
    atr_sl_multiplier: float = 1.0  # Stop loss multiplier for ATR
    atr_tp_multiplier: float = 2.0  # Take profit multiplier for ATR
    atr_period: int = 14  # ATR calculation period
    atr_timeframe: str = 'M5'  # MT5 timeframe for ATR calculation (M5 by default)
    atr_update_interval: int = 60  # Seconds between ATR recalculations

    # Trading interval (in seconds)
    trading_interval_seconds: int = 60  # 60 seconds
    
    # Default timeframes to monitor (in minutes)
    timeframes: dict = field(default_factory=lambda: {
        'M1': 1,
        'M5': 5,
        'M15': 15
    })
    # Number of candles to fetch for each timeframe
    candles_count: int = 200
    # Cache TTL in seconds (5 minutes)
    cache_ttl: int = 300

# Create a global config instance
config = Config()

# For backward compatibility, expose needed attributes directly
symbols = config.symbols
timeframes = config.timeframes
atr_period = config.atr_period
atr_timeframe = config.atr_timeframe
risk_per_trade = config.risk_per_trade
position_size = config.position_size
leverage = config.leverage
trailing_stop_pips = config.trailing_stop_pips
trailing_step_pips = config.trailing_step_pips
atr_sl_multiplier = config.atr_sl_multiplier
atr_tp_multiplier = config.atr_tp_multiplier
trading_interval_seconds = config.trading_interval_seconds
candles_count = config.candles_count
cache_ttl = config.cache_ttl
rates_count = config.rates_count
atr_update_interval = config.atr_update_interval

def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from a file if provided, otherwise return default."""
    if config_path:
        # TODO: Implement loading from file if needed
        pass
    return config
