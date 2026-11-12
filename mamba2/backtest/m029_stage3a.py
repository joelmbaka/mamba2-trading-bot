"""M029 Stage 3A: synthetic-only acquisition provenance and mock broker adapter.

There is deliberately no real downloader, MT5 import, connection, scheduler,
journal writer, or trading action here. Inputs are injected for offline tests.
Stage 3B connectivity and Stage 3C decision execution need separate approval.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from .m027_carry_aware_tsmom import (
    BIS_XRU_URL,
    OECD_STIR_URL,
    parse_bis_daily_spot_zip,
    parse_oecd_monthly_short_rates,
)
from .m028_forward_paper import (
    M028_FIXED_MAPPING,
    required_source_cutoffs,
    source_gate_ready,
)
from .m028_prospective import _frame_sha256
from .m029_prospective import (
    M029_MIN_VIABLE_CURRENCIES,
    M029_QUOTE_MAX_AGE,
    _parse_utc_iso,
    utc_iso,
    window_bounds,
    window_status,
)


class EvidenceRefused(RuntimeError):
    """An operational contract is violated; do not create a paper record."""


class ReadOnlyBroker(Protocol):
    """Mock-only transport here; an actual MT5 adapter is NOT authorized."""

    def symbol_info(self, symbol: str) -> Mapping[str, Any] | None: ...
    def symbol_info_tick(self, symbol: str) -> Mapping[str, Any] | None: ...
    def order_calc_margin(self, side: str, symbol: str, lots: float, price: float) -> float | None: ...


def _clock(clock: Callable[[], datetime]) -> datetime:
    value = clock()
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise EvidenceRefused("CLOCK_NOT_UTC_AWARE")
    # A clock may use a time zone offset but must refer to the same UTC instant.
    return value.astimezone(timezone.utc)


def _gate(month_id: str, clock: Callable[[], datetime]) -> datetime:
    current = _clock(clock)
    status = window_status(month_id, current)
    if status != "WINDOW_OPEN":
        raise EvidenceRefused(status)
    return current


def _blocking(
    month_id: str, clock: Callable[[], datetime], operation: Callable[[], Any]
) -> tuple[Any, datetime, datetime]:
    started = _gate(month_id, clock)
    response = operation()
    finished = _gate(month_id, clock)
    if finished < started:
        raise EvidenceRefused("CLOCK_MOVED_BACKWARD")
    return response, started, finished


def _source(
    *,
    month_id: str,
    clock: Callable[[], datetime],
    url: str,
    download: Callable[[str], bytes],
    parser: Callable[[bytes], Any],
    label: str,
) -> dict[str, Any]:
    # Acquisition times are measured by our clock, never copied from a
    # caller-provided "observed_at" or source metadata object.
    raw, started, finished = _blocking(month_id, clock, lambda: download(url))
    if type(raw) is not bytes or not raw:
        raise EvidenceRefused("SOURCE_BYTES_UNAVAILABLE")
    frame, parsed_at, parsed_finished = _blocking(
        month_id, clock, lambda: parser(raw)
    )
    if frame is None or frame.empty:
        raise EvidenceRefused("SOURCE_PANEL_EMPTY")
    if label == "BIS":
        if not isinstance(frame.index.max(), (datetime,)):
            # pandas Timestamp subclasses datetime, and this enforces a
            # date-valued normalized daily index rather than an arbitrary id.
            raise EvidenceRefused("BIS_DATE_INDEX_INVALID")
        max_period = frame.index.max().date().isoformat()
        normalized_hash = _frame_sha256(frame, index_label="date")
    elif label == "OECD":
        max_period = str(frame.index.max())
        if len(max_period) != 7 or max_period[4] != "-":
            raise EvidenceRefused("OECD_MONTH_INDEX_INVALID")
        normalized_hash = _frame_sha256(
            frame, index_label="month", period_index_as_string=True
        )
    else:
        raise EvidenceRefused("SOURCE_ID_UNKNOWN")
    if finished > parsed_at or parsed_at > parsed_finished:
        raise EvidenceRefused("SOURCE_CLOCK_ORDER_INVALID")
    return {
        "source_id": label,
        "url": url,
        "fetch_started_at_utc": utc_iso(started),
        "fetch_finished_at_utc": utc_iso(finished),
        "parsed_finished_at_utc": utc_iso(parsed_finished),
        "raw_sha256": sha256(raw).hexdigest(),
        "normalized_sha256": normalized_hash,
        "last_observation": max_period,
    }


def _number(row: Mapping[str, Any], field: str) -> float:
    import math

    try:
        result = float(row[field])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise EvidenceRefused("BROKER_METADATA_MISSING") from exc
    if not math.isfinite(result):
        raise EvidenceRefused("BROKER_METADATA_NONFINITE")
    return result


def _broker(
    *,
    month_id: str,
    clock: Callable[[], datetime],
    transport: ReadOnlyBroker,
) -> dict[str, Any]:
    started = _gate(month_id, clock)
    rows: dict[str, dict[str, Any]] = {}
    viable: list[str] = []
    scheduled, close = window_bounds(month_id)

    for currency, symbol in M028_FIXED_MAPPING.items():
        # These are the ONLY broker interface members this mock-bound routine
        # is permitted to invoke. No initialize, account_info, trade history,
        # symbol_select, orders, positions, order_check or order_send.
        try:
            metadata, _, _ = _blocking(
                month_id, clock, lambda symbol=symbol: transport.symbol_info(symbol)
            )
            tick, _, observed = _blocking(
                month_id, clock, lambda symbol=symbol: transport.symbol_info_tick(symbol)
            )
            if not isinstance(metadata, Mapping) or not isinstance(tick, Mapping):
                rows[currency] = {"symbol": symbol, "quote_viable": False}
                continue

            bid = _number(tick, "bid")
            ask = _number(tick, "ask")
            contract = _number(metadata, "contract_size")
            vmin = _number(metadata, "volume_min")
            vmax = _number(metadata, "volume_max")
            vstep = _number(metadata, "volume_step")
            if metadata.get("symbol") != symbol:
                raise EvidenceRefused("WRONG_BROKER_SYMBOL")
            tick_time = _parse_utc_iso(tick.get("quote_timestamp_utc"))
            fresh = (
                0 < bid <= ask and contract > 0
                and 0 < vmin <= vmax and vstep > 0
                and scheduled <= tick_time < close
                and timedelta(0) <= observed - tick_time <= M029_QUOTE_MAX_AGE
            )
            if not fresh:
                rows[currency] = {
                    "symbol": symbol,
                    "quote_viable": False,
                    "quote_observed_at_utc": utc_iso(observed),
                    "quote_timestamp_utc": utc_iso(tick_time),
                }
                continue

            # Margin is read-only, for both orientations. The future MT5
            # wrapper must map the plain BUY/SELL strings to frozen constants.
            buy, _, _ = _blocking(
                month_id, clock,
                lambda symbol=symbol, ask=ask: transport.order_calc_margin(
                    "BUY", symbol, 1.0, ask
                )
            )
            sell, _, _ = _blocking(
                month_id, clock,
                lambda symbol=symbol, bid=bid: transport.order_calc_margin(
                    "SELL", symbol, 1.0, bid
                )
            )
            import math
            margin_ok = (
                buy is not None and sell is not None
                and math.isfinite(float(buy)) and float(buy) > 0
                and math.isfinite(float(sell)) and float(sell) > 0
            )
            if not margin_ok:
                rows[currency] = {
                    "symbol": symbol,
                    "quote_viable": False,
                    "quote_timestamp_utc": utc_iso(tick_time),
                    "quote_observed_at_utc": utc_iso(observed),
                }
                continue

            rows[currency] = {
                "symbol": symbol,
                "quote_viable": True,
                "quote_timestamp_utc": utc_iso(tick_time),
                "quote_observed_at_utc": utc_iso(observed),
                "bid": bid,
                "ask": ask,
                "contract_size": contract,
                "volume_min": vmin,
                "volume_max": vmax,
                "volume_step": vstep,
                "buy_margin_per_lot": float(buy),
                "sell_margin_per_lot": float(sell),
            }
            viable.append(currency)
        except EvidenceRefused as exc:
            # A window expiry or failed clock cannot be converted into a
            # mere unavailable symbol. It is a hard stop.
            if str(exc) in (
                "WINDOW_NOT_OPEN", "MISSED_WINDOW",
                "INELIGIBLE_HISTORICAL_MONTH", "CLOCK_MOVED_BACKWARD",
                "CLOCK_NOT_UTC_AWARE",
            ):
                raise
            rows[currency] = {"symbol": symbol, "quote_viable": False}
        except (KeyError, ValueError, TypeError, OverflowError):
            rows[currency] = {"symbol": symbol, "quote_viable": False}

    finished = _gate(month_id, clock)
    return {
        "query_started_at_utc": utc_iso(started),
        "query_finished_at_utc": utc_iso(finished),
        "observed_at_utc": utc_iso(finished),
        "currencies": rows,
        "viable_currencies": sorted(viable),
        "viable_count": len(viable),
    }


def metadata_rehearsal(
    month_id: str,
    *,
    clock: Callable[[], datetime],
    downloader: Callable[[str], bytes],
    broker: ReadOnlyBroker,
    bis_parser: Callable[[bytes], Any] = parse_bis_daily_spot_zip,
    oecd_parser: Callable[[bytes], Any] = parse_oecd_monthly_short_rates,
) -> dict[str, Any]:
    """Mock-only acquisition rehearsal; never computes signals or writes files.

    Stage 3B may reuse the validated schema but real connectivity must be
    separately authorized. Never publish raw bytes or broker account data.
    """
    _gate(month_id, clock)  # no download before opening
    start, close = window_bounds(month_id)
    bis = _source(
        month_id=month_id, clock=clock, url=BIS_XRU_URL,
        download=downloader, parser=bis_parser, label="BIS"
    )
    oecd = _source(
        month_id=month_id, clock=clock, url=OECD_STIR_URL,
        download=downloader, parser=oecd_parser, label="OECD"
    )
    broker_snapshot = _broker(month_id=month_id, clock=clock, transport=broker)
    finished = _gate(month_id, clock)

    last_spot = bis["last_observation"]
    last_rate = oecd["last_observation"]
    source_ready = source_gate_ready(
        start, spot_max_date=last_spot, rate_max_month=last_rate
    )
    viable = broker_snapshot["viable_count"] >= M029_MIN_VIABLE_CURRENCIES
    return {
        "readiness_only": True,
        "month_id": month_id,
        "scheduled_decision_utc": utc_iso(start),
        "window_closes_utc": utc_iso(close),
        "observed_at_utc": utc_iso(finished),
        "source": {
            "BIS": bis, "OECD": oecd,
            **required_source_cutoffs(start),
        },
        "source_gate_pass": source_ready,
        "broker": broker_snapshot,
        "broker_gate_pass": viable,
        "classification": (
            "SOURCE_NOT_READY" if not source_ready
            else "BROKER_NOT_READY" if not viable
            else "METADATA_READY_ONLY"
        ),
        "safety": {
            "broker_initialized": False,
            "real_order_api_called": False,
            "account_data_read": False,
            "strategy_signal_computed": False,
            "target_lots_computed": False,
            "strategy_pnl_computed": False,
            "paper_decision_written": False,
        },
    }


def check_isolated_runtime_manifest(
    *,
    wine_binary: str,
    wine_prefix: str,
    system_wine_binary: str,
    original_prefix: str,
    bridge_python: str,
) -> dict[str, Any]:
    """Pure inspection of supplied paths; does not run Wine or test MT5 API."""
    paths = [wine_binary, wine_prefix, system_wine_binary,
             original_prefix, bridge_python]
    if any(not isinstance(x, str) or not x.startswith("/") for x in paths):
        raise EvidenceRefused("ISOLATED_RUNTIME_PATH_MISSING")
    real_paths = [str(Path(x).resolve(strict=False)) for x in paths]
    if real_paths[0] == real_paths[2] or real_paths[1] == real_paths[3]:
        raise EvidenceRefused("ISOLATION_NOT_PROVEN")
    if real_paths[4] == real_paths[0] or real_paths[4] == real_paths[2]:
        raise EvidenceRefused("BRIDGE_PYTHON_INVALID")
    return {
        "isolated_paths_distinct": True,
        "runtime_executed": False,
        "python_import_tested": False,
        "broker_connected": False,
        "read_only": True,
    }
