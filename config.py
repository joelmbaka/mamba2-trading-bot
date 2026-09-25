"""Configuration settings for the trading bot."""

from dataclasses import dataclass, field
import os
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


def _env_int(name: str, default: int | None = None) -> int | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class MT5Config:
    """MT5 connection configuration sourced from environment variables."""

    login: Optional[int] = field(
        default_factory=lambda: _env_int("MAMBA_MT5_LOGIN")
    )
    password: str = field(
        default_factory=lambda: os.getenv("MAMBA_MT5_PASSWORD", "")
    )
    server: str = field(
        default_factory=lambda: os.getenv("MAMBA_MT5_SERVER", "")
    )
    path: str = field(
        default_factory=lambda: os.getenv("MAMBA_MT5_PATH", "")
    )
    timeout: int = field(
        default_factory=lambda: _env_int("MAMBA_MT5_TIMEOUT", 60000) or 60000
    )
    portable: bool = field(
        default_factory=lambda: _env_bool("MAMBA_MT5_PORTABLE", False)
    )


@dataclass
class Config:
    """Main configuration class."""

    use_mock: bool = False
    mt5: MT5Config = field(default_factory=MT5Config)

    use_higher_tf: bool = False
    ENABLE_TREND_CONDITION = False
    ENABLE_RSI_CONDITION = False

    symbols: list = field(
        default_factory=lambda: [
            "EURUSD",
            "EURJPY",
            "GBPUSD",
            "GBPJPY",
            "USDJPY",
        ]
    )

    timeframe: str = "M1"
    position_size: float = 0.1
    leverage: int = 1000

    atr_sl_multiplier: float = 1.0
    atr_tp_multiplier: float = 2.0
    atr_period: int = 14
    atr_timeframe: str = "M5"
    atr_update_interval: int = 30

    trading_interval_seconds: int = 30

    stochastic_timeframes: dict = field(
        default_factory=lambda: {
            "higher": "M15",
            "trading": "M5",
            "entry": "M1",
        }
    )
    # These values match the production stochastic calculation that has been
    # in use since the LTS strategy revision. Keep them explicit so config and
    # runtime behavior cannot silently diverge.
    stochastic_k_period: int = 21
    stochastic_d_period: int = 7
    stochastic_slowing: int = 7

    timeframes: dict = field(
        default_factory=lambda: {
            "M1": 1,
            "M5": 5,
            "M15": 15,
        }
    )

    cache_ttl: int = 300

    rates_fetcher: dict = field(
        default_factory=lambda: {
            "update_interval": 30,
            "rates_count": 200,
        }
    )

    analytics_config: dict = field(
        default_factory=lambda: {
            "enable_analytics": True,
            "analysis_lookback_period": 180,
        }
    )


config = Config()

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
stochastic_d_period = config.stochastic_d_period
stochastic_slowing = config.stochastic_slowing
rates_fetcher = config.rates_fetcher
analytics_config = config.analytics_config
ENABLE_TREND_CONDITION = config.ENABLE_TREND_CONDITION
ENABLE_RSI_CONDITION = config.ENABLE_RSI_CONDITION

RUN_TRADER = False


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from a file if provided, otherwise return default."""
    if config_path:
        pass
    return config
