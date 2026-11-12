"""Synthetic contract tests only; never call MT5 or run historical economics."""
from datetime import datetime, timezone

import pytest

from mamba2.backtest.m030_parity import (
    EventSink, compare_events, event, load_jsonl, utc_millis,
)


def sample(**details):
    return event(
        engine="python", kind="SIGNAL", symbol="EURUSD",
        utc_time_ms=1_000, m1_source_open_utc="2026-09-10T00:00:00Z",
        signal="BUY", m1_k=23.5, **details,
    )


def test_requires_explicit_utc_time():
    assert utc_millis(datetime(2026, 9, 10, tzinfo=timezone.utc)) == 1788998400000
    with pytest.raises(ValueError):
        utc_millis(datetime(2026, 9, 10))


def test_identical_independent_events():
    a = sample()
    b = {**a, "source_engine": "mt5", "m1_k": 23.5 + 1e-10}
    assert compare_events([a], [b]) == {"matched": True, "events_compared": 1}


def test_first_divergence_and_raw_evidence():
    a = sample()
    b = {**a, "source_engine": "mt5", "signal": "NONE"}
    result = compare_events([a], [b])
    assert result["category"] == "DECISION_OR_ORDER"
    assert result["field"] == "signal"
    assert result["python"] == a
    assert result["mt5"] == b


def test_mismatched_boundary_fails_before_values():
    a = sample()
    b = {**a, "source_engine": "mt5", "utc_time_ms": 2000}
    assert compare_events([a], [b])["category"] == "BAR_OR_EVENT_ALIGNMENT"


def test_prices_not_rounded_by_default():
    a = sample(bid=1.10000)
    b = {**a, "source_engine": "mt5", "bid": 1.10001}
    assert compare_events([a], [b])["category"] == "PRICE_OR_EXECUTION"


def test_missing_event_and_field():
    a = sample()
    assert compare_events([a], [])["category"] == "MISSING_EVENT"
    b = {**a, "source_engine": "mt5"}
    del b["m1_k"]
    assert compare_events([a], [b])["category"] == "MISSING_FIELD"


def test_exclusive_immutable_jsonl(tmp_path):
    path = tmp_path / "events.jsonl"
    sink = EventSink()
    sink.emit(sample())
    sink.save(path)
    assert load_jsonl(path) == [sample()]
    with pytest.raises(FileExistsError):
        sink.save(path)


def test_schema_and_validations():
    with pytest.raises(ValueError):
        EventSink().emit({"schema_version": "wrong", "event_kind": "SIGNAL"})
    with pytest.raises(ValueError):
        sample(event_kind="EXIT")
    with pytest.raises(ValueError):
        compare_events([], [], price_tolerance=-0.1)
