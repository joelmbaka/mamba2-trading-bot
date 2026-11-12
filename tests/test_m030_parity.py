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


def test_mt5_csv_converter_requires_explicit_server_offset(tmp_path):
    from mamba2.backtest.m030_mt5_import import convert_decision_csv
    path = tmp_path / "probe.csv"
    path.write_text(
        "run_id,symbol,server_boundary,m1_source_open,m5_source_open,"
        "m1_k,m1_d,m5_k,m5_d,ema,atr,signal,reason\n"
        "sample,EURUSD,2026.09.10 03:01:00,2026.09.10 03:00:00,"
        "2026.09.10 02:55:00,19,21,49,51,1.1,0.001,NONE,NO_SIGNAL\n",
        encoding="utf-8",
    )
    events = convert_decision_csv(path, verified_server_utc_offset_minutes=180,
                                  expected_run_id="sample").events
    assert len(events) == 1
    assert events[0]["m1_source_open_utc"] == "2026-09-10T00:00:00Z"
    assert events[0]["m5_source_open_utc"] == "2026-09-09T23:55:00Z"
    assert events[0]["source_engine"] == "mt5"
    with pytest.raises(ValueError):
        convert_decision_csv(path, verified_server_utc_offset_minutes=180,
                             expected_run_id="wrong")
    with pytest.raises(ValueError):
        convert_decision_csv(path, verified_server_utc_offset_minutes=900,
                             expected_run_id="sample")


def test_mt5_csv_rejects_noncompleted_m5_candle(tmp_path):
    from mamba2.backtest.m030_mt5_import import convert_decision_csv
    path = tmp_path / "probe.csv"
    path.write_text(
        "run_id,symbol,server_boundary,m1_source_open,m5_source_open,"
        "m1_k,m1_d,m5_k,m5_d,ema,atr,signal,reason\n"
        "sample,EURUSD,2026.09.10 00:01:00,2026.09.10 00:00:00,"
        "2026.09.10 00:00:00,19,21,49,51,1.1,0.001,NONE,NO_SIGNAL\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="M5 bar is not completed"):
        convert_decision_csv(path, verified_server_utc_offset_minutes=0,
                             expected_run_id="sample")


def test_m030_bar_audit_accepts_distinct_m1_m5_origins(tmp_path):
    from mamba2.backtest.m030_bar_alignment import compare_bar_audit
    path = tmp_path / "audit.csv"
    path.write_text(
        "run_id,symbol,timeframe,server_bar_open,open,high,low,close\n"
        "sample,EURUSD,M1,2025.08.25 03:03:00,1.1,1.2,1.0,1.15\n"
        "sample,EURUSD,M5,2025.08.25 03:00:00,1.2,1.3,1.1,1.25\n",
        encoding="utf-8",
    )
    reference = {
        "M1": [{"bar_open_utc": "2025-08-25T00:03:00Z",
                "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15}],
        "M5": [{"bar_open_utc": "2025-08-25T00:00:00Z",
                "open": 1.2, "high": 1.3, "low": 1.1, "close": 1.25}],
    }
    result = compare_bar_audit(
        path, expected=reference, expected_run_id="sample",
        verified_server_utc_offset_minutes=180,
    )
    assert result == {"matched": True, "rows": {"M1": 1, "M5": 1}}
    modified = {**reference, "M5": [{**reference["M5"][0], "high": 1.31}]}
    mismatch = compare_bar_audit(
        path, expected=modified, expected_run_id="sample",
        verified_server_utc_offset_minutes=180,
    )
    assert mismatch["category"] == "SOURCE_OHLC"
    assert mismatch["timeframe"] == "M5"


def test_m030_bar_audit_rejects_mismatch_and_duplicate(tmp_path):
    from mamba2.backtest.m030_bar_alignment import compare_bar_audit
    path = tmp_path / "audit.csv"
    header = "run_id,symbol,timeframe,server_bar_open,open,high,low,close\n"
    m1 = "sample,EURUSD,M1,2025.08.25 00:03:00,1,2,0,1\n"
    m5 = "sample,EURUSD,M5,2025.08.25 00:00:00,1,2,0,1\n"
    expected = {
        tf: [{"bar_open_utc": f"2025-08-25T00:0{minute}:00Z",
              "open": 1, "high": 2, "low": 0, "close": 1}]
        for tf, minute in (("M1", 3), ("M5", 0))
    }
    path.write_text(header + m1 + m1 + m5, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate or unsorted"):
        compare_bar_audit(path, expected=expected, expected_run_id="sample",
                          verified_server_utc_offset_minutes=0)
    path.write_text(header + m1 + m5, encoding="utf-8")
    result = compare_bar_audit(path, expected=expected, expected_run_id="sample",
                               verified_server_utc_offset_minutes=180)
    assert result["category"] == "SOURCE_TIME"


def test_m030_bar_audit_detects_missing_prefix(tmp_path):
    from mamba2.backtest.m030_bar_alignment import compare_bar_audit
    path = tmp_path / "audit.csv"
    path.write_text(
        "run_id,symbol,timeframe,server_bar_open,open,high,low,close\n"
        "sample,EURUSD,M1,2025.08.25 00:03:00,1,2,0,1\n"
        "sample,EURUSD,M5,2025.08.25 00:00:00,1,2,0,1\n",
        encoding="utf-8",
    )
    expected = {
        "M1": [
            {"bar_open_utc": "2025-08-25T00:02:00Z",
             "open": 1, "high": 2, "low": 0, "close": 1},
            {"bar_open_utc": "2025-08-25T00:03:00Z",
             "open": 1, "high": 2, "low": 0, "close": 1},
        ],
        "M5": [{"bar_open_utc": "2025-08-25T00:00:00Z",
                "open": 1, "high": 2, "low": 0, "close": 1}],
    }
    mismatch = compare_bar_audit(path, expected=expected, expected_run_id="sample",
                                 verified_server_utc_offset_minutes=0)
    assert mismatch["category"] == "SOURCE_TIME"
    assert mismatch["timeframe"] == "M1"
