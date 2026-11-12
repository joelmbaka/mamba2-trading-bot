"""M025 literature-defined public FX benchmark machinery.

Stage 1 is intentionally pure and research-only: this module defines benchmark
signals, portfolio sorts, and data-sufficiency gates.  It does not run M025
historical economics or access MT5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


MOP_TSMOM_LOOKBACK_MONTHS = 12
MOP_TSMOM_HOLD_MONTHS = 1
MOP_TSMOM_TARGET_VOL = 0.40
MOP_TRADING_DAYS = 261
MOP_EWMA_DELTA = 60.0 / 61.0

MSSS_FORMATION_MONTHS = (1, 6, 12)
MSSS_HOLD_MONTHS = 1
FX_PORTFOLIO_COUNT = 6
MIN_CROSS_SECTION_CURRENCIES = 12
MIN_EVALUATION_MONTHS = 60


@dataclass(frozen=True)
class BenchmarkDataAudit:
    """Mechanical eligibility result for one benchmark input panel."""

    eligible: bool
    reasons: tuple[str, ...]
    observations: int
    eligible_observations: int


@dataclass(frozen=True)
class BenchmarkWeights:
    """Monthly benchmark weights plus an explicit fidelity label."""

    label: str
    weights: pd.DataFrame


@dataclass(frozen=True)
class MambaComparatorSnapshot:
    """M020-D comparator frozen before M023 completes."""

    stochastic: tuple[int, int, int] = (21, 7, 7)
    boundaries: tuple[float, float] = (20.0, 80.0)
    ema_period: int = 7
    atr_period: int = 14
    atr_timeframe: str = "M5"
    atr_sl_multiplier: float = 1.0
    atr_tp_multiplier: float = 2.0
    decision_spread_max_points: float = 10.0
    all_hours: bool = True
    sides: tuple[str, str] = ("BUY", "SELL")


MAMBA_M020D_SNAPSHOT = MambaComparatorSnapshot()


def _validate_frame(frame: pd.DataFrame, *, name: str) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame")
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError(f"{name} must use a DatetimeIndex")
    if frame.index.has_duplicates:
        raise ValueError(f"{name} index must be unique")
    if not frame.index.is_monotonic_increasing:
        frame = frame.sort_index()
    if not frame.columns.is_unique:
        raise ValueError(f"{name} columns must be unique")
    return frame.astype(float)


def ewma_ex_ante_volatility(daily_returns: pd.DataFrame) -> pd.DataFrame:
    """MOP-style annualized ex-ante volatility using information through t-1.

    The paper's exponentially weighted daily variance uses delta=60/61, giving
    a 60-day center of mass, and annualizes with 261 trading days. Pandas'
    adjusted EWM variance is the finite-history normalized implementation of
    that weighting scheme. The final shift enforces the t-1 information set.
    """

    returns = _validate_frame(daily_returns, name="daily_returns")
    alpha = 1.0 - MOP_EWMA_DELTA
    lagged_variance = (
        returns.ewm(alpha=alpha, adjust=True).var(bias=True).shift(1)
    )
    return np.sqrt(lagged_variance * MOP_TRADING_DAYS)


def _monthly_compounded_returns(daily_returns: pd.DataFrame) -> pd.DataFrame:
    return (1.0 + daily_returns).resample("ME").prod(min_count=1) - 1.0


def _longest_consecutive_month_run(mask: pd.Series) -> int:
    """Return the longest consecutive calendar-month run with a true gate."""

    if not isinstance(mask.index, pd.DatetimeIndex):
        raise TypeError("monthly eligibility mask must use a DatetimeIndex")
    selected = [
        int(timestamp.year) * 12 + int(timestamp.month)
        for timestamp, value in mask.items()
        if bool(value)
    ]
    if not selected:
        return 0

    longest = 1
    current = 1
    for previous, value in zip(selected, selected[1:]):
        if value == previous + 1:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    return longest


def _require_one_row_per_month(frame: pd.DataFrame, *, name: str) -> None:
    keys = [
        int(timestamp.year) * 12 + int(timestamp.month)
        for timestamp in frame.index
    ]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{name} must contain at most one row per calendar month")


def _currency_momentum_formation_returns(
    monthly_log_excess_returns: pd.DataFrame,
    *,
    formation_months: int,
) -> pd.DataFrame:
    """Paper-faithful cumulative log excess return over the formation window."""

    return monthly_log_excess_returns.rolling(
        formation_months,
        min_periods=formation_months,
    ).sum()


def tsmom_weights_from_excess_returns(
    daily_excess_returns: pd.DataFrame,
) -> BenchmarkWeights:
    """Build frozen MOP 12/1 monthly weights from a daily excess-return panel."""

    returns = _validate_frame(
        daily_excess_returns,
        name="daily_excess_returns",
    )
    monthly = _monthly_compounded_returns(returns)
    trailing = (
        (1.0 + monthly)
        .rolling(
            MOP_TSMOM_LOOKBACK_MONTHS,
            min_periods=MOP_TSMOM_LOOKBACK_MONTHS,
        )
        .apply(np.prod, raw=True)
        - 1.0
    )
    daily_vol = ewma_ex_ante_volatility(returns)
    monthly_vol = daily_vol.resample("ME").last().reindex(trailing.index)
    valid_vol = monthly_vol.where(monthly_vol > 0)
    formation_weights = np.sign(trailing) * (
        MOP_TSMOM_TARGET_VOL / valid_vol
    )
    # A signal formed at month-end t earns the return from t to t+1.
    # Shift once so a weights row can never be applied to its formation month.
    weights = formation_weights.shift(1)
    return BenchmarkWeights(label="MOP-TSMOM-12-1", weights=weights)


def tsmom_spot_proxy_weights(
    daily_spot_prices: pd.DataFrame,
) -> BenchmarkWeights:
    """Build an explicitly labelled spot-price proxy for MOP TSMOM.

    This helper exists to prevent price-only research from being silently
    described as a publication-faithful futures/forward excess-return replay.
    """

    prices = _validate_frame(
        daily_spot_prices,
        name="daily_spot_prices",
    )
    if (prices <= 0).any().any():
        raise ValueError("daily_spot_prices must be positive")
    returns = prices.pct_change(fill_method=None)
    result = tsmom_weights_from_excess_returns(returns)
    return BenchmarkWeights(
        label="TSMOM SPOT PROXY",
        weights=result.weights,
    )


def six_portfolio_members(
    signal: pd.Series,
    *,
    minimum_currencies: int = MIN_CROSS_SECTION_CURRENCIES,
) -> tuple[tuple[str, ...], ...]:
    """Deterministically split a currency cross-section into six rank buckets."""

    clean = signal.dropna().astype(float)
    if len(clean) < minimum_currencies:
        raise ValueError(
            f"at least {minimum_currencies} currencies are required; "
            f"got {len(clean)}"
        )

    ordered = sorted(
        clean.items(),
        key=lambda item: (item[1], str(item[0])),
    )
    labels = [str(label) for label, _ in ordered]
    split = np.array_split(
        np.asarray(labels, dtype=object),
        FX_PORTFOLIO_COUNT,
    )
    return tuple(
        tuple(str(value) for value in group.tolist())
        for group in split
    )


def _extreme_portfolio_weights(signal_table: pd.DataFrame) -> pd.DataFrame:
    table = _validate_frame(signal_table, name="signal_table")
    out = pd.DataFrame(
        0.0,
        index=table.index,
        columns=table.columns,
    )

    for timestamp, row in table.iterrows():
        try:
            portfolios = six_portfolio_members(row)
        except ValueError:
            out.loc[timestamp, :] = np.nan
            continue

        low, high = portfolios[0], portfolios[-1]
        out.loc[timestamp, :] = 0.0
        out.loc[timestamp, list(low)] = -1.0 / len(low)
        out.loc[timestamp, list(high)] = 1.0 / len(high)

    return out


def currency_momentum_weights(
    monthly_excess_returns: pd.DataFrame,
    *,
    formation_months: int,
) -> BenchmarkWeights:
    """Build MSSS high-minus-low weights from monthly log excess returns.

    Menkhoff et al. define currency excess returns in logs. Multi-month
    formation returns therefore aggregate additively across the formation
    window rather than by arithmetic-return compounding.
    """

    if formation_months not in MSSS_FORMATION_MONTHS:
        raise ValueError(
            "formation_months must be one of "
            f"{MSSS_FORMATION_MONTHS}"
        )

    returns = _validate_frame(
        monthly_excess_returns,
        name="monthly_excess_returns",
    )
    _require_one_row_per_month(returns, name="monthly_excess_returns")
    trailing = _currency_momentum_formation_returns(
        returns,
        formation_months=formation_months,
    )
    formation_weights = _extreme_portfolio_weights(trailing)
    # Month-end ranking at t is held during t+1.
    weights = formation_weights.shift(1)
    return BenchmarkWeights(
        label=f"MSSS-MOM({formation_months},1)",
        weights=weights,
    )


def carry_weights(
    monthly_carry_signal: pd.DataFrame,
) -> BenchmarkWeights:
    """Build six-portfolio HML-FX carry weights from an observed carry signal."""

    signal = _validate_frame(
        monthly_carry_signal,
        name="monthly_carry_signal",
    )
    _require_one_row_per_month(signal, name="monthly_carry_signal")
    formation_weights = _extreme_portfolio_weights(signal)
    # Month-end carry sort at t is held during t+1.
    return BenchmarkWeights(
        label="HML-FX-CARRY",
        weights=formation_weights.shift(1),
    )


def audit_tsmom_history(
    daily_returns: pd.DataFrame,
    *,
    minimum_evaluation_years: int = 5,
) -> BenchmarkDataAudit:
    """Require five evaluation years after the frozen 12-month warmup."""

    returns = _validate_frame(
        daily_returns,
        name="daily_returns",
    )
    observations = len(returns)
    if observations == 0:
        return BenchmarkDataAudit(
            eligible=False,
            reasons=("daily history is empty",),
            observations=0,
            eligible_observations=0,
        )

    monthly_presence = returns.notna().resample("ME").sum() > 0
    required_total = (
        minimum_evaluation_years * 12
        + MOP_TSMOM_LOOKBACK_MONTHS
    )
    reasons: list[str] = []

    if returns.shape[1] == 0:
        reasons.append("TSMOM requires at least one instrument")
        minimum_run = 0
    else:
        per_instrument_runs = {
            str(column): _longest_consecutive_month_run(
                monthly_presence[column]
            )
            for column in monthly_presence.columns
        }
        minimum_run = min(per_instrument_runs.values(), default=0)
        failing = {
            column: run
            for column, run in per_instrument_runs.items()
            if run < required_total
        }
        if failing:
            reasons.append(
                "TSMOM requires at least "
                f"{required_total} consecutive usable months per instrument "
                f"(12-month warmup plus {minimum_evaluation_years} complete "
                f"evaluation years); got {failing}"
            )

    eligible_months = max(
        0,
        minimum_run - MOP_TSMOM_LOOKBACK_MONTHS,
    )
    return BenchmarkDataAudit(
        eligible=not reasons,
        reasons=tuple(reasons),
        observations=observations,
        eligible_observations=eligible_months,
    )


def audit_cross_sectional_history(
    monthly_excess_returns: pd.DataFrame,
    *,
    return_kind: Literal["excess-return", "spot-proxy"] = "excess-return",
    carry_signal: pd.DataFrame | None = None,
    require_carry: bool = False,
) -> BenchmarkDataAudit:
    """Audit MSSS/carry inputs before any economic calculation."""

    returns = _validate_frame(
        monthly_excess_returns,
        name="monthly_excess_returns",
    )
    _require_one_row_per_month(
        returns,
        name="monthly_excess_returns",
    )
    reasons: list[str] = []

    if return_kind != "excess-return":
        reasons.append(
            "cross-sectional momentum/carry requires observed currency "
            "excess returns; spot-only proxy is not publication-faithful"
        )

    if returns.shape[1] < MIN_CROSS_SECTION_CURRENCIES:
        reasons.append(
            f"at least {MIN_CROSS_SECTION_CURRENCIES} distinct currencies "
            f"are required; got {returns.shape[1]}"
        )

    eligible_mask = (
        returns.notna().sum(axis=1)
        >= MIN_CROSS_SECTION_CURRENCIES
    )

    if require_carry:
        if carry_signal is None:
            reasons.append(
                "carry requires observed forward discount/rate signal"
            )
            carry_eligible = pd.Series(
                False,
                index=returns.index,
            )
        else:
            carry = _validate_frame(
                carry_signal,
                name="carry_signal",
            )
            _require_one_row_per_month(carry, name="carry_signal")
            if (
                not carry.index.equals(returns.index)
                or set(carry.columns) != set(returns.columns)
            ):
                reasons.append(
                    "carry signal index/columns must match "
                    "excess-return panel"
                )
                carry_eligible = pd.Series(
                    False,
                    index=returns.index,
                )
            else:
                carry = carry.reindex(columns=returns.columns)
                carry_eligible = (
                    carry.notna().sum(axis=1)
                    >= MIN_CROSS_SECTION_CURRENCIES
                )

        eligible_mask = eligible_mask & carry_eligible

    consecutive_eligible_months = _longest_consecutive_month_run(
        eligible_mask
    )
    required = (
        MIN_EVALUATION_MONTHS
        + max(MSSS_FORMATION_MONTHS)
    )

    if consecutive_eligible_months < required:
        reasons.append(
            "cross-sectional benchmarks require at least "
            f"{required} consecutive eligible months including "
            "12-month warmup; "
            f"got longest run {consecutive_eligible_months}"
        )

    return BenchmarkDataAudit(
        eligible=not reasons,
        reasons=tuple(reasons),
        observations=len(returns),
        eligible_observations=consecutive_eligible_months,
    )
