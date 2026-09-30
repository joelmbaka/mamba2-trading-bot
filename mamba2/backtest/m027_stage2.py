"""M027 Stage-2 readiness and frozen economic machinery.

Readiness is metadata-only: it determines the evaluation calendar from the
already frozen Stage-1 panel and reports no return magnitudes or strategy
statistics. Economic execution is a separate function and must not be called
before the readiness month-list hash is frozen in milestone documentation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .m027_carry_aware_tsmom import (
    M027_CURRENCIES,
    M027_COST_LABEL,
    M027_EWMA_DELTA,
    M027_TARGET_VOL,
    M027_TRADING_DAYS,
)


M027_APPROX_SHA256 = (
    "c0f166957d8879ba05cdfeb457ab8874657cd72900528856d81563d786b4848e"
)
M027_EVALUATION_CAP = pd.Timestamp("2026-08-31", tz="UTC")
M027_MIN_ELIGIBLE_CURRENCIES = 4
M027_MIN_EVALUATION_MONTHS = 60
M027_FORMATION_MONTHS = 12
M027_LABEL = "CARRY-AWARE SPOT TSMOM — PUBLIC-DATA APPROXIMATION"
M027_FROZEN_MONTH_LIST_SHA256 = (
    "c5cda6bb68904213dc46aa338887c19e7575e31cba8ab816e44469b81a3b4b40"
)


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_frozen_approximate_returns(path: str | Path) -> pd.DataFrame:
    candidate = Path(path)
    observed = _sha256(candidate)
    if observed != M027_APPROX_SHA256:
        raise ValueError(f"M027 approximate-return SHA changed: {observed}")

    frame = pd.read_csv(candidate, parse_dates=["date"])
    if list(frame.columns) != ["date", *M027_CURRENCIES]:
        raise ValueError("M027 approximate-return columns changed")
    if frame["date"].duplicated().any():
        raise ValueError("M027 approximate-return dates are duplicated")

    frame = frame.set_index("date").sort_index().astype(float)
    index = pd.DatetimeIndex(frame.index)
    if index.tz is None:
        index = index.tz_localize("UTC")
    else:
        index = index.tz_convert("UTC")
    frame.index = index
    return frame


def _monthly_log_returns(daily: pd.DataFrame) -> pd.DataFrame:
    return daily.resample("ME").sum(min_count=1)


def _daily_ex_ante_volatility(daily: pd.DataFrame) -> pd.DataFrame:
    alpha = 1.0 - M027_EWMA_DELTA
    variance = daily.ewm(alpha=alpha, adjust=True).var(bias=True).shift(1)
    return np.sqrt(variance * M027_TRADING_DAYS)


def _monthly_formation_and_vol(
    daily: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    monthly_log = _monthly_log_returns(daily)
    formation = monthly_log.rolling(
        M027_FORMATION_MONTHS,
        min_periods=M027_FORMATION_MONTHS,
    ).sum()
    monthly_vol = (
        _daily_ex_ante_volatility(daily)
        .resample("ME")
        .last()
        .reindex(monthly_log.index)
    )
    return monthly_log, formation, monthly_vol


def _longest_consecutive_true_block(mask: pd.Series) -> list[pd.Timestamp]:
    months = [
        timestamp
        for timestamp, value in mask.items()
        if bool(value)
    ]
    if not months:
        return []

    blocks: list[list[pd.Timestamp]] = []
    current = [months[0]]
    for timestamp in months[1:]:
        previous = current[-1]
        expected = (
            previous.to_period("M") + 1
        ).to_timestamp("M").tz_localize("UTC")
        if timestamp == expected:
            current.append(timestamp)
        else:
            blocks.append(current)
            current = [timestamp]
    blocks.append(current)

    # Frozen tie break: latest equally-long block.
    return max(blocks, key=lambda block: (len(block), block[-1]))


def _month_list_sha(months: list[pd.Timestamp]) -> str:
    payload = "\n".join(timestamp.strftime("%Y-%m-%d") for timestamp in months)
    if payload:
        payload += "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stage2_readiness(daily: pd.DataFrame) -> dict[str, Any]:
    """Return only evaluation-calendar metadata, never economic values."""

    monthly_log, formation, monthly_vol = _monthly_formation_and_vol(daily)
    realized = monthly_log.shift(-1)

    formation_available = formation.notna()
    vol_available = np.isfinite(monthly_vol) & (monthly_vol > 0)
    # Formation at t is held in t+1, so shift availability once.
    formation_weight_available = (formation_available & vol_available).shift(1)
    realized_available = monthly_log.notna()

    eligible = formation_weight_available & realized_available
    eligible_counts = eligible.sum(axis=1).astype(int)

    mask = (
        (eligible_counts >= M027_MIN_ELIGIBLE_CURRENCIES)
        & (eligible_counts.index <= M027_EVALUATION_CAP)
    )
    months = _longest_consecutive_true_block(mask)
    if len(months) < M027_MIN_EVALUATION_MONTHS:
        raise ValueError(
            "M027 Stage-2 readiness requires at least "
            f"{M027_MIN_EVALUATION_MONTHS} consecutive months; got {len(months)}"
        )

    folds = np.array_split(np.asarray(months, dtype=object), 3)
    fold_lists = [
        [pd.Timestamp(value) for value in fold.tolist()]
        for fold in folds
    ]
    month_counts = eligible_counts.reindex(months)

    return {
        "ok": True,
        "first_month": months[0].strftime("%Y-%m-%d"),
        "last_month": months[-1].strftime("%Y-%m-%d"),
        "months": len(months),
        "month_list_sha256": _month_list_sha(months),
        "folds": [
            {
                "name": f"F{index + 1}",
                "first_month": values[0].strftime("%Y-%m-%d"),
                "last_month": values[-1].strftime("%Y-%m-%d"),
                "months": len(values),
                "month_list_sha256": _month_list_sha(values),
            }
            for index, values in enumerate(fold_lists)
        ],
        "eligible_currency_count": {
            "min": int(month_counts.min()),
            "max": int(month_counts.max()),
            "median": float(month_counts.median()),
        },
        "evaluation_cap": M027_EVALUATION_CAP.strftime("%Y-%m-%d"),
        "minimum_eligible_currencies": M027_MIN_ELIGIBLE_CURRENCIES,
        "minimum_evaluation_months": M027_MIN_EVALUATION_MONTHS,
        "safety": {
            "return_values_reported": False,
            "signal_signs_reported": False,
            "portfolio_returns_computed": False,
            "economic_summary_computed": False,
        },
    }


def _maximum_drawdown(monthly_return: pd.Series) -> float:
    wealth = (1.0 + monthly_return).cumprod()
    return float((wealth / wealth.cummax() - 1.0).min())


def _summary(series: pd.Series) -> dict[str, Any]:
    clean = series.dropna().astype(float)
    if clean.empty:
        raise ValueError("cannot summarize empty M027 return series")
    mean_monthly = float(clean.mean())
    annualized_mean = 12.0 * mean_monthly
    annualized_vol = math.sqrt(12.0) * float(clean.std(ddof=1))
    sharpe = (
        annualized_mean / annualized_vol
        if annualized_vol > 0
        else float("nan")
    )
    return {
        "observations": int(len(clean)),
        "first_month": clean.index.min().strftime("%Y-%m-%d"),
        "last_month": clean.index.max().strftime("%Y-%m-%d"),
        "mean_monthly_return": mean_monthly,
        "annualized_arithmetic_mean": annualized_mean,
        "annualized_volatility": annualized_vol,
        "annualized_sharpe": sharpe,
        "maximum_drawdown": _maximum_drawdown(clean),
        "positive_month_fraction": float((clean > 0).mean()),
        "terminal_cumulative_wealth": float((1.0 + clean).prod()),
    }


def stage2_economics(
    daily: pd.DataFrame,
    *,
    expected_month_list_sha256: str = M027_FROZEN_MONTH_LIST_SHA256,
) -> dict[str, Any]:
    """Run the frozen M027 Stage-2 portfolio once readiness is frozen."""

    readiness = stage2_readiness(daily)
    if readiness["month_list_sha256"] != expected_month_list_sha256:
        raise ValueError("M027 frozen evaluation month-list SHA changed")

    monthly_log, formation, monthly_vol = _monthly_formation_and_vol(daily)
    monthly_arithmetic = np.exp(monthly_log) - 1.0

    valid_vol = monthly_vol.where(
        np.isfinite(monthly_vol) & (monthly_vol > 0)
    )
    formation_weights = np.sign(formation) * (
        M027_TARGET_VOL / valid_vol
    )
    weights = formation_weights.shift(1)

    contributions = weights * monthly_arithmetic
    valid = weights.notna() & monthly_arithmetic.notna()
    contributions = contributions.where(valid)
    eligible_counts = contributions.notna().sum(axis=1).astype(int)
    portfolio = contributions.mean(axis=1, skipna=True)
    portfolio = portfolio.where(
        eligible_counts >= M027_MIN_ELIGIBLE_CURRENCIES
    )

    months = pd.date_range(
        readiness["first_month"],
        readiness["last_month"],
        freq="ME",
        tz="UTC",
    )
    portfolio = portfolio.reindex(months)
    if portfolio.isna().any():
        raise ValueError("M027 frozen evaluation window contains missing portfolio months")

    summary = _summary(portfolio)

    fold_results = []
    for fold in readiness["folds"]:
        fold_series = portfolio.loc[
            pd.Timestamp(fold["first_month"], tz="UTC"):
            pd.Timestamp(fold["last_month"], tz="UTC")
        ]
        fold_results.append({
            "name": fold["name"],
            **_summary(fold_series),
        })

    yearly = (1.0 + portfolio).groupby(portfolio.index.year).prod() - 1.0
    eligible_years = int(len(yearly))
    positive_years = int((yearly > 0).sum())

    monthly_counts = eligible_counts.reindex(months).replace(0, np.nan)
    portfolio_contributions = contributions.reindex(months).div(
        monthly_counts,
        axis=0,
    )
    currency_contribution = portfolio_contributions.sum(axis=0, min_count=1)
    positive_currency = currency_contribution[currency_contribution > 0]
    total_positive = float(positive_currency.sum()) if not positive_currency.empty else 0.0
    if total_positive > 0:
        largest_positive_share = float(positive_currency.max() / total_positive)
    else:
        largest_positive_share = float("nan")

    supported = (
        summary["annualized_arithmetic_mean"] > 0
        and summary["annualized_sharpe"] > 0
        and summary["terminal_cumulative_wealth"] > 1.0
        and sum(
            item["annualized_arithmetic_mean"] > 0
            for item in fold_results
        ) >= 2
        and eligible_years > 0
        and positive_years / eligible_years >= 0.50
        and np.isfinite(largest_positive_share)
        and largest_positive_share <= 0.50
    )

    return {
        "label": M027_LABEL,
        "cost_label": M027_COST_LABEL,
        "evaluation_month_list_sha256": expected_month_list_sha256,
        "summary": summary,
        "eligible_currency_count": {
            "min": int(eligible_counts.reindex(months).min()),
            "median": float(eligible_counts.reindex(months).median()),
            "max": int(eligible_counts.reindex(months).max()),
        },
        "folds": fold_results,
        "calendar_years": {
            "eligible": eligible_years,
            "positive": positive_years,
            "positive_fraction": (
                float(positive_years / eligible_years)
                if eligible_years
                else float("nan")
            ),
        },
        "currency_contribution": {
            str(currency): float(value)
            for currency, value in currency_contribution.items()
            if np.isfinite(value)
        },
        "largest_positive_currency_contribution_share": largest_positive_share,
        "classification": (
            "SUPPORTED AS A GROSS PUBLIC-DATA APPROXIMATION"
            if supported
            else "NOT SUPPORTED"
        ),
        "safety": {
            "source_refreshed": False,
            "lag_search_run": False,
            "sign_search_run": False,
            "subperiod_search_run": False,
            "currency_subset_search_run": False,
            "m021_post_cutoff_outcomes_used": False,
            "m024_holdout_reused": False,
            "real_order_api_called": False,
        },
    }
