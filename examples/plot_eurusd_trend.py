"""Download recent 5-minute EURUSD data and plot a trend line.

Usage (inside the project root):
    # Activate your virtual-env first
    pip install yfinance matplotlib pandas numpy
    python examples/plot_eurusd_trend.py

The script saves the chart to ``eurusd_trend.png`` in the current directory.
"""
from __future__ import annotations

import sys
from datetime import datetime

import pandas as pd
import numpy as np

try:
    import yfinance as yf  # type: ignore
except ImportError:
    sys.exit("Please install yfinance first: pip install yfinance")

from mamba2.indicators.trend_line import plot_trend_line

SYMBOL = "EURUSD"  # yfinance ticker suffix added below
TF = "M5"          # 5-minute timeframe – for labelling only
LOOKBACK = 200      # bars used in regression
SAVE_PATH = "eurusd_trend.png"


def fetch_eurusd_5m(period: str = "2d") -> pd.DataFrame:
    """Fetch 5-minute EURUSD rates via yfinance and return DataFrame.

    The returned DataFrame has lowercase OHLC columns compatible with
    ``plot_trend_line`` (open/high/low/close) and a DateTimeIndex.
    """
    pair_ticker = "EURUSD=X"
    df: pd.DataFrame = yf.download(pair_ticker, interval="5m", period=period, progress=False)
    if df.empty:
        raise RuntimeError("No data fetched from yfinance – check internet connection")
    # yfinance column names are capitalised; rename & keep only OHLC
    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
    })
    return df[["open", "high", "low", "close"]]


class YFinanceFetcher:
    """Adapter that exposes the RateFetcher API (get_rates)."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def get_rates(self, symbol: str, timeframe: str):  # noqa: D401  (simple func)
        return self._df.copy()


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Downloading EURUSD 5-minute data …")
    data = fetch_eurusd_5m()
    print(f"Fetched {len(data)} bars.\nCalculating trend line and saving chart …")

    fetcher = YFinanceFetcher(data)
    fig = plot_trend_line(fetcher, symbol=SYMBOL, timeframe=TF, lookback=LOOKBACK, save_path=SAVE_PATH)
    if fig is None:
        sys.exit("Could not plot – see previous errors above.")

    print(f"Chart saved to {SAVE_PATH}")


if __name__ == "__main__":
    main()
