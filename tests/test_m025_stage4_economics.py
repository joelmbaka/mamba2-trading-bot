"""M025 Stage-4 frozen economic machinery tests."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd
import pytest

from mamba2.backtest.m025_stage4_economics import (
    AQR_LABEL,
    H10_LABEL,
    H10_SYMBOLS,
    LRV_LABEL,
    _canonical_monthly_series,
    compare_monthly_returns,
    h10_tsmom_spot_proxy,
    locate_lrv_layout,
    summarize_monthly_returns,
)


def _prices(days: int = 520) -> pd.DataFrame:
    index = pd.date_range("2018-01-01", periods=days, freq="B", tz="UTC")
    step = np.arange(days, dtype=float)
    data = {}
    for offset, symbol in enumerate(H10_SYMBOLS):
        daily = 0.0002 + (offset + 1) * 1e-7 + np.sin(step / 17) * 0.00005
        data[symbol] = (1.0 + daily).cumprod()
    return pd.DataFrame(data, index=index)


def test_h10_proxy_uses_exact_23_series_and_reports_valid_counts():
    proxy, counts = h10_tsmom_spot_proxy(_prices())
    assert proxy.name == H10_LABEL
    assert not proxy.empty
    assert counts.index.equals(proxy.index)
    assert (counts > 0).all()
    assert (counts <= 23).all()


def test_h10_proxy_does_not_fill_missing_daily_observation():
    prices = _prices()
    gap_date = prices.index[300]
    prices.loc[gap_date, "JPY"] = np.nan

    daily = prices.pct_change(fill_method=None)
    next_date = prices.index[301]

    assert pd.isna(daily.loc[gap_date, "JPY"])
    assert pd.isna(daily.loc[next_date, "JPY"])


def test_h10_future_mutation_cannot_change_earlier_proxy_returns():
    prices = _prices(days=700)
    control, _ = h10_tsmom_spot_proxy(prices)

    mutated = prices.copy()
    cutoff = mutated.index[-40]
    mutated.loc[cutoff:, "JPY"] *= 1.50
    treatment, _ = h10_tsmom_spot_proxy(mutated)

    earlier = control.index < cutoff.to_period("M").to_timestamp("M").tz_localize("UTC")
    pd.testing.assert_series_equal(
        control.loc[earlier],
        treatment.reindex(control.index).loc[earlier],
    )


def test_monthly_summary_formulas_are_frozen():
    index = pd.date_range("2020-01-31", periods=4, freq="ME", tz="UTC")
    series = pd.Series([0.10, -0.05, 0.02, 0.03], index=index)

    result = summarize_monthly_returns(series, label="X")

    expected_mean = float(series.mean())
    expected_vol = math.sqrt(12.0) * float(series.std(ddof=1))
    wealth = (1.0 + series).cumprod()
    expected_dd = float((wealth / wealth.cummax() - 1.0).min())

    assert result["mean_monthly_return"] == pytest.approx(expected_mean)
    assert result["annualized_arithmetic_mean"] == pytest.approx(12 * expected_mean)
    assert result["annualized_volatility"] == pytest.approx(expected_vol)
    assert result["maximum_drawdown"] == pytest.approx(expected_dd)
    assert result["positive_month_fraction"] == pytest.approx(0.75)


def test_comparison_uses_only_zero_lag_common_months():
    index = pd.date_range("2020-01-31", periods=4, freq="ME", tz="UTC")
    proxy = pd.Series([0.01, 0.02, -0.01, 0.03], index=index)
    reference = pd.Series([0.02, 0.01, -0.02, 0.04], index=index)

    result = compare_monthly_returns(proxy, reference)

    joined = pd.concat([proxy, reference], axis=1)
    diff = proxy - reference
    assert result["common_observations"] == 4
    assert result["pearson_correlation"] == pytest.approx(
        float(joined.iloc[:, 0].corr(joined.iloc[:, 1]))
    )
    assert result["annualized_mean_return_difference"] == pytest.approx(
        12.0 * float(diff.mean())
    )
    assert result["annualized_tracking_error"] == pytest.approx(
        math.sqrt(12.0) * float(diff.std(ddof=1))
    )


@dataclass
class _Cell:
    value: object
    ctype: int
    xf_index: int = 0


class _Sheet:
    def __init__(self, name: str, rows: list[list[_Cell]]):
        self.name = name
        self._rows = rows
        self.nrows = len(rows)
        self.ncols = max(len(row) for row in rows)

    def cell(self, row: int, col: int):
        if col >= len(self._rows[row]):
            return _Cell("", 0)
        return self._rows[row][col]


class _Book:
    def __init__(self, sheets):
        self._sheets = {sheet.name: sheet for sheet in sheets}

    def sheet_names(self):
        return list(self._sheets)

    def sheet_by_name(self, name):
        return self._sheets[name]


def test_lrv_layout_selects_exact_all_currencies_net_sheet():
    filler = [_Cell("", 0) for _ in range(8)]
    header = [
        _Cell("Date", 1),
        _Cell("Portfolio1", 1),
        _Cell("Portfolio2", 1),
        _Cell("Portfolio3", 1),
        _Cell("Portfolio4", 1),
        _Cell("Portfolio5", 1),
        _Cell("Portfolio6", 1),
        _Cell("HML", 1),
    ]
    date_row = [
        _Cell(1.0, 3),
        *[_Cell(0.0, 2) for _ in range(7)],
    ]
    net = _Sheet("All currencies (net)", [filler, header, date_row, date_row, date_row])
    gross = _Sheet("All currencies", [filler, header, date_row, date_row, date_row])
    layout = locate_lrv_layout(_Book([gross, net]))

    assert layout.sheet_name == "All currencies (net)"
    assert layout.header_row == 1
    assert layout.date_col == 0
    assert layout.portfolio_cols == (1, 2, 3, 4, 5, 6)
    assert layout.hml_col == 7


def test_lrv_layout_refuses_gross_only_workbook():
    sheet = _Sheet("All currencies", [[_Cell("", 0)]])
    with pytest.raises(ValueError, match="All currencies \\(net\\)"):
        locate_lrv_layout(_Book([sheet]))


def test_canonical_monthly_series_refuses_duplicate_months():
    index = pd.DatetimeIndex([
        pd.Timestamp("2020-01-15", tz="UTC"),
        pd.Timestamp("2020-01-31", tz="UTC"),
    ])
    with pytest.raises(ValueError, match="duplicate calendar months"):
        _canonical_monthly_series(pd.Series([0.1, 0.2], index=index), name="X")
