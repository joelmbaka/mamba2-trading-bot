"""Strict no-trade, no-MT5-dependency validation of M030 tester bar audits.

Expected source rows come from an independently hashed frozen source dataset.
A correct comparison does *not* establish tick-level execution parity.
"""
from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from datetime import timedelta
from pathlib import Path
import math

from .m030_mt5_import import _server_datetime


def _utc_label(dt) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def expected_prefix_from_frame(frame, *, until_utc) -> list[dict]:
    """Build expected source rows from an independent UTC-indexed dataframe.

    Full historical prefix, including independently seeded M1/M5 origins.
    Never resample M1 to fabricate a native M5 source.
    """
    rows = []
    for timestamp, bar in frame.iterrows():
        if timestamp >= until_utc:
            break
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("source bar times must be timezone-aware UTC")
        if timestamp.utcoffset() != timedelta(0):
            raise ValueError("expected frame index must be UTC")
        rows.append({
            "bar_open_utc": _utc_label(timestamp),
            "open": float(bar["open"]), "high": float(bar["high"]),
            "low": float(bar["low"]), "close": float(bar["close"]),
        })
    return rows


def compare_bar_audit(
    path: str | Path,
    *,
    expected: Mapping[str, Sequence[Mapping]],
    verified_server_utc_offset_minutes: int,
    expected_run_id: str,
    expected_symbol: str = "EURUSD",
    price_tolerance: float = 0.0,
) -> dict:
    """Compare exact ordered native-source prefixes; stop at first divergence.

    A numeric tolerance may only be enabled when source price precision and
    rounding are separately documented. The default is strict equality.
    """
    if set(expected) != {"M1", "M5"}:
        raise ValueError("both independent M1 and M5 histories required")
    if not expected_run_id:
        raise ValueError("expected run ID is required")
    if not math.isfinite(price_tolerance) or price_tolerance < 0:
        raise ValueError("invalid price tolerance")
    entries: dict[str, list[dict]] = {"M1": [], "M5": []}
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        needed = {"run_id", "symbol", "timeframe", "server_bar_open",
                  "open", "high", "low", "close"}
        if not needed.issubset(set(reader.fieldnames or [])):
            raise ValueError("incomplete bar-audit schema")
        for line_number, row in enumerate(reader, 2):
            if row["run_id"] != expected_run_id or row["symbol"] != expected_symbol:
                raise ValueError(f"run/symbol mismatch at line {line_number}")
            tf = row["timeframe"]
            if tf not in entries:
                raise ValueError(f"unexpected timeframe {tf} at line {line_number}")
            utc = _server_datetime(row["server_bar_open"],
                                   verified_server_utc_offset_minutes)
            record = {"bar_open_utc": _utc_label(utc)}
            for key in ("open", "high", "low", "close"):
                value = float(row[key])
                if not math.isfinite(value):
                    raise ValueError(f"non-finite {key} at line {line_number}")
                record[key] = value
            seen = entries[tf]
            if seen and record["bar_open_utc"] <= seen[-1]["bar_open_utc"]:
                raise ValueError(f"duplicate or unsorted {tf} at line {line_number}")
            seen.append(record)

    for tf in ("M1", "M5"):
        actual, reference = entries[tf], list(expected[tf])
        if not reference:
            raise ValueError(f"missing expected {tf} source history")
        for index in range(max(len(actual), len(reference))):
            if index >= len(actual) or index >= len(reference):
                return {"matched": False, "timeframe": tf, "index": index,
                        "category": "MISSING_SOURCE_BAR",
                        "expected": reference[index] if index < len(reference) else None,
                        "actual": actual[index] if index < len(actual) else None}
            for field in ("bar_open_utc", "open", "high", "low", "close"):
                x, y = reference[index][field], actual[index][field]
                equal = (x == y if field == "bar_open_utc"
                         else math.isclose(float(x), float(y), rel_tol=0.0,
                                           abs_tol=price_tolerance))
                if not equal:
                    return {"matched": False, "timeframe": tf, "index": index,
                            "category": ("SOURCE_TIME" if field == "bar_open_utc"
                                         else "SOURCE_OHLC"),
                            "field": field, "expected": dict(reference[index]),
                            "actual": actual[index]}
    return {"matched": True, "rows": {tf: len(entries[tf]) for tf in entries}}
