"""Deterministic, offline historical replay primitives."""

from .broker import (
    AccountCurrencyConversionError,
    ClosedTrade,
    HistoricalBroker,
    SymbolExecutionMetadata,
)
from .data import (
    PRICE_BAR_COLUMNS,
    REQUIRED_BAR_COLUMNS,
    HistoricalDataError,
    canonicalize_bars,
    canonicalize_price_bars,
)
from .feed import ReplayFeed
from .mt5_dataset import (
    DatasetIntegrityError,
    LoadedHistoricalDataset,
    export_mt5_dataset,
    load_mt5_dataset,
)
from .runner import BacktestBrokerAdapter, BacktestResult, BacktestRunner

__all__ = [
    "HistoricalBroker",
    "AccountCurrencyConversionError",
    "ClosedTrade",
    "SymbolExecutionMetadata",
    "BacktestBrokerAdapter",
    "BacktestResult",
    "BacktestRunner",
    "HistoricalDataError",
    "PRICE_BAR_COLUMNS",
    "REQUIRED_BAR_COLUMNS",
    "ReplayFeed",
    "canonicalize_bars",
    "canonicalize_price_bars",
    "DatasetIntegrityError",
    "LoadedHistoricalDataset",
    "export_mt5_dataset",
    "load_mt5_dataset",
]
