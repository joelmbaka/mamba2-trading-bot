"""Deterministic, offline historical replay primitives."""

from .broker import ClosedTrade, HistoricalBroker, SymbolExecutionMetadata
from .data import REQUIRED_BAR_COLUMNS, HistoricalDataError, canonicalize_bars
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
    "ClosedTrade",
    "SymbolExecutionMetadata",
    "BacktestBrokerAdapter",
    "BacktestResult",
    "BacktestRunner",
    "HistoricalDataError",
    "REQUIRED_BAR_COLUMNS",
    "ReplayFeed",
    "canonicalize_bars",
    "DatasetIntegrityError",
    "LoadedHistoricalDataset",
    "export_mt5_dataset",
    "load_mt5_dataset",
]
