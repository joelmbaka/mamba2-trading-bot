"""Convert M030 MQL5 no-order decision CSV to the canonical event schema.

MQL5 timestamps are **server time**, never automatically UTC. Require a
verified, explicit server-to-UTC offset. This does not establish tick identity.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .m030_parity import EventSink, event, utc_millis


def _server_datetime(value: str, utc_offset_minutes: int) -> datetime:
    if not isinstance(utc_offset_minutes, int) or not -840 <= utc_offset_minutes <= 840:
        raise ValueError("verified server UTC offset must be an integer in minutes")
    local = datetime.strptime(value, "%Y.%m.%d %H:%M:%S")
    source_tz = timezone(timedelta(minutes=utc_offset_minutes))
    return local.replace(tzinfo=source_tz).astimezone(timezone.utc)


def convert_decision_csv(path: str | Path, *, verified_server_utc_offset_minutes: int,
                         expected_run_id: str, expected_symbol: str = "EURUSD") -> EventSink:
    """Convert without guessing the broker server clock or rewriting source."""
    if not expected_run_id:
        raise ValueError("run id must be nonempty")
    sink = EventSink()
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        needed = {"run_id", "symbol", "server_boundary", "m1_source_open",
                  "m5_source_open", "m1_k", "m1_d", "m5_k", "m5_d",
                  "ema", "atr", "signal", "reason"}
        if not needed.issubset(set(reader.fieldnames or ())):
            raise ValueError("missing M030 decision columns")
        previous = None
        for row in reader:
            if row["run_id"] != expected_run_id or row["symbol"] != expected_symbol:
                raise ValueError("run or symbol mismatch")
            boundary = _server_datetime(row["server_boundary"], verified_server_utc_offset_minutes)
            opening = _server_datetime(row["m1_source_open"], verified_server_utc_offset_minutes)
            m5_open = _server_datetime(row["m5_source_open"], verified_server_utc_offset_minutes)
            if (boundary - opening) != timedelta(minutes=1):
                raise ValueError("M1 decision does not use most recently completed candle")
            # At a minute boundary the most recent *completed* M5 bar is
            # the bar beginning one M5 interval before its aligned close.
            m5_boundary = boundary.replace(
                minute=(boundary.minute // 5) * 5, second=0, microsecond=0
            )
            expected_m5_open = m5_boundary - timedelta(minutes=5)
            if m5_open > expected_m5_open:
                raise ValueError("M5 bar is not completed")
            if m5_open != expected_m5_open:
                raise ValueError("M5 source bar is stale or misaligned")
            if previous is not None and boundary <= previous:
                raise ValueError("duplicate or nonmonotonic tester boundary")
            previous = boundary
            signal = row["signal"]
            if signal not in {"BUY", "SELL", "NONE"}:
                raise ValueError("unexpected signal")
            sink.emit(event(
                engine="mt5", kind="SIGNAL", symbol=expected_symbol,
                utc_time_ms=utc_millis(boundary),
                m1_source_open_utc=opening.strftime("%Y-%m-%dT%H:%M:%SZ"),
                m5_source_open_utc=m5_open.strftime("%Y-%m-%dT%H:%M:%SZ"),
                run_id=expected_run_id, signal=signal,
                reason_or_error_code=row["reason"],
                m1_k=float(row["m1_k"]), m1_d=float(row["m1_d"]),
                m5_k=float(row["m5_k"]), m5_d=float(row["m5_d"]),
                ema=float(row["ema"]), atr=float(row["atr"]),
            ))
    return sink
