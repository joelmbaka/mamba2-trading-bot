"""Configuration settings for the trading bot."""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class MT5Config:
    """MT5 connection configuration."""
    login: int = 5037284070
    password: str = "UiRf!a8q"
    server: str = "MetaQuotes-Demo"
    path: str = ""  # Path to MT5 terminal executable
    timeout: int = 60000
    portable: bool = False
    """ Name     : echui nyamatonto
Type     : Forex Hedged USD
Server   : MetaQuotes-Demo
Login    : 5037284070
Password : UiRf!a8q
Investor : @sW4JdHo

    """

@dataclass
class Config:
    """Main configuration class."""
    # Broker settings
    use_mock: bool = False  # Set to False to use real MT5
    mt5: MT5Config = MT5Config()

    use_higher_tf: bool = False   
    ENABLE_TREND_CONDITION = False
    ENABLE_RSI_CONDITION = False
    
    # Trading symbols configuration
    symbols: list = field(default_factory=lambda: ['EURUSD', 'EURJPY', 'GBPUSD', 'GBPJPY', 'USDJPY'])
    
    # Trading settings
    timeframe: str = "M1"
    
    # Position sizing
    position_size: float = 0.1  # 1 standard lot = 100,000 units
    leverage: int = 1000  # Account leverage
    
    # Position manager

    atr_sl_multiplier: float = 1.0  # Stop loss multiplier for ATR (2:4 risk-reward ratio)
    atr_tp_multiplier: float = 2.0  # Take profit multiplier for ATR (2:4 risk-reward ratio)
    atr_period: int = 14  # ATR calculation period
    atr_timeframe: str = 'M5'  # MT5 timeframe for ATR calculation (M5 by default)
    atr_update_interval: int = 30  # Seconds between ATR recalculations

    # Trading interval (in seconds)
    trading_interval_seconds: int = 30  # 60 seconds
    
    # Stochastic strategy settings
    stochastic_timeframes: dict = field(default_factory=lambda: {"higher": "M15", "trading": "M5", "entry": "M1"})
    stochastic_k_period: int = 14
    
    # Default timeframes to monitor (in minutes)
    timeframes: dict = field(default_factory=lambda: {
        'M1': 1,
        'M5': 5,
        'M15': 15
    })

    # Cache TTL in seconds (5 minutes)
    cache_ttl: int = 300
    
    # Rates Fetcher Configuration
    rates_fetcher: dict = field(default_factory=lambda: {
        'update_interval': 30,  # How often to fetch new rates in seconds
        'rates_count': 200,      # Number of historical rates to fetch
    })

    # Analytics settings
    analytics_config: dict = field(default_factory=lambda: {
        'enable_analytics': True,  # Set to False to disable position analytics
        'analysis_lookback_period': 180  # Minutes of historical data to show in charts
    })

# Create a global config instance
config = Config()

# For backward compatibility, expose needed attributes directly
use_mock = config.use_mock
mt5 = config.mt5
symbols = config.symbols
timeframes = config.timeframes
atr_period = config.atr_period
atr_timeframe = config.atr_timeframe
position_size = config.position_size
leverage = config.leverage
use_higher_tf = config.use_higher_tf
atr_sl_multiplier = config.atr_sl_multiplier
atr_tp_multiplier = config.atr_tp_multiplier
trading_interval_seconds = config.trading_interval_seconds
cache_ttl = config.cache_ttl
atr_update_interval = config.atr_update_interval
stochastic_timeframes = config.stochastic_timeframes
stochastic_k_period = config.stochastic_k_period
rates_fetcher = config.rates_fetcher
analytics_config = config.analytics_config
ENABLE_TREND_CONDITION = config.ENABLE_TREND_CONDITION
ENABLE_RSI_CONDITION = config.ENABLE_RSI_CONDITION


RUN_TRADER = False  # Set to False to disable trader task

def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from a file if provided, otherwise return default."""
    if config_path:
        # TODO: Implement loading from file if needed
        pass
    return config

