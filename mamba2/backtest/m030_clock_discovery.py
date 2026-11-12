"""M030 1H: offline, no-broker clock discovery from immutable OHLC sequences.

The source CSV timestamps are an exporter *claim*, not broker clock proof.
No network, MT5, trading, or writing. One constant offset per tested window;
DST/time-varying offsets require separately justified adjacent windows.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
from pathlib import Path
from typing import Mapping

FROZEN_START = datetime(2026, 9, 10, tzinfo=timezone.utc)
FROZEN_END = datetime(2026, 9, 11, tzinfo=timezone.utc)
EXPECTED_COUNTS = {"M1": 1440, "M5": 288}
_FIELDS = ("open", "high", "low", "close")


def _digest(path: str | Path) -> str:
    sha = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _utc(value: str) -> datetime:
    value = value.strip()
    if not value:
        raise ValueError("empty UTC timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid UTC timestamp: {value}") from exc
    if result.tzinfo is None or result.utcoffset() != timedelta(0):
        raise ValueError("expected source timestamp must explicitly be UTC")
    if result.second or result.microsecond:
        raise ValueError("expected bar-open timestamp must be minute-aligned")
    return result


def _unix_seconds_utc(value: str) -> datetime:
    """Interpret the exporter 'time' field as an explicit UTC Unix second.

    This is an exporter format declaration, NOT independent proof of
    MetaQuotes-Demo historical server clock behavior.
    """
    raw = value.strip()
    if not raw or not raw.isascii() or not raw.isdecimal():
        raise ValueError("Unix UTC bar timestamp must be an integer epoch second")
    try:
        stamp = datetime.fromtimestamp(int(raw), tz=timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError("Unix UTC bar timestamp out of supported range") from exc
    if stamp.second or stamp.microsecond:
        raise ValueError("Unix UTC bar timestamp must be minute-aligned")
    return stamp


def _server(value: str) -> datetime:
    try:
        result = datetime.strptime(value, "%Y.%m.%d %H:%M:%S")
    except ValueError as exc:
        raise ValueError(f"invalid server-local timestamp: {value}") from exc
    if result.second or result.microsecond:
        raise ValueError("server bar open must be minute-aligned")
    return result


def _prices(record: Mapping[str, str]) -> tuple[Decimal, ...]:
    try:
        values = tuple(Decimal(record[name]) for name in _FIELDS)
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise ValueError("invalid OHLC values") from exc
    if not all(v.is_finite() for v in values):
        raise ValueError("non-finite OHLC")
    if values[1] < max(values[0], values[3]) or values[2] > min(values[0], values[3]):
        raise ValueError("OHLC extrema inconsistent")
    return values


def _load_reference(path: str | Path, *, start: datetime, end: datetime,
                    timestamp_format: str) -> dict:
    if timestamp_format not in {"iso8601_utc", "unix_seconds_utc"}:
        raise ValueError("reference timestamp format must be explicitly declared")
    expected = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        source_column = next(
            (key for key in ("bar_open_utc", "time", "datetime", "timestamp")
             if key in columns), None
        )
        if source_column is None or not set(_FIELDS).issubset(columns):
            raise ValueError("reference requires explicit UTC timestamp and OHLC columns")
        previous = None
        for row in reader:
            if timestamp_format == "unix_seconds_utc" and source_column != "time":
                raise ValueError("exporter epoch-second format requires 'time' column")
            stamp = (_unix_seconds_utc(row[source_column])
                     if timestamp_format == "unix_seconds_utc"
                     else _utc(row[source_column]))
            if previous is not None and stamp <= previous:
                raise ValueError("reference source timestamps duplicate or out of order")
            previous = stamp
            if start <= stamp < end:
                expected[stamp.replace(tzinfo=None)] = _prices(row)
    return expected


def _load_probe(path: str | Path, *, run_id: str) -> dict:
    records = {"M1": {}, "M5": {}}
    last_bar = {"M1": None, "M5": None}
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        required = {"run_id", "symbol", "timeframe", "server_bar_open",
                    "server_m1_boundary", "server_observed_tick", *_FIELDS}
        if not required.issubset(columns):
            raise ValueError("incomplete M030 clock-probe schema")
        for row in reader:
            if row["run_id"] != run_id or row["symbol"] != "EURUSD":
                raise ValueError("clock-probe run/symbol mismatch")
            tf = row["timeframe"]
            if tf not in records:
                raise ValueError("unexpected timeframe")
            opened = _server(row["server_bar_open"])
            boundary = _server(row["server_m1_boundary"])
            observed = datetime.strptime(row["server_observed_tick"],
                                         "%Y.%m.%d %H:%M:%S")
            if not opened < boundary <= observed:
                raise ValueError("uncompleted probe source bar")
            expected_open = (
                boundary-timedelta(minutes=1)
                if tf == "M1"
                else datetime(1970,1,1) +
                timedelta(seconds=(
                    int((boundary-datetime(1970,1,1)).total_seconds())//300-1
                )*300)
            )
            if opened != expected_open:
                raise ValueError("probe source timestamp is stale or shifted")
            if last_bar[tf] is not None and opened <= last_bar[tf]:
                raise ValueError("duplicate or reversed native bar")
            last_bar[tf] = opened
            records[tf][opened] = _prices(row)
    return records


def discover_clock_offset(
    probe_csv: str | Path, reference_m1_csv: str | Path,
    reference_m5_csv: str | Path, *, run_id: str,
    expected_sha256: Mapping[str, str],
    window_start: datetime = FROZEN_START,
    window_end: datetime = FROZEN_END,
    expected_counts: Mapping[str, int] = EXPECTED_COUNTS,
    candidate_offsets_minutes: range | tuple[int, ...] = range(-840, 841, 15),
    reference_timestamp_format: str = "iso8601_utc",
) -> dict:
    """Require a unique exact M1/M5 timestamp+OHLC mapping and full coverage.

    Candidate means server wall time = claimed UTC + offset. The canonical
    MT5 exporter uses reference_timestamp_format="unix_seconds_utc" for its
    integer 'time' column. The format must be selected explicitly; doing so
    does not independently verify the exporter's UTC clock assertion.
    """
    if not run_id:
        raise ValueError("run ID required")
    if window_start.tzinfo != timezone.utc or window_end.tzinfo != timezone.utc:
        raise ValueError("window timestamps must explicitly be UTC")
    if window_start >= window_end:
        raise ValueError("invalid window")
    paths = {"probe": probe_csv, "M1": reference_m1_csv, "M5": reference_m5_csv}
    if set(expected_sha256) != set(paths):
        raise ValueError("all independent source hashes are mandatory")
    actual_hashes = {name: _digest(path) for name, path in paths.items()}
    for key, actual in actual_hashes.items():
        if actual != expected_sha256[key]:
            raise ValueError(f"{key} SHA-256 mismatch")
    expected = {
        "M1": _load_reference(reference_m1_csv, start=window_start, end=window_end,
                              timestamp_format=reference_timestamp_format),
        "M5": _load_reference(reference_m5_csv, start=window_start, end=window_end,
                              timestamp_format=reference_timestamp_format),
    }
    for tf in ("M1", "M5"):
        if len(expected[tf]) != expected_counts[tf]:
            raise ValueError(f"incomplete canonical {tf} comparison window")
    native = _load_probe(probe_csv, run_id=run_id)
    successes = []
    failures = []
    for offset in candidate_offsets_minutes:
        if not isinstance(offset, int) or abs(offset) > 840:
            raise ValueError("candidate offset must be an integer within ±14h")
        discrepancy = None
        checked = {}
        for tf in ("M1", "M5"):
            checked[tf] = 0
            for utc_open, expected_ohlc in expected[tf].items():
                server_open = utc_open + timedelta(minutes=offset)
                observed = native[tf].get(server_open)
                if observed is None:
                    discrepancy = {"timeframe": tf, "reason": "MISSING_BAR",
                                   "utc_bar_open": utc_open.isoformat(),
                                   "server_bar_open": server_open.isoformat()}
                    break
                if observed != expected_ohlc:
                    discrepancy = {"timeframe": tf, "reason": "OHLC_DIFFERENCE",
                                   "utc_bar_open": utc_open.isoformat(),
                                   "server_bar_open": server_open.isoformat()}
                    break
                checked[tf] += 1
            if discrepancy is not None:
                break
        if discrepancy is None:
            successes.append(int(offset))
        else:
            failures.append({"offset_minutes": int(offset), **discrepancy})
    status = ("UNIQUE" if len(successes) == 1
              else "AMBIGUOUS" if successes else "NO_MATCH")
    return {
        "status": status, "offset_minutes": successes[0] if status == "UNIQUE" else None,
        "matching_candidates": successes,
        "expected_rows": {tf: len(expected[tf]) for tf in ("M1", "M5")},
        "observed_rows": {tf: len(native[tf]) for tf in ("M1", "M5")},
        "source_sha256": actual_hashes,
        "first_failures": failures,
        "note": "A match proves alignment only for these observed bars and this UTC window; not historical warm-up or tick identity.",
    }
