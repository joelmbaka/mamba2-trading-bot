"""M027 Stage-2 readiness/economic machinery tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mamba2.backtest.m027_carry_aware_tsmom import M027_CURRENCIES
from mamba2.backtest.m027_stage2 import (
    _month_list_sha,
    _summary,
    stage2_readiness,
)


def test_month_list_hash_is_order_sensitive():
    a = [
        pd.Timestamp("2020-01-31", tz="UTC"),
        pd.Timestamp("2020-02-29", tz="UTC"),
    ]
    b = list(reversed(a))
    assert _month_list_sha(a) != _month_list_sha(b)


def test_summary_uses_frozen_annualization():
    index = pd.date_range("2020-01-31", periods=4, freq="ME", tz="UTC")
    series = pd.Series([0.01, 0.02, -0.01, 0.03], index=index)
    result = _summary(series)

    assert result["annualized_arithmetic_mean"] == pytest.approx(
        12.0 * series.mean()
    )
    assert result["annualized_volatility"] == pytest.approx(
        np.sqrt(12.0) * series.std(ddof=1)
    )


def test_readiness_reports_no_return_values_or_economics():
    # Long synthetic panel with >=4 valid currencies. Values exist only to
    # establish finite/volatility availability; readiness must not report them.
    index = pd.date_range("2010-01-01", "2020-12-31", freq="B", tz="UTC")
    step = np.arange(len(index), dtype=float)
    data = {}
    for i, currency in enumerate(M027_CURRENCIES):
        if i < 5:
            data[currency] = 0.0001 + np.sin(step / (15 + i)) * 0.0002
        else:
            data[currency] = np.nan
    daily = pd.DataFrame(data, index=index)

    result = stage2_readiness(daily)

    assert result["months"] >= 60
    assert result["eligible_currency_count"]["min"] >= 4
    assert result["safety"]["return_values_reported"] is False
    assert result["safety"]["signal_signs_reported"] is False
    assert result["safety"]["portfolio_returns_computed"] is False
    assert "annualized_arithmetic_mean" not in result


def test_readiness_refuses_short_sample():
    index = pd.date_range("2019-01-01", "2020-12-31", freq="B", tz="UTC")
    daily = pd.DataFrame(0.0001, index=index, columns=M027_CURRENCIES)
    with pytest.raises(ValueError, match="at least 60 consecutive months"):
        stage2_readiness(daily)
