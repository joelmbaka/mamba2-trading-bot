"""M029 prospective month gates and immutable *paper* decision persistence.

Stage 1 is intentionally pure/local. This module never imports or initializes
MT5, downloads market data, computes strategy signals, or places orders.
The UTC clock for any future live adapter MUST be read inside that trusted
workstation action; test-injected timestamps are synthetic-only.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Mapping

from .m028_forward_paper import (
    M028_FIXED_CURRENCIES,
    decision_record_sha256,
    fifth_weekday_decision,
    required_source_cutoffs,
    seal_decision_record,
    source_gate_ready,
)

M029_FIRST_MONTH = "2026-12"
M029_WINDOW = timedelta(minutes=10)
M029_MIN_VIABLE_CURRENCIES = 4
M029_QUOTE_MAX_AGE = timedelta(seconds=300)
_MONTH = re.compile(r"([0-9]{4})-(0[1-9]|1[0-2])", re.ASCII)
_SHA256 = re.compile(r"[a-f0-9]{64}", re.ASCII)


def _month_parts(month_id: str) -> tuple[int, int]:
    if not isinstance(month_id, str) or _MONTH.fullmatch(month_id) is None:
        raise ValueError("month_id must be canonical YYYY-MM")
    year, month = int(month_id[:4]), int(month_id[5:])
    if year < 1:
        raise ValueError("year must be positive")
    return year, month


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


def _parse_utc_iso(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO-8601 UTC string")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if result.tzinfo is None or result.utcoffset() != timedelta(0):
        raise ValueError("timestamp must carry a UTC offset")
    return result.astimezone(timezone.utc)


def utc_iso(value: datetime) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def window_bounds(month_id: str) -> tuple[datetime, datetime]:
    year, month = _month_parts(month_id)
    start = fifth_weekday_decision(year, month)
    return start, start + M029_WINDOW


def window_status(month_id: str, now: datetime) -> str:
    """A pure wall-clock gate: no records, signals, or broker reads."""
    current = _utc(now)
    _month_parts(month_id)
    if month_id < M029_FIRST_MONTH:
        return "INELIGIBLE_HISTORICAL_MONTH"
    start, end = window_bounds(month_id)
    if current < start:
        return "WINDOW_NOT_OPEN"
    if current >= end:
        return "MISSED_WINDOW"
    return "WINDOW_OPEN"


def record_path(directory: Path, month_id: str) -> Path:
    _month_parts(month_id)
    return Path(directory) / f"{month_id}-decision.json"


def _validate_record(record: Mapping[str, Any], month_id: str) -> None:
    if not isinstance(record, Mapping):
        raise ValueError("decision record must be a mapping")
    if month_id < M029_FIRST_MONTH:
        raise ValueError("past October/November decisions may not be backfilled")
    start, end = window_bounds(month_id)
    if record.get("decision_id") != month_id:
        raise ValueError("decision_id disagrees with immutable file month")
    if record.get("scheduled_decision_utc") != utc_iso(start):
        raise ValueError("scheduled decision timestamp disagrees with calendar")
    created = _parse_utc_iso(record.get("created_at_utc"))
    if not start <= created < end:
        raise ValueError("record was not created during its prospective window")

    if record.get("holding_period_return") is not None:
        raise ValueError("decision creation cannot include holding-period P/L")
    source = record.get("source")
    broker = record.get("broker")
    plan = record.get("plan")
    if not isinstance(source, Mapping) or not isinstance(broker, Mapping):
        raise ValueError("source and broker metadata are required")
    if not isinstance(plan, Mapping):
        raise ValueError("paper plan mapping is required")
    cost = plan.get("cost_evidence")
    if not isinstance(cost, Mapping):
        raise ValueError("paper plan requires explicit cost evidence")
    for field in ("commission", "slippage", "financing", "net_pnl"):
        if cost.get(field) is not None:
            raise ValueError(f"{field} cannot be assumed known in M029 Stage 1")
    for field in ("bis_raw_sha256", "oecd_raw_sha256",
                  "spot_panel_sha256", "rate_panel_sha256"):
        value = source.get(field)
        if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
            raise ValueError(f"missing/invalid frozen source SHA: {field}")
    required = required_source_cutoffs(start)
    if any(source.get(k) != v for k, v in required.items()):
        raise ValueError("source cutoff metadata disagrees with decision month")
    for name, mapping in (("source", source), ("broker", broker)):
        observed = _parse_utc_iso(mapping.get("observed_at_utc"))
        if observed < start or observed >= end or observed > created:
            raise ValueError(f"{name} observation not within decision window")

    safe = record.get("safety")
    if not isinstance(safe, Mapping):
        raise ValueError("safety evidence required")
    for flag in (
        "real_order_api_called", "order_check_called",
        "position_change_api_called", "trade_history_read",
        "balance_or_equity_returned", "portfolio_pnl_computed",
        "m027_economics_rerun", "m021_post_cutoff_outcomes_used",
    ):
        if safe.get(flag) is not False:
            raise ValueError(f"unsafe or missing evidence flag: {flag}")


def read_decision(directory: Path, month_id: str) -> dict[str, Any] | None:
    """Verify an existing decision without ever changing it."""
    path = record_path(directory, month_id)
    if path.is_symlink():
        raise ValueError("refuse symlink decision record")
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError("decision path exists but is not a regular file")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("existing decision is unreadable; do not overwrite") from exc
    if not isinstance(record, dict):
        raise ValueError("existing decision is not a JSON object")
    _validate_record(record, month_id)
    declared = record.get("decision_record_sha256")
    if not isinstance(declared, str) or declared != decision_record_sha256(record):
        raise ValueError("existing decision hash mismatch; do not overwrite")
    return record


def write_decision(
    directory: Path,
    month_id: str,
    record: Mapping[str, Any],
    *,
    now: datetime,
) -> tuple[dict[str, Any], bool]:
    """Exclusive on-time paper record creation; synthetic timestamps for tests.

    The caller that will eventually bridge live sources MUST supply the UTC time
    read internally just before this call, and must be separately authorized.
    Returns (record, reused_existing). A corrupt/colliding record is never fixed.
    """
    directory = Path(directory)
    existing = read_decision(directory, month_id)
    if existing is not None:
        return existing, True

    status = window_status(month_id, now)
    if status != "WINDOW_OPEN":
        raise RuntimeError(status)
    if record.get("created_at_utc") != utc_iso(now):
        raise ValueError("created_at_utc must match current trusted clock")
    if record.get("decision_record_sha256") is not None:
        raise ValueError("caller must not supply a pre-sealed hash")
    _validate_record(record, month_id)

    sealed = seal_decision_record(record)
    encoded = json.dumps(
        sealed, indent=2, sort_keys=True, allow_nan=False
    ) + "\n"
    directory.mkdir(parents=True, exist_ok=True)
    if directory.is_symlink():
        raise ValueError("decision directory must not be a symlink")
    path = record_path(directory, month_id)
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        winner = read_decision(directory, month_id)
        if winner is None:
            raise ValueError("decision collision without readable record")
        return winner, True
    return sealed, False


def metadata_readiness(
    month_id: str,
    now: datetime,
    *,
    spot_max_date: str | None,
    rate_max_month: str | None,
    broker_currencies: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Synthetic/read-only *metadata* gate: no formation, lots, side, or P/L."""
    moment = _utc(now)
    status = window_status(month_id, moment)
    start, end = window_bounds(month_id)
    cutoff = required_source_cutoffs(start)
    source_ok = bool(
        spot_max_date and rate_max_month and source_gate_ready(
            start,
            spot_max_date=spot_max_date,
            rate_max_month=rate_max_month,
        )
    )
    viable: list[str] = []
    for code in M028_FIXED_CURRENCIES:
        row = broker_currencies.get(code)
        if not isinstance(row, Mapping):
            continue
        try:
            bid, ask = float(row["bid"]), float(row["ask"])
            margin_buy = float(row["buy_margin_per_lot"])
            margin_sell = float(row["sell_margin_per_lot"])
            tick = _parse_utc_iso(row["quote_timestamp_utc"])
            valid = (
                math.isfinite(bid) and math.isfinite(ask) and 0 < bid <= ask
                and math.isfinite(margin_buy) and margin_buy > 0
                and math.isfinite(margin_sell) and margin_sell > 0
                and timedelta(0) <= moment - tick <= M029_QUOTE_MAX_AGE
            )
        except (KeyError, ValueError, TypeError, OverflowError):
            valid = False
        if valid:
            viable.append(code)
    broker_ok = len(viable) >= M029_MIN_VIABLE_CURRENCIES
    if status == "INELIGIBLE_HISTORICAL_MONTH":
        classification = status
    elif status == "MISSED_WINDOW":
        classification = status
    elif not source_ok:
        classification = "SOURCE_NOT_READY"
    elif not broker_ok:
        classification = "BROKER_NOT_READY"
    else:
        classification = "READY_FOR_SCHEDULED_DECISION"
    return {
        "readiness_only": True,
        "decision_id": month_id,
        "scheduled_decision_utc": utc_iso(start),
        "window_closes_utc": utc_iso(end),
        "clock_gate": status,
        "source_gate_pass": source_ok,
        "broker_gate_pass": broker_ok,
        "viable_currencies": sorted(viable),
        "viable_count": len(viable),
        "required_source": cutoff,
        "classification": classification,
        "signal_computed": False,
        "target_lots_computed": False,
        "strategy_pnl_computed": False,
        "real_order_api_called": False,
    }
