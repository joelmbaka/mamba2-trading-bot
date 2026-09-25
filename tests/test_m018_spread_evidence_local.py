"""TEMPORARY local M018 spread-tail evidence extraction."""

import json
from pathlib import Path

import pandas as pd
import pytest

from mamba2.backtest.mt5_dataset import load_mt5_dataset


MANIFEST = Path(
    "backtest_data/first-baseline-20260901-20260925/manifest.json"
)

CASES = {
    "EURUSD": "2026-09-03T00:01:00Z",
    "GBPUSD": "2026-09-03T00:36:00Z",
    "EURJPY": "2026-09-14T00:01:00Z",
    "USDJPY": "2026-09-08T00:01:00Z",
    "GBPJPY": "2026-09-24T00:28:00Z",
}


def test_surface_spread_tail_source_evidence():
    if not MANIFEST.is_file():
        pytest.skip("accepted local dataset is unavailable")
    dataset = load_mt5_dataset(MANIFEST)
    evidence = {}

    for symbol, value in CASES.items():
        ts = pd.Timestamp(value)
        bid = dataset.m1_bars[symbol]
        ask = dataset.ask_m1_bars[symbol]
        point = dataset.symbol_metadata[symbol].point_size
        row = bid.loc[ts]
        ask_row = ask.loc[ts]
        window = []
        for stamp in bid.loc[
            ts - pd.Timedelta(minutes=2):ts + pd.Timedelta(minutes=2)
        ].index:
            if stamp not in ask.index:
                continue
            b = bid.loc[stamp]
            a = ask.loc[stamp]
            window.append(
                {
                    "time": stamp.isoformat(),
                    "bid_open": float(b["open"]),
                    "ask_open": float(a["open"]),
                    "open_spread_points": round(
                        (float(a["open"]) - float(b["open"])) / point,
                        6,
                    ),
                    "bid_close": float(b["close"]),
                    "ask_close": float(a["close"]),
                    "close_spread_points": round(
                        (float(a["close"]) - float(b["close"])) / point,
                        6,
                    ),
                    "m1_spread_field": float(b["spread"]),
                }
            )
        evidence[symbol] = {
            "time": value,
            "point_size": point,
            "bid_row": {
                k: float(row[k])
                for k in ("open", "high", "low", "close", "spread")
            },
            "ask_row": {
                k: float(ask_row[k])
                for k in ("open", "high", "low", "close")
            },
            "open_spread_points": round(
                (float(ask_row["open"]) - float(row["open"])) / point,
                6,
            ),
            "close_spread_points": round(
                (float(ask_row["close"]) - float(row["close"])) / point,
                6,
            ),
            "window": window,
        }

    assert False, "SPREAD_SOURCE_EVIDENCE=" + json.dumps(
        evidence,
        sort_keys=True,
        separators=(",", ":"),
    )
