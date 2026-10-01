"""M028 forward-paper contract machinery.

Pure deterministic helpers only. This module does not initialize MT5, call any
broker order API, inspect trade history, or compute strategy performance.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
import math
from typing import Any, Mapping

from .m027_carry_aware_tsmom import M027_TARGET_VOL


M028_FIXED_MAPPING: Mapping[str, str] = {
    "AUD": "AUDUSD",
    "CAD": "USDCAD",
    "CHF": "USDCHF",
    "EUR": "EURUSD",
    "GBP": "GBPUSD",
    "JPY": "USDJPY",
    "NZD": "NZDUSD",
    "SEK": "USDSEK",
}
M028_FOREIGN_BASE = frozenset({"AUD", "EUR", "GBP", "NZD"})
M028_FIXED_CURRENCIES = tuple(M028_FIXED_MAPPING)
M028_REFERENCE_EQUITY_USD = 10_000.0
M028_GROSS_LEVERAGE_CAP = 4.0
M028_MARGIN_UTILIZATION_CAP = 0.25
M028_MIN_EXECUTABLE_CURRENCIES = 4
M028_MIN_FORWARD_MONTHS = 12
M028_DECISION_HOUR_UTC = 12


def _require_currency(currency: str) -> str:
    code = str(currency).upper()
    if code not in M028_FIXED_MAPPING:
        raise ValueError(f"currency is outside frozen M028 universe: {currency!r}")
    return code


def _require_positive_finite(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return number


def fifth_weekday_decision(year: int, month: int) -> datetime:
    """Return 12:00 UTC on the fifth Monday-Friday day of a month."""

    count = 0
    for day in range(1, monthrange(year, month)[1] + 1):
        candidate = datetime(year, month, day, tzinfo=timezone.utc)
        if candidate.weekday() >= 5:
            continue
        count += 1
        if count == 5:
            return candidate.replace(hour=M028_DECISION_HOUR_UTC)
    raise ValueError("month does not contain five Monday-Friday weekdays")


def required_source_cutoffs(decision: datetime) -> dict[str, str]:
    """Return source completeness cutoffs for one prospective decision.

    A decision in month D uses formation through D-1. Daily carry in D-1 uses
    the completed rate month D-2 under the frozen M027 lag rule.
    """

    if decision.tzinfo is None:
        raise ValueError("decision timestamp must be timezone-aware")
    utc = decision.astimezone(timezone.utc)

    if utc.month == 1:
        spot_year, spot_month = utc.year - 1, 12
    else:
        spot_year, spot_month = utc.year, utc.month - 1
    spot_last_day = monthrange(spot_year, spot_month)[1]

    if spot_month == 1:
        rate_year, rate_month = spot_year - 1, 12
    else:
        rate_year, rate_month = spot_year, spot_month - 1

    return {
        "required_spot_through": (
            f"{spot_year:04d}-{spot_month:02d}-{spot_last_day:02d}"
        ),
        "required_rate_month": f"{rate_year:04d}-{rate_month:02d}",
    }


def source_gate_ready(
    decision: datetime,
    *,
    spot_max_date: str,
    rate_max_month: str,
) -> bool:
    required = required_source_cutoffs(decision)
    return (
        str(spot_max_date) >= required["required_spot_through"]
        and str(rate_max_month) >= required["required_rate_month"]
    )


def formation_sign(value: float) -> int:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("formation value must be finite")
    if number > 0:
        return 1
    if number < 0:
        return -1
    return 0


def broker_side(currency: str, signal_sign: int) -> str:
    """Translate long/short foreign-currency exposure into broker pair side."""

    code = _require_currency(currency)
    sign = int(signal_sign)
    if sign not in {-1, 0, 1}:
        raise ValueError("signal_sign must be -1, 0, or 1")
    if sign == 0:
        return "FLAT"

    foreign_is_base = code in M028_FOREIGN_BASE
    if foreign_is_base:
        return "BUY" if sign > 0 else "SELL"
    return "SELL" if sign > 0 else "BUY"


def raw_portfolio_weights(
    formation: Mapping[str, float],
    annualized_volatility: Mapping[str, float],
) -> dict[str, float]:
    """Translate frozen M027 signal/volatility into equal-weight notional weights."""

    eligible: list[tuple[str, int, float]] = []
    for currency in M028_FIXED_CURRENCIES:
        if currency not in formation or currency not in annualized_volatility:
            continue
        sign = formation_sign(float(formation[currency]))
        if sign == 0:
            continue
        vol = _require_positive_finite(
            float(annualized_volatility[currency]),
            f"{currency} annualized volatility",
        )
        eligible.append((currency, sign, vol))

    if not eligible:
        return {}

    denominator = float(len(eligible))
    return {
        currency: (sign * M027_TARGET_VOL / vol) / denominator
        for currency, sign, vol in eligible
    }


def apply_gross_leverage_cap(
    weights: Mapping[str, float],
    *,
    cap: float = M028_GROSS_LEVERAGE_CAP,
) -> tuple[dict[str, float], float]:
    ceiling = _require_positive_finite(cap, "gross leverage cap")
    clean = {str(key): float(value) for key, value in weights.items()}
    if any(not math.isfinite(value) for value in clean.values()):
        raise ValueError("weights must be finite")

    gross = sum(abs(value) for value in clean.values())
    scale = 1.0 if gross <= ceiling or gross == 0 else ceiling / gross
    return ({key: value * scale for key, value in clean.items()}, scale)


def usd_notional_to_lots(
    currency: str,
    usd_notional: float,
    *,
    contract_size: float,
    bid: float,
    ask: float,
) -> float:
    code = _require_currency(currency)
    notional = abs(float(usd_notional))
    if not math.isfinite(notional):
        raise ValueError("USD notional must be finite")
    if notional == 0:
        return 0.0

    contract = _require_positive_finite(contract_size, "contract size")
    bid_value = _require_positive_finite(bid, "bid")
    ask_value = _require_positive_finite(ask, "ask")
    if ask_value < bid_value:
        raise ValueError("ask must be greater than or equal to bid")

    if code in M028_FOREIGN_BASE:
        mid = (bid_value + ask_value) / 2.0
        return notional / (contract * mid)
    return notional / contract


def round_lots_toward_zero(
    lots: float,
    *,
    volume_min: float,
    volume_max: float,
    volume_step: float,
) -> float:
    """Round positive target lots down to broker step without exceeding target."""

    target = float(lots)
    if not math.isfinite(target) or target < 0:
        raise ValueError("lots must be finite and non-negative")
    minimum = _require_positive_finite(volume_min, "volume_min")
    maximum = _require_positive_finite(volume_max, "volume_max")
    step = _require_positive_finite(volume_step, "volume_step")
    if minimum > maximum:
        raise ValueError("volume_min cannot exceed volume_max")
    if target == 0:
        return 0.0

    clipped = min(target, maximum)
    d_target = Decimal(str(clipped))
    d_step = Decimal(str(step))
    units = (d_target / d_step).to_integral_value(rounding=ROUND_FLOOR)
    rounded = units * d_step

    if rounded < Decimal(str(minimum)):
        return 0.0
    return float(rounded)


def paper_entry_price(side: str, *, bid: float, ask: float) -> float | None:
    bid_value = _require_positive_finite(bid, "bid")
    ask_value = _require_positive_finite(ask, "ask")
    if ask_value < bid_value:
        raise ValueError("ask must be greater than or equal to bid")
    normalized = str(side).upper()
    if normalized == "BUY":
        return ask_value
    if normalized == "SELL":
        return bid_value
    if normalized == "FLAT":
        return None
    raise ValueError("side must be BUY, SELL, or FLAT")


def paper_exit_mark(side: str, *, bid: float, ask: float) -> float | None:
    bid_value = _require_positive_finite(bid, "bid")
    ask_value = _require_positive_finite(ask, "ask")
    if ask_value < bid_value:
        raise ValueError("ask must be greater than or equal to bid")
    normalized = str(side).upper()
    if normalized == "BUY":
        return bid_value
    if normalized == "SELL":
        return ask_value
    if normalized == "FLAT":
        return None
    raise ValueError("side must be BUY, SELL, or FLAT")


def apply_margin_utilization_cap(
    lots: Mapping[str, float],
    margin_per_lot: Mapping[str, float],
    volume_rules: Mapping[str, Mapping[str, float]],
    *,
    reference_equity: float = M028_REFERENCE_EQUITY_USD,
    utilization_cap: float = M028_MARGIN_UTILIZATION_CAP,
) -> tuple[dict[str, float], float, float]:
    """Apply one common margin scale, then round every position toward zero."""

    equity = _require_positive_finite(reference_equity, "reference equity")
    cap_fraction = _require_positive_finite(
        utilization_cap,
        "margin utilization cap",
    )
    if cap_fraction > 1:
        raise ValueError("margin utilization cap cannot exceed 1")

    clean_lots: dict[str, float] = {}
    projected = 0.0
    for currency, raw_lots in lots.items():
        code = _require_currency(currency)
        value = float(raw_lots)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{code} lots must be finite and non-negative")
        per_lot = _require_positive_finite(
            float(margin_per_lot[code]),
            f"{code} margin_per_lot",
        )
        clean_lots[code] = value
        projected += value * per_lot

    margin_limit = equity * cap_fraction
    scale = 1.0 if projected <= margin_limit or projected == 0 else margin_limit / projected

    scaled: dict[str, float] = {}
    for code, value in clean_lots.items():
        rules = volume_rules[code]
        scaled[code] = round_lots_toward_zero(
            value * scale,
            volume_min=float(rules["volume_min"]),
            volume_max=float(rules["volume_max"]),
            volume_step=float(rules["volume_step"]),
        )

    final_margin = sum(
        scaled[code] * float(margin_per_lot[code])
        for code in scaled
    )
    return scaled, scale, final_margin


def decision_record_sha256(record: Mapping[str, Any]) -> str:
    """Hash canonical JSON for an immutable paper decision record."""

    payload = {
        key: value
        for key, value in record.items()
        if key != "decision_record_sha256"
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def seal_decision_record(record: Mapping[str, Any]) -> dict[str, Any]:
    sealed = dict(record)
    sealed["decision_record_sha256"] = decision_record_sha256(sealed)
    return sealed
