"""M024 public FX benchmark Stage-1 tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mamba2.backtest.public_benchmarks import (
    FX_PORTFOLIO_COUNT,
    MAMBA_M020D_SNAPSHOT,
    MIN_CROSS_SECTION_CURRENCIES,
    MOP_EWMA_DELTA,
    MOP_TRADING_DAYS,
    MOP_TSMOM_HOLD_MONTHS,
    MOP_TSMOM_LOOKBACK_MONTHS,
    MOP_TSMOM_TARGET_VOL,
    MSSS_FORMATION_MONTHS,
    MSSS_HOLD_MONTHS,
    audit_cross_sectional_history,
    audit_tsmom_history,
    carry_weights,
    currency_momentum_weights,
    ewma_ex_ante_volatility,
    six_portfolio_members,
    tsmom_spot_proxy_weights,
    tsmom_weights_from_excess_returns,
)


def _daily_returns(
    start: str = "2015-01-01",
    end: str = "2022-01-01",
) -> pd.DataFrame:
    index = pd.date_range(start, end, freq="B", tz="UTC")
    step = np.arange(len(index), dtype=float)
    return pd.DataFrame(
        {
            "UP": 0.0002 + np.sin(step) * 0.0001,
            "DOWN": -0.0002 + np.cos(step) * 0.0001,
        },
        index=index,
    )


def _monthly_panel(
    currencies: int = 12,
    months: int = 80,
) -> pd.DataFrame:
    index = pd.date_range(
        "2010-01-31",
        periods=months,
        freq="ME",
        tz="UTC",
    )
    return pd.DataFrame(
        {
            f"C{i:02d}": np.linspace(
                0.001 * i,
                0.001 * i + 0.01,
                months,
            )
            for i in range(currencies)
        },
        index=index,
    )


def test_public_benchmark_constants_are_frozen():
    assert MOP_TSMOM_LOOKBACK_MONTHS == 12
    assert MOP_TSMOM_HOLD_MONTHS == 1
    assert MOP_TSMOM_TARGET_VOL == 0.40
    assert MOP_TRADING_DAYS == 261
    assert MOP_EWMA_DELTA == pytest.approx(60 / 61)
    assert MSSS_FORMATION_MONTHS == (1, 6, 12)
    assert MSSS_HOLD_MONTHS == 1
    assert FX_PORTFOLIO_COUNT == 6
    assert MIN_CROSS_SECTION_CURRENCIES == 12


def test_m020d_internal_comparator_is_frozen_before_m023():
    snapshot = MAMBA_M020D_SNAPSHOT
    assert snapshot.stochastic == (21, 7, 7)
    assert snapshot.boundaries == (20.0, 80.0)
    assert snapshot.ema_period == 7
    assert snapshot.atr_period == 14
    assert snapshot.atr_timeframe == "M5"
    assert snapshot.atr_sl_multiplier == 1.0
    assert snapshot.atr_tp_multiplier == 2.0
    assert snapshot.decision_spread_max_points == 10.0
    assert snapshot.all_hours is True
    assert snapshot.sides == ("BUY", "SELL")


def test_ex_ante_volatility_cannot_see_current_or_future_return():
    returns = _daily_returns()
    control = ewma_ex_ante_volatility(returns)

    mutated = returns.copy()
    mutated.iloc[-1, 0] = 0.50
    treatment = ewma_ex_ante_volatility(mutated)

    pd.testing.assert_series_equal(
        control["UP"],
        treatment["UP"],
    )


def test_tsmom_12_1_direction_and_label_are_fixed():
    returns = _daily_returns()
    result = tsmom_weights_from_excess_returns(returns)
    usable = result.weights.dropna(how="all")

    assert result.label == "MOP-TSMOM-12-1"
    assert not usable.empty
    assert (usable["UP"].dropna() > 0).all()
    assert (usable["DOWN"].dropna() < 0).all()


def test_spot_tsmom_is_never_labelled_publication_faithful():
    returns = _daily_returns()
    prices = (1.0 + returns).cumprod()
    result = tsmom_spot_proxy_weights(prices)

    assert result.label == "TSMOM SPOT PROXY"


def test_six_portfolio_sort_is_deterministic_and_balanced_for_12():
    signal = pd.Series(
        {f"C{i:02d}": float(i) for i in range(12)}
    )
    portfolios = six_portfolio_members(signal)

    assert len(portfolios) == 6
    assert all(len(bucket) == 2 for bucket in portfolios)
    assert portfolios[0] == ("C00", "C01")
    assert portfolios[-1] == ("C10", "C11")


def test_six_portfolio_sort_uses_name_as_deterministic_tiebreak():
    signal = pd.Series(
        {f"C{i:02d}": 1.0 for i in reversed(range(12))}
    )
    portfolios = six_portfolio_members(signal)

    assert portfolios[0] == ("C00", "C01")
    assert portfolios[-1] == ("C10", "C11")


@pytest.mark.parametrize("formation", (1, 6, 12))
def test_currency_momentum_long_high_short_low(formation):
    panel = _monthly_panel()
    result = currency_momentum_weights(
        panel,
        formation_months=formation,
    )
    row = result.weights.dropna(how="all").iloc[-1]

    assert result.label == f"MSSS-MOM({formation},1)"
    assert row[["C00", "C01"]].sum() == pytest.approx(-1.0)
    assert row[["C10", "C11"]].sum() == pytest.approx(1.0)
    assert row.sum() == pytest.approx(0.0)


def test_currency_momentum_rejects_unfrozen_formation_horizon():
    with pytest.raises(ValueError, match="formation_months"):
        currency_momentum_weights(
            _monthly_panel(),
            formation_months=3,
        )


def test_carry_long_high_short_low():
    signal = _monthly_panel()
    result = carry_weights(signal)
    row = result.weights.iloc[-1]

    assert result.label == "HML-FX-CARRY"
    assert row[["C00", "C01"]].sum() == pytest.approx(-1.0)
    assert row[["C10", "C11"]].sum() == pytest.approx(1.0)


def test_current_five_symbol_universe_is_refused_for_cross_sectional_work():
    five = _monthly_panel(currencies=5)
    audit = audit_cross_sectional_history(five)

    assert audit.eligible is False
    assert any(
        "at least 12 distinct currencies" in reason
        for reason in audit.reasons
    )


def test_cross_sectional_spot_proxy_is_refused():
    audit = audit_cross_sectional_history(
        _monthly_panel(),
        return_kind="spot-proxy",
    )

    assert audit.eligible is False
    assert any(
        "spot-only proxy" in reason
        for reason in audit.reasons
    )


def test_carry_requires_observed_carry_signal():
    audit = audit_cross_sectional_history(
        _monthly_panel(),
        require_carry=True,
    )

    assert audit.eligible is False
    assert any(
        "forward discount/rate signal" in reason
        for reason in audit.reasons
    )


def test_cross_sectional_gate_passes_sufficient_synthetic_panel():
    audit = audit_cross_sectional_history(_monthly_panel())

    assert audit.eligible is True
    assert audit.reasons == ()


def test_tsmom_gate_requires_five_years_after_twelve_month_warmup():
    short = _daily_returns("2020-01-01", "2024-12-31")
    long = _daily_returns("2015-01-01", "2022-01-01")

    assert audit_tsmom_history(short).eligible is False
    assert audit_tsmom_history(long).eligible is True
