"""Stage 3A journal boundary and timestamp provenance regression tests.

Creates only temporary synthetic records; never opens MT5 or network resources.
"""

from datetime import datetime, timedelta, timezone

import pytest

from mamba2.backtest.m029_prospective import (
    read_decision, record_path, utc_iso, write_decision,
)


OPEN = datetime(2026, 12, 7, 12, tzinfo=timezone.utc)
CLOSE = datetime(2026, 12, 7, 12, 10, tzinfo=timezone.utc)


def flat_record(at=OPEN):
    sha = lambda char: char * 64
    return {
        "version": 1,
        "decision_id": "2026-12",
        "scheduled_decision_utc": utc_iso(OPEN),
        "created_at_utc": utc_iso(at),
        "source": {
            "bis_raw_sha256": sha("a"),
            "oecd_raw_sha256": sha("b"),
            "spot_panel_sha256": sha("c"),
            "rate_panel_sha256": sha("d"),
            "observed_at_utc": utc_iso(at),
            "required_spot_through": "2026-11-30",
            "required_rate_month": "2026-10",
        },
        "broker": {"observed_at_utc": utc_iso(at)},
        "plan": {
            "status": "FORWARD_PAPER_NOT_READY",
            "reason": "BROKER_NOT_READY",
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


def test_final_clock_allows_on_time_synthetic_file_only(tmp_path):
    at = OPEN + timedelta(seconds=1)
    record, reused = write_decision(
        tmp_path, "2026-12", flat_record(at),
        now=at, clock=lambda: at + timedelta(microseconds=1)
    )
    assert reused is False
    assert read_decision(tmp_path, "2026-12") == record


@pytest.mark.parametrize(("final", "expected"), [
    (OPEN - timedelta(microseconds=1), "CLOCK_MOVED_BACKWARD"),
    (CLOSE, "MISSED_WINDOW"),
    (CLOSE + timedelta(seconds=1), "MISSED_WINDOW"),
])
def test_final_clock_refuses_without_creating_decision_file(tmp_path, final, expected):
    with pytest.raises(RuntimeError, match=expected):
        write_decision(
            tmp_path, "2026-12", flat_record(),
            now=OPEN, clock=lambda: final
        )
    assert not record_path(tmp_path, "2026-12").exists()


def test_missed_window_can_only_reuse_existing_valid_ledger(tmp_path):
    existing, first = write_decision(
        tmp_path, "2026-12", flat_record(),
        now=OPEN, clock=lambda: OPEN
    )
    assert first is False
    original = record_path(tmp_path, "2026-12").read_bytes()
    later, reused = write_decision(
        tmp_path, "2026-12", flat_record(),
        now=CLOSE, clock=lambda: CLOSE
    )
    assert reused is True
    assert later == existing
    assert record_path(tmp_path, "2026-12").read_bytes() == original


def test_parent_symlink_cannot_be_used_as_journal_directory(tmp_path):
    original = tmp_path / "actual"
    original.mkdir()
    link = tmp_path / "alias"
    link.symlink_to(original, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        write_decision(link, "2026-12", flat_record(), now=OPEN)
    assert not (original / "2026-12-decision.json").exists()


def test_missing_or_corrupt_existing_record_is_never_rewritten(tmp_path):
    p = record_path(tmp_path, "2026-12")
    p.write_text("bad-json", encoding="utf-8")
    with pytest.raises(ValueError, match="unreadable"):
        write_decision(
            tmp_path, "2026-12", flat_record(),
            now=OPEN, clock=lambda: OPEN
        )
    assert p.read_text() == "bad-json"


def test_old_october_november_months_remain_forbidden(tmp_path):
    for month in ("2026-10", "2026-11"):
        with pytest.raises(RuntimeError, match="INELIGIBLE_HISTORICAL_MONTH"):
            write_decision(tmp_path, month, flat_record(), now=OPEN,
                           clock=lambda: OPEN)
