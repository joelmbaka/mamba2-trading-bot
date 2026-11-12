"""Synthetic-only acceptance tests for the M029 prospective recovery gate."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

import pytest

from mamba2.backtest.m029_prospective import (
    M029_FIRST_MONTH,
    metadata_readiness,
    read_decision,
    record_path,
    utc_iso,
    window_bounds,
    window_status,
    write_decision,
)


def dt(y, m, d, h=0, minute=0, second=0):
    return datetime(y, m, d, h, minute, second, tzinfo=timezone.utc)


def sample_record(month="2026-12", at=None):
    start, _ = window_bounds(month)
    at = at or start
    observed = utc_iso(at)
    return {
        "version": 1,
        "decision_id": month,
        "scheduled_decision_utc": utc_iso(start),
        "created_at_utc": observed,
        "source": {
            "bis_raw_sha256": "a" * 64,
            "oecd_raw_sha256": "b" * 64,
            "spot_panel_sha256": "c" * 64,
            "rate_panel_sha256": "d" * 64,
            "observed_at_utc": observed,
            "required_spot_through": "2026-11-30",
            "required_rate_month": "2026-10",
        },
        "broker": {
            "observed_at_utc": observed,
            "currencies": {},
        },
        "plan": {
            "status": "FORWARD_PAPER_NOT_READY",
            "reason": "SOURCE_NOT_READY",
            "targets": {},
            "cost_evidence": {
                "commission": None,
                "slippage": None,
                "financing": None,
                "net_pnl": None,
            },
        },
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


def synthetic_quotes(at, count=8):
    quotes = {}
    for code in ("AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "SEK")[:count]:
        quotes[code] = {
            "bid": 1.0,
            "ask": 1.001,
            "buy_margin_per_lot": 1000,
            "sell_margin_per_lot": 1000,
            "quote_timestamp_utc": utc_iso(at),
        }
    return quotes


def test_m029_first_month_is_december_no_backfill():
    assert M029_FIRST_MONTH == "2026-12"
    assert window_bounds("2026-12") == (
        dt(2026, 12, 7, 12),
        dt(2026, 12, 7, 12, 10),
    )
    assert window_bounds("2027-01") == (
        dt(2027, 1, 7, 12),
        dt(2027, 1, 7, 12, 10),
    )
    assert window_status("2026-10", dt(2026, 10, 7, 12)) == (
        "INELIGIBLE_HISTORICAL_MONTH"
    )
    assert window_status("2026-11", dt(2026, 11, 6, 12)) == (
        "INELIGIBLE_HISTORICAL_MONTH"
    )


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (dt(2026, 12, 7, 11, 59, 59), "WINDOW_NOT_OPEN"),
        (dt(2026, 12, 7, 12), "WINDOW_OPEN"),
        (dt(2026, 12, 7, 12, 9, 59), "WINDOW_OPEN"),
        (dt(2026, 12, 7, 12, 10), "MISSED_WINDOW"),
        (dt(2026, 12, 8), "MISSED_WINDOW"),
        (dt(2027, 1, 1), "MISSED_WINDOW"),
    ],
)
def test_strict_half_open_window(now, expected):
    assert window_status("2026-12", now) == expected


def test_timestamps_must_be_timezone_aware_and_month_canonical():
    with pytest.raises(ValueError, match="timezone"):
        window_status("2026-12", datetime(2026, 12, 7, 12))
    for bad in ("2026-1", "2026-00", "2026-13", "../../2026-12", "0000-01"):
        with pytest.raises(ValueError):
            window_bounds(bad)


def test_same_instant_with_non_utc_offset_is_consistent():
    east_africa = timezone(timedelta(hours=3))
    now = datetime(2026, 12, 7, 15, 0, tzinfo=east_africa)
    assert window_status("2026-12", now) == "WINDOW_OPEN"
    assert utc_iso(now) == "2026-12-07T12:00:00Z"


def test_missing_file_probe_is_pure(tmp_path):
    path = record_path(tmp_path, "2026-12")
    assert not path.exists()
    assert read_decision(tmp_path, "2026-12") is None
    assert not path.exists()
    assert not tmp_path.joinpath("2026-12-decision.json").exists()


def test_on_time_synthetic_flat_record_is_exclusive_and_hash_checked(tmp_path):
    now = dt(2026, 12, 7, 12, 1)
    record = sample_record(at=now)
    stored, reused = write_decision(tmp_path, "2026-12", record, now=now)
    assert reused is False
    assert stored["decision_record_sha256"]
    assert stored["plan"]["cost_evidence"]["net_pnl"] is None
    assert read_decision(tmp_path, "2026-12") == stored

    original_bytes = record_path(tmp_path, "2026-12").read_bytes()
    new_payload = sample_record(at=now)
    new_payload["plan"]["reason"] = "BROKER_NOT_READY"
    same, reused = write_decision(tmp_path, "2026-12", new_payload, now=now)
    assert reused is True
    assert same == stored
    assert record_path(tmp_path, "2026-12").read_bytes() == original_bytes


@pytest.mark.parametrize("at", [
    dt(2026, 12, 7, 11, 59),
    dt(2026, 12, 7, 12, 10),
    dt(2026, 12, 8, 12),
])
def test_refuse_early_or_late_decision_without_creating_directory(tmp_path, at):
    with pytest.raises(RuntimeError, match="WINDOW_NOT_OPEN|MISSED_WINDOW"):
        write_decision(tmp_path / "journal", "2026-12", sample_record(at=at), now=at)
    assert not (tmp_path / "journal").exists()


@pytest.mark.parametrize("month, at", [
    ("2026-10", dt(2026, 10, 7, 12)),
    ("2026-11", dt(2026, 11, 6, 12)),
])
def test_refuse_october_november_even_at_their_original_time(tmp_path, month, at):
    with pytest.raises(RuntimeError, match="INELIGIBLE_HISTORICAL_MONTH"):
        write_decision(tmp_path, month, sample_record(at=at), now=at)


def test_refuse_tampered_hash_without_overwriting(tmp_path):
    now = dt(2026, 12, 7, 12, 1)
    write_decision(tmp_path, "2026-12", sample_record(at=now), now=now)
    file = record_path(tmp_path, "2026-12")
    parsed = json.loads(file.read_text())
    parsed["plan"]["reason"] = "TAMPERED"
    file.write_text(json.dumps(parsed))
    old = file.read_bytes()
    with pytest.raises(ValueError, match="hash mismatch"):
        read_decision(tmp_path, "2026-12")
    with pytest.raises(ValueError, match="hash mismatch"):
        write_decision(tmp_path, "2026-12", sample_record(at=now), now=now)
    assert file.read_bytes() == old


def test_refuse_corrupt_record_without_overwriting(tmp_path):
    file = record_path(tmp_path, "2026-12")
    file.write_text("{invalid")
    with pytest.raises(ValueError, match="unreadable"):
        write_decision(
            tmp_path, "2026-12",
            sample_record(at=dt(2026, 12, 7, 12)),
            now=dt(2026, 12, 7, 12),
        )
    assert file.read_text() == "{invalid"


def test_refuse_symlink_decision(tmp_path):
    target = tmp_path / "target.json"
    target.write_text("{}")
    file = record_path(tmp_path, "2026-12")
    file.symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        read_decision(tmp_path, "2026-12")


def test_refuse_unstamped_or_incomplete_cost_evidence(tmp_path):
    at = dt(2026, 12, 7, 12)
    record = sample_record(at=at)
    record["plan"]["cost_evidence"]["net_pnl"] = 1000
    with pytest.raises(ValueError, match="net_pnl"):
        write_decision(tmp_path, "2026-12", record, now=at)

    record = sample_record(at=at)
    record["safety"]["real_order_api_called"] = True
    with pytest.raises(ValueError, match="unsafe"):
        write_decision(tmp_path, "2026-12", record, now=at)

    record = sample_record(at=at)
    record["source"]["observed_at_utc"] = "2026-12-08T12:00:00Z"
    with pytest.raises(ValueError, match="source observation"):
        write_decision(tmp_path, "2026-12", record, now=at)
    assert not record_path(tmp_path, "2026-12").exists()


def test_metadata_gate_reports_only_sources_and_broker_viability():
    now = dt(2026, 12, 7, 12, 1)
    quotes = synthetic_quotes(now)
    ready = metadata_readiness(
        "2026-12", now,
        spot_max_date="2026-11-30",
        rate_max_month="2026-10",
        broker_currencies=quotes,
    )
    assert ready["classification"] == "READY_FOR_SCHEDULED_DECISION"
    assert ready["viable_count"] == 8
    assert ready["clock_gate"] == "WINDOW_OPEN"
    assert ready["signal_computed"] is False
    assert ready["target_lots_computed"] is False
    assert ready["strategy_pnl_computed"] is False

    source_failed = metadata_readiness(
        "2026-12", now,
        spot_max_date="2026-11-27",
        rate_max_month="2026-10",
        broker_currencies=quotes,
    )
    assert source_failed["classification"] == "SOURCE_NOT_READY"

    broker_failed = metadata_readiness(
        "2026-12", now,
        spot_max_date="2026-11-30",
        rate_max_month="2026-10",
        broker_currencies=synthetic_quotes(now, count=3),
    )
    assert broker_failed["classification"] == "BROKER_NOT_READY"


def test_quote_viability_rejects_stale_future_inverted_and_missing_margin():
    now = dt(2026, 12, 7, 12, 1)
    quotes = synthetic_quotes(now)
    quotes["AUD"]["quote_timestamp_utc"] = utc_iso(now - timedelta(seconds=301))
    quotes["CAD"]["quote_timestamp_utc"] = utc_iso(now + timedelta(seconds=1))
    quotes["CHF"]["ask"] = 0.9
    quotes["EUR"]["sell_margin_per_lot"] = None
    result = metadata_readiness(
        "2026-12", now,
        spot_max_date="2026-11-30",
        rate_max_month="2026-10",
        broker_currencies=quotes,
    )
    assert result["viable_count"] == 4
    assert result["broker_gate_pass"] is True
    assert result["viable_currencies"] == ["GBP", "JPY", "NZD", "SEK"]


def test_future_month_readiness_does_not_authorize_early_execution():
    result = metadata_readiness(
        "2026-12", dt(2026, 11, 12, 12),
        spot_max_date="2026-11-30",
        rate_max_month="2026-10",
        broker_currencies=synthetic_quotes(dt(2026, 11, 12, 12)),
    )
    assert result["clock_gate"] == "WINDOW_NOT_OPEN"
    assert result["signal_computed"] is False
    assert result["target_lots_computed"] is False


def test_hash_input_rejects_forged_presealed_record(tmp_path):
    at = dt(2026, 12, 7, 12)
    record = sample_record(at=at)
    record["decision_record_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="pre-sealed"):
        write_decision(tmp_path, "2026-12", record, now=at)
