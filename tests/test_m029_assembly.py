"""M029 Stage-2 synthetic-only assembly tests.

No network, MetaTrader, account, order, historical economics or P/L fixtures.
"""

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

import mamba2.backtest.m029_assembly as assembly
from mamba2.backtest.m029_prospective import (
    read_decision,
    utc_iso,
    write_decision,
)


AT = datetime(2026, 12, 7, 12, 1, tzinfo=timezone.utc)
CURRENCIES = ("AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "SEK")
PAIRS = ("AUDUSD", "USDCAD", "USDCHF", "EURUSD", "GBPUSD",
         "USDJPY", "NZDUSD", "USDSEK")


def broker(at=AT):
    return {
        code: {
            "symbol": pair,
            "bid": 1.0,
            "ask": 1.0002,
            "quote_timestamp_utc": utc_iso(at),
            "contract_size": 100_000,
            "volume_min": 0.01,
            "volume_max": 500,
            "volume_step": 0.01,
            "buy_margin_per_lot": 1000.0,
            "sell_margin_per_lot": 1000.0,
        }
        for code, pair in zip(CURRENCIES, PAIRS)
    }


def install_synthetic_parsers(monkeypatch, *, spot_date="2026-11-30", rate_month="2026-10"):
    spots = pd.DataFrame(
        {"AUD": [1.2]},
        index=pd.DatetimeIndex([spot_date], tz="UTC"),
    )
    rates = pd.DataFrame(
        {"USA": [3.0]},
        index=pd.period_range(rate_month, periods=1, freq="M"),
    )
    monkeypatch.setattr(assembly, "parse_bis_daily_spot_zip", lambda raw: spots)
    monkeypatch.setattr(assembly, "parse_oecd_monthly_short_rates", lambda raw: rates)


def draft(now=AT, quotes=None):
    return assembly.draft_from_supplied_snapshots(
        month_id="2026-12",
        now=now,
        bis_raw=b"SYNTHETIC BIS",
        oecd_raw=b"SYNTHETIC OECD",
        broker_currencies=broker() if quotes is None else quotes,
    )


@pytest.mark.parametrize("now", [
    datetime(2026, 12, 7, 11, 59, tzinfo=timezone.utc),
    datetime(2026, 12, 7, 12, 10, tzinfo=timezone.utc),
    datetime(2026, 12, 8, 12, tzinfo=timezone.utc),
])
def test_outside_window_refuses_before_touching_source(monkeypatch, now):
    def forbidden(_):
        raise AssertionError("must not parse source outside window")
    monkeypatch.setattr(assembly, "parse_bis_daily_spot_zip", forbidden)
    with pytest.raises(RuntimeError, match="WINDOW_NOT_OPEN|MISSED_WINDOW"):
        draft(now=now)


def test_missed_november_produces_no_draft(monkeypatch):
    monkeypatch.setattr(
        assembly, "parse_bis_daily_spot_zip",
        lambda _: (_ for _ in ()).throw(AssertionError("no parsing")),
    )
    with pytest.raises(RuntimeError, match="INELIGIBLE_HISTORICAL_MONTH"):
        assembly.draft_from_supplied_snapshots(
            month_id="2026-11",
            now=datetime(2026, 11, 6, 12, tzinfo=timezone.utc),
            bis_raw=b"mock",
            oecd_raw=b"mock",
            broker_currencies=broker(),
        )


def test_missing_spot_cutoff_is_flat_without_signal_or_target(monkeypatch, tmp_path):
    install_synthetic_parsers(monkeypatch, spot_date="2026-11-27")
    monkeypatch.setattr(
        assembly, "build_live_source_signal_snapshot",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("signal called")),
    )
    monkeypatch.setattr(
        assembly, "build_shadow_target_plan",
        lambda *args: (_ for _ in ()).throw(AssertionError("target called")),
    )
    record = draft()
    assert record["source_gate_pass"] is False
    assert record["signal"] is None
    assert record["plan"]["status"] == "FORWARD_PAPER_NOT_READY"
    assert record["plan"]["reason"] == "SOURCE_NOT_READY"
    assert record["holding_period_return"] is None
    assert record["plan"]["cost_evidence"]["net_pnl"] is None

    sealed, reused = write_decision(tmp_path, "2026-12", record, now=AT)
    assert reused is False
    assert read_decision(tmp_path, "2026-12") == sealed


def test_unavailable_broker_is_flat_without_signal(monkeypatch):
    install_synthetic_parsers(monkeypatch)
    monkeypatch.setattr(
        assembly, "build_live_source_signal_snapshot",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("signal called")),
    )
    incomplete = broker()
    for code in CURRENCIES[3:]:
        del incomplete[code]
    result = draft(quotes=incomplete)
    assert result["source_gate_pass"] is True
    assert result["broker"]["viable_count"] == 3
    assert result["signal"] is None
    assert result["plan"]["reason"] == "BROKER_NOT_READY"
    assert result["plan"]["targets"] == {}


def test_bad_symbol_and_stale_quote_excluded_from_broker_gate(monkeypatch):
    install_synthetic_parsers(monkeypatch)
    monkeypatch.setattr(
        assembly, "build_live_source_signal_snapshot",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("signal called")),
    )
    observations = broker()
    observations["AUD"]["symbol"] = "EURUSD"
    observations["CAD"]["quote_timestamp_utc"] = utc_iso(AT - timedelta(minutes=6))
    observations["CHF"]["quote_timestamp_utc"] = utc_iso(AT + timedelta(seconds=1))
    observations["EUR"]["volume_step"] = -1.0
    observations["GBP"]["ask"] = 0.5
    record = draft(quotes=observations)
    assert record["broker"]["viable_count"] == 3
    assert record["plan"]["reason"] == "BROKER_NOT_READY"
    assert record["broker"]["currencies"]["AUD"]["quote_viable"] is False


def test_ready_supplied_snapshots_delegate_to_frozen_m028_helpers(monkeypatch, tmp_path):
    install_synthetic_parsers(monkeypatch)
    calls = {"signal": 0, "plan": 0}

    def synthetic_live(**kwargs):
        calls["signal"] += 1
        assert kwargs["decision"] == datetime(2026, 12, 7, 12, tzinfo=timezone.utc)
        assert kwargs["now"] == AT
        return {
            "source": {"approximate_return_panel_sha256": "f" * 64},
            "signal": {
                "decision_id": "2026-12",
                "currencies": {
                    code: {
                        "signal_eligible": True,
                        "formation_value": 1.0,
                        "formation_sign": 1,
                        "annualized_ex_ante_volatility": 0.20,
                    }
                    for code in CURRENCIES
                },
            },
        }

    def synthetic_plan(signal, mapped):
        calls["plan"] += 1
        assert signal["decision_id"] == "2026-12"
        assert set(mapped) == set(CURRENCIES)
        assert all(row["quote_viable"] for row in mapped.values())
        return {
            "status": "FORWARD_PAPER_READY",
            "targets": {code: {"final_target_lots": 0.01} for code in CURRENCIES},
            "cost_evidence": {
                "commission": None,
                "slippage": None,
                "financing": None,
                "net_pnl": None,
            },
        }

    monkeypatch.setattr(assembly, "build_live_source_signal_snapshot", synthetic_live)
    monkeypatch.setattr(assembly, "build_shadow_target_plan", synthetic_plan)
    record = draft()
    assert record["source_gate_pass"] is True
    assert record["broker"]["viable_count"] == 8
    assert record["plan"]["status"] == "FORWARD_PAPER_READY"
    assert calls == {"signal": 1, "plan": 1}
    assert record["source"]["approximate_return_panel_sha256"] == "f" * 64
    assert record["holding_period_return"] is None
    assert record["safety"]["real_order_api_called"] is False

    stored, reused = write_decision(tmp_path, "2026-12", record, now=AT)
    assert reused is False
    assert read_decision(tmp_path, "2026-12") == stored


def test_snapshot_types_required_before_parse(monkeypatch):
    install_synthetic_parsers(monkeypatch)
    with pytest.raises(TypeError, match="raw bytes"):
        assembly.draft_from_supplied_snapshots(
            month_id="2026-12", now=AT,
            bis_raw="not bytes", oecd_raw=b"mock", broker_currencies=broker(),
        )
