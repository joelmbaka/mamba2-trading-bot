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


def build_shadow_target_plan(
    signal_snapshot: Mapping[str, Any],
    broker_snapshot: Mapping[str, Mapping[str, Any]],
    *,
    reference_equity: float = M028_REFERENCE_EQUITY_USD,
) -> dict[str, Any]:
    """Build one paper target plan without calculating any strategy return."""

    equity = _require_positive_finite(reference_equity, "reference equity")
    signal_rows = signal_snapshot.get("currencies")
    if not isinstance(signal_rows, Mapping):
        raise ValueError("signal_snapshot must contain currency rows")

    eligibility: dict[str, dict[str, Any]] = {}
    formation: dict[str, float] = {}
    volatility: dict[str, float] = {}
    eligible_codes: list[str] = []

    for currency in M028_FIXED_CURRENCIES:
        signal_row = signal_rows.get(currency)
        broker_row = broker_snapshot.get(currency)
        reason = None
        sign = None
        side = None

        if not isinstance(signal_row, Mapping):
            reason = "SIGNAL_UNAVAILABLE"
        elif not bool(signal_row.get("signal_eligible")):
            reason = "SIGNAL_UNAVAILABLE"
        else:
            raw_sign = signal_row.get("formation_sign")
            if raw_sign not in {-1, 0, 1}:
                reason = "SIGNAL_INVALID"
            elif int(raw_sign) == 0:
                reason = "FLAT_SIGNAL"
            else:
                sign = int(raw_sign)

        if reason is None:
            if not isinstance(broker_row, Mapping):
                reason = "BROKER_METADATA_UNAVAILABLE"
            elif not bool(broker_row.get("quote_viable")):
                reason = "QUOTE_NOT_VIABLE"

        if reason is None:
            side = broker_side(currency, int(sign))
            margin_key = (
                "buy_margin_per_lot"
                if side == "BUY"
                else "sell_margin_per_lot"
            )
            margin_value = broker_row.get(margin_key)
            try:
                margin_ok = (
                    margin_value is not None
                    and math.isfinite(float(margin_value))
                    and float(margin_value) > 0
                )
            except (TypeError, ValueError):
                margin_ok = False
            if not margin_ok:
                reason = "MARGIN_NOT_VIABLE"

        if reason is None:
            try:
                _require_positive_finite(
                    float(broker_row["contract_size"]),
                    f"{currency} contract size",
                )
                _require_positive_finite(
                    float(broker_row["volume_min"]),
                    f"{currency} volume_min",
                )
                _require_positive_finite(
                    float(broker_row["volume_max"]),
                    f"{currency} volume_max",
                )
                _require_positive_finite(
                    float(broker_row["volume_step"]),
                    f"{currency} volume_step",
                )
                bid = _require_positive_finite(
                    float(broker_row["bid"]),
                    f"{currency} bid",
                )
                ask = _require_positive_finite(
                    float(broker_row["ask"]),
                    f"{currency} ask",
                )
                if ask < bid:
                    raise ValueError("ask below bid")
                formation_value = float(signal_row["formation_value"])
                vol_value = _require_positive_finite(
                    float(signal_row["annualized_ex_ante_volatility"]),
                    f"{currency} annualized volatility",
                )
                if not math.isfinite(formation_value):
                    raise ValueError("formation is not finite")
            except (KeyError, TypeError, ValueError):
                reason = "EXECUTION_METADATA_INVALID"

        eligibility[currency] = {
            "eligible": reason is None,
            "reason": reason,
            "formation_sign": sign,
            "broker_side": side,
        }

        if reason is None:
            eligible_codes.append(currency)
            formation[currency] = formation_value
            volatility[currency] = vol_value

    if len(eligible_codes) < M028_MIN_EXECUTABLE_CURRENCIES:
        return {
            "status": "FORWARD_PAPER_NOT_READY",
            "reason": "FEWER_THAN_4_PRE_SIZING_ELIGIBLE",
            "reference_equity_usd": equity,
            "eligible_currencies": sorted(eligible_codes),
            "eligible_count": len(eligible_codes),
            "eligibility": eligibility,
            "targets": {},
            "gross_scale": None,
            "margin_scale": None,
            "projected_margin_usd": 0.0,
            "cost_evidence": {
                "commission": None,
                "commission_status": "UNPROVEN",
                "slippage": None,
                "slippage_status": "UNOBSERVED",
                "financing": None,
                "financing_status": "UNPROVEN",
                "net_pnl": None,
            },
        }

    raw_weights = raw_portfolio_weights(formation, volatility)
    capped_weights, gross_scale = apply_gross_leverage_cap(raw_weights)

    pre_margin_lots: dict[str, float] = {}
    margin_per_lot: dict[str, float] = {}
    volume_rules: dict[str, Mapping[str, float]] = {}
    targets: dict[str, dict[str, Any]] = {}

    for currency in eligible_codes:
        broker_row = broker_snapshot[currency]
        sign = int(signal_rows[currency]["formation_sign"])
        side = broker_side(currency, sign)
        weight = float(capped_weights[currency])
        usd_notional = abs(weight) * equity
        unrounded_lots = usd_notional_to_lots(
            currency,
            usd_notional,
            contract_size=float(broker_row["contract_size"]),
            bid=float(broker_row["bid"]),
            ask=float(broker_row["ask"]),
        )
        rounded_lots = round_lots_toward_zero(
            unrounded_lots,
            volume_min=float(broker_row["volume_min"]),
            volume_max=float(broker_row["volume_max"]),
            volume_step=float(broker_row["volume_step"]),
        )
        margin_key = (
            "buy_margin_per_lot"
            if side == "BUY"
            else "sell_margin_per_lot"
        )
        mpl = float(broker_row[margin_key])
        pre_margin_lots[currency] = rounded_lots
        margin_per_lot[currency] = mpl
        volume_rules[currency] = {
            "volume_min": float(broker_row["volume_min"]),
            "volume_max": float(broker_row["volume_max"]),
            "volume_step": float(broker_row["volume_step"]),
        }
        targets[currency] = {
            "symbol": M028_FIXED_MAPPING[currency],
            "formation_sign": sign,
            "broker_side": side,
            "raw_weight": float(raw_weights[currency]),
            "gross_capped_weight": weight,
            "target_usd_notional": usd_notional,
            "unrounded_target_lots": unrounded_lots,
            "pre_margin_rounded_lots": rounded_lots,
            "margin_per_lot": mpl,
            "bid": float(broker_row["bid"]),
            "ask": float(broker_row["ask"]),
            "paper_fill_price": paper_entry_price(
                side,
                bid=float(broker_row["bid"]),
                ask=float(broker_row["ask"]),
            ),
            "paper_exit_mark_at_decision": paper_exit_mark(
                side,
                bid=float(broker_row["bid"]),
                ask=float(broker_row["ask"]),
            ),
        }

    pre_margin_nonzero = [
        currency
        for currency, lots in pre_margin_lots.items()
        if lots > 0
    ]
    if len(pre_margin_nonzero) < M028_MIN_EXECUTABLE_CURRENCIES:
        return {
            "status": "FORWARD_PAPER_NOT_READY",
            "reason": "FEWER_THAN_4_AFTER_VOLUME_ROUNDING",
            "reference_equity_usd": equity,
            "eligible_currencies": sorted(eligible_codes),
            "eligible_count": len(eligible_codes),
            "eligibility": eligibility,
            "targets": targets,
            "gross_scale": gross_scale,
            "margin_scale": None,
            "projected_margin_usd": 0.0,
            "cost_evidence": {
                "commission": None,
                "commission_status": "UNPROVEN",
                "slippage": None,
                "slippage_status": "UNOBSERVED",
                "financing": None,
                "financing_status": "UNPROVEN",
                "net_pnl": None,
            },
        }

    final_lots, margin_scale, projected_margin = apply_margin_utilization_cap(
        pre_margin_lots,
        margin_per_lot,
        volume_rules,
        reference_equity=equity,
    )

    final_nonzero = [
        currency
        for currency, lots in final_lots.items()
        if lots > 0
    ]
    if len(final_nonzero) < M028_MIN_EXECUTABLE_CURRENCIES:
        for currency in targets:
            targets[currency]["final_target_lots"] = 0.0
        return {
            "status": "FORWARD_PAPER_NOT_READY",
            "reason": "FEWER_THAN_4_AFTER_MARGIN_SCALING",
            "reference_equity_usd": equity,
            "eligible_currencies": sorted(eligible_codes),
            "eligible_count": len(eligible_codes),
            "eligibility": eligibility,
            "targets": targets,
            "gross_scale": gross_scale,
            "margin_scale": margin_scale,
            "projected_margin_usd": 0.0,
            "cost_evidence": {
                "commission": None,
                "commission_status": "UNPROVEN",
                "slippage": None,
                "slippage_status": "UNOBSERVED",
                "financing": None,
                "financing_status": "UNPROVEN",
                "net_pnl": None,
            },
        }

    for currency, lots in final_lots.items():
        targets[currency]["final_target_lots"] = lots
        targets[currency]["projected_margin_usd"] = (
            lots * margin_per_lot[currency]
        )

    return {
        "status": "FORWARD_PAPER_READY",
        "reason": None,
        "reference_equity_usd": equity,
        "eligible_currencies": sorted(final_nonzero),
        "eligible_count": len(final_nonzero),
        "eligibility": eligibility,
        "targets": targets,
        "gross_scale": gross_scale,
        "gross_leverage_before_cap": sum(
            abs(value) for value in raw_weights.values()
        ),
        "gross_leverage_after_cap": sum(
            abs(value) for value in capped_weights.values()
        ),
        "margin_scale": margin_scale,
        "margin_utilization_cap": M028_MARGIN_UTILIZATION_CAP,
        "projected_margin_usd": projected_margin,
        "cost_evidence": {
            "commission": None,
            "commission_status": "UNPROVEN",
            "slippage": None,
            "slippage_status": "UNOBSERVED",
            "financing": None,
            "financing_status": "UNPROVEN",
            "net_pnl": None,
        },
        "safety": {
            "strategy_return_computed": False,
            "portfolio_pnl_computed": False,
            "broker_order_api_called": False,
        },
    }
