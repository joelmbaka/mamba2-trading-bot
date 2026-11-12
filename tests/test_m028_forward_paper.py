"""Tests for the frozen M028 forward-paper contract helpers."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mamba2.backtest.m028_forward_paper import (
    M028_GROSS_LEVERAGE_CAP,
    apply_gross_leverage_cap,
    apply_margin_utilization_cap,
    broker_side,
    decision_record_sha256,
    fifth_weekday_decision,
    paper_entry_price,
    paper_exit_mark,
    raw_portfolio_weights,
    required_source_cutoffs,
    round_lots_toward_zero,
    seal_decision_record,
    source_gate_ready,
    usd_notional_to_lots,
    build_shadow_target_plan,
)


def test_fifth_weekday_decision_is_frozen_at_noon_utc():
    assert fifth_weekday_decision(2026, 10) == datetime(
        2026, 10, 7, 12, 0, tzinfo=timezone.utc
    )
    assert fifth_weekday_decision(2026, 11) == datetime(
        2026, 11, 6, 12, 0, tzinfo=timezone.utc
    )


def test_source_cutoffs_follow_m027_one_month_rate_lag():
    decision = fifth_weekday_decision(2026, 10)
    assert required_source_cutoffs(decision) == {
        "required_spot_through": "2026-09-30",
        "required_rate_month": "2026-08",
    }
    assert source_gate_ready(
        decision,
        spot_max_date="2026-09-30",
        rate_max_month="2026-08",
    )
    assert not source_gate_ready(
        decision,
        spot_max_date="2026-09-29",
        rate_max_month="2026-08",
    )


@pytest.mark.parametrize(
    ("currency", "signal", "expected"),
    [
        ("AUD", 1, "BUY"),
        ("AUD", -1, "SELL"),
        ("EUR", 1, "BUY"),
        ("CAD", 1, "SELL"),
        ("CAD", -1, "BUY"),
        ("JPY", 1, "SELL"),
        ("JPY", -1, "BUY"),
        ("SEK", 0, "FLAT"),
    ],
)
def test_broker_side_preserves_foreign_currency_direction(currency, signal, expected):
    assert broker_side(currency, signal) == expected


def test_raw_weights_match_m027_scaling_then_equal_weight():
    formation = {"AUD": 2.0, "CAD": -3.0, "EUR": 1.0, "JPY": -1.0}
    vol = {"AUD": 0.20, "CAD": 0.10, "EUR": 0.40, "JPY": 0.20}
    weights = raw_portfolio_weights(formation, vol)

    assert weights["AUD"] == pytest.approx((0.40 / 0.20) / 4)
    assert weights["CAD"] == pytest.approx((-0.40 / 0.10) / 4)
    assert weights["EUR"] == pytest.approx((0.40 / 0.40) / 4)
    assert weights["JPY"] == pytest.approx((-0.40 / 0.20) / 4)


def test_gross_cap_uses_one_common_scale():
    weights = {"AUD": 2.0, "CAD": -2.0, "EUR": 2.0}
    scaled, scale = apply_gross_leverage_cap(weights)

    assert scale == pytest.approx(M028_GROSS_LEVERAGE_CAP / 6.0)
    assert sum(abs(value) for value in scaled.values()) == pytest.approx(
        M028_GROSS_LEVERAGE_CAP
    )
    assert scaled["AUD"] / weights["AUD"] == pytest.approx(scale)
    assert scaled["CAD"] / weights["CAD"] == pytest.approx(scale)


def test_lot_conversion_handles_both_quote_orientations():
    aud_lots = usd_notional_to_lots(
        "AUD",
        10_000,
        contract_size=100_000,
        bid=0.6999,
        ask=0.7001,
    )
    cad_lots = usd_notional_to_lots(
        "CAD",
        10_000,
        contract_size=100_000,
        bid=1.3999,
        ask=1.4001,
    )

    assert aud_lots == pytest.approx(10_000 / (100_000 * 0.7))
    assert cad_lots == pytest.approx(0.1)


def test_round_lots_never_rounds_up_and_respects_min_max():
    assert round_lots_toward_zero(
        0.109,
        volume_min=0.01,
        volume_max=500,
        volume_step=0.01,
    ) == pytest.approx(0.10)
    assert round_lots_toward_zero(
        0.009,
        volume_min=0.01,
        volume_max=500,
        volume_step=0.01,
    ) == 0.0
    assert round_lots_toward_zero(
        700,
        volume_min=0.01,
        volume_max=500,
        volume_step=0.01,
    ) == pytest.approx(500.0)


def test_bid_ask_paper_fill_and_exit_mark_are_side_correct():
    assert paper_entry_price("BUY", bid=1.1000, ask=1.1002) == pytest.approx(1.1002)
    assert paper_exit_mark("BUY", bid=1.1000, ask=1.1002) == pytest.approx(1.1000)
    assert paper_entry_price("SELL", bid=1.1000, ask=1.1002) == pytest.approx(1.1000)
    assert paper_exit_mark("SELL", bid=1.1000, ask=1.1002) == pytest.approx(1.1002)


def test_margin_cap_scales_every_position_by_one_factor_then_rounds_down():
    lots = {"AUD": 1.0, "CAD": 1.0, "EUR": 1.0, "JPY": 1.0}
    margin_per_lot = {
        "AUD": 1000.0,
        "CAD": 1000.0,
        "EUR": 1000.0,
        "JPY": 1000.0,
    }
    rules = {
        code: {"volume_min": 0.01, "volume_max": 500.0, "volume_step": 0.01}
        for code in lots
    }

    scaled, scale, final_margin = apply_margin_utilization_cap(
        lots,
        margin_per_lot,
        rules,
    )

    assert scale == pytest.approx(2500 / 4000)
    assert scaled == {
        "AUD": pytest.approx(0.62),
        "CAD": pytest.approx(0.62),
        "EUR": pytest.approx(0.62),
        "JPY": pytest.approx(0.62),
    }
    assert final_margin == pytest.approx(2480.0)


def test_decision_record_hash_is_canonical_and_sealed():
    a = {"decision": "2026-10-07T12:00:00Z", "currencies": ["AUD", "CAD"]}
    b = {"currencies": ["AUD", "CAD"], "decision": "2026-10-07T12:00:00Z"}

    assert decision_record_sha256(a) == decision_record_sha256(b)
    sealed = seal_decision_record(a)
    assert sealed["decision_record_sha256"] == decision_record_sha256(sealed)



def _synthetic_signal_snapshot(vol=0.20):
    currencies = {}
    for index, code in enumerate(
        ("AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "SEK")
    ):
        sign = 1 if index % 2 == 0 else -1
        currencies[code] = {
            "signal_eligible": True,
            "formation_value": float(sign),
            "formation_sign": sign,
            "annualized_ex_ante_volatility": vol,
        }
    return {"currencies": currencies}


def _synthetic_broker_snapshot():
    prices = {
        "AUD": (0.6999, 0.7001),
        "CAD": (1.3999, 1.4001),
        "CHF": (0.7999, 0.8001),
        "EUR": (1.0999, 1.1001),
        "GBP": (1.2999, 1.3001),
        "JPY": (149.99, 150.01),
        "NZD": (0.5999, 0.6001),
        "SEK": (9.999, 10.001),
    }
    result = {}
    for code, (bid, ask) in prices.items():
        result[code] = {
            "quote_viable": True,
            "bid": bid,
            "ask": ask,
            "contract_size": 100_000.0,
            "volume_min": 0.01,
            "volume_max": 500.0,
            "volume_step": 0.01,
            "buy_margin_per_lot": 1000.0,
            "sell_margin_per_lot": 1000.0,
        }
    return result


def test_shadow_target_plan_builds_ready_eight_currency_portfolio():
    result = build_shadow_target_plan(
        _synthetic_signal_snapshot(),
        _synthetic_broker_snapshot(),
    )

    assert result["status"] == "FORWARD_PAPER_READY"
    assert result["eligible_count"] == 8
    assert result["gross_scale"] == pytest.approx(1.0)
    assert result["projected_margin_usd"] > 0
    assert result["projected_margin_usd"] <= 2500.0
    assert result["cost_evidence"]["net_pnl"] is None
    assert all(
        row["final_target_lots"] > 0
        for row in result["targets"].values()
    )


def test_shadow_target_plan_applies_common_gross_cap():
    result = build_shadow_target_plan(
        _synthetic_signal_snapshot(vol=0.05),
        _synthetic_broker_snapshot(),
    )

    assert result["status"] == "FORWARD_PAPER_READY"
    assert result["gross_leverage_before_cap"] == pytest.approx(8.0)
    assert result["gross_leverage_after_cap"] == pytest.approx(4.0)
    assert result["gross_scale"] == pytest.approx(0.5)


def test_shadow_target_plan_flattens_when_broker_gate_drops_below_four():
    broker = _synthetic_broker_snapshot()
    for code in ("GBP", "JPY", "NZD", "SEK", "EUR"):
        broker[code]["quote_viable"] = False

    result = build_shadow_target_plan(
        _synthetic_signal_snapshot(),
        broker,
    )

    assert result["status"] == "FORWARD_PAPER_NOT_READY"
    assert result["reason"] == "FEWER_THAN_4_PRE_SIZING_ELIGIBLE"
    assert result["eligible_count"] == 3
    assert result["targets"] == {}
