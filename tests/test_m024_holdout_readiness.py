from __future__ import annotations

import pandas as pd
import pytest

from mamba2.backtest.m024_holdout_readiness import (
    M024_HOLDOUT_BLOCK_SIZE,
    M024_HOLDOUT_END_EXCLUSIVE_UTC,
    M024_HOLDOUT_START_UTC,
    M024_HOLDOUT_TRADING_DATES,
    _block_metadata,
)


def test_holdout_partition_is_exactly_frozen():
    assert M024_HOLDOUT_START_UTC == "2026-07-08T00:00:00Z"
    assert M024_HOLDOUT_END_EXCLUSIVE_UTC == "2026-09-25T00:00:00Z"
    assert M024_HOLDOUT_TRADING_DATES == 57
    assert M024_HOLDOUT_BLOCK_SIZE == 19


def test_holdout_blocks_are_three_fixed_19_date_chunks():
    dates = [
        date.date().isoformat()
        for date in pd.bdate_range("2026-07-01", periods=57, tz="UTC")
    ]
    blocks = _block_metadata(dates)

    assert [row["label"] for row in blocks] == ["H1", "H2", "H3"]
    assert [row["trading_dates"] for row in blocks] == [19, 19, 19]
    assert blocks[0]["first_date"] == dates[0]
    assert blocks[0]["last_date"] == dates[18]
    assert blocks[1]["first_date"] == dates[19]
    assert blocks[1]["last_date"] == dates[37]
    assert blocks[2]["first_date"] == dates[38]
    assert blocks[2]["last_date"] == dates[56]
    assert all(row["date_list_sha256"] for row in blocks)


def test_holdout_block_builder_refuses_any_other_date_count():
    dates = [
        date.date().isoformat()
        for date in pd.bdate_range("2026-07-01", periods=56, tz="UTC")
    ]
    with pytest.raises(ValueError, match="exactly 57"):
        _block_metadata(dates)


def test_readiness_module_has_no_economic_runtime_imports():
    import mamba2.backtest.m024_holdout_readiness as readiness

    namespace = readiness.__dict__
    forbidden = {
        "DiagnosticHistoricalBroker",
        "PortfolioBacktestRunner",
        "PositionManager",
        "ATRManager",
        "StochasticTripleTFStrategy",
        "build_baseline_report",
        "build_diagnostic_report",
    }
    assert forbidden.isdisjoint(namespace)
