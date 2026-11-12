"""M030 1Q: synthetic observer and public-indicator boundary contracts.

No historical replay, MT5, network, trading or file artifacts.
"""
from types import SimpleNamespace
from unittest.mock import Mock
import numpy as np
import pandas as pd
import pytest

from mamba2.backtest import m030_signal_observer
from mamba2.indicators.stochastic import get_stochastic
from mamba2.indicators.moving_average import get_moving_average
from mamba2.indicators.atr import get_atr


class StaticFetcher:
    def __init__(self, rates):
        self.rates = rates

    def get_rates(self, symbol, timeframe):
        return self.rates


class ObserverFeed:
    def __init__(self, *, bullish):
        self.current_time = pd.Timestamp("2026-09-10T12:01:00Z")
        self.m1 = pd.DataFrame({
            "open": [1.1000, 1.1000 if bullish else 1.1005],
            "high": [1.1005, 1.1007],
            "low": [1.0995, 1.0995],
            "close": [1.1002, 1.1005 if bullish else 1.1000],
        }, index=pd.date_range("2026-09-10T11:59:00Z", periods=2, freq="min"))
        self.m5 = pd.DataFrame({
            "open": [1.10], "high": [1.11], "low": [1.09], "close": [1.105],
        }, index=pd.DatetimeIndex(["2026-09-10T11:55:00Z"]))

    def get_visible_rates_for_indicator(self, symbol, timeframe):
        return self.m1 if timeframe == "M1" else self.m5


@pytest.mark.parametrize(
    ("direction", "older_extreme", "expected_signal"), [
        ("buy", 10.0, "BUY"),
        ("sell", 90.0, "SELL"),
    ])
@pytest.mark.parametrize("extreme_present", [True, False])
def test_real_observer_ten_candle_extreme_without_fresh_cross(
    monkeypatch, direction, older_extreme, expected_signal, extreme_present,
):
    monkeypatch.setattr(m030_signal_observer, "config", SimpleNamespace(
        ENABLE_RSI_CONDITION=False, ENABLE_TREND_CONDITION=False,
        use_higher_tf=False, stochastic_k_period=21,
        stochastic_d_period=7, stochastic_slowing=7,
    ))
    bullish = direction == "buy"
    if bullish:
        k = [older_extreme if extreme_present else 30.0] + [30.0] * 7 + [55.0, 60.0]
        d = [20.0] + [25.0] * 7 + [50.0, 50.0]
        m5k, m5d, ema = 60.0, 50.0, 1.1002
    else:
        k = [older_extreme if extreme_present else 70.0] + [70.0] * 7 + [45.0, 40.0]
        d = [80.0] + [75.0] * 7 + [50.0, 50.0]
        m5k, m5d, ema = 40.0, 50.0, 1.1003
    assert len(k) == 10
    assert (k[-2] > d[-2]) == (k[-1] > d[-1])

    def fake_stochastic(symbol, timeframe, **kwargs):
        if timeframe == "M1":
            assert kwargs["lookback_period"] == 10
            return {"k": pd.Series(k), "d": pd.Series(d)}
        return {"k": pd.Series([m5k]), "d": pd.Series([m5d])}

    monkeypatch.setattr(m030_signal_observer, "get_stochastic", fake_stochastic)
    monkeypatch.setattr(m030_signal_observer, "get_moving_average",
                        Mock(return_value=ema))
    monkeypatch.setattr(m030_signal_observer, "get_atr",
                        Mock(return_value=0.001))
    result = m030_signal_observer.observe_candidate(
        ObserverFeed(bullish=bullish), "EURUSD")
    assert result["signal"] == (expected_signal if extreme_present else "NONE")
    assert result["reason_or_error_code"] == (
        "ENTRY_CONDITIONS" if extreme_present else "NO_SIGNAL")


@pytest.mark.parametrize("visible", [34, 35])
def test_public_stochastic_21_7_7_first_eligible_bar(visible):
    x = np.arange(visible, dtype=float)
    close = 1.10 + 0.002 * np.sin(x / 4.0) + 0.0001 * x
    rates = pd.DataFrame({
        "open": close - 0.00003,
        "high": close + 0.0002,
        "low": close - 0.0002,
        "close": close,
    })
    result = get_stochastic(
        symbol="EURUSD", timeframe="M1", k_period=21, d_period=7,
        slowing=7, rate_fetcher=StaticFetcher(rates),
    )
    if visible == 34:
        assert result is None
    else:
        assert result is not None
        assert np.isfinite(result["k"].iloc[-1])
        assert np.isfinite(result["d"].iloc[-1])


def test_public_ema7_full_source_seed_differs_from_truncated_seed():
    # A deliberate discontinuity near the cutoff preserves an observable
    # first-close seeding difference (not a tautological >= 0 assertion).
    closes = [1.0] * 7 + [2.0] * 7
    def fetcher(values):
        return StaticFetcher(pd.DataFrame({"close": values}))
    current = closes[0]
    for price in closes[1:]:
        current = 0.25 * price + 0.75 * current
    complete = get_moving_average(
        "EURUSD", "M1", ma_period=7, ma_method="ema",
        rate_fetcher=fetcher(closes))
    truncated = get_moving_average(
        "EURUSD", "M1", ma_period=7, ma_method="ema",
        rate_fetcher=fetcher(closes[-7:]))
    assert complete == pytest.approx(current, abs=1e-12)
    assert complete == pytest.approx(
        pd.Series(closes).ewm(span=7, adjust=False).mean().iloc[-1])
    assert abs(complete - truncated) > 0.05


def test_public_atr14_14_vs_15_gap_sensitive_true_range():
    rows = []
    previous_close = None
    true_ranges = []
    for i in range(15):
        # At bar 8, the open gaps sharply above previous close.
        price = 1.10 + (0.012 if i >= 8 else 0.0) + 0.0001 * i
        high, low = price + 0.0003, price - 0.0003
        close = price + 0.0001
        rows.append(dict(open=price, high=high, low=low, close=close))
        tr = high - low
        if previous_close is not None:
            tr = max(tr, abs(high - previous_close),
                     abs(low - previous_close))
        true_ranges.append(tr)
        previous_close = close
    rates = pd.DataFrame(rows)
    assert get_atr("EURUSD", "M5", atr_period=14,
                   rate_fetcher=StaticFetcher(rates.iloc[:14])) == 0.0
    actual = get_atr("EURUSD", "M5", atr_period=14,
                     rate_fetcher=StaticFetcher(rates))
    assert true_ranges[8] > (rows[8]["high"] - rows[8]["low"])
    assert actual == pytest.approx(sum(true_ranges[1:15]) / 14, abs=1e-12)
