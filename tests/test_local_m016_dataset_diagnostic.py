"""Temporary local-control diagnostic for M016 exported dataset coverage."""

import json
from pathlib import Path

import pytest

from mamba2.backtest.mt5_dataset import load_mt5_dataset


def test_report_m016_conversion_coverage():
    manifest = Path(
        "backtest_data/first-baseline-20260901-20260925/manifest.json"
    )
    if not manifest.exists():
        pytest.skip("M016 local dataset is not present")

    dataset = load_mt5_dataset(manifest)
    indexes = {
        symbol: set(frame.index)
        for symbol, frame in dataset.m1_bars.items()
    }
    usdjpy = indexes["USDJPY"]
    detail = {
        "rows": {
            symbol: len(indexes[symbol])
            for symbol in sorted(indexes)
        },
        "eurjpy_without_usdjpy": [
            str(ts) for ts in sorted(indexes["EURJPY"] - usdjpy)
        ],
        "gbpjpy_without_usdjpy": [
            str(ts) for ts in sorted(indexes["GBPJPY"] - usdjpy)
        ],
        "usdjpy_without_eurjpy": [
            str(ts) for ts in sorted(usdjpy - indexes["EURJPY"])
        ],
        "usdjpy_without_gbpjpy": [
            str(ts) for ts in sorted(usdjpy - indexes["GBPJPY"])
        ],
    }
    pytest.fail(json.dumps(detail, sort_keys=True))
