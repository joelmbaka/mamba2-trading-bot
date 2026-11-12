"""M029 Stage 2: pure synthetic source/broker-to-paper-decision assembly.

Inputs are supplied bytes and metadata fixtures. This module does NOT download,
connect to MT5, send orders, or persist paper records. Future real adapters
require a separate prospectively frozen Stage-3 authorization.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
from typing import Any, Mapping

from .m027_carry_aware_tsmom import (
    parse_bis_daily_spot_zip,
    parse_oecd_monthly_short_rates,
    sha256_bytes,
)
from .m028_forward_paper import (
    M028_FIXED_MAPPING,
    build_shadow_target_plan,
    required_source_cutoffs,
    source_gate_ready,
)
from .m028_prospective import (
    _frame_sha256,
    build_live_source_signal_snapshot,
)
from .m029_prospective import (
    M029_QUOTE_MAX_AGE,
    M029_MIN_VIABLE_CURRENCIES,
    _parse_utc_iso,
    utc_iso,
    window_bounds,
    window_status,
)


def _costs_unproven() -> dict[str, Any]:
    return {
        "commission": None,
        "commission_status": "UNPROVEN",
        "slippage": None,
        "slippage_status": "UNOBSERVED",
        "financing": None,
        "financing_status": "UNPROVEN",
        "net_pnl": None,
    }


def _flat_plan(reason: str) -> dict[str, Any]:
    return {
        "status": "FORWARD_PAPER_NOT_READY",
        "reason": reason,
        "reference_equity_usd": 10_000.0,
        "targets": {},
        "cost_evidence": _costs_unproven(),
    }


def _normalized_broker_snapshot(
    broker_currencies: Mapping[str, Mapping[str, Any]],
    *,
    at: datetime,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Treat broker-supplied quote_viable as untrusted; recompute mechanically."""
    fixed: dict[str, dict[str, Any]] = {}
    viable: list[str] = []
    for currency, expected_symbol in M028_FIXED_MAPPING.items():
        source = broker_currencies.get(currency)
        row = dict(source) if isinstance(source, Mapping) else {}
        row["symbol"] = expected_symbol
        matched = isinstance(source, Mapping) and source.get("symbol") == expected_symbol
        try:
            bid = float(row["bid"])
            ask = float(row["ask"])
            long_margin = float(row["buy_margin_per_lot"])
            short_margin = float(row["sell_margin_per_lot"])
            contract = float(row["contract_size"])
            volume_min = float(row["volume_min"])
            volume_max = float(row["volume_max"])
            volume_step = float(row["volume_step"])
            quote_time = _parse_utc_iso(row["quote_timestamp_utc"])
            age = at - quote_time
            eligible = (
                matched
                and all(math.isfinite(v) for v in (
                    bid, ask, long_margin, short_margin, contract,
                    volume_min, volume_max, volume_step,
                ))
                and 0 < bid <= ask
                and long_margin > 0 and short_margin > 0
                and contract > 0
                and 0 < volume_min <= volume_max
                and volume_step > 0
                and timedelta(0) <= age <= M029_QUOTE_MAX_AGE
            )
        except (KeyError, TypeError, ValueError, OverflowError):
            eligible = False
        row["quote_viable"] = bool(eligible)
        if eligible:
            viable.append(currency)
        fixed[currency] = row
    return fixed, sorted(viable)


def draft_from_supplied_snapshots(
    *,
    month_id: str,
    now: datetime,
    bis_raw: bytes,
    oecd_raw: bytes,
    broker_currencies: Mapping[str, Mapping[str, Any]],
    prior_positions_lots: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Assemble one unsealed on-time draft, with NO I/O or live side effects.

    The supplied clock is synthetic. Calling this helper does NOT authorize a
    workstation decision. Only a separately reviewed future live adapter may
    supply actual within-window source and broker snapshots.
    """
    state = window_status(month_id, now)
    if state != "WINDOW_OPEN":
        raise RuntimeError(state)

    at = now.astimezone(timezone.utc)
    scheduled, _ = window_bounds(month_id)
    if month_id == "2026-12":
        if prior_positions_lots is not None and any(
            float(value) != 0 for value in prior_positions_lots.values()
        ):
            raise ValueError("first prospective month has no prior paper positions")
        prior = {currency: 0.0 for currency in M028_FIXED_MAPPING}
    else:
        if prior_positions_lots is None:
            raise RuntimeError("PRIOR_PAPER_STATE_REQUIRED")
        if set(prior_positions_lots) != set(M028_FIXED_MAPPING):
            raise ValueError("prior paper positions must cover the fixed eight currencies")
        prior = {currency: float(prior_positions_lots[currency]) for currency in M028_FIXED_MAPPING}
        if any(not math.isfinite(value) for value in prior.values()):
            raise ValueError("prior paper positions must be finite")
    if not isinstance(bis_raw, bytes) or not isinstance(oecd_raw, bytes):
        raise TypeError("BIS and OECD snapshots must be raw bytes")
    if not isinstance(broker_currencies, Mapping):
        raise TypeError("broker_currencies must be a mapping")

    # Source data is parsed only AFTER the prospective gate. Not even the
    # formation sign is inspected unless both source and broker gates pass.
    spot = parse_bis_daily_spot_zip(bis_raw)
    rates = parse_oecd_monthly_short_rates(oecd_raw)
    spot_max = None if spot.empty else spot.index.max().date().isoformat()
    rates_max = None if rates.empty else str(rates.index.max())
    cutoffs = required_source_cutoffs(scheduled)
    source_ok = bool(
        spot_max is not None
        and rates_max is not None
        and source_gate_ready(
            scheduled,
            spot_max_date=spot_max,
            rate_max_month=rates_max,
        )
    )
    source = {
        "bis_raw_sha256": sha256_bytes(bis_raw),
        "oecd_raw_sha256": sha256_bytes(oecd_raw),
        "spot_panel_sha256": _frame_sha256(spot, index_label="date"),
        "rate_panel_sha256": _frame_sha256(
            rates, index_label="month", period_index_as_string=True
        ),
        "spot_max_date": spot_max,
        "rate_max_month": rates_max,
        "observed_at_utc": utc_iso(at),
        **cutoffs,
    }
    fixed_broker, viable = _normalized_broker_snapshot(
        broker_currencies, at=at
    )
    broker = {
        "observed_at_utc": utc_iso(at),
        "viable_currencies": viable,
        "viable_count": len(viable),
        "currencies": fixed_broker,
    }
    signal = None
    if not source_ok:
        plan = _flat_plan("SOURCE_NOT_READY")
    elif len(viable) < M029_MIN_VIABLE_CURRENCIES:
        plan = _flat_plan("BROKER_NOT_READY")
    else:
        live = build_live_source_signal_snapshot(
            bis_raw=bis_raw,
            oecd_raw=oecd_raw,
            now=at,
            decision=scheduled,
        )
        signal = live["signal"]
        source.update({
            key: value
            for key, value in live["source"].items()
            if key not in {"observed_at_utc"}
        })
        plan = build_shadow_target_plan(signal, fixed_broker)

    return {
        "version": 1,
        "decision_id": month_id,
        "scheduled_decision_utc": utc_iso(scheduled),
        "created_at_utc": utc_iso(at),
        "feature_branch": "prospective-paper-recovery",
        "source": source,
        "source_gate_pass": source_ok,
        "signal": signal,
        "broker": broker,
        "plan": plan,
        "prior_positions_lots": prior,
        "holding_period_return": None,
        "safety": {
            "real_order_api_called": False,
            "order_check_called": False,
            "position_change_api_called": False,
            "trade_history_read": False,
            "balance_or_equity_returned": False,
            "portfolio_pnl_computed": False,
            "m027_economics_rerun": False,
            "m021_post_cutoff_outcomes_used": False,
        },
    }
