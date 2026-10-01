"""Prospective M028 source/signal helpers for the first paper decision.

The live/source-derived signal path is time-gated. Pure helpers may be tested
with synthetic data before the first permitted decision timestamp.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import math
from typing import Any

import pandas as pd

from .m027_carry_aware_tsmom import (
    M027_CURRENCIES,
    carry_aware_daily_excess_log_returns,
    parse_bis_daily_spot_zip,
    parse_oecd_monthly_short_rates,
    sha256_bytes,
)
from .m027_stage2 import _monthly_formation_and_vol
from .m028_forward_paper import (
    M028_FIXED_CURRENCIES,
    formation_sign,
    required_source_cutoffs,
    source_gate_ready,
)


M028_FIRST_DECISION_ID = "2026-10"
M028_FIRST_DECISION_UTC = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc)


def assert_first_decision_time(
    now: datetime,
    *,
    decision: datetime = M028_FIRST_DECISION_UTC,
) -> None:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if decision.tzinfo is None:
        raise ValueError("decision must be timezone-aware")
    if now.astimezone(timezone.utc) < decision.astimezone(timezone.utc):
        raise RuntimeError(
            "M028 first forward-paper decision is time-gated until "
            f"{decision.astimezone(timezone.utc).isoformat()}"
        )


def previous_completed_month_end(decision: datetime) -> pd.Timestamp:
    if decision.tzinfo is None:
        raise ValueError("decision must be timezone-aware")
    utc = pd.Timestamp(decision).tz_convert("UTC")
    current_month_start = utc.normalize().replace(day=1)
    return current_month_start - pd.Timedelta(days=1)


def _frame_sha256(
    frame: pd.DataFrame,
    *,
    index_label: str,
    period_index_as_string: bool = False,
) -> str:
    copy = frame.copy()
    if period_index_as_string:
        copy.index = copy.index.astype(str)
    buffer = io.StringIO()
    copy.to_csv(
        buffer,
        index=True,
        index_label=index_label,
        float_format="%.17g",
        lineterminator="\n",
    )
    return hashlib.sha256(buffer.getvalue().encode("utf-8")).hexdigest()


def signal_snapshot_from_daily(
    daily: pd.DataFrame,
    *,
    decision: datetime,
) -> dict[str, Any]:
    """Compute only the frozen formation/vol inputs for one decision month."""

    if list(daily.columns) != list(M027_CURRENCIES):
        raise ValueError("daily panel must use the frozen M027 currency columns")
    target_month_end = previous_completed_month_end(decision)
    _, formation, monthly_vol = _monthly_formation_and_vol(daily)

    if target_month_end not in formation.index:
        raise ValueError(
            f"prospective panel lacks completed month {target_month_end.date()}"
        )

    currencies: dict[str, dict[str, Any]] = {}
    eligible = []
    for currency in M028_FIXED_CURRENCIES:
        formation_value = formation.at[target_month_end, currency]
        vol_value = monthly_vol.at[target_month_end, currency]

        formation_ok = pd.notna(formation_value) and math.isfinite(
            float(formation_value)
        )
        vol_ok = (
            pd.notna(vol_value)
            and math.isfinite(float(vol_value))
            and float(vol_value) > 0
        )
        eligible_here = bool(formation_ok and vol_ok)

        row: dict[str, Any] = {
            "formation_available": bool(formation_ok),
            "volatility_available": bool(vol_ok),
            "signal_eligible": eligible_here,
            "formation_value": (
                float(formation_value) if formation_ok else None
            ),
            "formation_sign": (
                formation_sign(float(formation_value)) if formation_ok else None
            ),
            "annualized_ex_ante_volatility": (
                float(vol_value) if vol_ok else None
            ),
        }
        currencies[currency] = row
        if eligible_here and row["formation_sign"] != 0:
            eligible.append(currency)

    return {
        "decision_id": decision.strftime("%Y-%m"),
        "decision_timestamp_utc": decision.astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "formation_month_end": target_month_end.date().isoformat(),
        "currencies": currencies,
        "nonflat_signal_eligible_currencies": sorted(eligible),
        "nonflat_signal_eligible_count": len(eligible),
    }


def build_live_source_signal_snapshot(
    *,
    bis_raw: bytes,
    oecd_raw: bytes,
    now: datetime,
    decision: datetime = M028_FIRST_DECISION_UTC,
) -> dict[str, Any]:
    """Build the first live-source signal snapshot only after its time gate."""

    assert_first_decision_time(now, decision=decision)

    spot = parse_bis_daily_spot_zip(bis_raw)
    rates = parse_oecd_monthly_short_rates(oecd_raw)

    spot_max = None if spot.empty else spot.index.max().date().isoformat()
    rate_max = None if rates.empty else str(rates.index.max())
    if spot_max is None or rate_max is None:
        raise ValueError("prospective source panels are empty")
    if not source_gate_ready(
        decision,
        spot_max_date=spot_max,
        rate_max_month=rate_max,
    ):
        required = required_source_cutoffs(decision)
        raise RuntimeError(
            "M028 prospective source gate not ready: "
            f"spot={spot_max} need={required['required_spot_through']}; "
            f"rates={rate_max} need={required['required_rate_month']}"
        )

    daily = carry_aware_daily_excess_log_returns(spot, rates)
    signal = signal_snapshot_from_daily(daily, decision=decision)

    return {
        "decision_id": signal["decision_id"],
        "decision_timestamp_utc": signal["decision_timestamp_utc"],
        "source": {
            "bis_raw_sha256": sha256_bytes(bis_raw),
            "oecd_raw_sha256": sha256_bytes(oecd_raw),
            "spot_panel_sha256": _frame_sha256(
                spot,
                index_label="date",
            ),
            "rate_panel_sha256": _frame_sha256(
                rates,
                index_label="month",
                period_index_as_string=True,
            ),
            "approximate_return_panel_sha256": _frame_sha256(
                daily,
                index_label="date",
            ),
            "spot_max_date": spot_max,
            "rate_max_month": rate_max,
            **required_source_cutoffs(decision),
        },
        "signal": signal,
        "safety": {
            "strategy_return_computed": False,
            "portfolio_pnl_computed": False,
            "broker_order_api_called": False,
        },
    }
