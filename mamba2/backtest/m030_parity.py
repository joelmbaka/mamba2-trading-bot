"""M030 observation-only event format and first-divergence comparison.

No MT5 imports, no broker calls, no trading side effects.  The event sink is
explicitly opt-in, and JSONL outputs must be stored outside tracked histories.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "m030.events.v1"
KINDS = frozenset({
    "M1_CLOSE", "SIGNAL", "SUBMIT", "FILL", "SLTP_MODIFY",
    "EXIT", "REJECT", "ACCOUNT",
})
# Runtime-generated, implementation-specific ticket IDs are diagnostic; do not
# incorrectly require identical numeric IDs from independent engines.
ALIGNMENT_FIELDS = ("symbol", "event_kind", "utc_time_ms", "m1_source_open_utc")
EXACT_FIELDS = ("side", "volume_lots", "signal", "reason_or_error_code")
NUMERIC_FIELDS = ("m1_k", "m1_d", "m5_k", "m5_d", "ema", "atr",
                  "bid", "ask", "entry_or_exit_price", "sl", "tp",
                  "gross_pl", "commission", "swap", "net_pl")


def utc_millis(value: datetime) -> int:
    """Require offset-aware datetimes; never silently assume server-local UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("UTC event timestamp must be timezone-aware")
    return int(value.astimezone(timezone.utc).timestamp() * 1000)


def event(*, engine: str, kind: str, symbol: str, utc_time_ms: int,
          m1_source_open_utc: str, **details: Any) -> dict[str, Any]:
    if not engine or not symbol or kind not in KINDS:
        raise ValueError("invalid engine/symbol/event kind")
    if not isinstance(utc_time_ms, int) or utc_time_ms < 0:
        raise ValueError("utc_time_ms must be a nonnegative integer")
    if not m1_source_open_utc.endswith("Z"):
        raise ValueError("M1 bar open must be expressed in UTC")
    if "event_kind" in details or "schema_version" in details:
        raise ValueError("reserved event field")
    return {
        "schema_version": SCHEMA_VERSION,
        "source_engine": engine,
        "symbol": symbol,
        "event_kind": kind,
        "utc_time_ms": utc_time_ms,
        "m1_source_open_utc": m1_source_open_utc,
        **details,
    }


@dataclass
class EventSink:
    """Caller-owned in-memory collector. Nothing writes unless save() is called."""
    events: list[dict[str, Any]] = field(default_factory=list)

    def emit(self, record: Mapping[str, Any]) -> None:
        if record.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("wrong event schema version")
        if record.get("event_kind") not in KINDS:
            raise ValueError("unsupported event kind")
        self.events.append(dict(record))

    def save(self, path: str | Path) -> None:
        target = Path(path)
        if target.exists():
            raise FileExistsError(f"refusing to overwrite evidence: {target}")
        # Exclusive creation prevents accidental overwrite of immutable evidence.
        with target.open("x", encoding="utf-8", newline="\n") as stream:
            for record in self.events:
                stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    for number, record in enumerate(records, 1):
        if record.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"invalid event version at line {number}")
        if record.get("event_kind") not in KINDS:
            raise ValueError(f"invalid event kind at line {number}")
    return records


def _equal(left: Any, right: Any, *, atol: float) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left == right
    if isinstance(left, (float, int)) and isinstance(right, (float, int)):
        return math.isfinite(float(left)) and math.isfinite(float(right)) and math.isclose(
            float(left), float(right), rel_tol=0.0, abs_tol=atol)
    return left == right


def compare_events(
    python_events: Iterable[Mapping[str, Any]],
    mt5_events: Iterable[Mapping[str, Any]],
    *,
    indicator_tolerance: float = 1e-9,
    price_tolerance: float = 0.0,
) -> dict[str, Any]:
    """Compare ordered streams; stop on first difference, retaining raw records.

    IMPORTANT: a price tolerance must only be enabled after matching tick
    provenance and execution cadence have been independently established.
    """
    if indicator_tolerance < 0 or price_tolerance < 0:
        raise ValueError("tolerances must be non-negative")
    a, b = list(python_events), list(mt5_events)
    for index in range(max(len(a), len(b))):
        if index >= len(a) or index >= len(b):
            return {"matched": False, "index": index, "category": "MISSING_EVENT",
                    "python": a[index] if index < len(a) else None,
                    "mt5": b[index] if index < len(b) else None}
        left, right = a[index], b[index]
        fields = ("schema_version",) + ALIGNMENT_FIELDS + EXACT_FIELDS + NUMERIC_FIELDS
        for key in fields:
            if key not in left and key not in right:
                continue
            if key not in left or key not in right:
                return {"matched": False, "index": index, "field": key,
                        "category": "MISSING_FIELD", "python": dict(left), "mt5": dict(right)}
            tol = (indicator_tolerance if key in {"m1_k","m1_d","m5_k","m5_d","ema","atr"}
                   else price_tolerance if key in {"bid","ask","entry_or_exit_price","sl","tp"}
                   else 0.0)
            if not _equal(left[key], right[key], atol=tol):
                category = ("BAR_OR_EVENT_ALIGNMENT" if key in ALIGNMENT_FIELDS
                            else "INDICATOR_ARITHMETIC" if key in {"m1_k","m1_d","m5_k","m5_d","ema","atr"}
                            else "PRICE_OR_EXECUTION" if key in {"bid","ask","entry_or_exit_price","sl","tp"}
                            else "ACCOUNTING" if key in {"gross_pl","commission","swap","net_pl"}
                            else "DECISION_OR_ORDER")
                return {"matched": False, "index": index, "field": key,
                        "category": category, "python": dict(left), "mt5": dict(right)}
    return {"matched": True, "events_compared": len(a)}


def main() -> None:
    """Offline CLI: python -m mamba2.backtest.m030_parity python.jsonl mt5.jsonl"""
    import argparse
    parser = argparse.ArgumentParser(description="M030 event ledger parity (read-only)")
    parser.add_argument("python_jsonl")
    parser.add_argument("mt5_jsonl")
    args = parser.parse_args()
    outcome = compare_events(load_jsonl(args.python_jsonl), load_jsonl(args.mt5_jsonl))
    print(json.dumps(outcome, indent=2, sort_keys=True))
    if not outcome["matched"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
